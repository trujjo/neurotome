// visualization_config.js
class NeoViz {
    constructor(containerId) {
        this.container = d3.select(containerId);
        this.width = this.container.node().getBoundingClientRect().width;
        this.height = this.container.node().getBoundingClientRect().height;
        
        this.colorMap = {
            'nerve': '#ff7f0e',
            'bone': '#2ca02c',
            'neuro': '#d62728',
            'region': '#9467bd',
            'viscera': '#8c564b',
            'muscle': '#e377c2',
            'sense': '#7f7f7f',
            'vein': '#bcbd22',
            'artery': '#17becf',
            'cv': '#1f77b4',
            'function': '#ff9896',
            'sensory': '#98df8a',
            'gland': '#c5b0d5',
            'lymph': '#c49c94',
            'head': '#f7b6d2',
            'organ': '#c7c7c7',
            'sensation': '#dbdb8d',
            'skin': '#9edae5',
            'default': '#666666'
        };

        this.initializeSVG();
        this.initializeSimulation();
        this.initializeTooltip();
    }

    initializeSVG() {
        this.svg = this.container.append('svg')
            .attr('width', this.width)
            .attr('height', this.height);

        // Add zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                this.svg.select('g').attr('transform', event.transform);
            });

        this.svg.call(zoom);
        
        // Add a group for the graph elements
        this.graphGroup = this.svg.append('g');
    }

    initializeSimulation() {
        this.simulation = d3.forceSimulation()
            .force('link', d3.forceLink().id(d => d.id).distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2))
            .force('collision', d3.forceCollide().radius(30));
    }

    initializeTooltip() {
        this.tooltip = this.container.append('div')
            .attr('class', 'tooltip')
            .style('opacity', 0)
            .style('position', 'absolute')
            .style('background-color', 'rgba(0, 0, 0, 0.8)')
            .style('color', 'white')
            .style('padding', '5px')
            .style('border-radius', '5px')
            .style('pointer-events', 'none');
    }

    updateData(data) {
        // Clear existing elements
        this.graphGroup.selectAll('*').remove();

        // Create links
        this.links = this.graphGroup.append('g')
            .selectAll('line')
            .data(data.relationships)
            .enter()
            .append('line')
            .attr('class', 'link')
            .attr('stroke', '#999')
            .attr('stroke-opacity', 0.6);

        // Create nodes
        this.nodes = this.graphGroup.append('g')
            .selectAll('g')
            .data(data.nodes)
            .enter()
            .append('g')
            .attr('class', 'node')
            .call(d3.drag()
                .on('start', (event, d) => this.dragstarted(event, d))
                .on('drag', (event, d) => this.dragged(event, d))
                .on('end', (event, d) => this.dragended(event, d)));

        // Add circles to nodes
        this.nodes.append('circle')
            .attr('r', 10)
            .attr('fill', d => this.getNodeColor(d))
            .attr('stroke', '#fff')
            .attr('stroke-width', 1.5);

        // Add labels to nodes
        this.nodes.append('text')
            .attr('dx', 12)
            .attr('dy', '.35em')
            .text(d => d.properties.name || d.labels[0])
            .style('fill', '#fff')
            .style('font-size', '12px');

        // Add hover interactions
        this.nodes
            .on('mouseover', (event, d) => this.showTooltip(event, d))
            .on('mouseout', () => this.hideTooltip());

        // Update simulation
        this.simulation
            .nodes(data.nodes)
            .on('tick', () => this.ticked());

        this.simulation.force('link')
            .links(data.relationships);

        // Restart simulation
        this.simulation.alpha(1).restart();
    }

    getNodeColor(node) {
        const label = node.labels[0].toLowerCase();
        return this.colorMap[label] || this.colorMap.default;
    }

    ticked() {
        this.links
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);

        this.nodes
            .attr('transform', d => `translate(${d.x},${d.y})`);
    }

    dragstarted(event, d) {
        if (!event.active) this.simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    dragended(event, d) {
        if (!event.active) this.simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }

    showTooltip(event, d) {
        const properties = Object.entries(d.properties)
            .map(([key, value]) => `${key}: ${value}`)
            .join('<br>');

        this.tooltip.transition()
            .duration(200)
            .style('opacity', .9);
        
        this.tooltip.html(`
            <strong>Type:</strong> ${d.labels.join(', ')}<br>
            ${properties}
        `)
            .style('left', (event.pageX + 10) + 'px')
            .style('top', (event.pageY - 28) + 'px');
    }

    hideTooltip() {
        this.tooltip.transition()
            .duration(500)
            .style('opacity', 0);
    }

    resize() {
        this.width = this.container.node().getBoundingClientRect().width;
        this.height = this.container.node().getBoundingClientRect().height;

        this.svg
            .attr('width', this.width)
            .attr('height', this.height);

        this.simulation.force('center', d3.forceCenter(this.width / 2, this.height / 2));
        this.simulation.alpha(1).restart();
    }
}

// Create and export the visualization instance
const viz = new NeoViz('#visualization');
export { viz };
