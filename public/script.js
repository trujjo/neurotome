
document.addEventListener('DOMContentLoaded', () => {
    // Set up the D3 visualization
    const width = window.innerWidth;
    const height = window.innerHeight - 80;
    
    const svg = d3.select('#graph')
        .append('svg')
        .attr('width', width)
        .attr('height', height);
    
    const simulation = d3.forceSimulation()
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('charge', d3.forceManyBody().strength(-100))
        .force('collide', d3.forceCollide(30));
    
    // Load labels for filter
    fetch('/api/labels')
        .then(response => response.json())
        .then(labels => {
            const labelSelect = document.getElementById('labelFilter');
            labelSelect.innerHTML = labels.map(label => 
                `<option value="${label}">${label}</option>`
            ).join('');
        });
    
    // Handle filter application
    document.getElementById('applyFilters').addEventListener('click', () => {
        const selectedLabels = Array.from(document.getElementById('labelFilter').selectedOptions)
            .map(option => option.value);
        const location = document.getElementById('locationFilter').value;
        const system = document.getElementById('systemFilter').value;
        
        fetch('/api/nodes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                labels: selectedLabels,
                location,
                system
            })
        })
        .then(response => response.json())
        .then(nodes => updateVisualization(nodes));
    });
    
    function updateVisualization(nodes) {
        // Clear existing nodes
        svg.selectAll('*').remove();
        
        // Add new nodes
        const circles = svg.selectAll('circle')
            .data(nodes)
            .enter()
            .append('circle')
            .attr('class', d => `node node-${d.size}`)
            .style('fill', (d, i) => d3.schemeCategory10[i % 10])
            .call(d3.drag()
                .on('start', dragStarted)
                .on('drag', dragged)
                .on('end', dragEnded));
        
        // Add tooltips
        circles.append('title')
            .text(d => `Labels: ${d.labels.join(', ')}\nProperties: ${JSON.stringify(d.properties)}`);
        
        // Update simulation
        simulation.nodes(nodes)
            .on('tick', () => {
                circles
                    .attr('cx', d => d.x)
                    .attr('cy', d => d.y);
            });
        
        simulation.alpha(1).restart();
    }
    
    function dragStarted(event) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
    }
    
    function dragged(event) {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
    }
    
    function dragEnded(event) {
        if (!event.active) simulation.alphaTarget(0);
        event.subject.fx = null;
        event.subject.fy = null;
    }
});