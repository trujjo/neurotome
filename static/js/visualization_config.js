document.querySelectorAll('.tab-button').forEach(button => {
    button.addEventListener('click', () => {
        const tabId = button.getAttribute('data-tab');
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('active');
        });
        button.classList.add('active');
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(tabId).classList.add('active');
    });
});

document.getElementById('fetch-nodes').addEventListener('click', () => {
    fetch('/api/nodes/random')
        .then(response => response.json())
        .then(data => {
            visualizeData(data);
        });
});

document.getElementById('fetch-random-nodes').addEventListener('click', showRandomNodesWithRelationships);

async function showRandomNodesWithRelationships() {
    const statusDiv = document.getElementById('status');
    statusDiv.style.backgroundColor = '';
    statusDiv.innerHTML = 'Fetching data...';

    try {
        const response = await fetch('/api/nodes/random');
        const data = await response.json();

        const nodes = new Map();
        const links = [];

        data.forEach(record => {
            const source = record.n;
            const target = record.m;
            const relationship = record.rel;

            if (!source || !target || !relationship) {
                console.error('Invalid record:', record);
                return;
            }

            console.log('Source:', source);
            console.log('Target:', target);
            console.log('Relationship:', relationship);

            if (!nodes.has(source.id)) {
                nodes.set(source.id, {
                    id: source.id,
                    label: source.labels[0],
                    name: source.properties.name || 'Unnamed'
                });
            }

            if (!nodes.has(target.id)) {
                nodes.set(target.id, {
                    id: target.id,
                    label: target.labels[0],
                    name: target.properties.name || 'Unnamed'
                });
            }

            links.push({
                source: source.id,
                target: target.id,
                type: relationship.type
            });
        });

        statusDiv.innerHTML = 'Rendering graph...';
        createForceGraph(Array.from(nodes.values()), links);
        statusDiv.style.backgroundColor = '#28a745';
        statusDiv.innerHTML = 'Graph rendered successfully';

    } catch (error) {
        statusDiv.style.backgroundColor = '#dc3545';
        statusDiv.innerHTML = 'Error: ' + error.message;
        console.error('Error:', error);
    }
}

function createForceGraph(nodes, links) {
    const width = document.getElementById('visualization').clientWidth;
    const height = document.getElementById('visualization').clientHeight;

    // Clear previous visualization
    d3.select('#visualization').selectAll('*').remove();

    const svg = d3.select('#visualization').append('svg')
        .attr('width', width)
        .attr('height', height);

    const simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links).id(d => d.id))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2));

    const link = svg.append('g')
        .attr('class', 'links')
        .selectAll('line')
        .data(links)
        .enter().append('line')
        .attr('stroke-width', 1.5);

    const node = svg.append('g')
        .attr('class', 'nodes')
        .selectAll('circle')
        .data(nodes)
        .enter().append('circle')
        .attr('r', 5)
        .attr('fill', '#69b3a2')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));

    node.append('title')
        .text(d => d.name);

    simulation
        .nodes(nodes)
        .on('tick', ticked);

    simulation.force('link')
        .links(links);

    function ticked() {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);

        node
            .attr('cx', d => d.x)
            .attr('cy', d => d.y);
    }

    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
}

function checkNeo4jStatus() {
    fetch('/api/neo4j/status')
        .then(response => response.json())
        .then(data => {
            const statusDiv = document.getElementById('status');
            if (data.status === 'connected') {
                statusDiv.textContent = 'connected to neo4j';
                statusDiv.style.color = 'green';
            } else {
                statusDiv.textContent = 'disconnected from neo4j';
                statusDiv.style.color = 'red';
            }
        })
        .catch(error => {
            const statusDiv = document.getElementById('status');
            statusDiv.textContent = 'disconnected from neo4j';
            statusDiv.style.color = 'red';
        });
}

checkNeo4jStatus();
setInterval(checkNeo4jStatus, 60000); // Check status every 60 seconds