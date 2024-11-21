<!DOCTYPE html>
<html>
<head>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script src="/static/js/visualization.js"></script>
</head>
<body>
    <div id="visualization"></div>
</body>
</html>



let root;
let chart;

// Initialize the visualization
am5.ready(function() {
    // Create root element
    root = am5.Root.new("chartdiv");
    
    // Set themes
    root.setThemes([am5themes_Animated.new(root)]);
    
    // Create wrapper container
    let container = root.container.children.push(
        am5.Container.new(root, {
            width: am5.percent(100),
            height: am5.percent(100),
            layout: root.verticalLayout
        })
    );
    
    // Create network chart
    chart = container.children.push(
        am5hierarchy.ForceDirected.new(root, {
            downDepth: 1,
            initialDepth: 2,
            valueField: "value",
            categoryField: "name",
            childDataField: "children",
            centerStrength: 0.5,
            minRadius: 20,
            maxRadius: 35,
            linkWithField: "linkWith"
        })
    );
    
    // Node colors based on labels
    const colors = {
        muscle: "#4ECDC4",
        viscera: "#FFB347",
        sense: "#9B59B6",
        artery: "#FF6B6B",
        cv: "#3498DB",
        bone: "#95A5A6",
        neuro: "#2ECC71",
        nerve: "#45B7D1",
        gland: "#E74C3C",
        vein: "#D4A5A5",
        region: "#F1C40F",
        lymph: "#1ABC9C",
        organ: "#96CEB4",
        sensation: "#E67E22"
    };
    
    // Style nodes
    chart.circles.template.setAll({
        toggleKey: "active",
        interactive: true,
        strokeWidth: 2,
        radius: 25,
        fill: function(dataItem) {
            if (dataItem.dataContext.labels && dataItem.dataContext.labels.length > 0) {
                return am5.color(colors[dataItem.dataContext.labels[0].toLowerCase()] || "#999999");
            }
            return am5.color("#999999");
        },
        stroke: am5.color(0x555555),
        tooltipText: "{name}"
    });
    
    // Add hover state
    chart.circles.template.states.create("hover", {
        scale: 1.2,
        fill: am5.color(0xff7f50)
    });
    
    // Style links
    chart.links.template.setAll({
        strokeWidth: 2,
        strokeOpacity: 0.5,
        tooltipText: "{type}"
    });
    
    // Add click listener for zoom
    chart.circles.template.events.on("click", function(ev) {
        const dataItem = ev.target.dataItem;
        if (dataItem) {
            if (dataItem.get("active")) {
                dataItem.set("active", false);
                chart.zoomToDataItem(chart.homeDataItem);
            } else {
                chart.zoomToDataItem(dataItem);
                dataItem.set("active", true);
            }
        }
    });
    
    // Initialize filters
    populateFilters();
});

// Populate filter dropdowns
async function populateFilters() {
    try {
        // Fetch node labels from backend
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

        // Fetch relationship types from backend
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

        // Fetch locations from backend
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
    } catch (error) {
        console.error('Error populating filters:', error);
    }
}

// Call populateFilters when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    populateFilters();
});

// Fetch graph data based on filters
async function fetchGraphData(filters) {
    try {
        const nodeLabels = filters.nodeLabels || [];
        const relationships = filters.relationships || [];
        const location = filters.location;
        
        let query = `
        MATCH (n)
        ${nodeLabels.length ? 'WHERE any(label IN labels(n) WHERE label IN $nodeLabels)' : ''}
        ${location ? 'AND n.location = $location' : ''}
        WITH n
        OPTIONAL MATCH (n)-[r]->(m)
        ${relationships.length ? 'WHERE type(r) IN $relationships' : ''}
        WITH COLLECT(DISTINCT n) + COLLECT(DISTINCT m) as allNodes, 
             COLLECT(DISTINCT r) as allRels
        UNWIND allNodes as node
        WITH DISTINCT node, allRels
        RETURN 
            collect(DISTINCT {
                id: toString(id(node)),
                name: COALESCE(node.name, head(labels(node)) + '_' + id(node)),
                labels: labels(node),
                properties: properties(node)
            }) as nodes,
            [rel IN allRels | {
                id: toString(id(rel)),
                type: type(rel),
                source: toString(startNode(rel).id),
                target: toString(endNode(rel).id),
                properties: properties(rel)
            }] as relationships
        LIMIT 100
        `;
        
        const result = await session.run(query, {
            nodeLabels: nodeLabels,
            relationships: relationships,
            location: location
        });
        
        if (result.records.length === 0) {
            console.log('No data returned from query');
            return [];
        }
        
        return transformNeo4jData(result.records[0].get('nodes'), result.records[0].get('relationships'));
    } catch (error) {
        console.error('Error fetching graph data:', error);
        return [];
    } finally {
        await session.close();
    }
}

// Transform Neo4j data for visualization
function transformNeo4jData(nodes, relationships) {
    const nodesMap = new Map();
    
    // Process nodes
    nodes.forEach(node => {
        nodesMap.set(node.id, {
            id: node.id,
            name: node.name,
            labels: node.labels,
            value: 1,
            children: [],
            linkWith: [],
            properties: node.properties
        });
    });
    
    // Process relationships
    relationships.forEach(rel => {
        const sourceNode = nodesMap.get(rel.source);
        const targetNode = nodesMap.get(rel.target);
        
        if (sourceNode && targetNode) {
            // Add to children array
            sourceNode.children.push(targetNode);
            
            // Add to linkWith array
            if (!sourceNode.linkWith.includes(targetNode.id)) {
                sourceNode.linkWith.push(targetNode.id);
            }
        }
    });
    
    return Array.from(nodesMap.values());
}

