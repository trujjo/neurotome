from flask import Flask, render_template
from flask_cors import CORS  # For handling CORS if needed

app = Flask(__name__)
CORS(app)  # Enable CORS if needed

# Move your HTML files to a 'templates' folder
# Move your CSS and JS files to a 'static' folder

@app.route('/')
def index():
    return render_template('neo4j_explorer.html')

if __name__ == '__main__':
    app.run(debug=True)
