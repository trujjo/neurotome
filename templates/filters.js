// filters.js
class FilterManager {
    constructor(viz) {
        this.viz = viz;
        this.selectedNodeTypes = new Set();
        this.selectedLocations = new Set();
        this.selectedSublocations = new Set();
        
        this.initializeFilters();
        
        // Debug logging
        console.log('FilterManager initialized');
    }

    async initializeFilters() {
        try {
            await this.loadNodeTypes();
            await this.loadLocations();
            await this.loadSublocations();
            this.setupFilterButtons();
            
            // Load initial data
            await this.applyFilters();
        } catch (error) {
            console.error('Error initializing filters:', error);
        }
    }

    async loadNodeTypes() {
        try {
            const response = await fetch('/api/nodes/types');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const nodeTypes = await response.json();
            console.log('Loaded node types:', nodeTypes);
            this.createFilterButtons('node-type-filters', nodeTypes, this.selectedNodeTypes);
        } catch (error) {
            console.error('Error loading node types:', error);
        }
    }

    async loadLocations() {
        try {
            const response = await fetch('/api/nodes/locations');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const locations = await response.json();
            console.log('Loaded locations:', locations);
            this.createFilterButtons('location-filters', locations, this.selectedLocations);
        } catch (error) {
            console.error('Error loading locations:', error);
        }
    }

    async loadSublocations() {
        try {
            const response = await fetch('/api/nodes/sublocations');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const sublocations = await response.json();
            console.log('Loaded sublocations:', sublocations);
            this.createFilterButtons('sublocation-filters', sublocations, this.selectedSublocations);
        } catch (error) {
            console.error('Error loading sublocations:', error);
        }
    }

    createFilterButtons(containerId, items, selectedSet) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return;
        }
        
        container.innerHTML = ''; // Clear existing buttons

        items.forEach(item => {
            if (!item) return; // Skip null/undefined items
            
            const button = document.createElement('button');
            button.textContent = item;
            button.className = 'filter-button';
            button.addEventListener('click', () => {
                this.toggleFilter(button, item, selectedSet);
                console.log(`Filter ${item} toggled:`, selectedSet);
            });
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
        
        // Log current filter state
        console.log('Current filters:', {
            nodeTypes: Array.from(this.selectedNodeTypes),
            locations: Array.from(this.selectedLocations),
            sublocations: Array.from(this.selectedSublocations)
        });
        
        this.applyFilters();
    }

    async applyFilters() {
        try {
            const params = new URLSearchParams();
            
            // Add selected filters to params
            this.selectedNodeTypes.forEach(type => params.append('nodeTypes[]', type));
            this.selectedLocations.forEach(loc => params.append('locations[]', loc));
            this.selectedSublocations.forEach(subloc => params.append('sublocations[]', subloc));
            
            // Log the request URL
            const url = `/api/graph/filtered?${params.toString()}`;
            console.log('Fetching filtered data:', url);

            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Received filtered data:', data);
            
            if (data.error) {
                console.error('Error in filter response:', data.error);
                return;
            }

            // Update visualization with new data
            this.viz.updateData(data);
            
        } catch (error) {
            console.error('Error applying filters:', error);
        }
    }
}

export { FilterManager };
