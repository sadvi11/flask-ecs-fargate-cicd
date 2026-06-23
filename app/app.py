from flask import Flask, jsonify, request
import os

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "flask-ecs-fargate"}), 200

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Flask app running on ECS Fargate",
        "version": "1.0.0"
    }), 200

@app.route("/calculate", methods=["POST"])
def calculate():
    data = request.get_json()
    principal = data.get("principal", 0)
    annual_rate = data.get("annual_rate", 0)
    years = data.get("years", 0)

    if not all([principal, annual_rate, years]):
        return jsonify({"error": "principal, annual_rate, years required"}), 400

    monthly_rate = annual_rate / 100 / 12
    n = years * 12
    payment = principal * (monthly_rate * (1 + monthly_rate)**n) / ((1 + monthly_rate)**n - 1)

    return jsonify({
        "principal": principal,
        "annual_rate": annual_rate,
        "years": years,
        "monthly_payment": round(payment, 2),
        "total_payment": round(payment * n, 2)
    }), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
