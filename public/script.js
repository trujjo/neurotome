document.addEventListener('DOMContentLoaded', () => {
    // Initialize sidebar toggle functionality
    const filterToggle = document.getElementById('filterToggle');
    const filterContent = document.getElementById('filterContent');
    const arrow = filterToggle.querySelector('.arrow');

    filterToggle.addEventListener('click', () => {
        filterContent.classList.toggle('collapsed');
        arrow.style.transform = filterContent.classList.contains('collapsed') 
            ? 'rotate(-90deg)' 
            : 'rotate(0deg)';
    });

    // Ensure filterContent is visible by default
    filterContent.classList.remove('collapsed');
    filterToggle.classList.remove('collapsed');

    // Add loading indicators
    ['labelButtons', 'locationButtons', 'sublocationButtons', 'systemButtons'].forEach(id => {
        const container = document.getElementById(id);
        if (container) {
            container.innerHTML = '<h3>' + id.replace('Buttons', '') + '</h3><div class="loading">Loading...</div>';
        }
    });

    const width = window.innerWidth;
    const height = window.innerHeight - 80;
    
    // Create the SVG and add zoom behavior
    const svg = d3.select('#graph')
        .append('svg')
        .attr('width', width)
        .attr('height', height);

    // Create a container group for all content
    const container = svg.append('g');

    // Add zoom behavior
    const zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on('zoom', (event) => {
            container.attr('transform', event.transform);
        });

    svg.call(zoom);

    // Disable double-click zoom since we use it for node focusing
    svg.on('dblclick.zoom', null);

    // Add grid
    const gridSize = 50; // Size of grid cells
    const numXLines = Math.ceil(width / gridSize);
    const numYLines = Math.ceil(height / gridSize);

    // Add vertical grid lines
    for (let i = 0; i <= numXLines; i++) {
        container.append('line')
            .attr('class', 'grid-line')
            .attr('x1', i * gridSize)
            .attr('y1', 0)
            .attr('x2', i * gridSize)
            .attr('y2', height)
            .style('stroke', '#2a2a2a')
            .style('stroke-width', '1px');
    }

    // Add horizontal grid lines
    for (let i = 0; i <= numYLines; i++) {
        container.append('line')
            .attr('class', 'grid-line')
            .attr('x1', 0)
            .attr('y1', i * gridSize)
            .attr('x2', width)
            .attr('y2', i * gridSize)
            .style('stroke', '#2a2a2a')
            .style('stroke-width', '1px');
    }

    const simulation = d3.forceSimulation()
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('charge', d3.forceManyBody().strength(-100))
        .force('collide', d3.forceCollide(30))
        .on('tick', () => {
            // Keep nodes within bounds
            simulation.nodes().forEach(d => {
                d.x = Math.max(30, Math.min(width - 30, d.x));
                d.y = Math.max(30, Math.min(height - 30, d.y));
            });
        });

    // Modified loadLabels function to preserve selections
    function loadLabels() {
        const locations = Array.from(document.getElementById('locationFilter').selectedOptions)
            .map(option => option.value);
        const sublocations = Array.from(document.getElementById('sublocationFilter').selectedOptions)
            .map(option => option.value);
        const systems = Array.from(document.getElementById('systemFilter').selectedOptions)
            .map(option => option.value);
        
        const params = new URLSearchParams();
        if (locations.length) params.append('locations', locations.join(','));
        if (sublocations.length) params.append('sublocations', sublocations.join(','));
        if (systems.length) params.append('systems', systems.join(','));

        return fetch('/api/labels?' + params.toString())
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                return response.json();
            })
            .then(labels => {
                const labelSelect = document.getElementById('labelFilter');
                const currentSelections = Array.from(labelSelect.selectedOptions).map(opt => opt.value);
                
                // Only update if we have new labels
                if (Array.isArray(labels) && labels.length > 0) {
                    // Keep the current selections that are still valid
                    labelSelect.innerHTML = labels
                        .map(label => `<option value="${label}"${
                            currentSelections.includes(label) ? ' selected' : ''
                        }>${label}</option>`)
                        .join('');
                    
                    // Update sidebar buttons
                    updateSidebarButtons('labelButtons', labels);
                }
                return labels;
            })
            .catch(error => {
                console.error('Error loading labels:', error);
                return [];
            });
    }

    // Update loadDistinctValues function
    function loadDistinctValues() {
        const selectedLabels = Array.from(document.getElementById('labelFilter').selectedOptions)
            .map(option => option.value);
        const locations = Array.from(document.getElementById('locationFilter').selectedOptions)
            .map(option => option.value);
        const sublocations = Array.from(document.getElementById('sublocationFilter').selectedOptions)
            .map(option => option.value);
        const systems = Array.from(document.getElementById('systemFilter').selectedOptions)
            .map(option => option.value);
        
        const params = new URLSearchParams();
        if (selectedLabels.length === 1) params.append('label', selectedLabels[0]);
        if (locations.length) params.append('locations', locations.join(','));
        if (sublocations.length) params.append('sublocations', sublocations.join(','));
        if (systems.length) params.append('systems', systems.join(','));
    
        return fetch('/api/distinct-values?' + params.toString())
            .then(response => response.json())
            .then(data => updateFilterOptions(data));
    }

    // Modify updateFilterOptions to ensure it's actually updating
    function updateFilterOptions(data) {
        console.log('Updating filters with data:', data); // Debug log
        
        // Update dropdowns
        const locationSelect = document.getElementById('locationFilter');
        const sublocationSelect = document.getElementById('sublocationFilter');
        const systemSelect = document.getElementById('systemFilter');
        
        if (locationSelect && data.locations) {
            locationSelect.innerHTML = data.locations
                .map(loc => `<option value="${loc}">${loc}</option>`)
                .join('');
        }
        
        if (sublocationSelect && data.sublocations) {
            sublocationSelect.innerHTML = data.sublocations
                .map(subloc => `<option value="${subloc}">${subloc}</option>`)
                .join('');
        }
        
        if (systemSelect && data.systems) {
            systemSelect.innerHTML = data.systems
                .map(sys => `<option value="${sys}">${sys}</option>`)
                .join('');
        }

        // Update sidebar buttons
        updateSidebarButtons('labelButtons', data.labels || []);
        updateSidebarButtons('locationButtons', data.locations || []);
        updateSidebarButtons('sublocationButtons', data.sublocations || []);
        updateSidebarButtons('systemButtons', data.systems || []);
    }

    // Modified updateSidebarButtons function to handle button states correctly
    function updateSidebarButtons(containerId, items) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return;
        }

        console.log(`Updating ${containerId} with items:`, items); // Debug log

        const header = container.querySelector('h3') || document.createElement('h3');
        header.textContent = containerId.replace('Buttons', '');
        
        container.innerHTML = '';
        container.appendChild(header);

        if (!Array.isArray(items) || items.length === 0) {
            container.innerHTML += '<div class="loading">No items available</div>';
            return;
        }

        // Get corresponding filter select element
        const filterId = containerId.replace('Buttons', 'Filter');
        const filterSelect = document.getElementById(filterId);
        
        items.forEach(item => {
            if (!item) return;
            
            const button = document.createElement('button');
            button.className = 'sidebar-btn';
            button.textContent = item;
            button.dataset.value = item;
            
            // Check if this value is selected in the corresponding filter
            if (filterSelect) {
                const isSelected = Array.from(filterSelect.selectedOptions)
                    .some(option => option.value === item);
                if (isSelected) button.classList.add('selected');
            }
            
            button.addEventListener('click', () => {
                button.classList.toggle('selected');
                if (filterSelect) {
                    Array.from(filterSelect.options).forEach(opt => {
                        if (opt.value === item) {
                            opt.selected = button.classList.contains('selected');
                        }
                    });
                    filterSelect.dispatchEvent(new Event('change'));
                }
            });
            
            container.appendChild(button);
        });
    }

    // Update event listeners
    const labelFilter = document.getElementById('labelFilter');
    const locationFilter = document.getElementById('locationFilter');
    const sublocationFilter = document.getElementById('sublocationFilter');
    const systemFilter = document.getElementById('systemFilter');

    labelFilter.addEventListener('change', () => {
        loadDistinctValues();  // Remove the loadLabels call here
    });
    
    locationFilter.addEventListener('change', () => {
        loadLabels();  // Keep this single call
    });
    
    sublocationFilter.addEventListener('change', () => {
        loadLabels();  // Keep this single call
    });
    
    systemFilter.addEventListener('change', () => {
        loadLabels();  // Keep this single call
    });
    
    // Initial load
    loadLabels().then(() => loadDistinctValues());
    
    // Handle filter application
    document.getElementById('applyFilters').addEventListener('click', () => {
        const selectedLabels = Array.from(document.getElementById('labelFilter').selectedOptions)
            .map(option => option.value);
        const locations = Array.from(document.getElementById('locationFilter').selectedOptions)
            .map(option => option.value);
        const sublocations = Array.from(document.getElementById('sublocationFilter').selectedOptions)
            .map(option => option.value);
        const systems = Array.from(document.getElementById('systemFilter').selectedOptions)
            .map(option => option.value);
        
        fetch('/api/nodes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                labels: selectedLabels,
                locations,
                sublocations,
                systems
            })
        })
        .then(response => response.json())
        .then(nodes => updateVisualization(nodes));
    });

    // Add fit all button functionality
    document.getElementById('fitAll').addEventListener('click', () => {
        fitAll();
    });

    // Reset functionality
    document.getElementById('resetFilters').addEventListener('click', () => {
        // Reset filter selections
        document.getElementById('labelFilter').innerHTML = '';
        document.getElementById('locationFilter').value = '';
        document.getElementById('sublocationFilter').value = '';
        document.getElementById('systemFilter').value = '';

        // Clear visualization
        container.selectAll('*').remove();

        // Reset counters
        document.getElementById('nodeCount').textContent = '0';
        document.getElementById('relationshipCount').textContent = '0';

        // Reload initial data
        loadLabels().then(() => loadDistinctValues());

        // Reset detail buttons to default state (comprehensive)
        detailButtons.forEach(button => {
            button.classList.remove('selected');
            if (button.dataset.detail === 'major') {
                button.classList.add('selected');
            }
        });
        selectedDetails.clear();
        selectedDetails.add('major');
    });

    function updateVisualization(data) {
        // Clear the container instead of all SVG
        container.selectAll('*').remove();
        
        // Update counters
        document.getElementById('nodeCount').textContent = data.nodes.length;
        document.getElementById('relationshipCount').textContent = data.relationships.length;

        // Position nodes based on their stored coordinates or let simulation handle it
        data.nodes.forEach(node => {
            if (node.properties.x !== undefined && node.properties.y !== undefined) {
                node.x = parseFloat(node.properties.x);
                node.y = parseFloat(node.properties.y);
                node.fx = node.x; // Fix position if coordinates exist
                node.fy = node.y;
            }
        });

        // Add relationships first so they appear behind nodes
        const links = container.selectAll('line')
            .data(data.relationships)
            .enter()
            .append('line')
            .attr('class', 'relationship')
            .attr('stroke', '#999')
            .attr('stroke-width', 1);

        // Create node groups after relationships
        const nodes = container.selectAll('g')
            .data(data.nodes)
            .enter()
            .append('g')
            .attr('class', 'node-group')
            .call(d3.drag()  // Add drag behavior
                .on('start', dragStarted)
                .on('drag', dragged)
                .on('end', dragEnded));

        // Enable dragging on the background
        svg.call(d3.drag()
            .on('start', function(event) {
                // Only start drag if we click the background
                if (event.target.tagName === 'svg') {
                    const transform = d3.zoomTransform(svg.node());
                    event.subject = { x: transform.x, y: transform.y };
                }
            })
            .on('drag', function(event) {
                // Only drag if we started on the background
                if (event.subject) {
                    const transform = d3.zoomTransform(svg.node());
                    svg.attr('transform', `translate(${event.x}, ${event.y}) scale(${transform.k})`);
                }
            }));

        // Add node circles
        nodes.append('circle')
            .attr('class', 'node')
            .attr('r', d => d.size === 'large' ? 30 : d.size === 'medium' ? 20 : 15)
            .style('fill', '#1a1a1a');

        // Add text labels with dynamic font sizing
        nodes.append('text')
            .attr('class', 'node-label')
            .text(d => d.properties.name || d.labels[0])
            .attr('dy', '.35em')
            .style('font-size', d => {
                const baseSize = d.size === 'large' ? 14 : d.size === 'medium' ? 12 : 10;
                const textLength = (d.properties.name || d.labels[0]).length;
                const nodeRadius = d.size === 'large' ? 30 : d.size === 'medium' ? 20 : 15;
                return `${Math.min(baseSize, (nodeRadius * 1.8) / textLength)}px`;
            });

        // Add tooltips
        nodes.append('title')
            .text(d => `Labels: ${d.labels.join(', ')}\nProperties: ${JSON.stringify(d.properties)}`);

        // Update simulation with both nodes and links
        simulation
            .nodes(data.nodes)
            .force('link', d3.forceLink(data.relationships)
                .id(d => d.id)
                .distance(100))
            .on('tick', () => {
                links
                    .attr('x1', d => d.source.x)
                    .attr('y1', d => d.source.y)
                    .attr('x2', d => d.target.x)
                    .attr('y2', d => d.target.y);

                nodes.selectAll('circle')
                    .attr('cx', d => d.x)
                    .attr('cy', d => d.y);

                nodes.selectAll('text')
                    .attr('x', d => d.x)
                    .attr('y', d => d.y);
            });

        simulation.alpha(1).restart();
    }

    function fitAll() {
        const nodes = simulation.nodes();
        if (nodes.length === 0) return; // nothing to fit

        // Calculate the actual bounds of all nodes
        const bounds = {
            minX: d3.min(nodes, d => d.x),
            maxX: d3.max(nodes, d => d.x),
            minY: d3.min(nodes, d => d.y),
            maxY: d3.max(nodes, d => d.y)
        };

        const parent = svg.node().parentElement;
        const fullWidth = parent.clientWidth;
        const fullHeight = parent.clientHeight;
        
        // Calculate width and height with padding
        const padding = 50;
        const width = bounds.maxX - bounds.minX + padding * 2;
        const height = bounds.maxY - bounds.minY + padding * 2;
        
        // Calculate center points
        const midX = bounds.minX + width / 2;
        const midY = bounds.minY + height / 2;

        // Calculate scale with some padding
        const scale = 0.95 / Math.max(width / fullWidth, height / fullHeight);
        
        // Calculate translation to center the graph
        const translate = [
            fullWidth / 2 - scale * midX,
            fullHeight / 2 - scale * midY
        ];

        // Apply transform to the svg (not container)
        svg.transition()
            .duration(750)
            .call(
                d3.zoom().transform,
                d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale)
            );
    }

    function dragStarted(event) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
    }
    
    function dragged(event) {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
    }
    
    function dragEnded(event) {
        if (!event.active) simulation.alphaTarget(0);
        // Store new position if node was dragged
        if (event.subject.x !== event.subject.fx || event.subject.y !== event.subject.fy) {
            event.subject.properties.x = event.subject.x;
            event.subject.properties.y = event.subject.y;
        }
        event.subject.fx = null;
        event.subject.fy = null;
    }

    // Add detail button functionality
    const detailButtons = document.querySelectorAll('.detail-btn');
    // Detail levels are hierarchical:
    // - comprehensive: shows base level data
    // - meticulous: shows base + intermediate detail
    // - precise: shows all levels of detail
    const selectedDetails = new Set(['comprehensive']); // Start with base level selected

    detailButtons.forEach(button => {
        button.addEventListener('click', () => {
            const detail = button.dataset.detail;
            
            // Remove selected class from all buttons
            detailButtons.forEach(btn => btn.classList.remove('selected'));
            
            // Add selected class to clicked button
            button.classList.add('selected');
            
            // Update selectedDetails set based on hierarchy
            selectedDetails.clear();
            if (detail === 'precise') {
                selectedDetails.add('comprehensive');
                selectedDetails.add('meticulous');
                selectedDetails.add('precise');
            } else if (detail === 'meticulous') {
                selectedDetails.add('comprehensive');
                selectedDetails.add('meticulous');
            } else {
                selectedDetails.add('comprehensive');
            }
            
            // Trigger filter update
            document.getElementById('applyFilters').click();
        });
    });

    // Modify the existing applyFilters event handler
    document.getElementById('applyFilters').addEventListener('click', () => {
        const selectedLabels = Array.from(document.getElementById('labelFilter').selectedOptions)
            .map(option => option.value);
        const locations = Array.from(document.getElementById('locationFilter').selectedOptions)
            .map(option => option.value);
        const sublocations = Array.from(document.getElementById('sublocationFilter').selectedOptions)
            .map(option => option.value);
        const systems = Array.from(document.getElementById('systemFilter').selectedOptions)
            .map(option => option.value);
        
        fetch('/api/nodes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                labels: selectedLabels,
                locations,
                sublocations,
                systems,
                detail: Array.from(selectedDetails) // Changed from details to detail
            })
        })
        .then(response => response.json())
        .then(data => {
            // Filter nodes based on selected detail levels
            const filteredData = {
                nodes: data.nodes.filter(node => selectedDetails.has(node.properties.detail)),
                relationships: data.relationships.filter(rel => {
                    const sourceNode = data.nodes.find(n => n.id === rel.source);
                    const targetNode = data.nodes.find(n => n.id === rel.target);
                    return sourceNode && targetNode && 
                           selectedDetails.has(sourceNode.properties.detail) && 
                           selectedDetails.has(targetNode.properties.detail);
                })
            };
            updateVisualization(filteredData);
        });
    });

    // Update reset functionality
    document.getElementById('resetFilters').addEventListener('click', () => {
        // Reset filter selections
        document.getElementById('labelFilter').innerHTML = '';
        document.getElementById('locationFilter').value = '';
        document.getElementById('sublocationFilter').value = '';
        document.getElementById('systemFilter').value = '';

        // Clear visualization
        container.selectAll('*').remove();

        // Reset counters
        document.getElementById('nodeCount').textContent = '0';
        document.getElementById('relationshipCount').textContent = '0';

        // Reload initial data
        loadLabels().then(() => loadDistinctValues());

        // Reset detail buttons to default state (comprehensive)
        detailButtons.forEach(button => {
            button.classList.remove('selected');
            if (button.dataset.detail === 'major') {
                button.classList.add('selected');
            }
        });
        selectedDetails.clear();
        selectedDetails.add('major');
    });

    // Add background double-click to reset zoom
    d3.select('#graph').on('dblclick', () => {
        fitAll();
    });

    // Make sure initial load is triggered
    loadLabels()
        .then(() => loadDistinctValues())
        .catch(error => console.error('Error loading initial data:', error));
});