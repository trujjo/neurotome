// Neo4j connection
const driver = neo4j.driver(
    'neo4j+s://4e5eeae5.databases.neo4j.io:7687',
    neo4j.auth.basic('neo4j', 'Poconoco16!')
);

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
    
    // Generate and set data
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
    
    // First pass: Collect all nodes
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
    
    // Set up series for different node types
    chart.circles.template.setAll({
        toggleKey: "active",
        interactive: true,
        strokeWidth: 2,
        radius: 25,
        fill: am5.color(0x6794dc),
        stroke: am5.color(0x555555)
    });
    
    // Add hover state
    chart.circles.template.states.create("hover", {
        scale: 1.2,
        fill: am5.color(0xff7f50)
    });
    
    // Add click listener to zoom
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
    
    // Style the links
    chart.links.template.setAll({
        strokeWidth: 2,
        strokeOpacity: 0.5
    });
}

// Initialize locations dropdown
async function initializeLocations() {
    const session = driver.session();
    try {
        const result = await session.run(`
            MATCH (n)
            WHERE exists(n.location)
            RETURN DISTINCT n.location AS location
            ORDER BY location
        `);
        
        const locationSelect = document.getElementById('location');
        result.records.forEach(record => {
            const location = record.get('location');
            if (location) {
                const option = document.createElement('option');
                option.value = location;
                option.textContent = location;
                locationSelect.appendChild(option);
            }
        });
    } finally {
        await session.close();
    }
}

// Call initializeLocations when the page loads
document.addEventListener('DOMContentLoaded', initializeLocations);

// Clean up on page unload
window.addEventListener('unload', () => {
    if (driver) {
        driver.close();
    }
});