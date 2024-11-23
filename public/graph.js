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
