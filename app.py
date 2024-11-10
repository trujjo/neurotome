from flask import Flask, render_template_string

app = Flask(__name__)

# HTML template with embedded CSS and JavaScript
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            background-color: #1a1a1a;
            color: white;
            font-family: Arial, sans-serif;
            padding: 20px;
        }
        .type-buttons {
            display: grid;
            grid-template-rows: repeat(2, 1fr);
            grid-template-columns: repeat(9, 1fr);
            gap: 6px;
            margin-bottom: 12px;
            padding: 12px;
            background-color: #2d2d2d;
            border-radius: 4px;
            width: calc(100% - 24px);
        }
        .type-button {
            padding: 4px 8px;
            background-color: #cc5500;
            color: white;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            font-size: 10px;
            text-align: center;
            width: 100%;
            min-width: 60px;
            height: 25px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-transform: lowercase;
        }
        .type-button:hover {
            background-color: #ff6a00;
        }
        .type-button.active {
            background-color: #ff6a00;
            border: 2px solid #ffffff;
        }
        .controls {
            display: flex;
            gap: 8px;
            align-items: center;
            margin: 12px;
            background-color: #2d2d2d;
            padding: 12px;
            border-radius: 4px;
        }
        .button {
            background-color: #cc5500;
            color: white;
            border: none;
            border-radius: 3px;
            padding: 6px 12px;
            cursor: pointer;
            height: 25px;
            font-size: 10px;
            text-transform: lowercase;
        }
        #searchBox {
            padding: 6px;
            border-radius: 3px;
            border: 1px solid #666;
            background-color: #333;
            color: white;
            width: 180px;
            height: 25px;
            box-sizing: border-box;
            font-size: 10px;
        }
        #status {
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
        }
        #graph {
            width: 100%;
            height: 600px;
            background-color: #2d2d2d;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="type-buttons">
        <button class="type-button" onclick="showNodesByType('nerve')">nerve</button>
        <button class="type-button" onclick="showNodesByType('bone')">bone</button>
        <button class="type-button" onclick="showNodesByType('neuro')">neuro</button>
        <button class="type-button" onclick="showNodesByType('region')">region</button>
        <button class="type-button" onclick="showNodesByType('viscera')">viscera</button>
        <button class="type-button" onclick="showNodesByType('muscle')">muscle</button>
        <button class="type-button" onclick="showNodesByType('sense')">sense</button>
        <button class="type-button" onclick="showNodesByType('vein')">vein</button>
        <button class="type-button" onclick="showNodesByType('artery')">artery</button>
        
        <button class="type-button" onclick="showNodesByType('cv')">cv</button>
        <button class="type-button" onclick="showNodesByType('function')">function</button>
        <button class="type-button" onclick="showNodesByType('sensory')">sensory</button>
        <button class="type-button" onclick="showNodesByType('gland')">gland</button>
        <button class="type-button" onclick="showNodesByType('lymph')">lymph</button>
        <button class="type-button" onclick="showNodesByType('head')">head</button>
        <button class="type-button" onclick="showNodesByType('organ')">organ</button>
        <button class="type-button" onclick="showNodesByType('sensation')">sensation</button>
        <button class="type-button" onclick="showNodesByType('skin')">skin</button>
    </div>
    
    <div class="controls">
        <button class="button" onclick="showRandomNodesWithRelationships()">show random connected nodes</button>
        <input type="text" id="searchBox" placeholder="search nodes...">
    </div>
    
    <div id="status"></div>
    <div id="graph"></div>

    <script src="https://unpkg.com/neo4j-driver"></script>
    <script src="https://d3js.org/d3.v5.min.js"></script>
    <script>
        const driver = neo4j.driver(
            'neo4j+s://your-neo4j-uri:7687',
            neo4j.auth.basic('neo4j', 'your-password')
        );

        let searchTimeout;
        let currentNodes = [];
        let simulation;
        
        function initializeSearch() {
            const searchBox = document.getElementById('searchBox');
            searchBox.addEventListener('input', function(e) {
                clearTimeout(searchTimeout);
                const searchTerm = e.target.value;
                
                if (searchTerm.length >= 3) {
                    searchTimeout = setTimeout(() => {
                        searchNodes(searchTerm);
                    }, 300);
                } else {
                    const searchResults = document.getElementById('searchResults');
                    if (searchResults) {
                        searchResults.innerHTML = '';
                    }
                }
            });
        }

        async function searchNodes(searchTerm) {
            if (!driver) {
                document.getElementById('status').style.backgroundColor = '#dc3545';
                document.getElementById('status').innerHTML = 'Not connected to database';
                return;
            }

            const session = driver.session();
            try {
                const result = await session.run(`
                    MATCH (n)
                    WHERE toLower(n.name) CONTAINS toLower($searchTerm)
                    WITH n
                    OPTIONAL MATCH (n)-[r]-(m)
                    RETURN DISTINCT n, r, m
                    LIMIT 50
                `, { searchTerm });

                const nodes = new Map();
                const links = [];

                result.records.forEach(record => {
                    const source = record.get('n');
                    const target = record.get('m');
                    const relationship = record.get('r');

                    if (source && !nodes.has(source.identity.toString())) {
                        nodes.set(source.identity.toString(), {
                            id: source.identity.toString(),
                            label: source.labels[0],
                            name: source.properties.name || 'Unnamed'
                        });
                    }

                    if (target && !nodes.has(target.identity.toString())) {
                        nodes.set(target.identity.toString(), {
                            id: target.identity.toString(),
                            label: target.labels[0],
                            name: target.properties.name || 'Unnamed'
                        });
                    }

                    if (source && target && relationship) {
                        links.push({
                            source: source.identity.toString(),
                            target: target.identity.toString(),
                            type: relationship.type
                        });
                    }
                });

                currentNodes = Array.from(nodes.values());
                createForceGraph(currentNodes, links);
                
                document.getElementById('status').style.backgroundColor = '#28a745';
                document.getElementById('status').innerHTML = `Found ${currentNodes.length} matching nodes`;

            } catch (error) {
                document.getElementById('status').style.backgroundColor = '#dc3545';
                document.getElementById('status').innerHTML = 'Error: ' + error.message;
                console.error('Error:', error);
            } finally {
                await session.close();
            }
        }

        async function showRandomNodesWithRelationships() {
            if (!driver) {
                document.getElementById('status').style.backgroundColor = '#dc3545';
                document.getElementById('status').innerHTML = 'Not connected to database';
                return;
            }

            const session = driver.session();
            document.getElementById('status').innerHTML = 'Fetching random nodes...';
            
            try {
                const result = await session.run(`
                    MATCH (n)
                    WITH n, rand() as r
                    ORDER BY r
                    LIMIT 10
                    WITH COLLECT(n) as nodes
                    UNWIND nodes as n
                    OPTIONAL MATCH (n)-[r]-(m)
                    WHERE m IN nodes
                    RETURN DISTINCT n, r, m
                `);
                
                const nodes = new Map();
                const links = [];
                
                result.records.forEach(record => {
                    const source = record.get('n');
                    const target = record.get('m');
                    const relationship = record.get('r');
                    
                    if (source && !nodes.has(source.identity.toString())) {
                        nodes.set(source.identity.toString(), {
                            id: source.identity.toString(),
                            label: source.labels[0],
                            name: source.properties.name || 'Unnamed'
                        });
                    }
                    
                    if (target && !nodes.has(target.identity.toString())) {
                        nodes.set(target.identity.toString(), {
                            id: target.identity.toString(),
                            label: target.labels[0],
                            name: target.properties.name || 'Unnamed'
                        });
                    }
                    
                    if (source && target && relationship) {
                        links.push({
                            source: source.identity.toString(),
                            target: target.identity.toString(),
                            type: relationship.type
                        });
                    }
                });
                
                currentNodes = Array.from(nodes.values());
                createForceGraph(currentNodes, links);
                
                document.getElementById('status').style.backgroundColor = '#28a745';
                document.getElementById('status').innerHTML = 'Showing random connected nodes';
                
            } catch (error) {
                document.getElementById('status').style.backgroundColor = '#dc3545';
                document.getElementById('status').innerHTML = 'Error: ' + error.message;
                console.error('Error:', error);
            } finally {
                await session.close();
            }
        }

        async function showNodesByType(nodeType) {
            if (!driver) {
                document.getElementById('status').style.backgroundColor = '#dc3545';
                document.getElementById('status').innerHTML = 'Not connected to database';
                return;
            }

            // Update active button
            document.querySelectorAll('.type-button').forEach(btn => {
                if (btn.textContent === nodeType) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            });

            const session = driver.session();
            document.getElementById('status').innerHTML = 'Fetching ' + nodeType + ' nodes...';
            
            try {
                const result = await session.run(`
                    MATCH (n:${nodeType})
                    WITH n
                    OPTIONAL MATCH (n)-[r]-(m)
                    RETURN DISTINCT n, r, m
                    LIMIT 50
                `);
                
                const nodes = new Map();
                const links = [];
                
                result.records.forEach(record => {
                    const source = record.get('n');
                    const target = record.get('m');
                    const relationship = record.get('r');
                    
                    if (source && !nodes.has(source.identity.toString())) {
                        nodes.set(source.identity.toString(), {
                            id: source.identity.toString(),
                            label: source.labels[0],
                            name: source.properties.name || 'Unnamed'
                        });
                    }
                    
                    if (target && !nodes.has(target.identity.toString())) {
                        nodes.set(target.identity.toString(), {
                            id: target.identity.toString(),
                            label: target.labels[0],
                            name: target.properties.name || 'Unnamed'
                        });
                    }
                    
                    if (source && target && relationship) {
                        links.push({
                            source: source.identity.toString(),
                            target: target.identity.toString(),
                            type: relationship.type
                        });
                    }
                });
                
                currentNodes = Array.from(nodes.values());
                createForceGraph(currentNodes, links);
                
                document.getElementById('status').style.backgroundColor = '#28a745';
                document.getElementById('status').innerHTML = `Showing ${nodeType} nodes`;
                
            } catch (error) {
                document.getElementById('status').style.backgroundColor = '#dc3545';
                document.getElementById('status').innerHTML = 'Error: ' + error.message;
                console.error('Error:', error);
            } finally {
                await session.close();
            }
        }

        function createForceGraph(nodes, links) {
            const width = document.getElementById('graph').clientWidth;
            const height = document.getElementById('graph
