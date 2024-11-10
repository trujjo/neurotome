# Read the paste.txt file and modify it
with open('paste.txt', 'r') as file:
    content = file.read()

# Add the type buttons CSS
type_buttons_css = """
        .type-buttons {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            margin-bottom: 10px;
            padding: 10px;
            background-color: #2d2d2d;
            border-radius: 4px;
        }
        .type-button {
            padding: 5px 10px;
            background-color: #cc5500;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }
        .type-button:hover {
            background-color: #ff6a00;
        }
        .type-button.active {
            background-color: #ff6a00;
            border: 2px solid #ffffff;
        }
"""

# Reduce font size in existing CSS
content = content.replace("font-size: 8px", "font-size: 6px")

# Add type buttons CSS before the closing </style> tag
content = content.replace("</style>", type_buttons_css + "\
    </style>")

# Define the node types
node_types = [
    "nerve", "bone", "neuro", "region", "viscera", "muscle", "sense", 
    "vein", "artery", "cv", "function", "sensory", "gland", "lymph", 
    "head", "organ", "sensation", "skin"
]

# Create the type buttons HTML
type_buttons_html = '\
    <div class="type-buttons">\
'
for node_type in node_types:
    type_buttons_html += f'        <button class="type-button" onclick="showNodesByType(\'{node_type}\')">{node_type}</button>\
'
type_buttons_html += '    </div>\
'

# Add the type buttons HTML after the body tag
content = content.replace("<body>", "<body>\
" + type_buttons_html)

# Add the showNodesByType function before the closing </script> tag
show_nodes_function = """
        async function showNodesByType(nodeType) {
            if (!driver) {
                document.getElementById('status').style.backgroundColor = '#dc3545';
                document.getElementById('status').innerHTML = 'Not connected to database';
                return;
            }

            // Update active button
            document.querySelectorAll('.type-button').forEach(btn => {
                if (btn.textContent === nodeType) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            });

            const session = driver.session();
            document.getElementById('status').innerHTML = 'Fetching ' + nodeType + ' nodes...';
            
            try {
                const result = await session.run(`
                    MATCH (n:${nodeType})
                    WITH n
                    OPTIONAL MATCH (n)-[r]-(m)
                    RETURN DISTINCT n, r, m
                    LIMIT 50
                `);
                
                document.getElementById('status').innerHTML = 'Processing data...';
                
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
                document.getElementById('status').innerHTML = 'Rendering graph...';
                createForceGraph(currentNodes, links);
                document.getElementById('status').style.backgroundColor = '#28a745';
                document.getElementById('status').innerHTML = `Showing ${nodeType} nodes`;
                
            } catch (error) {
                document.getElementById('status').style.backgroundColor = '#dc3545';
                document.getElementById('status').innerHTML = 'Error: ' + error.message;
                console.error('Error:', error);
            } finally {
                await session.close();
            }
        }
"""

content = content.replace("</script>", show_nodes_function + "\
    </script>")

# Write the modified content to a new file
with open('neo4j_graph_modified.html', 'w') as file:
    file.write(content)

print("Successfully created neo4j_graph_modified.html with all modifications:"
      "\
- Reduced font size to 6px"
      "\
- Added type buttons with styling"
      "\
- Added showNodesByType function"
      "\
- Integrated with existing visualization code")
