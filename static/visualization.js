// Initialize Neo4j driver
const driver = neo4j.driver(
    'neo4j+s://4e5eeae5.databases.neo4j.io:7687',
    neo4j.auth.basic('neo4j', 'Poconoco16!')
);

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
    const session = driver.session();
    try {
        // Fetch node labels
        const labelResult = await session.run('CALL db.labels() YIELD label RETURN label ORDER BY label');
        const nodeLabelsSelect = document.getElementById('nodeLabels');
        nodeLabelsSelect.innerHTML = '';
        labelResult.records.forEach(record => {
            const option = document.createElement('option');
            option.value = record.get('label');
            option.textContent = record.get('label');
            nodeLabelsSelect.appendChild(option);
        });

        // Fetch relationship types
        const relResult = await session.run('CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType ORDER BY relationshipType');
        const relationshipsSelect = document.getElementById('relationships');
        relationshipsSelect.innerHTML = '';
        relResult.records.forEach(record => {
            const option = document.createElement('option');
            option.value = record.get('relationshipType');
            option.textContent = record.get('relationshipType');
            relationshipsSelect.appendChild(option);
        });

        // Fetch locations
        const locationResult = await session.run('MATCH (n) WHERE exists(n.location) RETURN DISTINCT n.location AS location ORDER BY location');
        const locationSelect = document.getElementById('location');
        locationSelect.innerHTML = '<option value="">All Locations</option>';
        locationResult.records.forEach(record => {
            const location = record.get('location');
            if (location) {
                const option = document.createElement('option');
                option.value = location;
                option.textContent = location;
                locationSelect.appendChild(option);
            }
        });
    } catch (error) {
        console.error('Error populating filters:', error);
    } finally {
        await session.close();
    }
}

// Fetch graph data based on filters
async function fetchGraphData(filters) {
    const session = driver.session();
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