class FilterManager {
    constructor(viz) {
        this.viz = viz;
        this.nodeTypeSelect = document.getElementById('nodeTypeFilter');
        this.locationSelect = document.getElementById('locationFilter');
        this.initializeFilters();
    }

    async initializeFilters() {
        try {
            const response = await fetch('/api/filters');
            const data = await response.json();
            if (data.success) {
                this.populateFilters(data.data);
            } else {
                console.error('Failed to load filters:', data.error);
            }
        } catch (error) {
            console.error('Failed to initialize filters:', error);
        }
    }

    populateFilters(data) {
        // Clear existing options
        this.nodeTypeSelect.innerHTML = '';
        this.locationSelect.innerHTML = '';

        // Get unique values
        const nodeTypes = [...new Set(data.map(item => item.labels).flat())];
        const locations = [...new Set(data.map(item => 
            item.properties && item.properties.location
        ).filter(Boolean))];
        
        // Populate node types
        nodeTypes.forEach(type => {
            const option = document.createElement('option');
            option.value = type;
            option.textContent = type;
            this.nodeTypeSelect.appendChild(option);
        });

        // Populate locations
        locations.forEach(location => {
            const option = document.createElement('option');
            option.value = location;
            option.textContent = location;
            this.locationSelect.appendChild(option);
        });
    }

    applyFilters() {
        const selectedNodeTypes = Array.from(this.nodeTypeSelect.selectedOptions)
            .map(opt => opt.value);
        const selectedLocations = Array.from(this.locationSelect.selectedOptions)
            .map(opt => opt.value);
        this.viz.updateWithFilters(selectedNodeTypes, selectedLocations);
    }
}
