from flask import Flask, render_template_string, jsonify
from datetime import datetime
import os
import logging
from neo4j import GraphDatabase
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Neo4j Configuration
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'password')

# Initialize Neo4j driver
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

html_template = '''<!DOCTYPE html>
<html>
<head>
    <title>Network Viewer</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        #graph-container {
            height: 600px;
            border: 1px solid #ddd;
            background-color: #f8f9fa;
        }
        .node-info {
            padding: 10px;
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <h2 class="mb-4">Network Visualization</h2>
                <div class="mb-3">
                    <select id="locationFilter" class="form-select d-inline-block w-auto me-2">
                        <option value="">Filter by Location</option>
                    </select>
                    <select id="sublocationFilter" class="form-select d-inline-block w-auto me-2">
                        <option value="">Filter by Sublocation</option>
                    </select>
                    <select id="typeFilter" class="form-select d-inline-block w-auto me-2">
                        <option value="">Filter by Type</option>
                    </select>
                    <button class="btn btn-secondary" onclick="clearFilters()">Clear Filters</button>
                    <button class="btn btn-primary ms-2" onclick="toggleNodeList()">Toggle Node List</button>
                </div>
                <div id="graph-container"></div>
                <div id="nodeList" style="display: none;" class="mt-3">
                    <h3>Node List</h3>
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Label</th>
                                <th>Type</th>
                                <th>Location</th>
                                <th>Sublocation</th>
                            </tr>
                        </thead>
                        <tbody id="nodeListBody"></tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script>
        let network, allNodes = [], allEdges = [];

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
                    borderWidth: 2,
                    shadow: true
                },
                edges: {
                    width: 2,
                    color: {
                        color: '#2B7CE9',
                        highlight: '#1B4C89',
                        hover: '#1B4C89'
                    },
                    smooth: {
                        type: 'continuous'
                    }
                },
                physics: {
                    stabilization: true,
                    barnesHut: {
                        gravitationalConstant: -80000,
                        springConstant: 0.001,
                        springLength: 200
                    }
                },
                interaction: {
                    hover: true,
                    tooltipDelay: 200
                }
            };
            
            network = new vis.Network(container, data, options);
            network.on('hoverNode', function(params) {
                const node = data.nodes.get(params.node);
                container.title = `Type: ${node.properties.type}\nLocation: ${node.properties.location}\nSublocation: ${node.properties.sublocation}`;
            });
            
            updateFilters(data.nodes);
            updateNodeList(data.nodes);
        }

        function updateFilters(nodes) {
            const locations = [...new Set(nodes.map(n => n.properties.location).filter(Boolean))];
            const sublocations = [...new Set(nodes.map(n => n.properties.sublocation).filter(Boolean))];
            const types = [...new Set(nodes.map(n => n.properties.type).filter(Boolean))];
            
            const updateSelect = (id, values) => {
                const select = document.getElementById(id);
                const placeholder = select.options[0].text;
                select.innerHTML = `<option value="">${placeholder}</option>`;
                values.sort().forEach(v => select.add(new Option(v, v)));
            };

            updateSelect('locationFilter', locations);
            updateSelect('sublocationFilter', sublocations);
            updateSelect('typeFilter', types);
        }

        function updateNodeList(nodes) {
            const tbody = document.getElementById('nodeListBody');
            tbody.innerHTML = nodes.map(node => `
                <tr>
                    <td>${node.id}</td>
                    <td>${node.label}</td>
                    <td>${node.properties.type || ''}</td>
                    <td>${node.properties.location || ''}</td>
                    <td>${node.properties.sublocation || ''}</td>
                </tr>
            `).join('');
        }

        function toggleNodeList() {
            const nodeList = document.getElementById('nodeList');
            nodeList.style.display = nodeList.style.display === 'none' ? 'block' : 'none';
        }

        function applyFilters() {
            const location = document.getElementById('locationFilter').value;
            const sublocation = document.getElementById('sublocationFilter').value;
            const type = document.getElementById('typeFilter').value;

            const filteredNodes = allNodes.filter(node => 
                (!location || node.properties.location === location) &&
                (!sublocation || node.properties.sublocation === sublocation) &&
                (!type || node.properties.type === type)
            );

            network.setData({
                nodes: new vis.DataSet(filteredNodes),
                edges: new vis.DataSet(allEdges.filter(edge =>
                    filteredNodes.some(n => n.id === edge.from) &&
                    filteredNodes.some(n => n.id === edge.to)
                ))
            });
            updateNodeList(filteredNodes);
        }

        function clearFilters() {
            ['locationFilter', 'sublocationFilter', 'typeFilter'].forEach(id => 
                document.getElementById(id).value = ''
            );
            network.setData({
                nodes: new vis.DataSet(allNodes),
                edges: new vis.DataSet(allEdges)
            });
            updateNodeList(allNodes);
        }

        fetch('/refresh-data')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    allNodes = data.graph_data.nodes;
                    allEdges = data.graph_data.edges;
                    initNetwork({
                        nodes: new vis.DataSet(allNodes),
                        edges: new vis.DataSet(allEdges)
                    });
                }
            })
            .catch(error => console.error('Error loading data:', error));

        ['locationFilter', 'sublocationFilter', 'typeFilter'].forEach(id =>
            document.getElementById(id).addEventListener('change', applyFilters)
        );
    </script>
</body>
</html>'''

def get_graph_data():
    with driver.session() as session:
        # Query to get all nodes with their properties
        nodes_query = '''
        MATCH (n)
        RETURN id(n) as id, 
               labels(n)[0] as label, 
               properties(n) as properties
        '''
        
        # Query to get all relationships
        edges_query = '''
        MATCH (n)-[r]->(m)
        RETURN id(n) as source, 
               id(m) as target,
               type(r) as type
        '''
        
        # Execute queries
        nodes_result = session.run(nodes_query)
        edges_result = session.run(edges_query)
        
        # Process nodes
        nodes = []
        for record in nodes_result:
            node = {
                'id': str(record['id']),
                'label': record['properties'].get('name', record['label']),
                'properties': {
                    'type': record['label'],
                    'location': record['properties'].get('location', ''),
                    'sublocation': record['properties'].get('sublocation', ''),
                    'direction': record['properties'].get('direction', ''),
                }
            }
            nodes.append(node)
        
        # Process relationships
        edges = []
        for record in edges_result:
            edge = {
                'from': str(record['source']),
                'to': str(record['target']),
                'label': record['type']
            }
            edges.append(edge)
            
        return {'nodes': nodes, 'edges': edges}

@app.route('/')
def home():
    return render_template_string(html_template)

@app.route('/refresh-data')
def refresh_data():
    try:
        graph_data = get_graph_data()
        return jsonify({
            'success': True,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'graph_data': graph_data
        })
    except Exception as e:
        logger.error(f"Error refreshing data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
