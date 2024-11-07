<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NeuroNetwork Explorer</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/vis-network@9.1.2/dist/vis-network.min.js"></script>
    <style>
        :root {
            --primary-bg: #1a1a1a;
            --secondary-bg: #2d2d2d;
            --burnt-orange: #CC5500;
            --text-primary: #e0e0e0;
            --text-secondary: #a0a0a0;
            --border-color: #404040;
        }
        
        /* ... [previous styles remain the same] ... */

        .search-container {
            background-color: var(--secondary-bg);
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            border: 1px solid var(--border-color);
        }

        .search-input {
            width: 100%;
            padding: 0.75rem;
            border-radius: 4px;
            background-color: var(--primary-bg);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
            font-size: 1rem;
        }

        .search-results {
            margin-top: 0.5rem;
            color: var(--text-secondary);
        }

        .highlighted-node {
            border: 2px solid var(--burnt-orange) !important;
            background-color: var(--burnt-orange) !important;
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="container">
            <h1 style="margin: 0; text-align: center;">NeuroNetwork Explorer</h1>
        </div>
    </nav>

    <div class="main-container">
        <!-- Sidebar with filters -->
        <div class="sidebar">
            <!-- ... [filter sections remain the same] ... -->
        </div>

        <!-- Main content -->
        <div class="content">
            <!-- Search Box -->
            <div class="search-container">
                <input type="text" 
                       id="searchInput" 
                       class="search-input" 
                       placeholder="Search nodes (min. 2 characters)...">
                <div id="searchResults" class="search-results"></div>
            </div>

            <!-- Network container -->
            <div id="network-container"></div>
        </div>
    </div>

    <script>
        // Initialize network visualization
        const container = document.getElementById('network-container');
        const data = {
            nodes: new vis.DataSet([]),
            edges: new vis.DataSet([])
        };
        
        const options = {
            nodes: {
                shape: 'dot',
                size: 16,
                font: {
                    size: 14,
                    color: '#e0e0e0'
                },
                borderWidth: 2,
                shadow: true
            },
            edges: {
                width: 2,
                color: {
                    color: '#404040',
                    highlight: '#CC5500'
                },
                smooth: {
                    type: 'continuous'
                }
            },
            physics: {
                stabilization: false,
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
        
        const network = new vis.Network(container, data, options);

        // Improved search functionality
        const searchInput = document.getElementById('searchInput');
        const searchResults = document.getElementById('searchResults');
        let searchTimeout = null;
        let highlightedNodes = new Set();

        function resetHighlights() {
            // Reset all previously highlighted nodes
            highlightedNodes.forEach(nodeId => {
                const node = data.nodes.get(nodeId);
                if (node) {
                    node.color = node.originalColor || undefined;
                    node.borderWidth = 1;
                    data.nodes.update(node);
                }
            });
            highlightedNodes.clear();
        }

        function highlightNode(nodeId) {
            const node = data.nodes.get(nodeId);
            if (node) {
                if (!node.originalColor) {
                    node.originalColor = node.color;
                }
                node.color = '#CC5500';
                node.borderWidth = 3;
                data.nodes.update(node);
                highlightedNodes.add(nodeId);
            }
        }

        function performSearch(searchTerm) {
            if (searchTerm.length < 2) {
                searchResults.textContent = 'Enter at least 2 characters to search';
                resetHighlights();
                return;
            }

            fetch(`/api/quick_search?term=${encodeURIComponent(searchTerm)}`)
                .then(response => response.json())
                .then(nodes => {
                    resetHighlights();
                    
                    if (nodes.length === 0) {
                        searchResults.textContent = 'No matches found';
                        return;
                    }

                    searchResults.textContent = `Found ${nodes.length} matching nodes`;
                    
                    // Highlight matching nodes
                    nodes.forEach(node => {
                        highlightNode(node.id);
                    });

                    // If there are matches, focus the network on the first match
                    if (nodes.length > 0) {
                        network.focus(nodes[0].id, {
                            scale: 1.5,
                            animation: true
                        });
                    }
                })
                .catch(error => {
                    console.error('Search error:', error);
                    searchResults.textContent = 'Error performing search';
                });
        }

        searchInput.addEventListener('input', (event) => {
            clearTimeout(searchTimeout);
            const searchTerm = event.target.value.trim();
            
            searchTimeout = setTimeout(() => {
                performSearch(searchTerm);
            }, 300); // 300ms debounce
        });

        // Load initial graph data
        fetch('/api/graph')
            .then(response => response.json())
            .then(graphData => {
                data.nodes.add(graphData.nodes);
                data.edges.add(graphData.edges);
            })
            .catch(error => {
                console.error('Error loading graph:', error);
            });

        // ... [rest of your existing code for filters, etc.] ...
    </script>
</body>
</html>
