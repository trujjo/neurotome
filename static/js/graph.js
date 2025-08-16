
class GraphVisualization {
    constructor() {
        this.nodes = [];
        this.links = [];
        this.simulation = null;
        this.svg = null;
        this.width = 0;
        this.height = 0;
        this.init();
    }

    init() {
        this.checkDatabaseStatus();
        this.setupEventListeners();
    }

    setupEventListeners() {
        document.addEventListener('DOMContentLoaded', () => {
            const randomButton = document.getElementById('randomButton');
            if (randomButton) {
                randomButton.addEventListener('click', () => this.loadRandomNodes());
            }
        });
    }

    async checkDatabaseStatus() {
        try {
            this.updateStatus('Checking database connection...', 'info');
            
            const response = await fetch('/api/neo4j/status');
            const data = await response.json();
            
            if (response.ok) {
                this.updateStatus(
                    `Connected to ${data.database_info?.name || 'Neo4j'} (${data.database_info?.version || 'Unknown version'})`,
                    'success'
                );
            } else {
                throw new Error(data.error || 'Connection failed');
            }
        } catch (error) {
            this.updateStatus(`Database connection error: ${error.message}`, 'error');
            console.error('Database status check failed:', error);
        }
    }

    async loadRandomNodes() {
        try {
            this.updateStatus('Fetching random nodes...', 'info');
            
            const response = await fetch('/api/nodes/random');
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || `HTTP ${response.status}`);
            }
            
