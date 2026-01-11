import os
import sys
from flask import Flask

# Ensure the 'api' directory is in the path for Vercel
sys.path.append(os.path.dirname(__file__))

from utils import get_all_contributors, resolve_country_code
from widget import widget_bp

app = Flask(__name__)
app.register_blueprint(widget_bp)

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5002))
    app.run(host="0.0.0.0", port=port, debug=True)
