# Autonomous Network Healing Platform

A full-stack Python educational project inspired by the supplied requirements:
- Alarm detection and root cause analysis (RCA)
- Automated recovery workflow
- REST API architecture
- Kafka and NETCONF/RESTCONF integration planning
- Ubuntu-friendly and Visual Studio Code-friendly setup

> **Safety:** This package is a simulation. It does not connect to or change real routers, switches, firewalls, or access points. Real device integration needs vendor-specific configuration, credentials, access controls, testing, and explicit authorization.

## Features

- Flask REST backend and responsive HTML/CSS/JavaScript dashboard
- Network device health view: status, latency, packet loss and CPU
- Demo fault injection: high latency, packet loss, device down, high CPU
- RCA explanation and recommended recovery action per alarm
- Audible browser alarm (browser may require a click to enable audio)
- Simulated auto-heal and healing history
- Acknowledge alarms and heal all active alarms
- Health endpoint at `/api/health`

## Requirements

- Python 3.10 or newer
- Visual Studio Code
- Internet connection for the first install of Flask

## Run in Visual Studio Code (Windows)

1. Extract `autonomous_network_healing_platform.zip`.
2. Open the extracted `autonomous_network_healing_platform` folder in VS Code.
3. Open **Terminal → New Terminal**.
4. Create a virtual environment:

   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, use Command Prompt and run:
   ```bat
   .venv\Scripts\activate.bat
   ```

5. Install dependencies:
   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```
6. Start the server:
   ```bash
   python app.py
   ```
7. Open <http://127.0.0.1:5000> in your browser.

## Run on Ubuntu / Linux

```bash
cd autonomous_network_healing_platform
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then visit <http://127.0.0.1:5000>.

## Demo walkthrough

1. Open the dashboard.
2. On a device row, click **Latency**, **Loss**, **Down**, or **CPU**.
3. The alarm section shows the likely root cause and recommended recovery.
4. The browser emits an audible alarm if sound is enabled.
5. Click **Auto-heal** for one alarm or **Heal all active alarms**.
6. Observe the device return to Healthy and the action appear in Healing history.

## REST API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Service health |
| GET | `/api/status` | Devices, alarms, events and healing history |
| POST | `/api/simulate` | Inject a demo fault: `{"device_id":"RTR-01","fault":"high_latency"}` |
| POST | `/api/heal/<alarm_id>` | Simulate recovery for an alarm |
| POST | `/api/heal-all` | Heal all active alarms |
| POST | `/api/acknowledge/<alarm_id>` | Acknowledge an alarm |

Supported fault values: `high_latency`, `packet_loss`, `device_down`, `high_cpu`.

## Architecture

```text
Browser dashboard (HTML/CSS/JavaScript)
                 |
              Flask REST API
                 |
        Network Healing Engine
          /       |        \
     Monitoring   RCA     Healing workflow
                 |
       Simulation device inventory
```

## NETCONF / RESTCONF and Kafka extension points

The supplied specification mentions NETCONF, REST APIs and Kafka. This starter keeps the core demo dependency-light and safe. For a production/advanced version:

- Implement a `DeviceAdapter` interface with separate NETCONF and RESTCONF implementations.
- Use a maintained client such as `ncclient` for NETCONF after verifying device compatibility.
- Use `requests` or a vendor SDK for RESTCONF; store secrets in environment variables or a secrets manager.
- Publish alarm and healing events to Kafka with a maintained Kafka client (for example, `confluent-kafka`) if a Kafka broker is deployed.
- Add authentication, role-based access, audit logs, approval gates, change rollback and device allowlists before real reconfiguration.
- Begin in read-only mode and test in a lab environment before enabling write operations.

No Kafka broker or real-device credentials are required for the demo.

## Project layout

```text
autonomous_network_healing_platform/
├── app.py
├── network_engine.py
├── requirements.txt
├── README.md
├── .gitignore
├── templates/
│   └── index.html
├── static/
│   ├── app.js
│   └── style.css
└── tests/
    └── test_network_engine.py
```

## Troubleshooting

- **`python` not found:** install Python 3.10+ and enable “Add Python to PATH”, or use `py` on Windows.
- **Flask not found:** activate `.venv` and run `pip install -r requirements.txt`.
- **Port 5000 already in use:** close the other app using it, or change the port in `app.py`.
- **No sound:** click the Sound button or interact with the page first; browser autoplay policies can block audio.
