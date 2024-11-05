from flask import Flask, render_template_string, jsonify
from datetime import datetime
import os
import logging
import json
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Define the HTML template
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
                container.title = `Type: ${node.properties.type}\nLocation: ${node.properties.location}`;
            });
            
            updateFilters(data.nodes);
            updateNodeList(data.nodes);
        }

        function updateFilters(nodes) {
            const locations = [...new Set(nodes.map(n => n.properties.location).filter(Boolean))];
            const types = [...new Set(nodes.map(n => n.properties.type).filter(Boolean))];
            
            ['locationFilter', 'typeFilter'].forEach((id, i) => {
                const select = document.getElementById(id);
                const values = i === 0 ? locations : types;
                select.innerHTML = `<option value="">${id === 'locationFilter' ? 'Filter by Location' : 'Filter by Type'}</option>`;
                values.sort().forEach(v => select.add(new Option(v, v)));
            });
        }

        function updateNodeList(nodes) {
            const tbody = document.getElementById('nodeListBody');
            tbody.innerHTML = nodes.map(node => `
                <tr>
                    <td>${node.id}</td>
                    <td>${node.label}</td>
                    <td>${node.properties.type || ''}</td>
                    <td>${node.properties.location || ''}</td>
                </tr>
            `).join('');
        }

        function toggleNodeList() {
            const nodeList = document.getElementById('nodeList');
            nodeList.style.display = nodeList.style.display === 'none' ? 'block' : 'none';
        }

        function applyFilters() {
            const location = document.getElementById('locationFilter').value;
            const type = document.getElementById('typeFilter').value;

            const filteredNodes = allNodes.filter(node => 
                (!location || node.properties.location === location) &&
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
            ['locationFilter', 'typeFilter'].forEach(id => 
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

        ['locationFilter', 'typeFilter'].forEach(id =>
            document.getElementById(id).addEventListener('change', applyFilters)
        );
    </script>
</body>
</html>'''

@app.route('/')
def home():
    return render_template_string(html_template)

@app.route('/refresh-data')
def refresh_data():
    nodes = []
    edges = []
    
    # Define meaningful locations and types
    locations = ['San Francisco', 'New York', 'London', 'Tokyo', 'Singapore']
    node_types = ['Server', 'Database', 'Client']
    
    
    # Load data from StrokeChaser.xlsx
    import pandas as pd
    df = pd.read_excel('StrokeChaser.xlsx')

    # Extract nodes and their properties
    nodes = []
    for index, row in df.iterrows():
        nodes.append({
            'id': str(index),
            'label': row['Node'],
            'properties': {
                'location': row['Location'],
                'sublocation': row['Sublocation'],
                'type': row['Type']
            }
        })

    # Generate edges based on some logic (e.g., same location or type)
    edges = []
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            if nodes[i]['properties']['location'] == nodes[j]['properties']['location']:
                edges.append({
                    'from': nodes[i]['id'],
                    'to': nodes[j]['id'],
                    'label': 'SAME_LOCATION'
                })
            elif nodes[i]['properties']['type'] == nodes[j]['properties']['type']:
                edges.append({
                    'from': nodes[i]['id'],
                    'to': nodes[j]['id'],
                    'label': 'SAME_TYPE'
                })

    # Return the response with properly formatted JSON
    return jsonify({
        'success': True,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'graph_data': {
            'nodes': nodes,
            'edges': edges
        },
        'filters': {
            'locations': df['Location'].unique().tolist(),
            'types': df['Type'].unique().tolist()
        }
    })
return jsonify({
        'success': True,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'graph_data': {
            'nodes': nodes,
            'edges': edges
        },
        'filters': {
            'locations': locations,
            'types': node_types
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
