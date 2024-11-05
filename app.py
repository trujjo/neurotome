
from flask import Flask, render_template_string, jsonify
from datetime import datetime
import os
import logging
import json

app = Flask(__name__)

@app.route('/')
def home():
    return render_template_string(html_template)

@app.route('/refresh-data')
def refresh_data():
    # Example data - in a real application, this would pull from your database
    # without any limit
    nodes = []
    edges = []
    
    # Generate more test data
    for i in range(1, 501):  # Increased to 500 nodes for testing
        nodes.append({
            'id': str(i),
            'label': 'Node ' + str(i),
            'properties': {
                'location': 'Location ' + str((i % 5) + 1),  # 5 different locations
                'type': 'Type ' + str((i % 3) + 1)  # 3 different types
            }
        })
        
        # Create edges (connecting each node to several others)
        if i > 1:
            # Connect to previous node
            edges.append({
                'from': str(i),
                'to': str(i-1),
                'label': 'CONNECTS_TO'
            })
            # Connect to a random earlier node
            if i > 10:
                import random
                random_target = random.randint(1, i-2)
                edges.append({
                    'from': str(i),
                    'to': str(random_target),
                    'label': 'CONNECTS_TO'
                })    return jsonify({
        'success': True,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'graph_data': {'nodes': nodes, 'edges': edges},
        'filters': {
            'locations': ['A', 'B'],
            'types': ['Type1', 'Type2']
        }
    })

html_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Network Viewer</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
</head>
<body>
    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <div class="mb-3">
                    <select id="locationFilter" class="form-select d-inline-block w-auto me-2">
                        <option value="">Filter by Location</option>
                    </select>
                    <select id="typeFilter" class="form-select d-inline-block w-auto me-2">
                        <option value="">Filter by Type</option>
                    </select>
                    <button class="btn btn-secondary" onclick="clearFilters()">Clear Filters</button>
                    <button class="btn btn-primary ms-2" onclick="toggleNodeList()">View All</button>
                </div>
                <div id="graph-container" style="height: 600px; border: 1px solid #ddd;"></div>
                <div id="nodeList" style="display: none;" class="mt-3">
                    <table class="table">
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
            network = new vis.Network(container, data, {
                nodes: {shape: 'dot', size: 30},
                physics: {enabled: true}
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
                values.forEach(v => select.add(new Option(v, v)));
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
            });

        ['locationFilter', 'typeFilter'].forEach(id =>
            document.getElementById(id).addEventListener('change', applyFilters)
        );
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True)
