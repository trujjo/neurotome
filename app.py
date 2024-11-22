
from flask import Flask, jsonify, request, send_from_directory
import os

app = Flask(__name__)

# Serve static files from public directory
@app.route('/')
def index():
    return send_from_directory('public', 'index.html')

@app.route('/<path:path>')
def serve_file(path):
    return send_from_directory('public', path)

if __name__ == '__main__':
    app.run(debug=True)