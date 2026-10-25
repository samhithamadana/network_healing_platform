"""Safe, self-contained network simulation and healing logic.

The demo never changes real network devices. Production NETCONF/RESTCONF adapters
should be added only after authentication, authorization, validation and approvals.
"""
from datetime import datetime, timezone
from uuid import uuid4
from threading import RLock

def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

class NetworkHealingEngine:
    def __init__(self):
        self._lock = RLock()
        self.devices = [
            {"id": "RTR-01", "name": "Core Router 01", "type": "Router", "status": "Healthy",
             "latency_ms": 18, "packet_loss": 0.0, "cpu": 31, "interface": "GigabitEthernet0/1"},
            {"id": "SW-02", "name": "Distribution Switch 02", "type": "Switch", "status": "Healthy",
             "latency_ms": 11, "packet_loss": 0.0, "cpu": 24, "interface": "GigabitEthernet1/0/1"},
            {"id": "FW-03", "name": "Edge Firewall 03", "type": "Firewall", "status": "Healthy",
             "latency_ms": 23, "packet_loss": 0.0, "cpu": 42, "interface": "WAN"},
            {"id": "AP-04", "name": "Access Point 04", "type": "Access Point", "status": "Healthy",
             "latency_ms": 9, "packet_loss": 0.0, "cpu": 19, "interface": "radio0"},
        ]
        self.alarms = []
        self.events = [{"id": str(uuid4()), "time": now(), "level": "INFO",
                        "message": "Platform started in safe simulation mode."}]
        self.healing_history = []

    def _event(self, level, message):
        self.events.insert(0, {"id": str(uuid4()), "time": now(), "level": level, "message": message})
        self.events = self.events[:40]

    def _create_alarm(self, device, fault, description, severity="CRITICAL"):
        existing = next((a for a in self.alarms if a["device_id"] == device["id"]
                         and a["fault"] == fault and a["status"] == "Active"), None)
        if existing:
            return existing
        causes = {
            "high_latency": ("Congestion or overloaded link", "Reduce traffic load / reroute traffic"),
            "packet_loss": ("Unstable interface or congested path", "Reset simulated interface / reroute traffic"),
            "device_down": ("Device or management connectivity failure", "Restart simulated device service"),
            "high_cpu": ("Control-plane process overload", "Restart simulated high-CPU process"),
        }
        cause, action = causes.get(fault, ("Unknown network fault", "Run diagnostic checks"))
        alarm = {"id": str(uuid4())[:8], "device_id": device["id"], "device_name": device["name"],
                 "fault": fault, "severity": severity, "description": description,
                 "root_cause": cause, "recommended_action": action, "status": "Active",
                 "created_at": now(), "acknowledged": False}
        self.alarms.insert(0, alarm)
        self._event("CRITICAL", f"Alarm {alarm['id']} raised for {device['id']}: {description}")
        return alarm

    def snapshot(self):
        with self._lock:
            return {"devices": self.devices, "alarms": self.alarms, "events": self.events,
                    "healing_history": self.healing_history,
                    "summary": {
                        "total_devices": len(self.devices),
                        "healthy_devices": sum(d["status"] == "Healthy" for d in self.devices),
                        "active_alarms": sum(a["status"] == "Active" for a in self.alarms),
                        "healed_alarms": sum(a["status"] == "Healed" for a in self.alarms),
                    },
                    "mode": "SIMULATION ONLY"}

    def simulate_fault(self, device_id, fault):
        allowed = {"high_latency", "packet_loss", "device_down", "high_cpu"}
        with self._lock:
            if fault not in allowed:
                return {"ok": False, "error": f"Unsupported fault. Choose: {', '.join(sorted(allowed))}"}
            device = next((d for d in self.devices if d["id"] == device_id), None)
            if not device:
                return {"ok": False, "error": "Device not found"}
            if fault == "high_latency":
                device.update(status="Degraded", latency_ms=240)
                alarm = self._create_alarm(device, fault, "Latency exceeded threshold (240 ms).")
            elif fault == "packet_loss":
                device.update(status="Degraded", packet_loss=18.5, latency_ms=95)
                alarm = self._create_alarm(device, fault, "Packet loss exceeded threshold (18.5%).")
            elif fault == "device_down":
                device.update(status="Down", latency_ms=0, packet_loss=100.0)
                alarm = self._create_alarm(device, fault, "Device stopped responding to health checks.")
            else:
                device.update(status="Degraded", cpu=97)
                alarm = self._create_alarm(device, fault, "CPU utilization exceeded threshold (97%).")
            self._event("WARNING", f"Fault injected into {device_id}: {fault} (simulation).")
            return {"ok": True, "alarm": alarm, "device": device}

    def heal_alarm(self, alarm_id):
        with self._lock:
            alarm = next((a for a in self.alarms if a["id"] == alarm_id), None)
            if not alarm:
                return {"ok": False, "error": "Alarm not found"}
            if alarm["status"] == "Healed":
                return {"ok": True, "alarm": alarm, "message": "Alarm was already healed"}
            device = next(d for d in self.devices if d["id"] == alarm["device_id"])
            # Simulation-only recovery values
            device.update(status="Healthy", latency_ms={"RTR-01": 18, "SW-02": 11, "FW-03": 23, "AP-04": 9}.get(device["id"], 15),
                          packet_loss=0.0, cpu={"RTR-01": 31, "SW-02": 24, "FW-03": 42, "AP-04": 19}.get(device["id"], 25))
            alarm["status"] = "Healed"
            alarm["healed_at"] = now()
            action = {"id": str(uuid4())[:8], "alarm_id": alarm_id, "device_id": device["id"],
                      "action": alarm["recommended_action"], "result": "SUCCESS (simulated)",
                      "time": now(), "mode": "SIMULATION ONLY"}
            self.healing_history.insert(0, action)
            self.healing_history = self.healing_history[:30]
            self._event("SUCCESS", f"Auto-healing completed for {device['id']} using simulated action.")
            return {"ok": True, "alarm": alarm, "device": device, "action": action}

    def heal_all(self):
        with self._lock:
            ids = [a["id"] for a in self.alarms if a["status"] == "Active"]
        results = [self.heal_alarm(alarm_id) for alarm_id in ids]
        return {"ok": True, "healed_count": sum(r.get("ok", False) for r in results), "results": results}

    def acknowledge_alarm(self, alarm_id):
        with self._lock:
            alarm = next((a for a in self.alarms if a["id"] == alarm_id), None)
            if not alarm:
                return {"ok": False, "error": "Alarm not found"}
            alarm["acknowledged"] = True
            self._event("INFO", f"Alarm {alarm_id} acknowledged by operator.")
            return {"ok": True, "alarm": alarm}
