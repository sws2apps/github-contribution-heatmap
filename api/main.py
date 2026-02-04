import os
import sys

# Ensure the 'api' directory is in the path for Vercel module discovery
api_dir = os.path.dirname(os.path.abspath(__file__))
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

from flask import Flask
from widget import widget_bp

app = Flask(__name__)
app.register_blueprint(widget_bp)

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5002))
    app.run(host="0.0.0.0", port=port, debug=False)
