let network = null;
let driver = null;

async function initializeDriver() {
    try {
        driver = neo4j.driver(
            NEO4J_CONFIG.uri,
            neo4j.auth.basic(NEO4J_CONFIG.user, NEO4J_CONFIG.password)
        );
        
        // Test connection
        const session = driver.session();
        await session.run("RETURN 1");
        session.close();
        
        await loadLabels();
        updateStatus('Connected to database', 'success');
    } catch (error) {
        updateStatus('Connection failed: ' + error.message, 'danger');
    }
}

function updateStatus(message, type = 'info') {
    const status = document.getElementById('status');
    status.className = `alert alert-${type}`;
    status.textContent = message;
}

async function loadLabels() {
    const session = driver.session();
    try {
        const result = await session.run("CALL db.labels()");
        const controls = document.getElementById('controls');
        controls.innerHTML = ''; // Clear existing buttons
        
        result.records.forEach(record => {
            const label = record.get(0);
            const button = document.createElement('button');
            button.className = 'label-button';
            button.textContent = `${label} Nodes`;
            button.onclick = () => loadNodesWithLabel(label);
            controls.appendChild(button);
        });
    } finally {
        await session.close();
    }
}

async function loadNodesWithLabel(label) {
    const session = driver.session();
    try {
        updateStatus(`Loading ${label} nodes...`);
        
        const result = await session.run(
            `MATCH (n:${label}) 
             OPTIONAL MATCH (n)-[r]-(m) 
             RETURN n, r, m 
             LIMIT 100`
        );

        const nodes = new vis.DataSet();
        const edges = new vis.DataSet();
        const nodeMap = new Map();

        result.records.forEach(record => {
            const node = record.get('n');
            const rel = record.get('r');
            const connectedNode = record.get('m');

            if (!nodeMap.has(node.identity.low)) {
                nodes.add({
                    id: node.identity.low,
                    label: node.properties.name || label,
                    title: JSON.stringify(node.properties, null, 2),
                    group: label
                });
                nodeMap.set(node.identity.low, true);
            }

            if (connectedNode && !nodeMap.has(connectedNode.identity.low)) {
                nodes.add({
                    id: connectedNode.identity.low,
                    label: connectedNode.properties.name || connectedNode.labels[0],
                    title: JSON.stringify(connectedNode.properties, null, 2),
                    group: connectedNode.labels[0]
                });
                nodeMap.set(connectedNode.identity.low, true);
            }

            if (rel) {
                edges.add({
                    from: node.identity.low,
                    to: connectedNode.identity.low,
                    label: rel.type,
                    arrows: 'to'
                });
            }
        });

        const container = document.getElementById('graph');
        const data = { nodes, edges };
        const options = {
            nodes: {
                shape: 'dot',
                size: 16,
                font: {
                    size: 12
                }
            },
            edges: {
                font: {
                    size: 10,
                    align: 'middle'
                },
                color: { color: '#848484' },
                arrows: {
                    to: { enabled: true, scaleFactor: 0.5 }
                }
            },
            physics: {
                enabled: true,
                stabilization: {
                    iterations: 100
                },
                solver: 'forceAtlas2Based'
            }
        };

        network = new vis.Network(container, data, options);
        
        network.on('click', function(params) {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                const node = nodes.get(nodeId);
                showNodeInfo(node);
            } else {
                hideNodeInfo();
            }
        });

        updateStatus(`Loaded ${nodes.length} nodes and ${edges.length} relationships`, 'success');
    } catch (error) {
        updateStatus(`Error loading nodes: ${error.message}`, 'danger');
    } finally {
        await session.close();
    }
}

function showNodeInfo(node) {
    const nodeInfo = document.getElementById('nodeInfo');
    const nodeDetails = document.getElementById('nodeDetails');
    
    let detailsHtml = '<div class="node-properties">';
    for (const [key, value] of Object.entries(JSON.parse(node.title))) {
        detailsHtml += `
            <div class="node-property">
                <strong>${key}:</strong> 
                <span>${value}</span>
            </div>`;
    }
    detailsHtml += '</div>';
    
    nodeDetails.innerHTML = detailsHtml;
    nodeInfo.style.display = 'block';
}

function hideNodeInfo() {
    document.getElementById('nodeInfo').style.display = 'none';
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', initializeDriver);
