class NeoViz {
    constructor() {
        this.config = {
            containerId: "viz",
            neo4j: {
                serverUrl: NEO4J_URI,
                serverUser: NEO4J_USER,
                serverPassword: NEO4J_PASSWORD
            },
            visConfig: {
                nodes: {
                    shape: 'circle',
                    font: {
                        size: 15,
                        color: '#ffffff'
                    },
                    borderWidth: 2,
                    size: 25
                },
                edges: {
                    arrows: {
                        to: {enabled: true, scaleFactor: 0.5}
                    },
                    color: '#808080',
                    width: 1
                },
                physics: {
                    enabled: true,
                    solver: 'forceAtlas2Based'
                }
            },
            labels: {
                Node: {
                    label: 'name',
                    [NeoVis.NEOVIS_ADVANCED_CONFIG]: {
                        function: '',
                        title: (node) => {
                            return node.properties.name;
                        },
                        color: '#4CAF50'
                    }
                }
            },
            relationships: {
                CONNECTED_TO: {
                    thickness: 'weight',
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

    updateWithFilters(nodeTypes, locations) {
        let cypher = "MATCH (n)-[r]-(m)";
        if (nodeTypes.length || locations.length) {
            const conditions = [];
            if (nodeTypes.length) {
                conditions.push(`(${nodeTypes.map(t => `n:${t}`).join(' OR ')})`);
            }
            if (locations.length) {
                conditions.push(`n.location IN [${locations.map(l => `'${l}'`).join(',')}]`);
            }
            cypher += ` WHERE ${conditions.join(' AND ')}`;
        }
        cypher += " RETURN n,r,m";
        this.viz.renderWithCypher(cypher);
    }
}
