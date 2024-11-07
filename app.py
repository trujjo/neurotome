# Write a minimal app.py to test Gunicorn deployment
minimal_app = '''from flask import Flask

# Create the Flask application instance
app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello World!'

# This is only used when running locally
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
'''

# Write the minimal app to app.py
with open('app.py', 'w') as f:
    f.write(minimal_app)

# Create a requirements.txt file
requirements = '''flask==3.0.0
gunicorn==21.2.0
neo4j==5.14.1'''

with open('requirements.txt', 'w') as f:
    f.write(requirements)

print("Created minimal app.py and requirements.txt to test Gunicorn deployment")
print("\
To test locally:")
print("1. pip install -r requirements.txt")
print("2. gunicorn app:app")
print("\
If this works, we'll add the Neo4j functionality back")
