# F1 Telemetry Replay Dashboard 

> Real-time F1 telemetry replay pipeline: OpenF1 API -> FastAPI -> InfluxDB -> Grafana

Personal project to get used to Grafana and data-engineering tooling

> **To run it**, see [`docs/RUNBOOK.md`](docs/RUNBOOK.md)

---

## Architecture

Ingestion and replay are two separate phases (OpenF1 is rate-limited, so we download **once**
into Postgres, then replay locally as often as we want):

```
INGEST (once):  OpenF1 API -> ingest.py -> PostgreSQL
REPLAY (∞):     PostgreSQL -> feeder -> FastAPI -> InfluxDB -> Grafana & TrackMap frontend
```

| Component | Role                                                             |
|---|------------------------------------------------------------------|
| `ingest/ingest.py` | Downloads a session's telemetry from OpenF1 into PostgreSQL      |
| `feeder/feeder.py` | Reads `car_data` from Postgres and replays it in real time       |
| `api/api.py` | FastAPI endpoint that receives telemetry points                  |
| `api/influx_client.py` | Writes time-series data into InfluxDB                            |
| PostgreSQL | Permanent raw store                                              |
| InfluxDB | Time-series store for the live replay             |
| Grafana | Real-time dashboard (datasource + dashboard provisioned as code) |

---

## Data

Telemetry is sourced from the **[OpenF1 API](https://openf1.org)**, a free, open-source REST API providing real-time and historical F1 data.

- ~33,800 data points at ~3.7 Hz

---

---

Thomas, Networks & Software Engineering in a work-study program 
    @ CGI France & ENSEIRB-MATMECA Bordeaux  

GitHub : [@TheRevGodish](https://github.com/TheRevGodish)