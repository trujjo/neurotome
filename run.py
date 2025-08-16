import os
from app import app

if __name__ == "__main__":
    # Use environment variables for configuration
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV") == "development"
    
    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug
    )