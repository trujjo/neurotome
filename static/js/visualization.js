class GraphVisualization {
    constructor(containerId) {
        this.containerId = containerId;
        this.container = d3.select(`#${containerId}`);
        this.width = this.container.node().getBoundingClientRect().width;
        this.height = this.container.node().getBoundingClientRect().height;
        
        this.simulation = null;
        this.svg = null;
        this.zoom = null;
        this.g = null;
        
        this.nodes = [];
        this.links = [];
        
        this.init();
        this.setupEventListeners();
    }

    init() {
        // Create SVG
        this.svg = this.container.append('svg')
            .attr('width', '100%')
            .attr('height', '100%')
            .attr('viewBox', [0, 0, this.width, this.height]);

        // Setup zoom behavior
        this.zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => this.handleZoom(event));

        this.svg.call(this.zoom);

        // Create main group for graph
        this.g = this.svg.append('g');

        // Add arrow marker definitions
        this.defineArrowMarkers();
    }

    defineArrowMarkers() {
        const defs = this.svg.append('defs');
        defs.append('marker')
            .attr('id', 'arrowhead')
            .attr('viewBox', '-0 -5 10 10')
            .attr('refX', 20)
            .attr('refY', 0)
            .attr('orient', 'auto')
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .append('path')
            .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
            .attr('fill', '#999');
    }

    setupEventListeners() {
        // Zoom controls
        document.getElementById('zoomIn').addEventListener('click', () => this.handleZoomButton(1.2));
        document.getElementById('zoomOut').addEventListener('click', () => this.handleZoomButton(0.8));
        document.getElementById('zoomReset').addEventListener('click', () => this.resetZoom());
        
        // Window resize
        window.addEventListener('resize', () => this.handleResize());
    }

    handleZoomButton(scale) {
        this.svg.transition()
            .duration(500)
            .call(this.zoom.scaleBy, scale);
    }

    resetZoom() {
        this.svg.transition()
            .duration(500)
            .call(this.zoom.transform, d3.zoomIdentity);
    }

    handleResize() {
        this.width = this.container.node().getBoundingClientRect().width;
        this.height = this.container.node().getBoundingClientRect().height;
        this.svg.attr('viewBox', [0, 0, this.width, this.height]);
        if (this.simulation) {
            this.simulation.force('center', d3.forceCenter(this.width / 2, this.height / 2));
            this.simulation.alpha(0.3).restart();
        }
    }

    updateData(data) {
        this.nodes = data.nodes;
        this.links = data.relationships;
        this.render();
    }

    render() {
        // Clear previous elements
        this.g.selectAll('*').remove();

        // Create links
        const links = this.g.append('g')
            .selectAll('line')
            .data(this.links)
            .enter()
            .append('line')
            .attr('class', 'link')
            .attr('marker-end', 'url(#arrowhead)');

        // Create nodes
        const nodes = this.g.append('g')
            .selectAll('g')
            .data(this.nodes)
            .enter()
            .append('g')
            .attr('class', 'node')
            .call(d3.drag()
                .on('start', (event, d) => this.dragStarted(event, d))
                .on('drag', (event, d) => this.dragged(event, d))
                .on('end', (event, d) => this.dragEnded(event, d)));

        // Add circles to nodes
        nodes.append('circle')
            .attr('r', 10)
            .attr('fill', d => this.getNodeColor(d.labels[0]))
            .on('mouseover', (event, d) => this.showTooltip(event, d))
            .on('mouseout', () => this.hideTooltip());

        // Add labels to nodes
        nodes.append('text')
            .text(d => d.properties.name || d.labels[0])
            .attr('dx', 12)
            .attr('dy', '.35em');

        // Setup force simulation
        this.simulation = d3.forceSimulation(this.nodes)
            .force('link', d3.forceLink(this.links)
                .id(d => d.id)
                .distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2))
            .force('collision', d3.forceCollide().radius(30))
            .on('tick', () => this.ticked(links, nodes));
    }

    ticked(links, nodes) {
        links
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);

        nodes.attr('transform', d => `translate(${d.x},${d.y})`);
    }

    getNodeColor(label) {
        const colors = {
            'Person': '#ff7f0e',
            'Movie': '#1f77b4',
            'Genre': '#2ca02c',
            'Actor': '#d62728',
            'Director': '#9467bd',
            // Add more mappings as needed
        };
        return colors[label] || '#666666';
    }

    showTooltip(event, d) {
        const tooltip = d3.select('#tooltip');
        tooltip.style('display', 'block')
            .html(`
                <strong>${d.labels.join(', ')}</strong><br>
                ${Object.entries(d.properties)
                    .map(([key, value]) => `${key}: ${value}`)
                    .join('<br>')}
            `)
            .style('left', (event.pageX + 10) + 'px')
            .style('top', (event.pageY - 10) + 'px');
    }

    hideTooltip() {
        d3.select('#tooltip').style('display', 'none');
    }

    handleZoom(event) {
        this.g.attr('transform', event.transform);
    }

    dragStarted(event, d) {
        if (!