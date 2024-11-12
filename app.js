// Tab switching functionality
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', function() {
        // Remove active class from all tabs and sections
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.filter-section').forEach(s => s.classList.remove('active'));
        
        // Add active class to clicked tab and corresponding section
        this.classList.add('active');
        document.getElementById(`${this.dataset.tab}-section`).classList.add('active');
    });
});

// Button toggle functionality and active filter tracking
document.querySelectorAll('.filter-button').forEach(button => {
    button.addEventListener('click', function() {
        this.classList.toggle('active');
        updateActiveFilters();
    });
});

// Function to update active filters display
function updateActiveFilters() {
    const activeFiltersContainer = document.getElementById('active-filters');
    activeFiltersContainer.innerHTML = '';
    
    const activeButtons = document.querySelectorAll('.filter-button.active');
    activeButtons.forEach(button => {
        const pill = document.createElement('div');
        pill.className = 'active-filter-pill';
        pill.innerHTML = `
            ${button.textContent}
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" width="16" height="16">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
        `;
        pill.addEventListener('click', () => {
            button.classList.remove('active');
            updateActiveFilters();
        });
        activeFiltersContainer.appendChild(pill);
    });
}

// Function to generate Cypher query based on filter type and values
function generateCypherQuery(filterType, filters) {
    let query = '';
    
    switch(filterType) {
        case 'tissue':
            // Match nodes with specific labels (e.g., n:artery, n:bone)
            query = `
                MATCH (n)
                WHERE any(label in [${filters.map(f => `'${f}'`).join(', ')}] 
                      WHERE label in labels(n))
                WITH n LIMIT 50
                OPTIONAL MATCH (n)-[r]-(m)
                RETURN n, r, m
                LIMIT 50
            `;
            break;
            
        case 'location':
            query = `
                MATCH (n)
                WHERE any(loc in [${filters.map(f => `'${f}'`).join(', ')}] 
                      WHERE loc in n.locations OR loc in n.sublocations)
                WITH n LIMIT 50
                OPTIONAL MATCH (n)-[r]-(m)
                RETURN n, r, m
                LIMIT 50
            `;
            break;
            
        case 'relationship':
            query = `
                MATCH (n)-[r]->(m)
                WHERE type(r) in [${filters.map(f => `'${f}'`).join(', ')}]
                WITH n, r, m LIMIT 50
                RETURN n, r, m
                LIMIT 50
            `;
            break;
    }
    
    return query.trim();
}

// Show 50 button click handler
document.getElementById('show-fifty-btn').addEventListener('click', function() {
    const activeFilters = Array.from(document.querySelectorAll('.filter-button.active'))
        .map(button => button.textContent.trim().toLowerCase());
    
    if (activeFilters.length === 0) {
        alert('please select at least one filter');
        return;
    }

    // Show loading state
    this.innerHTML = `
        <svg class="animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" width="20" height="20">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        loading...
    `;

    // Get the current tab to determine filter type
    const activeTab = document.querySelector('.tab.active').dataset.tab;
    
    // Generate Cypher query
    const cypherQuery = generateCypherQuery(activeTab, activeFilters);
    console.log('Generated Cypher Query:', cypherQuery);

    // Create visualization data
    const nodes = new vis.DataSet();
    const edges = new vis.DataSet();
    
    // Sample node generation (replace with actual Neo4j data)
    let nodeCount = 0;
    const maxNodes = 50;
    
    activeFilters.forEach(filter => {
        if (nodeCount >= maxNodes) return;
        
        nodes.add({
            id: `${filter}_main`,
            label: filter,
            group: activeTab,
            color: {
                background: getColorForType(activeTab),
                border: getBorderColorForType(activeTab)
            }
        });
        nodeCount++;

        const relatedCount = Math.min(5, maxNodes - nodeCount);
        for (let i = 0; i < relatedCount; i++) {
            if (nodeCount >= maxNodes) break;
            
            const relatedId = `${filter}_related_${i}`;
            nodes.add({
                id: relatedId,
                label: `${filter}_${i}`,
                group: 'related',
                color: {
                    background: getLighterColor(getColorForType(activeTab)),
                    border: getColorForType(activeTab)
                }
            });
            
            edges.add({
                from: `${filter}_main`,
                to: relatedId,
                arrows: 'to'
            });
            
            nodeCount++;
        }
    });

    // Create network
    const container = document.getElementById('network-container');
    const data = {
        nodes: nodes,
        edges: edges
    };
    
    const options = {
        nodes: {
            shape: 'dot',
            size: 20,
            font: {
                size: 14,
                face: 'system-ui'
            },
            borderWidth: 2,
            shadow: true
        },
        edges: {
            width: 2,
            color: {
                color: '#64748b',
                highlight: '#4f46e5'
            },
            smooth: {
                type: 'continuous'
            }
        },
        physics: {
            stabilization: true,
            barnesHut: {
                gravitationalConstant: -80000,
                springConstant: 0.001,
                springLength: 200
            }
        },
        interaction: {
            hover: true,
            tooltipDelay: 200
        }
    };
    
    const network = new vis.Network(container, data, options);
    
    network.once('stabilizationIterationsDone', () => {
        this.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
            </svg>
            show me 50
        `;
    });
});

// Helper functions for network visualization
function getColorForType(type) {
    const colors = {
        tissue: '#818cf8',    // Indigo
        location: '#34d399',  // Emerald
        relationship: '#f472b6' // Pink
    };
    return colors[type] || '#94a3b8';
}

function getBorderColorForType(type) {
    const colors = {
        tissue: '#4f46e5',    // Darker Indigo
        location: '#059669',  // Darker Emerald
        relationship: '#db2777' // Darker Pink
    };
    return colors[type] || '#64748b';
}

function getLighterColor(hexColor) {
    let r = parseInt(hexColor.slice(1,3), 16);
    let g = parseInt(hexColor.slice(3,5), 16);
    let b = parseInt(hexColor.slice(5,7), 16);
    
    r = Math.floor((r + 255) / 2);
    g = Math.floor((g + 255) / 2);
    b = Math.floor((b + 255) / 2);
    
    return '#' + [r,g,b].map(x => {
        const hex = x.toString(16);
        return hex.length === 1 ? '0' + hex : hex;
    }).join('');
}
