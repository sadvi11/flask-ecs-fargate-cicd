import math
import os

from flask import Flask, jsonify, request

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

MAX_PRINCIPAL = 1_000_000_000
MAX_RATE = 100
MAX_YEARS = 100


def _positive_number(data, field, upper):
    """Return a positive finite number <= upper, or raise ValueError."""
    value = data.get(field)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a number")
    if not math.isfinite(value) or value <= 0 or value > upper:
        raise ValueError(f"{field} must be greater than 0 and at most {upper}")
    return value


@app.route("/calculate", methods=["POST"])
def calculate():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "request body must be a JSON object"}), 400

    try:
        principal = _positive_number(data, "principal", MAX_PRINCIPAL)
        annual_rate = _positive_number(data, "annual_rate", MAX_RATE)
        years = _positive_number(data, "years", MAX_YEARS)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    monthly_rate = annual_rate / 100 / 12
    n = years * 12
    payment = principal * (monthly_rate * (1 + monthly_rate) ** n) / ((1 + monthly_rate) ** n - 1)

    return jsonify({
        "principal": principal,
        "annual_rate": annual_rate,
        "years": years,
        "monthly_payment": round(payment, 2),
        "total_payment": round(payment * n, 2)
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