            const data = await response.json();
            this.processGraphData(data);
            
        } catch (error) {
            this.updateStatus(`Error loading nodes: ${error.message}`, 'error');
            console.error('Failed to load nodes:', error);
        }
    }

    processGraphData(data) {
        this.updateStatus('Processing graph data...', 'info');
        
        const nodeMap = new Map();
        const links = [];

        data.forEach(record => {
            const sourceNode = record.n;
            const targetNode = record.m;
            const relationship = record.rel;

            // Add source node
            if (!nodeMap.has(sourceNode.id)) {
                nodeMap.set(sourceNode.id, {
                    id: sourceNode.id,
                    labels: sourceNode.labels,
                    properties: sourceNode.properties,
                    name: sourceNode.properties.name || 
                          sourceNode.properties.title || 
                          `${sourceNode.labels[0] || 'Node'} ${sourceNode.id}`
                });
            }

            // Add target node
            if (!nodeMap.has(targetNode.id)) {
                nodeMap.set(targetNode.id, {
                    id: targetNode.id,
                    labels: targetNode.labels,
                    properties: targetNode.properties,
                    name: targetNode.properties.name || 
                          targetNode.properties.title || 
                          `${targetNode.labels[0] || 'Node'} ${targetNode.id}`
                });
            }

            // Add relationship
            links.push({
                source: sourceNode.id,
                target: targetNode.id,
                type: relationship.type,
                properties: relationship.properties || {}
            });
        });

        this.nodes = Array.from(nodeMap.values());
        this.links = links;

        this.renderGraph();
        this.updateStatus(`Graph rendered: ${this.nodes.length} nodes, ${this.links.length} relationships`, 'success');
    }

    renderGraph() {
        this.clearGraph();
        this.setupSVG();
        this.createForceSimulation();
        this.drawGraph();
    }

    clearGraph() {
        d3.select("#graph").selectAll("*").remove();
    }

    setupSVG() {
        const container = document.getElementById('graph');
        this.width = container.clientWidth;
        this.height = container.clientHeight;

        this.svg = d3.select("#graph")
            .append("svg")
            .attr("width", this.width)
            .attr("height", this.height);

        // Add zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on("zoom", (event) => {
                this.svg.selectAll("g").attr("transform", event.transform);
            });

        this.svg.call(zoom);
    }

    createForceSimulation() {
        this.simulation = d3.forceSimulation(this.nodes)
            .force("link", d3.forceLink(this.links).id(d => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(this.width / 2, this.height / 2))
            .force("collision", d3.forceCollide().radius(30));
    }

    drawGraph() {
        const container = this.svg.append("g");

        // Draw links
        const link = container.append("g")
            .attr("class", "links")
            .selectAll("line")
            .data(this.links)
            .enter().append("line")
            .attr("stroke", "#999")
            .attr("stroke-opacity", 0.6)
            .attr("stroke-width", 2);

        // Draw link labels
        const linkLabel = container.append("g")
            .attr("class", "link-labels")
            .selectAll("text")
            .data(this.links)
            .enter().append("text")
            .attr("font-size", "10px")
            .attr("fill", "#666")
            .attr("text-anchor", "middle")
            .text(d => d.type);

        // Draw nodes
        const node = container.append("g")
            .attr("class", "nodes")
            .selectAll("circle")
            .data(this.nodes)
            .enter().append("circle")
            .attr("r", 15)
            .attr("fill", d => this.getNodeColor(d.labels[0]))
            .attr("stroke", "#fff")
            .attr("stroke-width", 2)
            .call(this.createDragBehavior());

        // Draw node labels
        const nodeLabel = container.append("g")
            .attr("class", "node-labels")
            .selectAll("text")
            .data(this.nodes)
            .enter().append("text")
            .attr("font-size", "12px")
            .attr("fill", "#fff")
            .attr("text-anchor", "middle")
            .attr("dy", 4)
            .text(d => this.truncateText(d.name, 15));

        // Add tooltips
        node.append("title")
            .text(d => `${d.labels.join(', ')}\n${JSON.stringify(d.properties, null, 2)}`);

        // Update positions on simulation tick
        this.simulation.on("tick", () => {
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            linkLabel
                .attr("x", d => (d.source.x + d.target.x) / 2)
                .attr("y", d => (d.source.y + d.target.y) / 2);

            node
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);

            nodeLabel
                .attr("x", d => d.x)
                .attr("y", d => d.y);
        });
    }

    createDragBehavior() {
        return d3.drag()
            .on("start", (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            })
            .on("drag", (event, d) => {
                d.fx = event.x;
                d.fy = event.y;
            })
            .on("end", (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            });
    }

    getNodeColor(label) {
        const colors = {
            'Person': '#ff6b6b',
            'Organization': '#4ecdc4',
            'Location': '#45b7d1',
            'Event': '#96ceb4',
            'Document': '#ffeaa7',
            'Concept': '#dda0dd',
            'default': '#74b9ff'
        };
        return colors[label] || colors.default;
    }

    truncateText(text, maxLength) {
        if (!text) return '';
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    }

    updateStatus(message, type = 'info') {
        const statusElement = document.getElementById('status');
        if (!statusElement) return;

        statusElement.textContent = message;
        
        // Remove existing status classes
        statusElement.className = statusElement.className.replace(/\b(status-\w+)\b/g, '');
        
        // Add new status class
        statusElement.classList.add(`status-${type}`);
        
        // Set background color based on type
        const colors = {
            'success': '#28a745',
            'error': '#dc3545',
            'info': '#17a2b8',
            'warning': '#ffc107'
        };
        
        statusElement.style.backgroundColor = colors[type] || colors.info;
    }
}

// Initialize the graph visualization when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.graphViz = new GraphVisualization();
});

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
        .each(function(d) {
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
    d3.select("#graph").selectAll(".node-label").each(function(d) {
        if (activeTypes.has(d.label)) {
            d3.select(this).style("display", "block");
        } else {
            d3.select(this).style("display", "none");
        }
    });

    d3.select("#graph").selectAll("circle").each(function(d) {
        if (activeTypes.has(d.label)) {
            d3.select(this).style("display", "block");
        } else {
            d3.select(this).style("display", "none");
        }
    });

    d3.select("#graph").selectAll(".link").each(function(d) {
        if (activeTypes.has(d.source.label) && activeTypes.has(d.target.label)) {
            d3.select(this).style("display", "block");
        } else {
            d3.select(this).style("display", "none");
        }
    });

    // Hide or show relationship names based on node visibility
    d3.select("#graph").selectAll(".link-label").each(function(d) {
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
    d3.select("#graph").selectAll(".link").each(function(d) {
        if (activeTypes.has(d.source.label) && activeTypes.has(d.target.label)) {
            d3.select(this).style("display", "block");
        } else {
            d3.select(this).style("display", "none");
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    initDriver();
    generateLocationButtons();
});

window.onbeforeunload = () => {
    if (driver) {
        driver.close();
    }
};