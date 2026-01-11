import os
from flask import Flask
from utils import get_all_contributors, resolve_country_code

app = Flask(__name__)

# === Register Blueprints ===
from widget import widget_bp
app.register_blueprint(widget_bp)

if __name__ == '__main__':
    # Local development server
    port = int(os.getenv("PORT", 5002))
    app.run(host="0.0.0.0", port=port, debug=True)


# === Register Blueprints ===
from widget import widget_bp

app.register_blueprint(widget_bp)


if __name__ == '__main__':
    app.run(port=5002, debug=True)
