let driver;
let simulation;

// Initialize Neo4j connection
async function initNeo4j() {
    try {
        driver = neo4j.driver(NEO4J_URI, neo4j.auth.basic(NEO4J_USER, NEO4J_PASSWORD));
        await driver.verifyConnectivity();
        console.log("Connected to Neo4j successfully");
        initializeFilters();
        updateVisualization();
    } catch (error) {
        showError("Failed to connect to Neo4j: " + error.message);
    }
}

function showError(message) {
    const errorContainer = document.getElementById('error-container');
    errorContainer.innerHTML = `<div class="error-message">${message}</div>`;
}

function initializeFilters() {
    // Initialize tissue type filters
    const tissueFiltersContainer = document.getElementById('tissue-filters');
    tissueTypes.forEach(tissue => {
        const checkbox = document.createElement('label');
        checkbox.className = 'filter-checkbox';
        checkbox.innerHTML = `
            <input type="checkbox" value="${tissue}" checked>
            <span>${tissue}</span>
        `;
        tissueFiltersContainer.appendChild(checkbox);
    });

    // Initialize location filters
    const locationSelect = document.getElementById('location-select');
    Object.keys(locationData).forEach(location => {
        const option = document.createElement('option');
        option.value = location;
        option.textContent = location;
        locationSelect.appendChild(option);
    });

    // Initialize relationship filters
    const relationshipFiltersContainer = document.getElementById('relationship-filters');
    relationships.forEach(rel => {
        const checkbox = document.createElement('label');
        checkbox.className = 'filter-checkbox';
        checkbox.innerHTML = `
            <input type="checkbox" value="${rel}" checked>
            <span>${rel}</span>
        `;
        relationshipFiltersContainer.appendChild(checkbox);
    });

    // Add event listeners
    locationSelect.addEventListener('change', updateSublocations);
    document.querySelectorAll('.filter-checkbox input').forEach(checkbox => {
        checkbox.addEventListener('change', updateVisualization);
    });
}

async function updateVisualization() {
    try {
        const selectedTissues = Array.from(document.querySelectorAll('#tissue-filters input:checked')).map(cb => cb.value);
        const selectedLocation = document.getElementById('location-select').value;
        const selectedSublocation = document.getElementById('sublocation-select').value;
        const selectedRelationships = Array.from(document.querySelectorAll('#relationship-filters input:checked')).map(cb => cb.value);

        if (selectedTissues.length === 0) {
            showError("Please select at least one tissue type");
            return;
        }

        const session = driver.session();
        try {
            const query = `
                MATCH (n)-[r]->(m)
                WHERE any(label IN labels(n) WHERE label IN $tissueTypes)
                AND any(label IN labels(m) WHERE label IN $tissueTypes)
                AND type(r) IN $relationships
                ${selectedLocation !== 'all' ? "AND (n.location = $location OR m.location = $location)" : ''}
                ${selectedSublocation !== 'all' ? "AND (n.sublocation = $sublocation OR m.sublocation = $sublocation)" : ''}
                RETURN n, r, m
            `;

            const result = await session.run(query, {
                tissueTypes: selectedTissues,
                relationships: selectedRelationships,
                location: selectedLocation,
                sublocation: selectedSublocation
            });

            renderGraph(result.records);
        } finally {
            await session.close();
        }
    } catch (error) {
        showError("Error updating visualization: " + error.message);
    }
}

function renderGraph(records) {
    const nodes = new Set();
    const links = [];
    
    records.forEach(record => {
        const source = record.get('n');
        const target = record.get('m');
        const relationship = record.get('r');
        
        nodes.add(source);
        nodes.add(target);
        links.push({
            source: source,
            target: target,
            type: relationship.type
        });
    });

    const width = document.getElementById('graph-container').clientWidth;
    const height = document.getElementById('graph-container').clientHeight;

    // Clear existing graph
    d3.select("#graph-container").selectAll("*").remove();

    const svg = d3.select("#graph-container")
        .append("svg")
        .attr("width", width)
        .attr("height", height);

    if (simulation) {
        simulation.stop();
    }

    simulation = d3.forceSimulation(Array.from(nodes))
        .force("link", d3.forceLink(links).id(d => d.identity))
        .force("charge", d3.forceManyBody().strength(-100))
        .force("center", d3.forceCenter(width / 2, height / 2));

    const link = svg.append("g")
        .selectAll("line")
        .data(links)
        .enter().append("line")
        .attr("stroke", "#999")
        .attr("stroke-opacity", 0.6);

    const node = svg.append("g")
        .selectAll("circle")
        .data(Array.from(nodes))
        .enter().append("circle")
        .attr("r", 5)
        .attr("fill", "#69b3a2");

    simulation.on("tick", () => {
        link
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);

        node
            .attr("cx", d => d.x)
            .attr("cy", d => d.y);
    });
}

function updateSublocations() {
    const locationSelect = document.getElementById('location-select');
    const sublocationSelect = document.getElementById('sublocation-select');
    const selectedLocation = locationSelect.value;
    
    sublocationSelect.innerHTML = '<option value="all">All Sublocations</option>';
    
    if (selectedLocation !== 'all') {
        locationData[selectedLocation].forEach(sublocation => {
            const option = document.createElement('option');
            option.value = sublocation;
            option.textContent = sublocation;
            sublocationSelect.appendChild(option);
        });
    }
    
    updateVisualization();
}

// Initialize the visualization
document.addEventListener('DOMContentLoaded', initNeo4j);
