from flask import Flask
from api.controller import employee_blueprint

app = Flask(__name__)

# Register Blueprints
app.register_blueprint(employee_blueprint, url_prefix="/api/employee")

if __name__ == "__main__":
    app.run(debug=True, port=5002)
