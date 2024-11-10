class NeoViz {
    constructor() {
        this.config = {
            containerId: "viz",
            neo4j: neo4jConfig,
            labels: {
                Node: {
                    caption: "name",
                    size: "pagerank",
                    community: "community"
                }
            },
            relationships: {
                CONNECTED_TO: {
                    thickness: "weight",
                    caption: false
                }
            },
            initialCypher: "MATCH (n)-[r]-(m) RETURN n,r,m"
        };
        this.viz = new NeoVis.default(this.config);
    }

    render() {
        this.viz.render();
    }

    updateWithFilters(filters) {
        let cypher = "MATCH (n)-[r]-(m)";
        const conditions = [];
        
        if (filters.nodeTypes.length) {
            conditions.push(`(${filters.nodeTypes.map(t => `n:${t}`).join(' OR ')})`);
        }
        
        if (filters.sublocations.length) {
            conditions.push(`n.location IN [${filters.sublocations.map(l => `'${l}'`).join(',')}]`);
        }
        
        if (conditions.length) {
            cypher += ` WHERE ${conditions.join(' AND ')}`;
        }
        
        cypher += " RETURN n,r,m";
        this.viz.renderWithCypher(cypher);
    }
}
