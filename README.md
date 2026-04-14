# F1 Telemetry Replay Dashboard

> Real-time F1 telemetry replay pipeline — OpenF1 API → FastAPI → InfluxDB → Grafana

Personnal projectto get used to Grafana and data processing tools.

---

## Architecture
OpenF1 API → openf1_feeder.py → FastAPI (Uvicorn) → InfluxDB → Grafana

| Component | Role |
|---|---|
| `openf1_feeder.py` | Fetches F1 telemetry from OpenF1 API and replays it in real time |
| `api.py` | FastAPI endpoint that receives telemetry points |
| `influx_client.py` | Writes time-series data into InfluxDB |
| InfluxDB | Time-series database storing all telemetry |
| Grafana | Real-time dashboard with auto-refresh |

---

## Data

Telemetry is sourced from the **[OpenF1 API](https://openf1.org)** — a free, open-source REST API providing real-time and historical F1 data.

- ~33,800 data points at ~3.7 Hz

---

## Stack

- **Python 3.11** — feeder, API, InfluxDB client
- **FastAPI + Uvicorn** — REST API server
- **InfluxDB 2** — time-series database
- **Grafana** — dashboard & visualization
- **Docker** — runs InfluxDB and Grafana locally

---

## Getting Started

### Prerequisites

- Docker Desktop (if launched from Windows)
- Python 3.11+

### 1. Clone the repository

```bash
git clone https://github.com/TheRevGodish/f1-telemetry-replay-dashboard.git
cd f1-telemetry-replay-dashboard
```

### 2. Create and activate the virtual environment

```bash
python -m venv .venv
```

On Windows :
```bash
.venv\Scripts\activate
```

On Linux/Mac :
```bash
source .venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Start InfluxDB and Grafana

```bash
docker compose up -d
```

- InfluxDB → http://localhost:8086 (`admin` / `password`)
- Grafana → http://localhost:3000 (`admin` / `admin`)

### 5. Start the API server

In a first terminal (with venv activated) :

```bash
uvicorn api.api:app --reload
```

API running at → http://localhost:8000  
Interactive docs → http://localhost:8000/docs

### 6. Start the feeder

In a second terminal (with venv activated) :

```bash
python feeder/openf1_feeder.py
```

The feeder fetches all telemetry points for the selected driver and replays them in real time, respecting the original timestamps between each data point.

---

## Roadmap

- [ ] Multi-driver support — replay all 20 drivers simultaneously with threading
- [ ] Driver tags — one dashboard per driver in Grafana
- [ ] Battery strategy layer — energy consumption model and race strategy algorithm

---

## Author

Thomas — Software Engineering in a work-study program 
    @ CGI France & ENSEIRB-MATMECA Bordeaux  

GitHub : [@TheRevGodish](https://github.com/TheRevGodish)