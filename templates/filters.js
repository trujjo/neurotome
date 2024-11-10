// filters.js
class FilterManager {
    constructor(viz) {
        this.viz = viz;
        this.selectedNodeTypes = new Set();
        this.selectedLocations = new Set();
        this.selectedSublocations = new Set();
        
        // Add configuration options
        this.config = {
            highlightOpacity: 1,
            fadeOpacity: 0.2,
            transitionDuration: 300,
            highlightColor: '#ff9900',
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
            
            this.setupFilterButtons();
            this.setupResetButton();
            await this.applyFilters();
        } catch (error) {
            console.error('Error initializing filters:', error);
            this.showErrorMessage('Failed to initialize filters');
        }
    }

    setupResetButton() {
        const resetButton = document.createElement('button');
        resetButton.textContent = 'Reset Filters';
        resetButton.className = 'reset-button';
        resetButton.onclick = () => this.resetFilters();
        
        const filterContainer = document.querySelector('.filter-container');
        filterContainer.appendChild(resetButton);
    }

    resetFilters() {
        this.selectedNodeTypes.clear();
        this.selectedLocations.clear();
        this.selectedSublocations.clear();
        
        // Reset button styles
        document.querySelectorAll('.filter-button').forEach(button => {
            button.classList.remove('selected');
        });
        
        this.applyFilters();
    }

    createFilterButtons(containerId, items, selectedSet) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = ''; // Clear existing buttons
        
        items.forEach(item => {
            const button = document.createElement('button');
            button.textContent = item;
            button.className = 'filter-button';
            button.id = `filter-${containerId}-${item}`;
            
            // Add tooltip
            button.title = `Filter by ${item}`;
            
            button.onclick = () => this.toggleFilter(item, selectedSet, button);
            container.appendChild(button);
        });
    }

    toggleFilter(item, selectedSet, button) {
        if (selectedSet.has(item)) {
            selectedSet.delete(item);
            button.classList.remove('selected');
        } else {
            selectedSet.add(item);
            button.classList.add('selected');
        }
        
        this.applyFilters();
    }

    async applyFilters() {
        const nodes = this.viz.graph.nodes();
        const links = this.viz.graph.links();
        
        // If no filters are selected, reset everything
        if (this.selectedNodeTypes.size === 0 && 
            this.selectedLocations.size === 0 && 
            this.selectedSublocations.size === 0) {
            
            this.resetVisualization(nodes, links);
            return;
        }

        // Apply filters to nodes
        nodes.forEach(node => {
            const matchesType = this.selectedNodeTypes.size === 0 || 
                              this.selectedNodeTypes.has(node.labels[0]);
            const matchesLocation = this.selectedLocations.size === 0 || 
                                  this.selectedLocations.has(node.properties.location);
            const matchesSublocation = this.selectedSublocations.size === 0 || 
                                     this.selectedSublocations.has(node.properties.sublocation);

            const isMatch = matchesType && matchesLocation && matchesSublocation;
            
            // Update node appearance
            this.updateNodeAppearance(node, isMatch);
        });

        // Update links visibility
        this.updateLinksVisibility(links, nodes);

        // Restart the simulation with new parameters
        this.viz.simulation
            .alpha(0.3)
            .alphaTarget(0)
            .restart();
    }

    updateNodeAppearance(node, isMatch) {
        // Update node properties for visualization
        node.opacity = isMatch ? this.config.highlightOpacity : this.config.fadeOpacity;
        node.highlighted = isMatch;
        
        // Update visual properties
        d3.select(node.element)
            .transition()
            .duration(this.config.transitionDuration)
            .attr('opacity', node.opacity)
            .style('fill', isMatch ? this.config.highlightColor : this.config.defaultColor);

        // Bring matched nodes to front
        if (isMatch) {
            node.element.parentNode.appendChild(node.element);
        }
    }

    updateLinksVisibility(links, nodes) {
        links.forEach(link => {
            const sourceVisible = nodes.find(n => n.id === link.source.id)?.highlighted;
            const targetVisible = nodes.find(n => n.id === link.target.id)?.highlighted;
            
            d3.select(link.element)
                .transition()
                .duration(this.config.transitionDuration)
                .attr('opacity', (sourceVisible && targetVisible) ? 1 : 0.1);
        });
    }

    resetVisualization(nodes, links) {
        // Reset nodes
        nodes.forEach(node => {
            node.opacity = 1;
            node.highlighted = false;
            
            d3.select(node.element)
                .transition()
                .duration(this.config.transitionDuration)
                .attr('opacity', 1)
                .style('fill', this.config.defaultColor);
        });

        // Reset links
        links.forEach(link => {
            d3.select(link.element)
                .transition()
                .duration(this.config.transitionDuration)
                .attr('opacity', 1);
        });
    }

    showErrorMessage(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        document.body.appendChild(errorDiv);
        
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }
}

export { FilterManager };
