from flask import Flask, render_template, jsonify, request
from neo4j import GraphDatabase
import os

app = Flask(__name__)

# Neo4j connection configuration
uri = ""bolt://4e5eeae5.databases.neo4j.io:7687""
user = ""neo4j""
password = ""Poconoco16!""

driver = GraphDatabase.driver(uri, auth=(user, password))

def get_all_nodes(tx):
    query = """"""
    MATCH (n)
    RETURN n, labels(n) as types, 
           CASE WHEN exists(n.x) THEN n.x ELSE rand() END as x,
           CASE WHEN exists(n.y) THEN n.y ELSE rand() END as y
    """"""
    result = tx.run(query)
    return [{""id"": record[""n""].id,
             ""label"": record[""n""].get(""name"", str(record[""n""].id)),
             ""type"": record[""types""][0] if record[""types""] else ""Unknown"",
             ""x"": record[""x""],
             ""y"": record[""y""],
             ""properties"": dict(record[""n""])} for record in result]

def get_all_relationships(tx):
    query = """"""
    MATCH (a)-[r]->(b)
    RETURN id(r) as id, type(r) as type, 
           id(a) as source, id(b) as target
    """"""
    result = tx.run(query)
    return [{""id"": record[""id""],
             ""type"": record[""type""],
             ""from"": record[""source""],
             ""to"": record[""target""]} for record in result]

def get_node_types(tx):
    query = """"""
    MATCH (n)
    RETURN DISTINCT labels(n) as types
    """"""
    result = tx.run(query)
    return [record[""types""][0] for record in result if record[""types""]]

def get_nodes_by_type(tx, node_type):
    query = """"""
    MATCH (n)
    WHERE $node_type IN labels(n)
    RETURN n,
           CASE WHEN exists(n.x) THEN n.x ELSE rand() END as x,
           CASE WHEN exists(n.y) THEN n.y ELSE rand() END as y
    """"""
    result = tx.run(query, node_type=node_type)
    return [{""id"": record[""n""].id,
             ""label"": record[""n""].get(""name"", str(record[""n""].id)),
             ""x"": record[""x""],
             ""y"": record[""y""],
             ""type"": node_type} for record in result]

def quick_search_nodes(tx, search_term):
    query = """"""
    MATCH (n)
    WHERE toLower(n.name) CONTAINS toLower($search_term)
       OR toString(id(n)) CONTAINS $search_term
    RETURN n,
           CASE WHEN exists(n.x) THEN n.x ELSE rand() END as x,
           CASE WHEN exists(n.y) THEN n.y ELSE rand() END as y
    LIMIT 10
    """"""
    result = tx.run(query, search_term=search_term)
    return [{""id"": record[""n""].id,
             ""label"": record[""n""].get(""name"", str(record[""n""].id)),
             ""x"": record[""x""],
             ""y"": record[""y""],
             ""type"": list(record[""n""].labels)[0] if record[""n""].labels else ""Unknown""} for record in result]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/graph')
def get_graph():
    with driver.session() as session:
        nodes = session.execute_read(get_all_nodes)
        relationships = session.execute_read(get_all_relationships)
    return jsonify({""nodes"": nodes, ""edges"": relationships})

@app.route('/api/node_types')
def get_available_node_types():
    with driver.session() as session:
        types = session.execute_read(get_node_types)
    return jsonify(types)

@app.route('/api/nodes_by_type/<node_type>')
def get_nodes_of_type(node_type):
    with driver.session() as session:
        nodes = session.execute_read(get_nodes_by_type, node_type)
    return jsonify(nodes)

@app.route('/api/quick_search')
def quick_search():
    search_term = request.args.get('term', '')
    if len(search_term) < 2:
        return jsonify([])
    with driver.session() as session:
        nodes = session.execute_read(quick_search_nodes, search_term)
    return jsonify(nodes)

if __name__ == '__main__':
    app.run(debug=True)
