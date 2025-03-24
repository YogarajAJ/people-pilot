from flask import Flask
from api.controller import employee_blueprint
import os

app = Flask(__name__)

# Register Blueprints
app.register_blueprint(employee_blueprint, url_prefix="/api/employee")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5002))
    app.run(host="0.0.0.0", port=port, debug=True)