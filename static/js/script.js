function openTab(evt, tabName) {
    const tabContents = document.getElementsByClassName('tab-content');
    for (let i = 0; i < tabContents.length; i++) {
        tabContents[i].classList.remove('active');
    }
    const tabButtons = document.getElementsByClassName('tab-button');
    for (let i = 0; i < tabButtons.length; i++) {
        tabButtons[i].classList.remove('active');
    }
    document.getElementById(tabName).classList.add('active');
    evt.currentTarget.classList.add('active');
}

function generateLocationButtons() {
    const locationContainer = document.getElementById('location-buttons-container');
    for (const region in locationData) {
        if (locationData.hasOwnProperty(region)) {
            const regionDiv = document.createElement('div');
            regionDiv.className = 'location-group';

            const regionTitle = document.createElement('div');
            regionTitle.className = 'location-group-title';
            regionTitle.textContent = region;
            regionDiv.appendChild(regionTitle);

            const buttonContainer = document.createElement('div');
            buttonContainer.className = 'location-buttons';

            locationData[region].forEach(location => {
                const locationButton = document.createElement('button');
                locationButton.className = 'type-button';
                locationButton.textContent = location;
                locationButton.onclick = () => toggleNodesByType(location);
                buttonContainer.appendChild(locationButton);
            });

            regionDiv.appendChild(buttonContainer);
            locationContainer.appendChild(regionDiv);
        }
    }
}

let driver;
let activeTypes = new Set();

async function initDriver() {
    try {
        driver = neo4j.driver(
            "neo4j+s://4e5eeae5.databases.neo4j.io:7687",
            neo4j.auth.basic("neo4j", "Poconoco16!")
        );

        const session = driver.session();
        await session.run("RETURN 1");
        await session.close();

        document.getElementById('status').style.backgroundColor = '#28a745';
        document.getElementById('status').innerHTML = 'Connected to database';
    } catch (error) {
        document.getElementById('status').style.backgroundColor = '#dc3545';
        document.getElementById('status').innerHTML = 'Connection error: ' + error.message;
        console.error('Connection error:', error);
    }
}

async function showRandomNodesWithRelationships() {
    if (!driver) {
        document.getElementById('status').style.backgroundColor = '#dc3545';
        document.getElementById('status').innerHTML = 'Not connected to database';
        return;
    }

    const session = driver.session();
    document.getElementById('status').innerHTML = 'Fetching data...';

    try {
        const result = await session.run(`
                MATCH (n)
                WITH n, rand() as random
                ORDER BY random
                LIMIT 5
                MATCH (n)-[rel]-(m)
                RETURN DISTINCT n, rel, m
                LIMIT 100
            `);

        document.getElementById('status').innerHTML = 'Processing data...';

        const nodes = new Map();
        const links = [];

        result.records.forEach(record => {
            const source = record.get('n');
            const target = record.get('m');
            const relationship = record.get('rel');

            if (!nodes.has(source.identity.toString())) {
                nodes.set(source.identity.toString(), {
                    id: source.identity.toString(),
                    label: source.labels[0],
                    name: source.properties.name || 'Unnamed'
                });
            }

            if (!nodes.has(target.identity.toString())) {
                nodes.set(target.identity.toString(), {
                    id: target.identity.toString(),
                    label: target.labels[0],
                    name: target.properties.name || 'Unnamed'
                });
            }

            links.push({
                source: source.identity.toString(),
                target: target.identity.toString(),
                type: relationship.type
            });
        });

        document.getElementById('status').innerHTML = 'Rendering graph...';
        createForceGraph(Array.from(nodes.values()), links);
        document.getElementById('status').style.backgroundColor = '#28a745';
        document.getElementById('status').innerHTML = 'Graph rendered successfully';

    } catch (error) {
        document.getElementById('status').style.backgroundColor = '#dc3545';
        document.getElementById('status').innerHTML = 'Error: ' + error.message;
        console.error('Error:', error);
    } finally {
        await session.close();
    }
}

