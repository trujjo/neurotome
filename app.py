from flask import Flask, render_template, render_template_string, jsonify, request
from neo4j import GraphDatabase
import logging
from neo4j.exceptions import ServiceUnavailable

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Neo4j connection configuration
NEO4J_URI = "bolt://4e5eeae5.databases.neo4j.io:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "Poconoco16!"

# HTML template with JavaScript for handling the path finding
html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Anatomical Pathway Explorer</title>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body { 
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            display: grid;
            grid-template-columns: 300px 1fr;
            gap: 20px;
        }
        .sidebar {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .visualization {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            height: 600px;
        }
        #network {
            width: 100%;
            height: 100%;
            border: 1px solid #ddd;
        }
        select, input, button {
            width: 100%;
            padding: 8px;
            margin: 5px 0;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        button {
            background-color: #CC5500;
            color: white;
            border: none;
            cursor: pointer;
        }
        button:hover {
            background-color: #A34400;
        }
        #path-details {
            margin-top: 20px;
            padding: 10px;
            background: #f8f8f8;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <h3>Path Finder</h3>
            <select id="source-node">
                <option value="">Select Source Node</option>
                {% for node in nodes %}
                    <option value="{{ node }}">{{ node }}</option>
                {% endfor %}
            </select>
            
            <select id="target-node">
                <option value="">Select Target Node</option>
                {% for node in nodes %}
                    <option value="{{ node }}">{{ node }}</option>
                {% endfor %}
            </select>
            
            <button onclick="findPath()">Find Pathway</button>
            <button onclick="clearVisualization()">Clear</button>
            
            <div id="path-details"></div>
        </div>
        
        <div class="visualization">
            <div id="network"></div>
        </div>
    </div>

    <script>
        let network = null;
        let nodes = new vis.DataSet();
        let edges = new vis.DataSet();
        
        // Initialize the network visualization
        function initNetwork() {
            const container = document.getElementById('network');
            const data = {
                nodes: nodes,
                edges: edges
            };
            const options = {
                nodes: {
                    shape: 'dot',
                    size: 16
                },
                edges: {
                    arrows: 'to',
                    smooth: {
                        type: 'cubicBezier'
                    }
                },
                physics: {
                    stabilization: true,
                    barnesHut: {
                        gravitationalConstant: -80000,
                        springConstant: 0.001,
                        springLength: 200
                    }
                }
            };
            
            network = new vis.Network(container, data, options);
        }
        
        // Find the path between selected nodes
        function findPath() {
            const source = document.getElementById('source-node').value;
            const target = document.getElementById('target-node').value;
            
            if (!source || !target) {
                alert('Please select both source and target nodes');
                return;
            }
            
            fetch('/api/find_path', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    source: source,
                    target: target
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    document.getElementById('path-details').innerHTML = `Error: ${data.error}`;
                    return;
                }
                visualizePath(data.path);
            })
            .catch(error => {
                console.error('Error:', error);
                document.getElementById('path-details').innerHTML = `Error: ${error.message}`;
            });
        }
        
        // Visualize the path in the network
        function visualizePath(path) {
            nodes.clear();
            edges.clear();
            
            // Add nodes and edges from the path
            path.segments.forEach((segment, index) => {
                nodes.add({
                    id: segment.start.identity,
                    label: segment.start.properties.name,
                    title: segment.start.properties.name
                });
                
                if (index === path.segments.length - 1) {
                    nodes.add({
                        id: segment.end.identity,
                        label: segment.end.properties.name,
                        title: segment.end.properties.name
                    });
                }
                
                edges.add({
                    from: segment.start.identity,
                    to: segment.end.identity,
                    label: segment.relationship.type
                });
            });
            
            // Update path details
            const pathDetails = document.getElementById('path-details');
            pathDetails.innerHTML = `Path found with ${path.segments.length} steps`;
        }
        
        function clearVisualization() {
            nodes.clear();
            edges.clear();
            document.getElementById('path-details').innerHTML = '';
        }
        
        // Initialize the network when the page loads
        window.addEventListener('load', initNetwork);
    </script>
</body>
</html>
"""

class Neo4jConnection:
    def __init__(self):
        self._driver = None
        self.connect()

    def connect(self):
        try:
            self._driver = GraphDatabase.driver(
                NEO4J_URI,
                auth=(NEO4J_USER, NEO4J_PASSWORD),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_timeout=5
            )
            logger.info("Successfully connected to Neo4j database")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {str(e)}")
            self._driver = None
            raise

    def close(self):
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def get_session(self):
        if not self._driver:
            self.connect()
        return self._driver.session()

def get_all_nodes():
    try:
        connection = Neo4jConnection()
        with connection.get_session() as session:
            result = session.run("MATCH (n) RETURN DISTINCT n.name AS name ORDER BY name")
            nodes = [record["name"] for record in result]
        connection.close()
        return nodes
    except Exception as e:
        logger.error(f"Error getting nodes: {str(e)}")
        return []

@app.route('/')
def index():
    try:
        nodes = get_all_nodes()
        return render_template_string(html_template, nodes=nodes)
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        return render_template_string(html_template, nodes=[], error="Failed to connect to database")

@app.route('/api/find_path', methods=['POST'])
def find_path():
    try:
        data = request.json
        source_name = data.get('source')
        target_name = data.get('target')
        
        connection = Neo4jConnection()
        with connection.get_session() as session:
            query = """
            MATCH (source {name: $source_name})
            MATCH (target {name: $target_name})
            MATCH path = shortestPath((source)-[*]->(target))
            RETURN path
            """
            result = session.run(query, source_name=source_name, target_name=target_name)
            path = result.single()
            
        connection.close()
        
        if path:
            return jsonify({'path': path['path']})
        else:
            return jsonify({'error': 'No path found'}), 404
    except Exception as e:
        logger.error(f"Error finding path: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
