let network = null;
let driver = null;

async function initializeDriver() {
    const uri = "neo4j+s://4e5eeae5.databases.neo4j.io:7687";
    const user = "neo4j";
    const password = "Poconoco16!";
    
    try {
        driver = neo4j.driver(uri, neo4j.auth.basic(user, password));
        await loadLabels();
    } catch (error) {
        document.getElementById('status').innerHTML = `
            <div style="color: red;">Connection failed: ${error.message}</div>
        `;
    }
}

async function loadLabels() {
    const session = driver.session();
    try {
        const result = await session.run("CALL db.labels()");
        const controls = document.getElementById('controls');
        
        result.records.forEach(record => {
            const label = record.get(0);
            const button = document.createElement('button');
            button.className = 'label-button';
            button.textContent = `${label} Nodes`;
            button.onclick = () => loadNodesWithLabel(label);
            controls.appendChild(button);
        });
        
        document.getElementById('status').innerHTML = `
            <div style="color: green;">✓ Connected to database</div>
        `;
    } finally {
        await session.close();
    }
}

async function loadNodesWithLabel(label) {
    const session = driver.session();
    try {
        document.getElementById('status').innerHTML = `Loading ${label} nodes...`;
        
        // Query nodes and their relationships
        const result = await session.run(
            `MATCH (n:${label}) 
             OPTIONAL MATCH (n)-[r]-(m) 
             RETURN n, r, m 
             LIMIT 100`
        );

        // Create network datasets
        const nodes = new vis.DataSet();
        const edges = new vis.DataSet();
        const nodeMap = new Map();

        result.records.forEach(record => {
            const node = record.get('n');
            const rel = record.get('r');
            const connectedNode = record.get('m');

            // Add main node if not already added
            if (!nodeMap.has(node.identity.low)) {
                nodes.add({
                    id: node.identity.low,
                    label: node.properties.name || label,
                    title: JSON.stringify(node.properties, null, 2),
                    color: '#3498db'
                });
                nodeMap.set(node.identity.low, true);
            }

            // Add connected node and relationship if they exist
            if (connectedNode && !nodeMap.has(connectedNode.identity.low)) {
                nodes.add({
                    id: connectedNode.identity.low,
                    label: connectedNode.properties.name || connectedNode.labels[0],
                    title: JSON.stringify(connectedNode.properties, null, 2),
                    color: '#e74c3c'
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

        // Configure and create network
        const container = document.getElementById('graph');
        const data = { nodes, edges };
        const options = {
            nodes: {
                shape: 'dot',
                size: 10,
                font: {
                    size: 12
                }
            },
            edges: {
                font: {
                    size: 10,
                    align: 'middle'
                },
                color: { color: '#848484' }
            },
            physics: {
                enabled: true,
                stabilization: {
                    iterations: 100
                }
            }
        };

        network = new vis.Network(container, data, options);
        
        // Add node click event
        network.on('click', function(params) {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                const node = nodes.get(nodeId);
                const nodeInfo = document.getElementById('nodeInfo');
                nodeInfo.innerHTML = `
                    <h3>${node.label}</h3>
                    