function createForceGraph(nodes, links) {
    d3.select("#graph").selectAll("*").remove();

    const width = document.getElementById('graph').clientWidth;
    const height = document.getElementById('graph').clientHeight;

    const svg = d3.select("#graph")
        .append("svg")
        .attr("width", width)
        .attr("height", height);

    const simulation = d3.forceSimulation(nodes)
        .force("link", d3.forceLink(links).id(d => d.id).distance(200))
        .force("charge", d3.forceManyBody().strength(-500))
        .force("center", d3.forceCenter(width / 2, height / 2));

    const link = svg.append("g")
        .selectAll("line")
        .data(links)
        .enter()
        .append("line")
        .attr("class", "link")
        .style("stroke", "#808080")
        .style("stroke-width", 2);

    const linkLabel = svg.append("g")
        .selectAll("text")
        .data(links)
        .enter()
        .append("text")
        .attr("class", "link-label")
        .text(d => d.type);

    const node = svg.append("g")
        .selectAll("g")
        .data(nodes)
        .enter()
        .append("g");

    node.append("circle")
        .attr("r", 30)
        .style("fill", "#cc5500")
        .style("stroke", "#ff6a00")
        .style("stroke-width", 2);

    node.append("text")
        .attr("class", "node-label")
        .attr("dy", ".35em")
        .text(d => d.name)
        .each(function (d) {
            let text = d3.select(this);
            let words = d.name.split(' ');
            let line = [];
            let lineNumber = 0;
            let lineHeight = 1.1;
            let y = text.attr("y");
            let dy = parseFloat(text.attr("dy"));
            let tspan = text.text(null).append("tspan").attr("x", 0).attr("y", y).attr("dy", dy + "em");

            words.forEach(word => {
                line.push(word);
                tspan.text(line.join(" "));
                if (tspan.node().getComputedTextLength() > 50) {
                    line.pop();
                    tspan.text(line.join(" "));
                    line = [word];
                    tspan = text.append("tspan").attr("x", 0).attr("y", y).attr("dy", ++lineNumber * lineHeight + dy + "em").text(word);
                }
            });
        });

    node.call(d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended));

    simulation.on("tick", () => {
        link
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);

        linkLabel
            .attr("x", d => (d.source.x + d.target.x) / 2)
            .attr("y", d => (d.source.y + d.target.y) / 2);

        node
            .attr("transform", d => `translate(${d.x},${d.y})`);
    });

    function dragstarted(d) {
        if (!d3.event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    function dragged(d) {
        d.fx = d3.event.x;
        d.fy = d3.event.y;
    }

    function dragended(d) {
        if (!d3.event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
}

function toggleNodesByType(type) {
    if (activeTypes.has(type)) {
        activeTypes.delete(type);
    } else {
        activeTypes.add(type);
    }
    filterNodes();
    cleanUpRelationships();
}

function filterNodes() {
    d3.select("#graph").selectAll(".node-label").each(function (d) {
        if (activeTypes.has(d.label)) {
            d3.select(this).style("display", "block");
        } else {
            d3.select(this).style("display", "none");
        }
    });

    d3.select("#graph").selectAll("circle").each(function (d) {
        if (activeTypes.has(d.label)) {
            d3.select(this).style("display", "block");
        } else {
            d3.select(this).style("display", "none");
        }
    });

    d3.select("#graph").selectAll(".link").each(function (d) {
        if (activeTypes.has(d.source.label) && activeTypes.has(d.target.label)) {
            d3.select(this).style("display", "block");
        } else {
            d3.select(this).style("display", "none");
        }
    });

    // Hide or show relationship names based on node visibility
    d3.select("#graph").selectAll(".link-label").each(function (d) {
        if (activeTypes.has(d.source.label) && activeTypes.has(d.target.label)) {
            d3.select(this).style("display", "block");
        } else {
            d3.select(this).style("display", "none");
        }
    });
}

function clearNodeTypes() {
    activeTypes.clear();
    filterNodes();
    cleanUpRelationships();
}

function cleanUpRelationships() {
    d3.select("#graph").selectAll(".link").each(function (d) {
        if (activeTypes.has(d.source.label) && activeTypes.has(d.target.label)) {
            d3.select(this).style("display", "block");
        } else {
            d3.select(this).style("display", "none");
        }
    });
}

// Initialize zoom behavior
const zoom = d3.zoom()
    .scaleExtent([0.1, 4]) // Min and max zoom scales
    .on('zoom', (event) => {
        svg.attr('transform', event.transform);
    });

// Apply zoom behavior to the SVG container
const svg = d3.select('#graph-container svg')
    .call(zoom)
    .on("dblclick.zoom", null); // Disable double-click zoom

// Store current transform
let currentTransform = d3.zoomIdentity;

// Zoom in function
function zoomIn() {
    currentTransform = currentTransform.scale(1.2);
    svg.transition()
        .duration(300)
        .call(zoom.transform, currentTransform);
}

// Zoom out function
function zoomOut() {
    currentTransform = currentTransform.scale(0.8);
    svg.transition()
        .duration(300)
        .call(zoom.transform, currentTransform);
}

// Fit all function
function fitAll() {
    const bounds = document.querySelector('#graph-container svg g').getBBox();
    const parent = document.querySelector('#graph-container');
    const fullWidth = parent.clientWidth;
    const fullHeight = parent.clientHeight;
    
    const midX = bounds.x + bounds.width / 2;
    const midY = bounds.y + bounds.height / 2;
    
    // Calculate scale to fit
    const scale = Math.min(
        0.9 * fullWidth / bounds.width,
        0.9 * fullHeight / bounds.height
    );
    
    currentTransform = d3.zoomIdentity
        .translate(fullWidth / 2 - midX * scale, fullHeight / 2 - midY * scale)
        .scale(scale);

    svg.transition()
        .duration(750)
        .call(zoom.transform, currentTransform);
}

// Add touch gesture support
let touchDistance = 0;
let initialScale = 1;

svg.on('touchstart', (event) => {
    if (event.touches.length === 2) {
        touchDistance = Math.hypot(
            event.touches[0].pageX - event.touches[1].pageX,
            event.touches[0].pageY - event.touches[1].pageY
        );
        initialScale = currentTransform.k;
    }
});

svg.on('touchmove', (event) => {
    if (event.touches.length === 2) {
        event.preventDefault();
        
        const newDistance = Math.hypot(
            event.touches[0].pageX - event.touches[1].pageX,
            event.touches[0].pageY - event.touches[1].pageY
        );
        
        const delta = newDistance / touchDistance;
        const newScale = initialScale * delta;
        
        if (newScale >= 0.1 && newScale <= 4) {
            const center = {
                x: (event.touches[0].pageX + event.touches[1].pageX) / 2,
                y: (event.touches[0].pageY + event.touches[1].pageY) / 2
            };
            
            currentTransform = d3.zoomIdentity
                .translate(currentTransform.x, currentTransform.y)
                .scale(newScale);
            
            svg.call(zoom.transform, currentTransform);
        }
    }
});

// Initialize with fit all
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(fitAll, 500); // Slight delay to ensure graph is rendered
});

document.addEventListener('DOMContentLoaded', function() {
    const optionsContainer = document.querySelector('.options-container');
    let selectedButton = null;

    optionsContainer.addEventListener('click', function(e) {
        if (e.target.classList.contains('option-button')) {
            // Remove previous selection
            if (selectedButton) {
                selectedButton.classList.remove('selected');
            }
            
            // Select new button
            e.target.classList.add('selected');
            selectedButton = e.target;
            
            // Get selected value
            const selectedOption = e.target.dataset.option;
            console.log('Selected option:', selectedOption);
        }
    });
});