// filters.js
class FilterManager {
    constructor(viz) {
        this.viz = viz;
        this.selectedNodeTypes = new Set();
        this.selectedLocations = new Set();
        this.selectedSublocations = new Set();
        
        // Configuration options
        this.config = {
            highlightOpacity: 1,
            fadeOpacity: 0.2,
            transitionDuration: 300,
            highlightColor: '#D35400',
            defaultColor: '#67a9cf'
        };
        
        this.initializeFilters();
    }

    async initializeFilters() {
        try {
            await Promise.all([
                this.loadNodeTypes(),
                this.loadLocations(),
                this.loadSublocations()
            ]);
            this.updateStats();
        } catch (error) {
            console.error('Error initializing filters:', error);
            this.showErrorMessage('Failed to initialize filters');
        }
    }

    async loadNodeTypes() {
        try {
            const response = await fetch('/api/nodes/types');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const nodeTypes = await response.json();
            this.createFilterButtons('node-type-filters', nodeTypes, this.selectedNodeTypes);
        } catch (error) {
            console.error('Error loading node types:', error);
        }
    }

    async loadLocations() {
        try {
            const response = await fetch('/api/nodes/locations');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const locations = await response.json();
            this.createFilterButtons('location-filters', locations, this.selectedLocations);
        } catch (error) {
            console.error('Error loading locations:', error);
        }
    }

    async loadSublocations() {
        try {
            const response = await fetch('/api/nodes/sublocations');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const sublocations = await response.json();
            this.createFilterButtons('sublocation-filters', sublocations, this.selectedSublocations);
        } catch (error) {
            console.error('Error loading sublocations:', error);
        }
    }

    createFilterButtons(containerId, items, selectedSet) {
        const container = document.getElementById(containerId);
        if (!container) return;

        items.forEach(item => {
            const button = document.createElement('button');
            button.textContent = item;
            button.className = 'filter-btn';
            button.addEventListener('click', () => this.toggleFilter(button, item, selectedSet));
            container.appendChild(button);
        });
    }

    toggleFilter(button, item, selectedSet) {
        if (selectedSet.has(item)) {
            selectedSet.delete(item);
            button.classList.remove('active');
        } else {
            selectedSet.add(item);
            button.classList.add('active');
        }
        
        this.updateVisualization();
        this.updateStats();
    }

    updateStats() {
        const stats = {
            nodeTypes: this.selectedNodeTypes.size,
            locations: this.selectedLocations.size,
            sublocations: this.selectedSublocations.size
        };

        document.getElementById('nodeTypeStats').textContent = 
            `${stats.nodeTypes} selected`;
        document.getElementById('locationStats').textContent = 
            `${stats.locations} selected`;
        document.getElementById('sublocationStats').textContent = 
            `${stats.sublocations} selected`;
    }

    async updateVisualization() {
        try {
            const params = new URLSearchParams();
            
            this.selectedNodeTypes.forEach(type => params.append('nodeTypes[]', type));
            this.selectedLocations.forEach(loc => params.append('locations[]', loc));
            this.selectedSublocations.forEach(subloc => params.append('sublocations[]', subloc));
            
            const url = `/api/graph/filtered?${params.toString()}`;
            const response = await fetch(url);
            
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            
            // Update the visualization
            this.viz.updateData(data);
            
            // Apply visual filtering effects
            this.applyVisualFilters(data);
            
        } catch (error) {
            console.error('Error updating visualization:', error);
            this.showErrorMessage('Failed to update visualization');
        }
    }

    applyVisualFilters(data) {
        const nodes = this.viz.graph.nodes();
        const hasActiveFilters = this.selectedNodeTypes.size > 0 || 
                               this.selectedLocations.size > 0 || 
                               this.selectedSublocations.size > 0;

        nodes.forEach(node => {
            const matchesType = this.selectedNodeTypes.size === 0 || 
                              this.selectedNodeTypes.has(node.labels[0]);
            const matchesLocation = this.selectedLocations.size === 0 || 
                                  this.selectedLocations.has(node.properties.location);
            const matchesSublocation = this.selectedSublocations.size === 0 || 
                                     this.selectedSublocations.has(node.properties.sublocation);

            const matches = matchesType && matchesLocation && matchesSublocation;

            // Apply visual effects
            node.style = {
                opacity: hasActiveFilters ? 
                    (matches ? this.config.highlightOpacity : this.config.fadeOpacity) : 
                    this.config.highlightOpacity,
                fill: matches ? this.config.highlightColor : this.config.defaultColor
            };
        });

        this.viz.simulation.alpha(0.3).restart();
    }

    showErrorMessage(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        document.body.appendChild(errorDiv);
        setTimeout(() => errorDiv.remove(), 3000);
    }

    clearNodeTypes() {
        this.selectedNodeTypes.clear();
        document.querySelectorAll('#node-type-filters .filter-btn').forEach(button => {
            button.classList.remove('active');
        });
        this.updateVisualization();
        this.updateStats();
    }

    clearLocationGroup(location) {
        const buttons = document.querySelectorAll(`[data-location="${location}"]`);
        buttons.forEach(button => {
            const sublocation = button.dataset.sublocation;
            this.selectedSublocations.delete(sublocation);
            button.classList.remove('active');
        });
        this.selectedLocations.delete(location);
        this.updateVisualization();
        this.updateStats();
    }
}

export { FilterManager };
