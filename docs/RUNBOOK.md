# Run the app locally

```powershell
docker compose up -d          # start Postgres, InfluxDB, Grafana, pgAdmin, api, feeder
```

Then open **http://localhost:3000** (`admin` / `admin`) -> dashboard

To re-watch a replay from the start and reset dashboards :

```powershell
docker exec influxdb influx delete --bucket bucket --org docs --token token --start 1970-01-01T00:00:00Z --stop 2100-01-01T00:00:00Z
docker compose restart feeder
```

---

## First-time setup

### 1. Python environment

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Build the local images

`api` and `feeder` are **built locally**. Build them once, and again after any code change:

```powershell
docker build -t f1:api    -f api/Dockerfile .
docker build -t f1:feeder -f feeder/Dockerfile .
```

### 3. Start the stack

```powershell
docker compose up -d
```

This boots Postgres (empty on first run), InfluxDB, Grafana (datasource + dashboard), pgAdmin, api, and feeder. On the very first boot Postgres runs
`ingest/schema.sql` automatically to create the `car_data` table.

### 4. Ingest the telemetry into Postgres

The feeder replays from Postgres, so it must contain data first. With the venv active:

```powershell
python ingest/ingest.py --session-key 11245 --driver-number 10
```

This talks to the OpenF1 API (rate-limited) and only needs to be done **once**, so the data
persists in the `postgres_data` volume.

### 5. Watch the replay

The `feeder` container started in step 3 may have exited because Postgres was empty. Kick it
again now that data is loaded:

```powershell
docker compose restart feeder
docker logs -f f1-feeder
```

- Open **http://localhost:3000** -> the dashboard shows speed / throttle+brake / RPM / gear / DRS.
- Open **http://localhost:5173** -> live replay on the track map
---

## After you change code

| You changed…                | Do this                                                                 |
|-----------------------------|-------------------------------------------------------------------------|
| `api/*.py`                  | `docker build -t f1:api -f api/Dockerfile .` then `docker compose up -d --force-recreate api` |
| `feeder/*.py`               | `docker build -t f1:feeder -f feeder/Dockerfile .` then `docker compose up -d --force-recreate feeder` |
| `grafana/**` (datasource/dashboard) | `docker compose restart grafana` (bind-mounted, no rebuild)      |
| `docker-compose.yaml`       | `docker compose up -d`                                                  |
| `ingest/schema.sql`         | `docker compose down -v` then redo First-time setup (schema only runs on an empty volume) |

---

## Access the interfaces

| Service    | URL                          | Login                        |
|------------|------------------------------|------------------------------|
| Grafana    | http://localhost:3000        | `admin` / `admin`            |
| API docs   | http://localhost:8000/docs   | —                            |
| InfluxDB   | http://localhost:8086        | `admin` / `password`         |
| pgAdmin    | http://localhost:5050        | `admin@admin.com` / `password` |
| PostgreSQL | localhost:5432               | `f1user` / `f1password` (db `f1data`) |

From **pgAdmin**, connect to Postgres with Host = `postgres` (the service name, **not**
`localhost`), port 5432, db `f1data`.

---

## Full reset (wipe all data and start clean)

```powershell
docker compose down -v
```

Then redo **First-time setup** from step 3 (images survive `down -v`, so you can skip step 2
unless you changed code).