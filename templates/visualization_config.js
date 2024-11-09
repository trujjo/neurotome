# Create the complete frontend code
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
        this.setupFilterListeners();
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
            .on('tick', () => this.ticked());
    }

    initializeTooltip() {
        this.tooltip = d3.select('body').append('div')
            .attr('class', 'tooltip')
            .style('opacity', 0)
            .style('position', 'absolute')
            .style('pointer-events', 'none')
            .style('background', 'white')
            .style('padding', '5px')
            .style('border', '1px solid #ccc')
            .style('border-radius', '5px');
    }

    setupFilterListeners() {
        // Set up event listeners for filters
        ['nodeTypeFilter', 'locationFilter', 'sublocationFilter'].forEach(filterId => {
            const filter = document.getElementById(filterId);
            if (filter) {
                filter.addEventListener('change', () => this.updateFilters());
            }
        });
    }

    updateData(nodes, relationships) {
        // Stop the current simulation
        if (this.simulation) {
            this.simulation.stop();
        }

        // Clear existing elements
        this.graphGroup.selectAll('*').remove();

        // Create the links
        this.links = this.graphGroup.append('g')
            .selectAll('line')
            .data(relationships)
            .enter()
            .append('line')
            .attr('stroke', '#999')
            .attr('stroke-opacity', 0.6);

        // Create the nodes
        this.nodes = this.graphGroup.append('g')
            .selectAll('circle')
            .data(nodes)
            .enter()
            .append('circle')
            .attr('r', 5)
            .attr('fill', d => this.getNodeColor(d))
            .call(d3.drag()
                .on('start', (event, d) => this.dragstarted(event, d))
                .on('drag', (event, d) => this.dragged(event, d))
                .on('end', (event, d) => this.dragended(event, d)))
            .on('mouseover', (event, d) => this.showTooltip(event, d))
            .on('mouseout', () => this.hideTooltip());

        // Update simulation
        this.simulation.nodes(nodes);
        this.simulation.force('link').links(relationships);
        this.simulation.alpha(1).restart();
    }

    updateFilters() {
        const selectedNodeTypes = Array.from(document.querySelectorAll('#nodeTypeFilter option:checked')).map(opt => opt.value);
        const selectedLocations = Array.from(document.querySelectorAll('#locationFilter option:checked')).map(opt => opt.value);
        const selectedSublocations = Array.from(document.querySelectorAll('#sublocationFilter option:checked')).map(opt => opt.value);

        const params = new URLSearchParams();
        selectedNodeTypes.forEach(type => params.append('nodeTypes[]', type));
        selectedLocations.forEach(location => params.append('locations[]', location));
        selectedSublocations.forEach(sublocation => params.append('sublocations[]', sublocation));

        fetch(`/api/graph/filtered?${params.toString()}`)
            .then(response => response.json())
            .then(data => {
                this.updateData(data.nodes, data.relationships);
            })
            .catch(error => console.error('Error updating filters:', error));
    }

    getNodeColor(node) {
        const label = node.labels[0].toLowerCase();
        return this.colorMap[label] || this.colorMap.default;
    }

    ticked() {
        if (this.links) {
            this.links
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
        }

        if (this.nodes) {
            this.nodes
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);
        }
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
        const properties = Object.entries(d.properties || {})
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

// Initialize filters when the page loads
document.addEventListener('DOMContentLoaded', () => {
    // Create visualization instance
    window.viz = new NeoViz('#visualization');
    
    // Populate filters
    populateFilters();
});

function populateFilters() {
    // Fetch all distinct node types
    fetch('/api/nodes/types')
        .then(response => response.json())
        .then(types => {
            const typeFilter = document.getElementById('nodeTypeFilter');
            types.forEach(type => {
                const option = document.createElement('option');
                option.value = type;
                option.textContent = type;
                typeFilter.appendChild(option);
            });
        })
        .catch(error => console.error('Error loading node types:', error));

    // Fetch all distinct locations
    fetch('/api/nodes/locations')
        .then(response => response.json())
        .then(locations => {
            const locationFilter = document.getElementById('locationFilter');
            locations.forEach(location => {
                const option = document.createElement('option');
                option.value = location;
                option.textContent = location;
                locationFilter.appendChild(option);
            });
        })
        .catch(error => console.error('Error loading locations:', error));

    // Fetch all distinct sublocations
    fetch('/api/nodes/sublocations')
        .then(response => response.json())
        .then(sublocations => {
            const sublocationFilter = document.getElementById('sublocationFilter');
            sublocations.forEach(sublocation => {
                const option = document.createElement('option');
                option.value = sublocation;
                option.textContent = sublocation;
                sublocationFilter.appendChild(option);
            });
        })
        .catch(error => console.error('Error loading sublocations:', error));
}

with open('visualization_config.js', 'w') as f:
    f.write(frontend_code)

print("Created updated visualization_config.js with the following improvements:")
print("1. Added complete NeoViz class implementation")
print("2. Added proper error handling for API calls")
print("3. Added filter setup and initialization")
print("4. Added proper event handling for filters")
print("5. Added resize handling")
print("6. Added proper tooltip implementation")
