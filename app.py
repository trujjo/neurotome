@app.route('/nodes/<node_type>')
def get_nodes_by_type(node_type):
    try:
        with driver.session() as session:
            # Modified query to get nodes of specific type with their relationships
            query = f"""
            MATCH (n:{node_type})
            OPTIONAL MATCH (n)-[r]-(m)
            WITH n, r, m
            RETURN DISTINCT 
                id(n) as id,
                labels(n) as labels,
                properties(n) as properties,
                collect(DISTINCT {{
                    relationshipType: type(r),
                    nodeId: id(m),
                    nodeLabels: labels(m),
                    nodeProperties: properties(m)
                }}) as connections
            """
            
            result = session.run(query)
            nodes_data = []
            relationships_data = []
            
            for record in result:
                # Add the main node
                nodes_data.append({
                    'id': str(record['id']),
                    'label': record['labels'][0],
                    'properties': record['properties']
                })
                
                # Add connected nodes and relationships
                for conn in record['connections']:
                    if conn['nodeId'] is not None:
                        # Add connected node
                        nodes_data.append({
                            'id': str(conn['nodeId']),
                            'label': conn['nodeLabels'][0],
                            'properties': conn['nodeProperties']
                        })
                        # Add relationship
                        relationships_data.append({
                            'from': str(record['id']),
                            'to': str(conn['nodeId']),
                            'type': conn['relationshipType']
                        })

            return jsonify({
                'nodes': list({node['id']: node for node in nodes_data}.values()),  # Remove duplicates
                'relationships': relationships_data
            })
    except Exception as e:
        logging.error(f"Error in get_nodes_by_type: {str(e)}")
        return jsonify({'error': str(e)}), 500
