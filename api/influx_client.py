from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import WriteOptions, SYNCHRONOUS, ASYNCHRONOUS
from datetime import datetime

INFLUXDB_URL = "http://influxdb:8086"
INFLUXDB_TOKEN = "token"
INFLUXDB_ORG = "docs"
INFLUXDB_BUCKET = "bucket"

client = InfluxDBClient(
    url=INFLUXDB_URL,
    token=INFLUXDB_TOKEN,
    org=INFLUXDB_ORG
)

#write_api = client.write_api(write_options=WriteOptions(
#   batch_size=10,
#   flush_interval=500
#))
write_api = client.write_api(write_options=SYNCHRONOUS)

def write_telemetry(data: dict):
    timestamp = data.get("timestamp")
    point = (
        Point("telemetry")
        .field("speed", float(data.get("speed", 0)))
        .field("throttle", float(data.get("throttle", 0)))
        .field("brake", float(data.get("brake", 0)))
        .field("rpm", float(data.get("rpm", 0)))
        .field ("n_gear", int(data.get("n_gear", 0)))
        .field("drs", int(data.get("drs") or 0))
    )
    if timestamp:
        point = point.time(datetime.fromisoformat(timestamp))

    write_api.write(bucket=INFLUXDB_BUCKET, record=point)