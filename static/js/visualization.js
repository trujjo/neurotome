// static/js/visualization.js

document.addEventListener('DOMContentLoaded', () => {
    populateFilters();
});

// Populate filter dropdowns
async function populateFilters() {
    try {
        // Fetch node labels from backend
        const labelResponse = await fetch('/api/labels');
        const labels = await labelResponse.json();
        const labelFilters = document.getElementById('label-filters');
        labelFilters.innerHTML = '';
        labels.forEach(label => {
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `label-${label}`;
            checkbox.value = label;
            const labelElement = document.createElement('label');
            labelElement.htmlFor = `label-${label}`;
            labelElement.textContent = label;
            labelFilters.appendChild(checkbox);
            labelFilters.appendChild(labelElement);
            labelFilters.appendChild(document.createElement('br'));
        });

        // Fetch locations from backend
        const locationResponse = await fetch('/api/locations');
        const locations = await locationResponse.json();
        const locationFilters = document.getElementById('location-filters');
        locationFilters.innerHTML = '';
        locations.forEach(location => {
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `location-${location}`;
            checkbox.value = location;
            const labelElement = document.createElement('label');
            labelElement.htmlFor = `location-${location}`;
            labelElement.textContent = location;
            locationFilters.appendChild(checkbox);
            locationFilters.appendChild(labelElement);
            locationFilters.appendChild(document.createElement('br'));
        });
    } catch (error) {
        console.error('Error populating filters:', error);
    }
}

// Fetch graph data based on filters
async function fetchGraphData(filters) {
    const params = new URLSearchParams(filters);
    const response = await fetch(`/api/nodes/filtered?${params}`);
    return response.json();
}

// Update the visualization based on selected filters
function updateVisualization() {
    const selectedLabels = Array.from(document.querySelectorAll('#label-filters input:checked')).map(checkbox => checkbox.value);
    const selectedLocations = Array.from(document.querySelectorAll('#location-filters input:checked')).map(checkbox => checkbox.value);

    const filters = {};
    if (selectedLabels.length) filters.labels = selectedLabels;
    if (selectedLocations.length) filters.locations = selectedLocations;

    fetchGraphData(filters)
        .then(data => {
            console.log('Received data:', data);
            visualizeData(data);
        })
        .catch(error => console.error('Error fetching data:', error));
}

// Visualize the data using D3.js
function visualizeData(data) {
    console.log('Visualizing data:', data);
    if (!data || !data.nodes || !data.relationships) {
        console.error('Invalid data format:', data);
        return;
    }

    // Clear previous visualization
    d3.select('#visualization').selectAll('*').remove();

    const width = document.getElementById('visualization').clientWidth || 800;
    const height = document.getElementById('visualization').clientHeight || 600;

    const svg = d3.select('#visualization')
        .append('svg')
        .attr('width', width)
        .attr('height', height);

    // Create simulation
    const simulation = d3.forceSimulation(data.nodes)
        .force('link', d3.forceLink(data.relationships).id(d => d.id).distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(30));

    // Add links
    const link = svg.append('g')
        .selectAll('line')
        .data(data.relationships)
        .enter()
        .append('line')
        .attr('stroke', '#999')
        .attr('stroke-width', 1)
        .attr('stroke-opacity', 0.6);

    // Add nodes
    const node = svg.append('g')
        .selectAll('circle')
        .data(data.nodes)
        .enter()
        .append('circle')
        .attr('r', 10)
        .attr('fill', d => getNodeColor(d.labels[0]))
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));

    // Add labels
    const labels = svg.append('g')
        .selectAll('text')
        .data(data.nodes)
        .enter()
        .append('text')
        .text(d => d.properties.name || d.labels[0])
        .attr('dx', 12)
        .attr('dy', '.35em')
        .style('fill', '#000')
        .style('font-size', '12px');

    // Simulation tick function
    simulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);

        node
            .attr('cx', d => d.x)
            .attr('cy', d => d.y);

        labels
            .attr('x', d => d.x)
            .attr('y', d => d.y);
    });

    // Drag event handlers
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

// Helper function to assign colors based on node labels
function getNodeColor(label) {
    const colors = {
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
        // Add more labels and colors as needed
    };
    return colors[label.toLowerCase()] || '#666666';
}

// Add event listener for the apply filters button
document.getElementById('applyFilters').addEventListener('click', updateVisualization);