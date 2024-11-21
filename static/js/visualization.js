// visualization.js
const driver = neo4j.driver(
    'neo4j+s://4e5eeae5.databases.neo4j.io:7687',
    neo4j.auth.basic('neo4j', 'Poconoco16!')
);

class GraphVisualization {
    constructor() {
        this.width = window.innerWidth - 400; // Accounting for sidebars
        this.height = window.innerHeight;
        
        this.svg = d3.select('#visualization')
            .append('svg')
            .attr('width', this.width)
            .attr('height', this.height);
            
        // Add zoom capabilities
        this.zoom = d3.zoom()
            .scaleExtent([0.1, 10])
            .on('zoom', (event) => {
                this.graphGroup.attr('transform', event.transform);
            });
            
        this.svg.call(this.zoom);
        
        // Create a group for graph elements
        this.graphGroup = this.svg.append('g');
            
        this.simulation = d3.forceSimulation()
            .force('link', d3.forceLink().id(d => d.id).distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2))
            .force('collision', d3.forceCollide().radius(50));
            
        this.nodeFilters = new Set();
        this.locationFilters = new Set();
        
        this.initializeFilters();
    }

    async fetchFilteredData() {
        const session = driver.session();
        try {
            // Build dynamic Cypher query based on filters
            let query = 'MATCH (n)';
            const conditions = [];
            const params = {};

            if (this.nodeFilters.size > 0) {
                conditions.push(`any(label IN labels(n) WHERE label IN $nodeLabels)`);
                params.nodeLabels = Array.from(this.nodeFilters);
            }

            if (this.locationFilters.size > 0) {
                conditions.push('n.location IN $locations');
                params.locations = Array.from(this.locationFilters);
            }

            if (conditions.length > 0) {
                query += ' WHERE ' + conditions.join(' AND ');
            }

            // Find relationships between filtered nodes
            query += `
                WITH n
                MATCH (n)-[r]-(m)
                WHERE id(n) < id(m)
                RETURN DISTINCT n, r, m
            `;

            const result = await session.run(query, params);
            return this.processNeo4jData(result.records);
        } finally {
            await session.close();
        }
    }

    processNeo4jData(records) {
        const nodes = new Map();
        const links = [];
        
        records.forEach(record => {
            const sourceNode = record.get('n');
            const targetNode = record.get('m');
            const relationship = record.get('r');
            
            // Process source node
            const sourceId = sourceNode.identity.toString();
            if (!nodes.has(sourceId)) {
                nodes.set(sourceId, {
                    id: sourceId,
                    labels: sourceNode.labels,
                    properties: sourceNode.properties,
                    // Add more node properties as needed
                });
            }
            
            // Process target node
            const targetId = targetNode.identity.toString();
            if (!nodes.has(targetId)) {
                nodes.set(targetId, {
                    id: targetId,
                    labels: targetNode.labels,
                    properties: targetNode.properties,
                    // Add more node properties as needed
                });
            }
            
            // Process relationship
            links.push({
                source: sourceId,
                target: targetId,
                type: relationship.type,
                properties: relationship.properties
            });
        });
        
        return {
            nodes: Array.from(nodes.values()),
            links: links
        };
    }

    async updateVisualization() {
        const graphData = await this.fetchFilteredData();
        
        // Clear existing visualization
        this.graphGroup.selectAll('*').remove();

        // Create arrow markers for relationships
        this.graphGroup.append('defs').selectAll('marker')
            .data(['end'])
            .join('marker')
            .attr('id', 'arrow')
            .attr('viewBox', '0 -5 10 10')
            .attr('refX', 15)
            .attr('refY', 0)
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .attr('orient', 'auto')
            .append('path')
            .attr('d', 'M0,-5L10,0L0,5')
            .attr('fill', '#999');

        // Create links
        const link = this.graphGroup.append('g')
            .selectAll('line')
            .data(graphData.links)
            .join('line')
            .attr('class', 'link')
            .attr('marker-end', 'url(#arrow)');

        // Create nodes
        const node = this.graphGroup.append('g')
            .selectAll('.node')
            .data(graphData.nodes)
            .join('g')
            .attr('class', 'node')
            .call(this.drag(this.simulation));

        // Add circles for nodes
        node.append('circle')
            .attr('r', 10)
            .attr('fill', d => this.getNodeColor(d.labels[0]));

        // Add labels
        node.append('text')
            .attr('dx', 15)
            .attr('dy', '.35em')
            .text(d => d.properties.name || d.labels[0])
            .attr('font-size', '12px');

        // Add title on hover
        node.append('title')
            .text(d => {
                const props = Object.entries(d.properties)
                    .map(([key, value]) => `${key}: ${value}`)
                    .join('\n');
                return `Labels: ${d.labels.join(', ')}\n${props}`;
            });

        // Update simulation
        this.simulation
            .nodes(graphData.nodes)
            .force('link').links(graphData.links);

        // Handle simulation tick
        this.simulation.on('tick', () => {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            node
                .attr('transform', d => `translate(${d.x},${d.y})`);
        });

        // Restart simulation
        this.simulation.alpha(1).restart();
    }

    drag(simulation) {
        function dragstarted(event) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
        }
        
        function dragged(event) {
            event.subject.fx = event.x;
            event.subject.fy = event.y;
        }
        
        function dragended(event) {
            if (!event.active) simulation.alphaTarget(0);
            event.subject.fx = null;
            event.subject.fy = null;
        }
        
        return d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended);
    }

    async initializeFilters() {
        const session = driver.session();
        try {
            // Fetch all node labels
            const labelResult = await session.run('CALL db.labels()');
            const labels = labelResult.records.map(record => record.get(0));
            
            // Fetch all locations
            const locationResult = await session.run('MATCH (n) WHERE exists(n.location) RETURN DISTINCT n.location');
            const locations = locationResult.records.map(record => record.get(0));
            
            this.createFilterCheckboxes('label-filters', labels, this.nodeFilters);
            this.createFilterCheckboxes('location-filters', locations, this.locationFilters);
        } finally {
            await session.close();
        }
    }

    createFilterCheckboxes(containerId, items, filterSet) {
        const container = document.getElementById(containerId);
        container.innerHTML = ''; // Clear existing checkboxes
        
        items.forEach(item => {
            const div = document.createElement('div');
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.value = item;
            checkbox.id = `checkbox-${item}`;
            
            checkbox.addEventListener('change', async (e) => {
                if (e.target.checked) {
                    filterSet.add(item);
                } else {
                    filterSet.delete(item);
                }
                await this.updateVisualization();
            });
            
            const label = document.createElement('label');
            label.htmlFor = `checkbox-${item}`;
            label.textContent = item;
            
            div.appendChild(checkbox);
            div.appendChild(label);
            container.appendChild(div);
        });
    }

    getNodeColor(label) {
        const colors = {
            Person: '#ff7f0e',
            Location: '#2ca02c',
            Organization: '#1f77b4',
            Event: '#d62728',
            Project: '#9467bd',
            Resource: '#8c564b',
            Task: '#e377c2'
        };
        return colors[label] || '#999';
    }
}

// Initialize the visualization
const visualization = new GraphVisualization();