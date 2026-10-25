from flask import Flask, jsonify, render_template, request
from datetime import datetime, timezone
from network_engine import NetworkHealingEngine

app = Flask(__name__)
engine = NetworkHealingEngine()

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/api/status")
def status():
    return jsonify(engine.snapshot())

@app.post("/api/simulate")
def simulate():
    payload = request.get_json(silent=True) or {}
    device_id = payload.get("device_id")
    fault = payload.get("fault", "high_latency")
    result = engine.simulate_fault(device_id, fault)
    return jsonify(result), (200 if result.get("ok") else 400)

@app.post("/api/heal/<alarm_id>")
def heal(alarm_id):
    result = engine.heal_alarm(alarm_id)
    return jsonify(result), (200 if result.get("ok") else 404)

@app.post("/api/heal-all")
def heal_all():
    return jsonify(engine.heal_all())

@app.post("/api/acknowledge/<alarm_id>")
def acknowledge(alarm_id):
    result = engine.acknowledge_alarm(alarm_id)
    return jsonify(result), (200 if result.get("ok") else 404)

@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "service": "autonomous-network-healing-platform",
                    "timestamp": datetime.now(timezone.utc).isoformat()})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
