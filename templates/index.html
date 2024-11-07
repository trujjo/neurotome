<!DOCTYPE html>
<html>
<head>
    <title>Neo4j Graph Visualization</title>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {
            background-color: #1a1a1a;
            color: #ffffff;
            margin: 0;
            padding: 15px;
            font-family: 'Arial', sans-serif;
        }
        .button-container {
            padding: 15px;
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            background-color: #232323;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .node-button {
            background-color: #cc5500;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.3px;
            min-width: 60px;
        }
        .node-button:hover {
            background-color: #ff6600;
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(204, 85, 0, 0.3);
        }
        .active {
            background-color: #ff8533;
            box-shadow: 0 0 10px rgba(255, 133, 51, 0.5);
        }
        #viz {
            width: 100%;
            height: 700px;
            background-color: #1e1e1e;
            border: 1px solid #333;
            border-radius: 8px;
        }
    </style>
</head>
<body>
    <div class="button-container" id="nodeTypeButtons"></div>
    <div id="viz"></div>

    <script>
        let network = null;
        const container = document.getElementById('viz');
        
        // Create buttons dynamically
        fetch('/api/node-types')
            .then(response => response.json())
            .then(data => {
                const buttonContainer = document.getElementById('nodeTypeButtons');
                data.node_types.forEach(type => {
                    const button = document.createElement('button');
                    button.className = 'node-button';
                    button.textContent = type;
                    button.onclick = () => loadGraphData(type);
                    buttonContainer.appendChild(button);
                });
            });

        function loadGraphData(nodeType) {
            // Update active button
            document.querySelectorAll('.node-button').forEach(btn => {
                btn.classList.remove('active');
                if (btn.textContent === nodeType) {
                    btn.classList.add('active');
                }
            });

            // Fetch graph data
            fetch(`/api/nodes/${nodeType}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        visualizeGraph(data.data);
                    }
                });
        }

        function visualizeGraph(graphData) {
            // Process the graph data
            const nodes = new Set();
            const edges = [];
            const nodesArray = [];

            graphData.forEach(record => {
                const source = record.n;
                const target = record.m;
                const relationship = record.r;

                if (!nodes.has(source.id)) {
                    nodes.add(source.id);
                    nodesArray.push({
                        id: source.id,
                        label: source.properties.name || source.id,
                        color: getNodeColor(source.labels[0])
                    });
                }

                if (!nodes.has(target.id)) {
                    nodes.add(target.id);
                    nodesArray.push({
                        id: target.id,
                        label: target.properties.name || target.id,
                        color: getNodeColor(target.labels[0])
                    });
                }

                edges.push({
                    from: source.id,
                    to: target.id,
                    label: relationship.type,
                    arrows: 'to'
                });
            });

            const data = {
                nodes: new vis.DataSet(nodesArray),
                edges: new vis.DataSet(edges)
            };

            const options = {
                nodes: {
                    shape: 'dot',
                    size: 16,
                    font: {
                        color: '#ffffff'
                    }
                },
                edges: {
                    color: '#ffffff',
                    font: {
                        color: '#ffffff'
                    }
                },
                physics: {
                    stabilization: false,
                    barnesHut: {
                        gravitationalConstant: -80000,
                        springConstant: 0.001,
                        springLength: 200
                    }
                }
            };

            // Destroy existing network if it exists
            if (network !== null) {
                network.destroy();
            }

            network = new vis.Network(container, data, options);
        }

        function getNodeColor(label) {
            const colors = {
                'nerve': '#ff0000',
                'bone': '#00ff00',
                'neuro': '#0000ff',
                // Add more colors for other node types
            };
            return colors[label] || '#cccccc';
        }

        // Load initial graph data
        fetch('/api/graph')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    visualizeGraph(data.data);
                }
            });
    </script>
</body>
</html>
