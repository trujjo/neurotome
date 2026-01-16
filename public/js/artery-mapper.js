class ArteryMapper {
    constructor() {
        this.arteries = [];
        this.allItems = [];
        this.currentView = 'simple';
        this.graphData = null;
        this.simulation = null;
        
        this.initializeElements();
        this.attachEventListeners();
        this.loadData();
    }

    initializeElements() {
        this.startSelect = document.getElementById('start-select');
        this.endSelect = document.getElementById('end-select');
        this.findPathBtn = document.getElementById('find-path-btn');
        this.resultsSection = document.getElementById('results-section');
        this.arteryCount = document.getElementById('artery-count');
        this.viewBtns = document.querySelectorAll('.view-btn');
    }

    attachEventListeners() {
        this.findPathBtn.addEventListener('click', () => this.findPath());
        
        this.viewBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const view = e.target.dataset.view;
                this.switchView(view);
            });
        });
    }

    async loadData() {
        try {
            const [arteriesRes, allItemsRes, statsRes] = await Promise.all([
                fetch('/api/arteries/only'),
                fetch('/api/arteries/all'),
                fetch('/api/stats?label=artery')
            ]);

            this.arteries = await arteriesRes.json();
            this.allItems = await allItemsRes.json();
            const stats = await statsRes.json();

            this.populateDropdowns();
            this.arteryCount.textContent = stats.count || 0;
        } catch (error) {
            console.error('Error loading data:', error);
            this.showError('Failed to load data');
        }
    }

    populateDropdowns() {
        const createOptions = (items) => 
            items.map(item => `<option value="${item.name}">${item.name}</option>`).join('');

        this.startSelect.innerHTML = '<option value="">Select start artery...</option>' + createOptions(this.arteries);
        this.endSelect.innerHTML = '<option value="">Select end artery...</option>' + createOptions(this.allItems);
    }

    async findPath() {
        const start = this.startSelect.value;
        const end = this.endSelect.value;

        if (!start || !end) {
            this.showMessage('Please select both start and end arteries');
            return;
        }

        try {
            const response = await fetch('/api/path/find', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ start, end })
            });

            if (!response.ok) {
                throw new Error('Path not found');
            }

            const data = await response.json();
            this.displayResults(data);
        } catch (error) {
            console.error('Error finding path:', error);
            this.showError('No path found between these arteries');
        }
    }

    displayResults(data) {
        this.currentData = data;
        
        switch(this.currentView) {
            case 'simple':
                this.renderSimpleView(data);
                break;
            case 'detailed':
                this.renderDetailedView(data);
                break;
            case 'graph':
                this.renderGraphView(data);
                break;
        }
    }

    renderSimpleView(data) {
        const path = data.arteries.map(a => a.name).join(' → ');
        this.resultsSection.innerHTML = `
            <div class="path-result">
                <div class="path-header">
                    <h3>Path Found (${data.distance} steps)</h3>
                </div>
                <div class="path-simple">${path}</div>
            </div>
        `;
    }

    renderDetailedView(data) {
        const steps = data.arteries.map((artery, i) => {
            const relationship = i < data.relationships.length ? data.relationships[i] : null;
            const direction = i < data.directions.length ? data.directions[i] : null;
            
            return `
                <div class="path-step">
                    <div class="step-number">${i + 1}</div>
                    <div class="step-content">
                        <div class="step-artery">${artery.name}</div>
                        ${relationship ? `
                            <div class="step-relationship">
                                <span class="relationship-type">${relationship}</span>
                                <span class="relationship-direction">${direction === 'forward' ? '↓' : '↑'}</span>
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }).join('');

        this.resultsSection.innerHTML = `
            <div class="path-result">
                <div class="path-header">
                    <h3>Detailed Path (${data.distance} steps)</h3>
                </div>
                <div class="path-detailed">${steps}</div>
            </div>
        `;
    }

    async renderGraphView(data) {
        if (!this.graphData) {
            await this.loadFullGraph();
        }

        const pathIds = new Set(data.arteries.map(a => a.id));
        const highlightedNodes = this.graphData.nodes.filter(n => pathIds.has(n.id));
        const highlightedLinks = this.graphData.links.filter(l => 
            pathIds.has(l.source.id || l.source) && pathIds.has(l.target.id || l.target)
        );

        this.resultsSection.innerHTML = `
            <div class="path-result">
                <div class="path-header">
                    <h3>Graph View (${data.distance} steps)</h3>
                </div>
                <div id="graph-container"></div>
            </div>
        `;

        this.renderD3Graph(highlightedNodes, highlightedLinks);
    }

    async loadFullGraph() {
        try {
            const response = await fetch('/api/graph/all');
            this.graphData = await response.json();
        } catch (error) {
            console.error('Error loading graph:', error);
            this.showError('Failed to load graph data');
        }
    }

    renderD3Graph(nodes, links) {
        const container = document.getElementById('graph-container');
        const width = container.clientWidth;
        const height = 600;

        container.innerHTML = '';

        const svg = d3.select('#graph-container')
            .append('svg')
            .attr('width', width)
            .attr('height', height);

        const g = svg.append('g');

        // Background for zoom/pan
        svg.append('rect')
            .attr('width', width)
            .attr('height', height)
            .attr('fill', 'transparent');

        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .filter(event => !event.button && event.target.tagName !== 'circle')
            .on('zoom', (event) => g.attr('transform', event.transform));

        svg.call(zoom);

        this.simulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(links).id(d => d.id).distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(30));

        // Links
        const link = g.append('g')
            .selectAll('line')
            .data(links)
            .join('line')
            .attr('stroke', '#4b5563')
            .attr('stroke-width', 2);

        // Link labels
        const linkLabel = g.append('g')
            .selectAll('text')
            .data(links)
            .join('text')
            .attr('class', 'link-label')
            .attr('font-size', '10px')
            .attr('fill', '#9ca3af')
            .text(d => d.type);

        // Nodes
        const node = g.append('g')
            .selectAll('circle')
            .data(nodes)
            .join('circle')
            .attr('r', 8)
            .attr('fill', '#d97706')
            .attr('stroke', '#b86f1a')
            .attr('stroke-width', 2)
            .style('cursor', 'grab')
            .call(this.createDrag(this.simulation));

        // Node labels
        const nodeLabel = g.append('g')
            .selectAll('text')
            .data(nodes)
            .join('text')
            .attr('class', 'node-label')
            .attr('dx', 12)
            .attr('dy', 4)
            .attr('font-size', '12px')
            .attr('fill', '#e5e7eb')
            .text(d => d.name);

        // Tick function
        this.simulation.on('tick', () => {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            linkLabel
                .attr('x', d => (d.source.x + d.target.x) / 2)
                .attr('y', d => (d.source.y + d.target.y) / 2);

            node
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);

            nodeLabel
                .attr('x', d => d.x)
                .attr('y', d => d.y);
        });

        // Double-click to unpin
        node.on('dblclick', (event, d) => {
            d.fx = null;
            d.fy = null;
        });
    }

    createDrag(simulation) {
        function dragstarted(event, d) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
            d3.select(this).style('cursor', 'grabbing');
        }

        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;
        }

        function dragended(event, d) {
            if (!event.active) simulation.alphaTarget(0);
            d3.select(this).style('cursor', 'grab');
        }

        return d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended);
    }

    switchView(view) {
        this.currentView = view;
        
        this.viewBtns.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.view === view);
        });

        if (this.currentData) {
            this.displayResults(this.currentData);
        }
    }

    showMessage(message) {
        this.resultsSection.innerHTML = `<div class="message">${message}</div>`;
    }

    showError(message) {
        this.resultsSection.innerHTML = `<div class="error">${message}</div>`;
    }
}

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    new ArteryMapper();
});
