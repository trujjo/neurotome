function getFontSize(node, text) {
    const baseSize = node.size === 'large' ? 14 : node.size === 'medium' ? 12 : 10;
    const textLength = text.length;
    const nodeRadius = node.size === 'large' ? 30 : node.size === 'medium' ? 20 : 15;
    // Scale down font size if text is too long
    return Math.min(baseSize, (nodeRadius * 1.8) / textLength);
}

// In the node text creation/update section:
const nodeText = nodeElements.selectAll('text')
    .data(nodes)
    .join('text')
    .text(d => d.properties.name || d.labels[0])
    .attr('dy', '.35em')
    .attr('text-anchor', 'middle')
    .style('font-size', d => `${getFontSize(d, d.properties.name || d.labels[0])}px`)
    .style('fill', 'black')
    .style('pointer-events', 'none');
