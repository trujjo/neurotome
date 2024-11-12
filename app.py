// Network initialization
const container = document.getElementById('network');
const data = {
    nodes: new vis.DataSet([]),
    edges: new vis.DataSet([])
};

const options = {
    nodes: {
        shape: 'dot',
        size: 16,
        font: {
            size: 14,
            color: getComputedStyle(document.documentElement).getPropertyValue('--text-primary'),
            face: 'Inter'
        },
        borderWidth: 2,
        shadow: true
    },
    edges: {
        width: 2,
        color: {
            color: getComputedStyle(document.documentElement).getPropertyValue('--text-secondary'),
            highlight: getComputedStyle(document.documentElement).getPropertyValue('--accent'),
            hover: getComputedStyle(document.documentElement).getPropertyValue('--accent')
        },
        smooth: {
            type: 'continuous'
        },
        arrows: {
            to: { enabled: true }
        }
    },
    physics: {
        enabled: true,
        barnesHut: {
            gravitationalConstant: -80000,
            centralGravity: 0.3,
            springLength: 200,
            springConstant: 0.04,
            damping: 0.09
        },
        stabilization: {
            enabled: true,
            iterations: 1000,
            updateInterval: 100
        }
    },
    interaction: {
        hover: true,
        tooltipDelay: 200,
        zoomView: true,
        dragView: true,
        multiselect: true
    }
};

const network = new vis.Network(container, data, options);

// Theme Toggle
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
const savedTheme = localStorage.getItem('theme');

function setTheme(isDark) {
    document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    updateNetworkColors();
}

if (savedTheme) {
    setTheme(savedTheme === 'dark');
} else {
    setTheme(prefersDark.matches);
}

// Update network colors when theme changes
function updateNetworkColors() {
    const textColor = getComputedStyle(document.documentElement).getPropertyValue('--text-primary');
    const secondaryColor = getComputedStyle(document.documentElement).getPropertyValue('--text-secondary');
    const accentColor = getComputedStyle(document.documentElement).getPropertyValue('--accent');

    network.setOptions({
        nodes: {
            font: { color: textColor }
        },
        edges: {
            color: {
                color: secondaryColor,
                highlight: accentColor,
                hover: accentColor
            }
        }
    });
}

// Filter functionality
const filterButtons = document.querySelectorAll('.filter-button');
const selectionCount = document.getElementById('selection-count');
const nodeCount = document.getElementById('node-count');
const edgeCount = document.getElementById('edge-count');
const queryTime = document.getElementById('query-time');

filterButtons.forEach(button => {
    button.addEventListener('click', () => {
        button.classList.toggle('active');
        updateNetwork();
    });
});

// Search functionality
const searchInput = document.querySelector('.search-bar input');
searchInput.addEventListener('input', (e) => {
    const searchTerm = e.target.value.toLowerCase();
    filterButtons.forEach(button => {
        const text = button.textContent.toLowerCase();
        button.style.display = text.includes(searchTerm) ? '' : 'none';
    });
});

// Update network based on filters
function updateNetwork() {
    const startTime = performance.now();
    
    const activeFilters = Array.from(document.querySelectorAll('.filter-button.active'))
        .map(button => ({
            value: button.textContent,
            type: button.dataset.type
        }));

    // Update selection count
    selectionCount.textContent = activeFilters.length;

    // Clear existing network
    data.nodes.clear();
    data.edges.clear();

    // Add nodes based on active filters
    let nodeId = 1;
    activeFilters.forEach(filter => {
        data.nodes.add({
            id: nodeId,
            label: filter.value,
            group: filter.type,
            title: `${filter.value} (${filter.type})`,
            color: {
                background: getColorForType(filter.type),
                border: getBorderColorForType(filter.type)
            }
        });
        nodeId++;
    });

    // Add random edges between nodes
    const nodeIds = data.nodes.getIds();
    nodeIds.forEach(fromId => {
        const numConnections = Math.floor(Math.random() * 3) + 1;
        for (let i = 0; i < numConnections; i++) {
            const toId = nodeIds[Math.floor(Math.random() * nodeIds.length)];
            if (fromId !== toId) {
                data.edges.add({
                    from: fromId,
                    to: toId
                });
            }
        }
    });

    // Update status bar
    const endTime = performance.now();
    nodeCount.textContent = `${data.nodes.length} nodes`;
    edgeCount.textContent = `${data.edges.length} edges`;
    queryTime.textContent = `${Math.round(endTime - startTime)}ms`;
}

// Tool buttons
const toolButtons = document.querySelectorAll('.tool-button[data-tool]');
toolButtons.forEach(button => {
    button.addEventListener('click', () => {
        toolButtons.forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');
        
        switch (button.dataset.tool) {
            case 'pan':
                network.setOptions({ interaction: { dragNodes: false, dragView: true } });
                break;
            case 'zoom':
                network.setOptions({ interaction: { dragNodes: false, dragView: false, zoomView: true } });
                break;
            case 'select':
                network.setOptions({ interaction: { dragNodes: true, dragView: true } });
                break;
        }
    });
});

// Reset view
document.getElementById('reset-view').addEventListener('click', () => {
    network.fit();
});

// Export PNG
document.getElementById('export-png').addEventListener('click', () => {
    const canvas = container.querySelector('canvas');
    const link = document.createElement('a');
    link.download = 'network.png';
    link.href = canvas.toDataURL();
    link.click();
});

// Toggle physics
document.getElementById('toggle-physics').addEventListener('click', () => {
    const physics = !network.physics.options.enabled;
    network.setOptions({ physics: { enabled: physics } });
});

// Node selection
network.on('selectNode', function(params) {
    showNodeDetails(params.nodes[0]);
});

network.on('deselectNode', function() {
    hideNodeDetails();
});

// Helper functions
function getColorForType(type) {
    const colors = {
        tissue: '#818cf8',    // Indigo
        location: '#34d399',  // Emerald
        connection: '#f472b6' // Pink
    };
    return colors[type] || '#94a3b8';
}

function getBorderColorForType(type) {
    const colors = {
        tissue: '#4f46e5',    // Darker Indigo
        location: '#059669',  // Darker Emerald
        connection: '#db2777' // Darker Pink
    };
    return colors[type] || '#64748b';
}

function showNodeDetails(nodeId) {
    const node = network.body.nodes[nodeId];
    const detailsPanel = document.querySelector('.panel-content');
    
    if (node) {
        detailsPanel.innerHTML = `
            <div class="node-details">
                <h4 style="color: ${node.options.color.border}">${node.options.label}</h4>
                <p>Type: ${node.options.group}</p>
                <p>Connections: ${network.getConnectedNodes(nodeId).length}</p>
            </div>
        `;
    }
}

function hideNodeDetails() {
    const detailsPanel = document.querySelector('.panel-content');
    detailsPanel.innerHTML = `
        <div class="no-selection">
            <i class="fas fa-mouse-pointer"></i>
            <p>Select a node to view details</p>
        </div>
    `;
}

// Initial network update
updateNetwork();
