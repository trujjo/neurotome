// Neo4j connection and visualization setup
let root;
let chart;

// Initialize the chart
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
    
    // Set up node colors based on labels
    const colors = {
        artery: "#FF6B6B",
        muscle: "#4ECDC4",
        nerve: "#45B7D1",
        organ: "#96CEB4",
        vein: "#D4A5A5"
    };
    
    // Style nodes
    chart.circles.template.setAll({
        toggleKey: "active",
        interactive: true,
        strokeWidth: 2,
        radius: 25,
        fill: function(dataItem) {
            return am5.color(colors[dataItem.dataContext.label.toLowerCase()] || "#999999");
        },
        stroke: am5.color(0x555555)
    });
    
    // Add hover state
    chart.circles.template.states.create("hover", {
        scale: 1.2,
        fill: am5.color(0xff7f50)
    });
    
    // Style links
    chart.links.template.setAll({
        strokeWidth: 2,
        strokeOpacity: 0.5
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
    
    // Initial data fetch
    updateVisualization();
});

async function fetchGraphData(filters) {
    const session = driver.session();
    try {
        const nodeLabels = filters.nodeLabels || [];
        const relationships = filters.relationships || [];
        const location = filters.location;
        
        let query = `
        MATCH (n)
        WHERE ${nodeLabels.length ? 'any(label IN labels(n) WHERE label IN $nodeLabels)' : 'true'}
        ${location ? 'AND n.location = $location' : ''}
        WITH n
        OPTIONAL MATCH (n)-[r]->(m)
        WHERE ${relationships.length ? 'type(r) IN $relationships' : 'true'}
        RETURN n, r, m
        LIMIT 100
        `;
        
        const result = await session.run(query, {
            nodeLabels: nodeLabels,
            relationships: relationships,
            location: location
        });
        
        return transformNeo4jData(result.records);
    } finally {
        await session.close();
    }
}

function transformNeo4jData(records) {
    const nodes = new Map();
    const relationships = new Set();
    
    // First pass: Collect nodes
    records.forEach(record => {
        const startNode = record.get('n');
        const endNode = record.get('m');
        
        if (!nodes.has(startNode.identity.toString())) {
            nodes.set(startNode.identity.toString(), {
                id: startNode.identity.toString(),
                name: startNode.properties.name || startNode.labels[0] + '_' + startNode.identity,
                label: startNode.labels[0],
                value: 1,
                children: []
            });
        }
        
        if (endNode && !nodes.has(endNode.identity.toString())) {
            nodes.set(endNode.identity.toString(), {
                id: endNode.identity.toString(),
                name: endNode.properties.name || endNode.labels[0] + '_' + endNode.identity,
                label: endNode.labels[0],
                value: 1,
                children: []
            });
        }
    });
    
    // Second pass: Build relationships
    records.forEach(record => {
        const rel = record.get('r');
        if (rel) {
            const startNodeId = rel.startNodeIdentity.toString();
            const endNodeId = rel.endNodeIdentity.toString();
            
            const startNode = nodes.get(startNodeId);
            const endNode = nodes.get(endNodeId);
            
            if (startNode && endNode) {
                startNode.children.push(endNode);
                relationships.add(`${startNodeId}-${endNodeId}`);
            }
        }
    });
    
    // Convert to array and add linkWith property
    const nodesArray = Array.from(nodes.values());
    nodesArray.forEach(node => {
        node.linkWith = Array.from(relationships)
            .filter(rel => rel.startsWith(node.id))
            .map(rel => rel.split('-')[1]);
    });
    
    return nodesArray;
}

async function updateVisualization() {
    const filters = {
        nodeLabels: Array.from(document.getElementById('nodeLabels').selectedOptions).map(opt => opt.value),
        relationships: Array.from(document.getElementById('relationships').selectedOptions).map(opt => opt.value),
        location: document.getElementById('location').value
    };
    
    const data = await fetchGraphData(filters);
    chart.data.setAll(data);
}

// Add event listener for the apply filters button
document.getElementById('applyFilters').addEventListener('click', updateVisualization);