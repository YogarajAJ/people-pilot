from flask import Flask
from flask_restful import Api
from api.controller import employee_blueprint
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
api = Api(app)

# Register Blueprints
app.register_blueprint(employee_blueprint, url_prefix="/api/employee")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5002))
    app.run(host="0.0.0.0", port=port, debug=True)