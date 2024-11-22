try:
    from .app import app
except ImportError:
    try:
        from app import app
    except ImportError:
        raise ImportError("Could not import app. Make sure app.py exists in the correct location.")

if __name__ == "__main__":
    app.run(debug=True)