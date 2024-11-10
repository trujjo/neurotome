class FilterManager {
    constructor() {
        this.activeNodeTypes = new Set();
        this.activeLocations = new Set();
        this.activeSublocations = new Set();
        this.viz = new NeoViz();
        this.initializeTabs();
        this.initializeNodeTypes();
        this.initializeLocationGroups();
        this.initializeEventListeners();
        this.updateStats();
        this.viz.render();
    }

    initializeTabs() {
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', () => {
                document.querySelectorAll('.tab-button').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.filter-section').forEach(s => s.classList.remove('active'));
                button.classList.add('active');
                document.getElementById(button.dataset.tab).classList.add('active');
            });
        });
    }

    initializeNodeTypes() {
        const container = document.getElementById('nodeTypeFilters');
        nodeTypes.forEach(type => {
            const button = document.createElement('button');
            button.className = 'filter-btn';
            button.setAttribute('data-type', type);
            button.textContent = type;
            button.onclick = () => this.toggleNodeType(button);
            container.appendChild(button);
        });
    }

    initializeLocationGroups() {
        const container = document.getElementById('locationGroups');
        container.innerHTML = '';
        
        Object.entries(locationData).forEach(([location, sublocations]) => {
            const group = document.createElement('div');
            group.className = 'filter-group';
            
            const header = document.createElement('div');
            header.className = 'filter-group-title';
            
            const title = document.createElement('h3');
            title.className = 'location-header';
            title.textContent = location;
            title.onclick = () => this.toggleLocationGroup(location);
            
            const clearBtn = document.createElement('button');
            clearBtn.className = 'clear-btn';
            clearBtn.textContent = 'Clear';
            clearBtn.onclick = (e) => {
                e.stopPropagation();
                this.clearLocationGroup(location);
            };
            
            header.appendChild(title);
            header.appendChild(clearBtn);
            
            const buttons = document.createElement('div');
            buttons.className = 'filter-buttons';
            
            sublocations.forEach(sublocation => {
                const button = document.createElement('button');
                button.className = 'filter-btn';
                button.setAttribute('data-location', location);
                button.setAttribute('data-sublocation', sublocation);
                button.textContent = sublocation;
                button.onclick = () => this.toggleSublocation(button);
                buttons.appendChild(button);
            });
            
            group.appendChild(header);
            group.appendChild(buttons);
            container.appendChild(group);
        });
    }

    initializeEventListeners() {
        document.querySelectorAll('#node-types .filter-btn').forEach(button => {
            button.addEventListener('click', () => this.toggleNodeType(button));
        });
    }

    toggleNodeType(button) {
        if (button.classList.contains('active')) {
            this.activeNodeTypes.delete(button.dataset.type);
            button.classList.remove('active');
        } else {
            this.activeNodeTypes.add(button.dataset.type);
            button.classList.add('active');
        }
        this.updateVisualization();
        this.updateStats();
    }

    toggleLocationGroup(location) {
        const buttons = document.querySelectorAll(`[data-location="${location}"]`);
        const allActive = Array.from(buttons).every(btn => btn.classList.contains('active'));
        
        buttons.forEach(button => {
            const sublocation = button.dataset.sublocation;
            if (allActive) {
                this.activeSublocations.delete(sublocation);
                button.classList.remove('active');
            } else {
                this.activeSublocations.add(sublocation);
                button.classList.add('active');
            }
        });
        
        if (allActive) {
            this.activeLocations.delete(location);
        } else {
            this.activeLocations.add(location);
        }
        
        this.updateVisualization();
        this.updateStats();
    }

    toggleSublocation(button) {
        const location = button.dataset.location;
        const sublocation = button.dataset.sublocation;
        
        if (button.classList.contains('active')) {
            this.activeSublocations.delete(sublocation);
            button.classList.remove('active');
            if (!document.querySelectorAll(`[data-location="${location}"].active`).length) {
                this.activeLocations.delete(location);
            }
        } else {
            this.activeSublocations.add(sublocation);
            button.classList.add('active');
            this.activeLocations.add(location);
        }
        
        this.updateVisualization();
        this.updateStats();
    }

    clearNodeTypes() {
        this.activeNodeTypes.clear();
        document.querySelectorAll('#node-types .filter-btn').forEach(button => {
            button.classList.remove('active');
        });
        this.updateVisualization();
        this.updateStats();
    }

    clearLocationGroup(location) {
        const buttons = document.querySelectorAll(`[data-location="${location}"]`);
        buttons.forEach(button => {
            const sublocation = button.dataset.sublocation;
            this.activeSublocations.delete(sublocation);
            button.classList.remove('active');
        });
        this.activeLocations.delete(location);
        this.updateVisualization();
        this.updateStats();
    }

    updateStats() {
        document.getElementById('nodeTypeStats').textContent = 
            `${this.activeNodeTypes.size} node types selected`;
        document.getElementById('locationStats').textContent = 
            `${this.activeSublocations.size} locations selected`;
    }

    updateVisualization() {
        const filters = {
            nodeTypes: Array.from(this.activeNodeTypes),
            locations: Array.from(this.activeLocations),
            sublocations: Array.from(this.activeSublocations)
        };
        this.viz.updateWithFilters(filters);
    }
}

// Initialize the filter manager when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.filterManager = new FilterManager();
});
