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
            'nerve': '#ff7f0e',
            'bone': '#2ca02c',
            'neuro': '#d62728',
            'region': '#9467bd',
            'viscera': '#8c564b',
            'muscle': '#e377c2',
            'sense': '#7f7f7f',
            'vein': '#bcbd22',
            'artery': '#17becf',
            'cv': '#1f77b4'
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
        if (!event.active) this.simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    dragEnded(event, d) {
        if (!event.active) this.simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
}

// Filter and data loading functionality
async function populateFilters() {
    try {
        // Fetch and populate node labels
        const labelResponse = await fetch('/api/labels');
        const labels = await labelResponse.json();
        const nodeLabelsSelect = document.getElementById('nodeLabels');
        nodeLabelsSelect.innerHTML = '';
        labels.forEach(label => {
            const option = document.createElement('option');
            option.value = label;
            option.textContent = label;
            nodeLabelsSelect.appendChild(option);
        });

        // Fetch and populate relationship types
        const relResponse = await fetch('/api/relationship-types');
        const relationships = await relResponse.json();
        const relationshipsSelect = document.getElementById('relationships');
        relationshipsSelect.innerHTML = '';
        relationships.forEach(relType => {
            const option = document.createElement('option');
            option.value = relType;
            option.textContent = relType;
            relationshipsSelect.appendChild(option);
        });

        // Fetch and populate locations
        const locationResponse = await fetch('/api/locations');
        const locations = await locationResponse.json();
        const locationSelect = document.getElementById('location');
        locationSelect.innerHTML = '<option value="">All Locations</option>';
        locations.forEach(location => {
            if (location) {
                const option = document.createElement('option');
                option.value = location;
                option.textContent = location;
                locationSelect.appendChild(option);
            }
        });

        // Setup event listeners for filters
        setupFilterEventListeners();
        
    } catch (error) {
        console.error('Error populating filters:', error);
        showError('Failed to load filter options');
    }
}

function setupFilterEventListeners() {
    // Setup search functionality
    document.getElementById('labelSearch')?.addEventListener('input', (e) => {
        filterOptions('nodeLabels', e.target.value);
    });

    document.getElementById('relSearch')?.addEventListener('input', (e) => {
        filterOptions('relationships', e.target.value);
    });

    // Setup clear filters
    document.getElementById('clearFilters')?.addEventListener('click', () => {
        document.getElementById('nodeLabels').selectedIndex = -1;
        document.getElementById('relationships').selectedIndex = -1;
        document.getElementById('location').value = '';
        updateSelectedCounts();
    });

    // Apply filters
    document.getElementById('applyFilters')?.addEventListener('click', () => {
        updateVisualization();
    });

    // Track selected counts
    ['nodeLabels', 'relationships'].forEach(id => {
        document.getElementById(id)?.addEventListener('change', updateSelectedCounts);
    });
}

function filterOptions(selectId, searchText) {
    const select = document.getElementById(selectId);
    const options = select.options;
    
    for (let i = 0; i < options.length; i++) {
        const option = options[i];
        const text = option.text.toLowerCase();
        const search = searchText.toLowerCase();
        
        option.style.display = text.includes(search) ? '' : 'none';
    }
}

function updateSelectedCounts() {
    const labelCount = document.getElementById('labelCount');
    const relCount = document.getElementById('relCount');
    
    if (labelCount) {
        labelCount.textContent = document.getElementById('nodeLabels').selectedOptions.length;
    }
    if (relCount) {
        relCount.textContent = document.getElementById('relationships').selectedOptions.length;
    }
}

async function updateVisualization() {
    const loadingElement = document.getElementById('loading');
    try {
        if (loadingElement) loadingElement.style.display = 'block';

        const nodeLabels = Array.from(document.getElementById('nodeLabels').selectedOptions).map(option => option.value);
        const relationships = Array.from(document.getElementById('relationships').selectedOptions).map(option => option.value);
        const location = document.getElementById('location').value;

        const params = new URLSearchParams();
        if (nodeLabels.length) params.append('labels', nodeLabels.join(','));
        if (relationships.length) params.append('relationships', relationships.join(','));
        if (location) params.append('location', location);

        const response = await fetch(`/api/nodes/filtered?${params}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        if (window.graphViz) {
            window.graphViz.updateData(data);
        }
    } catch (error) {
        console.error('Error updating visualization:', error);
        showError('Failed to update visualization');
    } finally {
        if (loadingElement) loadingElement.style.display = 'none';
    }
}

function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    
    const container = document.querySelector('.main-content');
    container.insertBefore(errorDiv, container.firstChild);
    
    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}

// Initialize visualization when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.graphViz = new GraphVisualization('visualization');
    populateFilters();
    // Load initial data
    updateVisualization();
});