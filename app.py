from flask import Flask, render_template, render_template_string, jsonify
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
            # Test the connection
            with self._driver.session() as session:
                session.run("RETURN 1").single()
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

class UI_Design:
    def __init__(self):
        self.db = Neo4jConnection()

    def get_initial_data(self):
        try:
            with self.db.get_session() as session:
                # Get all anatomical regions for the dropdown
                locations_query = """
                    MATCH (n)
                    WITH DISTINCT n.location as location
                    WHERE location IS NOT NULL
                    RETURN location
                    ORDER BY location
                """
                locations = session.run(locations_query).values()
                
                # Get all node types for filtering
                types_query = """
                    MATCH (n)
                    WITH DISTINCT labels(n)[0] as type
                    RETURN type
                    ORDER BY type
                """
                node_types = session.run(types_query).values()
                
                # Get relationship types
                rels_query = """
                    MATCH ()-[r]->()
                    WITH DISTINCT type(r) as type
                    RETURN type
                    ORDER BY type
                """
                rel_types = session.run(rels_query).values()
                
                return {
                    'locations': [loc[0] for loc in locations],
                    'node_types': [type[0] for type in node_types],
                    'relationship_types': [rel[0] for rel in rel_types]
                }
        except ServiceUnavailable as e:
            logger.error(f"Database connection error: {str(e)}")
            return {'error': 'Database connection error', 'locations': [], 'node_types': [], 'relationship_types': []}
        except Exception as e:
            logger.error(f"Error getting initial data: {str(e)}")
            return {'error': 'Internal server error', 'locations': [], 'node_types': [], 'relationship_types': []}

    def close(self):
        self.db.close()

# HTML template (your existing template code here)
html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Anatomical Pathway Explorer</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/dist/vis-network.min.css">
    <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/vis-network.min.js"></script>
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
        .main-content {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .network-container {
            width: 100%;
            height: 600px;
            border: 1px solid #ddd;
        }
        .search-box {
            margin-bottom: 15px;
        }
        .filter-section {
            margin-bottom: 20px;
        }
        .button {
            background-color: #CC5500;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            width: 100%;
            margin-bottom: 10px;
        }
        .button:hover {
            background-color: #A34400;
        }
        select, input {
            width: 100%;
            padding: 8px;
            margin-bottom: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .error-message {
            color: red;
            padding: 10px;
            margin: 10px 0;
            background-color: #ffebee;
            border-radius: 4px;
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <div class="search-box">
                <h3>Source Node</h3>
                <input type="text" id="source-search" placeholder="Search source node...">
                <select id="source-type">
                    <option value="">Select Type</option>
                    {% for type in node_types %}
                    <option value="{{ type }}">{{ type }}</option>
                    {% endfor %}
                </select>
                <select id="source-location">
                    <option value="">Select Location</option>
                    {% for location in locations %}
                    <option value="{{ location }}">{{ location }}</option>
                    {% endfor %}
                </select>
            </div>
            
            <div class="search-box">
                <h3>Target Node</h3>
                <input type="text" id="target-search" placeholder="Search target node...">
                <select id="target-type">
                    <option value="">Select Type</option>
                    {% for type in node_types %}
                    <option value="{{ type }}">{{ type }}</option>
                    {% endfor %}
                </select>
                <select id="target-location">
                    <option value="">Select Location</option>
                    {% for location in locations %}
                    <option value="{{ location }}">{{ location }}</option>
                    {% endfor %}
                </select>
            </div>
            
            <div class="filter-section">
                <h3>Relationship Types</h3>
                <select id="relationship-types" multiple>
                    {% for rel_type in relationship_types %}
                    <option value="{{ rel_type }}">{{ rel_type }}</option>
                    {% endfor %}
                </select>
            </div>
            
            <button class="button" onclick="findPath()">Find Pathway</button>
            <button class="button" onclick="clearVisualization()">Clear</button>
        </div>
        
        <div class="main-content">
            <div id="error-message" class="error-message"></div>
            <div id="network-container" class="network-container"></div>
            <div id="path-details"></div>
        </div>
    </div>

    <script>
        // Initialize network visualization
        var container = document.getElementById('network-container');
        var data = {
            nodes: new vis.DataSet([]),
            edges: new vis.DataSet([])
        };
        var options = {
            nodes: {
                shape: 'dot',
                size: 16
            },
            edges: {
                arrows: 'to'
            },
            physics: {
                enabled: true,
                solver: 'forceAtlas2Based',
                forceAtlas2Based: {
                    gravitationalConstant: -26,
                    centralGravity: 0.005,
                    springLength: 230,
                    springConstant: 0.18
                },
                maxVelocity: 146,
                minVelocity: 0.75,
                timestep: 0.5
            }
        };
        var network = new vis.Network(container, data, options);

        function showError(message) {
            const errorDiv = document.getElementById('error-message');
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        }

        function hideError() {
            document.getElementById('error-message').style.display = 'none';
        }

        function findPath() {
            hideError();
            const sourceNode = document.getElementById('source-search').value;
            const targetNode = document.getElementById('target-search').value;
            
            if (!sourceNode || !targetNode) {
                showError('Please select both source and target nodes');
                return;
            }

            // Add API call to backend here
            fetch('/api/find_path', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    source: sourceNode,
                    target: targetNode,
                    relationshipTypes: Array.from(document.getElementById('relationship-types').selectedOptions).map(opt => opt.value)
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showError(data.error);
                } else {
                    updateVisualization(data);
                }
            })
            .catch(error => {
                showError('Error finding pathway: ' + error.message);
            });
        }

        function clearVisualization() {
            data.nodes.clear();
            data.edges.clear();
            document.getElementById('path-details').innerHTML = '';
            hideError();
        }

        function updateVisualization(pathData) {
            // Implementation for updating the visualization
            // This will be implemented when we add the backend path finding logic
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    try:
        ui = UI_Design()
        data = ui.get_initial_data()
        ui.close()
        
        if 'error' in data:
            logger.error(f"Error in index route: {data['error']}")
            return render_template_string(html_template, 
                                       locations=[], 
                                       node_types=[], 
                                       relationship_types=[],
                                       error=data['error'])
        
        return render_template_string(html_template, **data)
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        return render_template_string(html_template, 
                                   locations=[], 
                                   node_types=[], 
                                   relationship_types=[],
                                   error="Failed to connect to database")

@app.route('/api/find_path', methods=['POST'])
def find_path():
    try:
        data = request.json
        ui = UI_Design()
        # Implement path finding logic here
        ui.close()
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error finding path: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
