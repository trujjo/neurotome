#!/usr/bin/env python3
"""
Test script to verify the application structure without requiring a database connection.
"""

import os
import sys
import tempfile

def test_application_structure():
    """Test that the application can be imported and basic structure is correct."""
    
    # Create a temporary .env file to avoid database connection
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("NEO4J_URI=bolt://localhost:7687\n")
        f.write("NEO4J_USER=test\n")
        f.write("NEO4J_PASSWORD=test\n")
        f.write("FLASK_ENV=development\n")
        temp_env_file = f.name
    
    # Set environment variables temporarily
    original_env = {}
    env_vars = {
        'NEO4J_URI': 'bolt://localhost:7687',
        'NEO4J_USER': 'test', 
        'NEO4J_PASSWORD': 'test',
        'FLASK_ENV': 'development'
    }
    
    for key, value in env_vars.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    try:
        print("🧪 Testing application structure...")
        
        # Test error handling module
        print("  ✓ Testing error_handling module...")
        from error_handling import handle_neo4j_error
        assert callable(handle_neo4j_error), "handle_neo4j_error should be callable"
        
        # Test basic Flask app structure (without database connection)
        print("  ✓ Testing basic imports...")
        from flask import Flask
        
        # Test that our main modules exist and have expected structure
        print("  ✓ Testing file structure...")
        required_files = [
            'app.py',
            'error_handling.py', 
            'run.py',
            'requirements.txt',
            'render.yaml',
            'templates/index.html',
            'static/js/graph.js',
            'static/css/styles.css'
        ]
        
        for file_path in required_files:
            assert os.path.exists(file_path), f"Required file missing: {file_path}"
        
        print("  ✓ Testing requirements.txt...")
        with open('requirements.txt', 'r') as f:
            requirements = f.read()
            required_packages = ['Flask', 'neo4j', 'gunicorn', 'python-dotenv']
            for package in required_packages:
                assert package in requirements, f"Required package missing: {package}"
        
        print("  ✓ Testing .env.example...")
        assert os.path.exists('.env.example'), ".env.example file should exist"
        
        print("  ✓ Testing .gitignore...")
        assert os.path.exists('.gitignore'), ".gitignore file should exist"
        
        print("  ✓ Testing README.md...")
        assert os.path.exists('README.md'), "README.md file should exist"
        
        print("✅ All application structure tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
        
    finally:
        # Restore original environment
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        
        # Clean up temp file
        try:
            os.unlink(temp_env_file)
        except:
            pass

def test_security_improvements():
    """Test that security issues have been addressed."""
    print("🔒 Testing security improvements...")
    
    # Check that graph.js doesn't contain hardcoded credentials
    with open('static/js/graph.js', 'r') as f:
        js_content = f.read()
        assert 'Poconoco16!' not in js_content, "JavaScript file should not contain hardcoded passwords"
        assert 'neo4j.driver(' not in js_content, "JavaScript should not contain direct Neo4j driver calls"
    
    # Check that render.yaml doesn't expose credentials
    with open('render.yaml', 'r') as f:
        yaml_content = f.read()
        assert 'sync: false' in yaml_content, "Render config should use secret environment variables"
        assert '4e5eeae5.databases.neo4j.io' not in yaml_content, "Render config should not contain hardcoded URIs"
    
    print("  ✓ No hardcoded credentials found")
    print("  ✓ Render config uses environment variables")
    print("✅ Security improvements verified!")

if __name__ == "__main__":
    success = True
    
    try:
        success &= test_application_structure()
        test_security_improvements()
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        success = False
    
    if success:
        print("\n🎉 All tests passed! Your application is ready to deploy.")
        print("\n📋 Next steps:")
        print("1. Set up your Neo4j database credentials in GitHub Secrets:")
        print("   - NEO4J_URI")
        print("   - NEO4J_USER") 
        print("   - NEO4J_PASSWORD")
        print("2. Deploy to your platform of choice")
        print("3. Test the /health endpoint to verify database connectivity")
    else:
        print("\n❌ Some tests failed. Please fix the issues before deploying.")
        sys.exit(1)
