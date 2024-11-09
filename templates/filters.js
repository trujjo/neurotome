// filters.js
class FilterManager {
    constructor(viz) {
        this.viz = viz;
        this.selectedNodeTypes = new Set();
        this.selectedLocations = new Set();
        this.selectedSublocations = new Set();
        
        this.initializeFilters();
    }

    async initializeFilters() {
        await this.loadNodeTypes();
        await this.loadLocations();
        await this.loadSublocations();
        this.setupFilterButtons();
    }

    async loadNodeTypes() {
        try {
            const response = await fetch('/api/nodes/types');
            const nodeTypes = await response.json();
            this.createFilterButtons('node-type-filters', nodeTypes, this.selectedNodeTypes);
        } catch (error) {
            console.error('Error loading node types:', error);
        }
    }

    async loadLocations() {
        try {
            const response = await fetch('/api/nodes/locations');
            const locations = await response.json();
            this.createFilterButtons('location-filters', locations, this.selectedLocations);
        } catch (error) {
            console.error('Error loading locations:', error);
        }
    }

    async loadSublocations() {
        try {
            const response = await fetch('/api/nodes/sublocations');
            const sublocations = await response.json();
            this.createFilterButtons('sublocation-filters', sublocations, this.selectedSublocations);
        } catch (error) {
            console.error('Error loading sublocations:', error);
        }
    }

    createFilterButtons(containerId, items, selectedSet) {
        const container = document.getElementById(containerId);
        container.innerHTML = ''; // Clear existing buttons

        items.forEach(item => {
            const button = document.createElement('button');
            button.textContent = item;
            button.className = 'filter-button';
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
        this.applyFilters();
    }

    async applyFilters() {
        try {
            const params = new URLSearchParams();
            
            if (this.selectedNodeTypes.size > 0) {
                this.selectedNodeTypes.forEach(type => params.append('nodeTypes[]', type));
            }
            if (this.selectedLocations.size > 0) {
                this.selectedLocations.forEach(loc => params.append('locations[]', loc));
            }
            if (this.selectedSublocations.size > 0) {
                this.selectedSublocations.forEach(subloc => params.append('sublocations[]', subloc));
            }

            const response = await fetch(`/api/graph/filtered?${params.toString()}`);
            const data = await response.json();
            
            if (data.error) {
                console.error('Error applying filters:', data.error);
                return;
            }

            this.viz.updateData(data);
        } catch (error) {
            console.error('Error applying filters:', error);
        }
    }
}

export { FilterManager };
