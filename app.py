
from flask import Flask, render_template_string, jsonify
from py2neo import Graph
from datetime import datetime
import os
from dotenv import load_dotenv
import json
import logging
import ssl

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Neo4j connection configuration
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://4e5eeae5.databases.neo4j.io:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'Poconoco16!')

# HTML template as a separate string
html_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Neuronetwork Viewer</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        .container { margin-top: 20px; }
        .search-box { margin-bottom: 20px; }
        .refresh-section { margin-bottom: 20px; }
        .last-updated { font-size: 0.9em; color: #666; }
        #graph-container { 
            height: 600px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background-color: #f8f9fa;
        }
        .controls {
            margin-bottom: 20px;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">Neuronetwork Explorer</a>
            <div class="d-flex">
                <span class="navbar-text text-light me-3">
                    Last updated: <span id="lastUpdated">Never</span>
                </span>
                <button id="refreshButton" class="btn btn-outline-light">
                    Refresh Data
                </button>
            </div>
        </div>
    </nav>
    
    <div class="container">
        <div class="row">
            <div class="col-md-12">
                <div class="controls">
                    <div class="row">
                        <div class="col-md-4">
                            <input type="text" id="searchInput" class="form-control" placeholder="Search nodes...">
                        </div>
                        <div class="col-md-8">
                            <button class="btn btn-secondary me-2" onclick="zoomIn()">Zoom In</button>
                            <button class="btn btn-secondary me-2" onclick="zoomOut()">Zoom Out</button>
                            <button class="btn btn-secondary me-2" onclick="centerGraph()">Center</button>
                            <button class="btn btn-info me-2" onclick="togglePhysics()">Toggle Physics</button>
                        </div>
                    </div>
                </div>
                <div id="graph-container"></div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let network;
        let physicsEnabled = true;

        function initNetwork(data) {
            const container = document.getElementById('graph-container');
            const options = {
                nodes: {
                    shape: 'dot',
                    size: 30,
                    font: {
                        size: 12,
                        color: '#333'
                    },
                    borderWidth: 2
                },
                edges: {
                    width: 2,
                    arrows: {
                        to: { enabled: true, scaleFactor: 1 }
                    }
                },
                physics: {
                    enabled: true,
                    barnesHut: {
                        gravitationalConstant: -2000,
                        centralGravity: 0.3,
                        springLength: 95
                    }
                }
            };

            network = new vis.Network(container, data, options);
            
            network.on('selectNode', function(params) {
                if (params.nodes.length > 0) {
                    const nodeId = params.nodes[0];
                    const node = data.nodes.get(nodeId);
                    alert(`Node Details:\nID: ${node.id}\nLabel: ${node.label}\nProperties: ${JSON.stringify(node.properties, null, 2)}`);
                }
            });
        }

        function zoomIn() {
            network.moveTo({
                scale: network.getScale() * 1.2
            });
        }

        function zoomOut() {
            network.moveTo({
                scale: network.getScale() * 0.8
            });
        }

        function centerGraph() {
            network.fit({
                animation: true
            });
        }

        function togglePhysics() {
            physicsEnabled = !physicsEnabled;
            network.setOptions({ physics: { enabled: physicsEnabled } });
        }

        document.getElementById('searchInput').addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const allNodes = network.body.data.nodes.get();
            const matchingNodes = allNodes.filter(node => 
                node.label.toLowerCase().includes(searchTerm) ||
                JSON.stringify(node.properties).toLowerCase().includes(searchTerm)
            );
            
            network.selectNodes(matchingNodes.map(n => n.id));
            if (matchingNodes.length > 0) {
                network.focus(matchingNodes[0].id, {
                    scale: 1.2,
                    animation: true
                });
            }
        });

        document.getElementById('refreshButton').addEventListener('click', function() {
            this.disabled = true;
            this.innerHTML = 'Refreshing...';
            
            fetch('/refresh-data')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('lastUpdated').textContent = data.timestamp;
                    if (data.success) {
                        initNetwork(data.graph_data);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Error refreshing data. Please try again.');
                })
                .finally(() => {
                    this.disabled = false;
                    this.innerHTML = 'Refresh Data';
                });
        });

        fetch('/refresh-data').then(response => response.json()).then(data => {
            if (data.success) {
                initNetwork(data.graph_data);
                document.getElementById('lastUpdated').textContent = data.timestamp;
            }
        });
    </script>
</body>
</html>
'''

def get_neo4j_connection():
    try:
        logger.info(f"Attempting to connect to Neo4j at {NEO4J_URI}")
        graph = Graph(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
            secure=True,
            verify=True
        )
        # Test the connection
        graph.run("MATCH (n) RETURN count(n) LIMIT 1").data()
        logger.info("Successfully connected to Neo4j")
        return graph
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {str(e)}")
        raise

def get_neo4j_data():
    try:
        graph = get_neo4j_connection()
        
        # Query to get nodes and relationships
        query = '''
        MATCH (n)-[r]->(m)
        RETURN DISTINCT 
            id(n) as source_id, 
            labels(n) as source_labels,
            properties(n) as source_props,
            type(r) as relationship_type,
            id(m) as target_id,
            labels(m) as target_labels,
            properties(m) as target_props
        LIMIT 100
        '''
        
        logger.info("Executing Neo4j query")
        results = graph.run(query).data()
        logger.info(f"Query returned {len(results)} results")
        
        # Process results into vis.js format
        nodes = {}
        edges = []
        
        for record in results:
            # Process source node
            source_id = str(record['source_id'])
            if source_id not in nodes:
                nodes[source_id] = {
                    'id': source_id,
                    'label': record['source_labels'][0],
                    'properties': record['source_props'],
                    'color': '#97c2fc'
                }
            
            # Process target node
            target_id = str(record['target_id'])
            if target_id not in nodes:
                nodes[target_id] = {
                    'id': target_id,
                    'label': record['target_labels'][0],
                    'properties': record['target_props'],
                    'color': '#97c2fc'
                }
            
            # Process relationship
            edges.append({
                'from': source_id,
                'to': target_id,
                'label': record['relationship_type'],
                'arrows': 'to'
            })
        
        graph_data = {
            'nodes': list(nodes.values()),
            'edges': edges
        }
        
        return True, graph_data
    except Exception as e:
        logger.error(f"Error in get_neo4j_data: {str(e)}")
        return False, str(e)

@app.route('/')
def home():
    return render_template_string(html_template)

@app.route('/refresh-data')
def refresh_data():
    success, data = get_neo4j_data()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    response_data = {
        'success': success,
        'timestamp': timestamp,
        'message': 'Data refreshed successfully' if success else f'Error: {data}',
        'graph_data': data if success else None
    }
    logger.info(f"Refresh data response: {response_data['message']}")
    return jsonify(response_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
