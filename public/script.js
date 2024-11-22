document.addEventListener('DOMContentLoaded', () => {
    // Set up the D3 visualization
    const width = window.innerWidth;
    const height = window.innerHeight - 80;
    
    const svg = d3.select('#graph')
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .call(d3.zoom().on('zoom', (event) => {
            svg.attr('transform', event.transform);
        }))
        .append('g');

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

    // Load distinct values for filters
    fetch('/api/distinct-values')
        .then(response => response.json())
        .then(data => {
            const locationSelect = document.getElementById('locationFilter');
            const systemSelect = document.getElementById('systemFilter');
            locationSelect.innerHTML = '<option value="">All Locations</option>' + 
                data.locations.map(loc => `<option value="${loc}">${loc}</option>`).join('');
            systemSelect.innerHTML = '<option value="">All Systems</option>' + 
                data.systems.map(sys => `<option value="${sys}">${sys}</option>`).join('');
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

    // Add fit all button functionality
    document.getElementById('fitAll').addEventListener('click', () => {
        fitAll();
    });

    function updateVisualization(data) {
        svg.selectAll('*').remove();

        // Add relationships first (so they appear behind nodes)
        const links = svg.selectAll('line')
            .data(data.relationships)
            .enter()
            .append('line')
            .attr('class', 'relationship')
            .attr('stroke', '#999')
            .attr('stroke-width', 1);

        // Add nodes
        const nodes = svg.selectAll('circle')
            .data(data.nodes)
            .enter()
            .append('g')
            .attr('class', 'node-group');

        const colorMap = {
            'Person': '#1f77b4',
            'Location': '#ff7f0e',
            'Node': '#2ca02c',
            // Add more mappings as needed
        };

        nodes.append('circle')
            .attr('class', d => `node node-${d.size}`)
            .style('fill', '#1a1a1a'); // Same color as the background

        // Add text labels inside nodes
        nodes.append('text')
            .attr('class', 'node-label')
            .text(d => d.properties.name || d.labels[0])
            .attr('dy', '.35em');

        // Update tooltips to include relationship info
        nodes.append('title')
            .text(d => `Labels: ${d.labels.join(', ')}\nProperties: ${JSON.stringify(d.properties)}`);

        // Update simulation with both nodes and links
        simulation
            .nodes(data.nodes)
            .force('link', d3.forceLink(data.relationships)
                .id(d => d.id)
                .distance(100))
            .on('tick', () => {
                links
                    .attr('x1', d => d.source.x)
                    .attr('y1', d => d.source.y)
                    .attr('x2', d => d.target.x)
                    .attr('y2', d => d.target.y);

                nodes.selectAll('circle')
                    .attr('cx', d => d.x)
                    .attr('cy', d => d.y);

                nodes.selectAll('text')
                    .attr('x', d => d.x)
                    .attr('y', d => d.y);
            });

        simulation.alpha(1).restart();
    }

    function fitAll() {
        const bounds = svg.node().getBBox();
        const parent = svg.node().parentElement;
        const fullWidth = parent.clientWidth;
        const fullHeight = parent.clientHeight;
        const width = bounds.width;
        const height = bounds.height;
        const midX = bounds.x + width / 2;
        const midY = bounds.y + height / 2;

        if (width === 0 || height === 0) return; // nothing to fit

        const scale = 0.85 / Math.max(width / fullWidth, height / fullHeight);
        const translate = [fullWidth / 2 - scale * midX, fullHeight / 2 - scale * midY];

        svg.transition()
            .duration(750)
            .call(
                d3.zoom().transform,
                d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale)
            );
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