import pydantic
from fastapi import FastAPI
from pydantic import BaseModel
from influx_client import write_telemetry

app = FastAPI()

class TelemetryData(BaseModel):
    speed: float
    throttle: float
    brake: float
    rpm: float
    n_gear: int
    drs: int | None = None
    timestamp: str | None = None

@app.post("/telemetry")
def receive_telemetry_for_replay(data: TelemetryData):
    print(f"Received: speed={data.speed}, throttle={data.throttle}, rpm={data.rpm} timestamp={data.timestamp}")
    write_telemetry(data.model_dump())
    return {"status": "ok"}