function updateVisualization() {
    fetch('/api/nodes/random')
        .then(response => response.json())
        .then(data => {
            console.log('Received data:', data);
            if (!data.nodes || !data.nodes.length) {
                console.error('No nodes received');
                return;
            }
            createForceGraph(data.nodes, data.relationships);
        })
        .catch(error => console.error('Error:', error));
}

function updateVisualization() {
    const nodeLabels = Array.from(document.getElementById('nodeLabels').selectedOptions).map(option => option.value);
    const relationships = Array.from(document.getElementById('relationships').selectedOptions).map(option => option.value);
    const location = document.getElementById('location').value;

    const params = new URLSearchParams();
    nodeLabels.forEach(label => params.append('labels', label));
    relationships.forEach(rel => params.append('relationships', rel));
    if (location) params.append('location', location);

    fetch(`/api/nodes/filtered?${params}`)
        .then(response => response.json())
        .then(data => {
            console.log('Received data:', data);
            visualizeData(data);
        })
        .catch(error => console.error('Error:', error));
}

// Add event listener for the apply filters button
document.getElementById('applyFilters').addEventListener('click', updateVisualization);

// Clean up on page unload
window.addEventListener('unload', () => {
    if (driver) {
        driver.close();
    }
});

function visualizeData(data) {
    console.log('Visualizing data:', data);
    if (!data || !data.nodes || !data.relationships) {
        console.error('Invalid data format:', data);
        return;
    }

    // Your visualization code here
}

function createForceGraph(nodes, links) {
    // Clear any existing visualization
    d3.select('#visualization').selectAll('*').remove();
    
    console.log('Creating visualization with:', {nodes, links});

    // Set explicit dimensions
    const width = 800;
    const height = 600;

    // Create SVG container with explicit size
    const svg = d3.select('#visualization')
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .style('border', '1px solid #ccc'); // Visual debug helper

    // Add container for zoom
    const g = svg.append('g');

    // Add zoom behavior
    const zoom = d3.zoom()
        .on('zoom', (event) => {
            g.attr('transform', event.transform);
        });
    svg.call(zoom);

    // Create simulation
    const simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links).id(d => d.id).distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(30));

    // Create links
    const link = g.append('g')
        .selectAll('line')
        .data(links)
        .enter()
        .append('line')
        .attr('stroke', '#999')
        .attr('stroke-width', 1);

    // Create nodes
    const node = g.append('g')
        .selectAll('g')
        .data(nodes)
        .enter()
        .append('g')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));

    // Add circles to nodes
    node.append('circle')
        .attr('r', 10)
        .attr('fill', '#69b3a2');

    // Add labels to nodes
    node.append('text')
        .attr('dx', 12)
        .attr('dy', '.35em')
        .text(d => d.properties.name || d.labels[0])
        .style('fill', '#fff')
        .style('font-size', '12px');

    // Tick function
    simulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);

        node
            .attr('transform', d => `translate(${d.x},${d.y})`);
    });

    // Drag functions
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

    // Debug logging
    console.log('Visualization created');
}

function visualizeData(data) {
    console.log('Visualizing data:', data);
    if (!data || !data.nodes || !data.relationships) {
        console.error('Invalid data format:', data);
        return;
    }

    const width = document.getElementById('visualization').clientWidth;
    const height = document.getElementById('visualization').clientHeight;

    // Clear previous visualization
    d3.select('#visualization').selectAll('*').remove();

    const svg = d3.select('#visualization')
        .append('svg')
        .attr('width', width)
        .attr('height', height);

    // Create simulation with proper data references
    const simulation = d3.forceSimulation(data.nodes)
        .force('link', d3.forceLink(data.relationships)
            .id(d => d.id)
            .distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(30));

    // Draw relationships
    const link = svg.append('g')
        .selectAll('line')
        .data(data.relationships)
        .enter()
        .append('line')
        .attr('stroke', '#999')
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', 1);

    // Draw nodes
    const node = svg.append('g')
        .selectAll('circle')
        .data(data.nodes)
        .enter()
        .append('circle')
        .attr('r', 5)
        .attr('fill', d => getNodeColor(d.labels[0]))
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));

    // Add node labels
    const labels = svg.append('g')
        .selectAll('text')
        .data(data.nodes)
        .enter()
        .append('text')
        .text(d => d.properties.name || d.labels[0])
        .attr('font-size', '8px')
        .attr('dx', 8)
        .attr('dy', 3)
        .style('fill', '#fff');

    // Update positions on tick
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
            .attr('x', d => d.x + 8)
            .attr('y', d => d.y);
    });
}

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
        'cv': '#1f77b4'
    };
    return colors[label.toLowerCase()] || '#666666';
}

@app.route('/api/labels')
def get_labels():
    try:
        with get_neo4j_driver().session() as session:
            result = session.run('CALL db.labels() YIELD label RETURN label ORDER BY label')
            labels = [record['label'] for record in result]
            return jsonify(labels)
    except Exception as e:
        app.logger.error(f"Error in get_labels: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/relationship-types')
def get_relationship_types():
    try:
        with get_neo4j_driver().session() as session:
            result = session.run('CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType ORDER BY relationshipType')
            relationships = [record['relationshipType'] for record in result]
            return jsonify(relationships)
    except Exception as e:
        app.logger.error(f"Error in get_relationship_types: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/locations')
def get_locations():
    try:
        with get_neo4j_driver().session() as session:
            result = session.run('MATCH (n) WHERE exists(n.location) RETURN DISTINCT n.location AS location ORDER BY location')
            locations = [record['location'] for record in result if record['location']]
            return jsonify(locations)
    except Exception as e:
        app.logger.error(f"Error in get_locations: {str(e)}")
        return jsonify({"error": str(e)}), 500
