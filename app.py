# Read the existing file and modify it
with open('paste.txt', 'r') as file:
    content = file.read()

# Update the search functionality to auto-recognize after 3 letters
search_function_update = """
        let searchTimeout;
        
        function initializeSearch() {
            const searchBox = document.getElementById('searchBox');
            searchBox.addEventListener('input', function(e) {
                clearTimeout(searchTimeout);
                const searchTerm = e.target.value;
                
                if (searchTerm.length >= 3) {
                    searchTimeout = setTimeout(() => {
                        searchNodes(searchTerm);
                    }, 300); // 300ms delay for performance
                } else {
                    const searchResults = document.getElementById('searchResults');
                    searchResults.innerHTML = '';
                }
            });
        }

        async function searchNodes(searchTerm) {
            if (!driver) {
                document.getElementById('status').style.backgroundColor = '#dc3545';
                document.getElementById('status').innerHTML = 'Not connected to database';
                return;
            }

            const session = driver.session();
            try {
                const result = await session.run(`
                    MATCH (n)
                    WHERE toLower(n.name) CONTAINS toLower($searchTerm)
                    WITH n
                    OPTIONAL MATCH (n)-[r]-(m)
                    RETURN DISTINCT n, r, m
                    LIMIT 50
                `, { searchTerm });

                const nodes = new Map();
                const links = [];

                result.records.forEach(record => {
                    const source = record.get('n');
                    const target = record.get('m');
                    const relationship = record.get('r');

                    if (source && !nodes.has(source.identity.toString())) {
                        nodes.set(source.identity.toString(), {
                            id: source.identity.toString(),
                            label: source.labels[0],
                            name: source.properties.name || 'Unnamed'
                        });
                    }

                    if (target && !nodes.has(target.identity.toString())) {
                        nodes.set(target.identity.toString(), {
                            id: target.identity.toString(),
                            label: target.labels[0],
                            name: target.properties.name || 'Unnamed'
                        });
                    }

                    if (source && target && relationship) {
                        links.push({
                            source: source.identity.toString(),
                            target: target.identity.toString(),
                            type: relationship.type
                        });
                    }
                });

                currentNodes = Array.from(nodes.values());
                createForceGraph(currentNodes, links);
                
                document.getElementById('status').style.backgroundColor = '#28a745';
                document.getElementById('status').innerHTML = `Found ${currentNodes.length} matching nodes`;

            } catch (error) {
                document.getElementById('status').style.backgroundColor = '#dc3545';
                document.getElementById('status').innerHTML = 'Error: ' + error.message;
                console.error('Error:', error);
            } finally {
                await session.close();
            }
        }
"""

# Fix the random nodes function
random_nodes_function = """
        async function showRandomNodesWithRelationships() {
            if (!driver) {
                document.getElementById('status').style.backgroundColor = '#dc3545';
                document.getElementById('status').innerHTML = 'Not connected to database';
                return;
            }

            const session = driver.session();
            document.getElementById('status').innerHTML = 'Fetching random nodes...';
            
            try {
                const result = await session.run(`
                    MATCH (n)
                    WITH n, rand() as r
                    ORDER BY r
                    LIMIT 10
                    WITH COLLECT(n) as nodes
                    UNWIND nodes as n
                    OPTIONAL MATCH (n)-[r]-(m)
                    WHERE m IN nodes
                    RETURN DISTINCT n, r, m
                `);
                
                const nodes = new Map();
                const links = [];
                
                result.records.forEach(record => {
                    const source = record.get('n');
                    const target = record.get('m');
                    const relationship = record.get('r');
                    
                    if (source && !nodes.has(source.identity.toString())) {
                        nodes.set(source.identity.toString(), {
                            id: source.identity.toString(),
                            label: source.labels[0],
                            name: source.properties.name || 'Unnamed'
                        });
                    }
                    
                    if (target && !nodes.has(target.identity.toString())) {
                        nodes.set(target.identity.toString(), {
                            id: target.identity.toString(),
                            label: target.labels[0],
                            name: target.properties.name || 'Unnamed'
                        });
                    }
                    
                    if (source && target && relationship) {
                        links.push({
                            source: source.identity.toString(),
                            target: target.identity.toString(),
                            type: relationship.type
                        });
                    }
                });
                
                currentNodes = Array.from(nodes.values());
                createForceGraph(currentNodes, links);
                
                document.getElementById('status').style.backgroundColor = '#28a745';
                document.getElementById('status').innerHTML = 'Showing random connected nodes';
                
            } catch (error) {
                document.getElementById('status').style.backgroundColor = '#dc3545';
                document.getElementById('status').innerHTML = 'Error: ' + error.message;
                console.error('Error:', error);
            } finally {
                await session.close();
            }
        }
"""

# Add initialization call
init_call = """
        // Initialize search functionality when document is ready
        document.addEventListener('DOMContentLoaded', function() {
            initializeSearch();
        });
"""

# Replace the old search function and add the new random nodes function
content = content.replace("async function searchNodes(searchTerm) {", search_function_update)
content = content.replace("async function showRandomNodesWithRelationships() {", random_nodes_function)

# Add initialization call before the closing </script> tag
content = content.replace("</script>", init_call + "\
    </script>")

# Write the modified content to a new file
with open('neo4j_graph_modified.html', 'w') as file:
    file.write(content)

print("Successfully updated neo4j_graph_modified.html with all modifications:"
      "\
- Fixed random nodes button functionality"
      "\
- Added auto-search after 3 letters"
      "\
- Added search debouncing (300ms)"
      "\
- Improved error handling and status messages")
