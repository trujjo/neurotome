<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Neo4j Network Visualization</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body, html {
            margin: 0;
            padding: 0;
            height: 100%;
            font-family: Arial, sans-serif;
        }
        .container {
            display: flex;
            height: 100%;
        }
        .sidebar {
            width: 250px;
            padding: 20px;
            background-color: #f5f5f5;
            overflow-y: auto;
        }
        .visualization {
            flex-grow: 1;
            position: relative;
        }
        #mynetwork {
            width: 100%;
            height: 100%;
            position: absolute;
        }
        .button-group {
            margin-bottom: 20px;
        }
        .button-group h3 {
            margin-bottom: 10px;
        }
        button {
            background-color: #CC5500;  /* Burnt Orange */
            color: white;
            border: none;
            padding: 8px 16px;
            margin: 4px;
            border-radius: 4px;
            cursor: pointer;
            transition: opacity 0.3s;
        }
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        button:hover:not(:disabled) {
            opacity: 0.8;
        }
        .filter-button {
            background-color: #CC5500;
        }
        .clear-button {
            background-color: #ff3333;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <div class="button-group">
                <h3>Node Types</h3>
                {% for node_type in metadata.node_types %}
                <button onclick="addNodesByType('{{ node_type }}')">{{ node_type }}</button>
                {% endfor %}
            </div>

            <div class="button-group">
                <h3>Locations</h3>
                {% for location in metadata.locations %}
                <button class="filter-button" data-criteria="location" data-value="{{ location }}" 
                        onclick="filterByLocation('{{ location }}')">{{ location }}</button>
                {% endfor %}
            </div>

            <div class="button-group">
                <h3>Sublocations</h3>
                {% for sublocation in metadata.sublocations %}
                <button class="filter-button" data-criteria="sublocation" data-value="{{ sublocation }}"
                        onclick="filterBySublocation('{{ sublocation }}')">{{ sublocation }}</button>
                {% endfor %}
            </div>

            <div class="button-group">
                <h3>Relationships</h3>
                {% for rel_type in metadata.relationship_types %}
                <button class="filter-button" data-criteria="relationship" data-value="{{ rel_type }}"
                        onclick="filterByRelationship('{{ rel_type }}')">{{ rel_type }}</button>
                {% endfor %}
            </div>

            <button class="clear-button" onclick="clearNetwork()">Clear All</button>
        </div>
        
        <div class="visualization">
            <div id="mynetwork"></div>
        </div>
    </div>

    <script type="text/javascript">
        // Create a network visualization
        var container = document.getElementById('mynetwork');
        var nodes = new vis.DataSet([]);
        var edges = new vis.DataSet([]);
        
        var data = {
            nodes: nodes,
            edges: edges
        };
        
        var options = {
            nodes: {
                shape: 'dot',
                size: 30,
                font: {
                    size: 14
                }
            },
            edges: {
                font: {
                    size: 14,
                    align: 'middle'
                },
                arrows: 'to',
                color: {
                    color: '#848484',
                    highlight: '#848484',
                    hover: '#848484'
                },
                width: 2
            },
            physics: {
                enabled: false
            }
        };
        
        var network = new vis.Network(container, data, options);

        // Network manipulation functions
        function addNodesByType(nodeType) {
            fetch('/get_nodes', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    node_type: nodeType
                })
            })
            .then(response => response.json())
            .then(newNodes => {
                nodes.update(newNodes);
                updateFilterButtons();
            });
        }

        function filterByLocation(location) {
            const visibleNodes = nodes.get().filter(node => 
                JSON.parse(node.title).location === location
            );
            nodes.update(visibleNodes.map(node => ({...node, hidden: false})));
            nodes.update(nodes.get().filter(node => 
                !visibleNodes.find(vn => vn.id === node.id)
            ).map(node => ({...node, hidden: true})));
            updateFilterButtons();
        }

        function filterBySublocation(sublocation) {
            const visibleNodes = nodes.get().filter(node => 
                JSON.parse(node.title).sublocation === sublocation
            );
            nodes.update(visibleNodes.map(node => ({...node, hidden: false})));
            nodes.update(nodes.get().filter(node => 
                !visibleNodes.find(vn => vn.id === node.id)
            ).map(node => ({...node, hidden: true})));
            updateFilterButtons();
        }

        function filterByRelationship(relType) {
            fetch('/get_relationships', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    relationship_type: relType
                })
            })
            .then(response => response.json())
            .then(newEdges => {
                edges.clear();
                edges.update(newEdges);
                // Show only nodes that are part of these relationships
                const connectedNodeIds = new Set();
                newEdges.forEach(edge => {
                    connectedNodeIds.add(edge.from);
                    connectedNodeIds.add(edge.to);
                });
                nodes.update(nodes.get().map(node => ({
                    ...node,
                    hidden: !connectedNodeIds.has(node.id)
                })));
                updateFilterButtons();
            });
        }

        function clearNetwork() {
            nodes.clear();
            edges.clear();
            updateFilterButtons();
        }

        function updateFilterButtons() {
            document.querySelectorAll('.filter-button').forEach(button => {
                const criteria = button.getAttribute('data-criteria');
                const value = button.getAttribute('data-value');
                const hasNodes = nodes.get().some(node => {
                    const props = JSON.parse(node.title);
                    return props[criteria] === value && !node.hidden;
                });
                button.disabled = !hasNodes;
            });
        }
    </script>
</body>
</html>