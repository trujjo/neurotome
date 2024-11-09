// Force Graph Configuration
const graphConfig = {
    nodeId: d => d.id,
    nodeGroup: d => d.labels[0],
    nodeTitle: d => `${d.labels.join(', ')}\n${Object.entries(d.properties).map(([k,v]) => `${k}: ${v}`).join('\n')}`,
    linkSource: d => d.source,
    linkTarget: d => d.target,
    width: 800,
    height: 600,
    nodeRadius: 5,
    
    // Color configuration
    nodeColor: d => {
        const colorMap = {
            'nerve': '#ff7f0e',
            'muscle': '#1f77b4',
            'bone': '#2ca02c',
            'region': '#d62728',
            'vessel': '#9467bd',
            'default': '#7f7f7f'
        };
        return colorMap[d.labels[0]] || colorMap.default;
    },
    
    // Link configuration
    linkStroke: '#999',
    linkStrokeOpacity: 0.6,
    linkStrokeWidth: d => Math.sqrt(d.value),
    
    // Forces configuration
    d3Force: {
        center: {
            x: 400,
            y: 300
        },
        charge: {
            strength: -30,
            distanceMax: 200
        },
        link: {
            distance: 50,
            iterations: 1
        }
    },
    
    // Interaction
    onNodeClick: node => {
        console.log('Clicked node:', node);
        highlightConnectedNodes(node);
    },
    
    onLinkClick: link => {
        console.log('Clicked link:', link);
        showRelationshipDetails(link);
    }
};

// Node highlighting
function highlightConnectedNodes(node) {
    const connectedNodes = new Set();
    graph.links.forEach(link => {
        if (link.source.id === node.id) connectedNodes.add(link.target.id);
        if (link.target.id === node.id) connectedNodes.add(link.source.id);
    });
    
    graph.nodes.forEach(n => {
        n.highlighted = n.id === node.id || connectedNodes.has(n.id);
    });
    
    updateVisualization();
}

// Relationship details
function showRelationshipDetails(link) {
    const details = document.getElementById('relationship-details');
    details.innerHTML = `
        <h3>Relationship Details</h3>
        <p>Type: ${link.type}</p>
        <p>Source: ${link.source.labels.join(', ')}</p>
        <p>Target: ${link.target.labels.join(', ')}</p>
        ${Object.entries(link.properties || {}).map(([k,v]) => `<p>${k}: ${v}</p>`).join('')}
    `;
    details.style.display = 'block';
}

// Update visualization
function updateVisualization() {
    // Update node appearance
    node.attr('fill', d => d.highlighted ? '#ff0' : graphConfig.nodeColor(d))
        .attr('r', d => d.highlighted ? 8 : graphConfig.nodeRadius);
    
    // Update link appearance
    link.attr('stroke-width', d => {
        const sourceHighlighted = d.source.highlighted;
        const targetHighlighted = d.target.highlighted;
        return (sourceHighlighted && targetHighlighted) ? 2 : 1;
    });
}

// Legend creation
function createLegend() {
    const legend = d3.select('#graph-legend')
        .append('g')
        .attr('class', 'legend')
        .attr('transform', 'translate(20,20)');

    const legendItems = Object.entries(graphConfig.nodeColor.colorMap);
    
    legendItems.forEach(([label, color], i) => {
        const legendRow = legend.append('g')
            .attr('transform', `translate(0, ${i * 20})`);
            
        legendRow.append('circle')
            .attr('cx', 10)
            .attr('cy', 10)
            .attr('r', 6)
            .style('fill', color);
            
        legendRow.append('text')
            .attr('x', 25)
            .attr('y', 10)
            .text(label)
            .style('font-size', '12px')
            .attr('alignment-baseline', 'middle');
    });
}

// Export configuration
export { graphConfig, createLegend };
