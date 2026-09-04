import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from influx_client import write_telemetry, write_location
from track_repository import fetch_track
from ws_manager import manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    manager.bind_loop(asyncio.get_running_loop())
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class TelemetryData(BaseModel):
    driver_number: int
    speed: float
    throttle: float
    brake: float
    rpm: float
    n_gear: int
    drs: int | None = None
    timestamp: str | None = None

class LocationData(BaseModel):
    driver_number: int
    x: float
    y: float
    z: float
    timestamp: str | None = None

@app.post("/telemetry")
def receive_telemetry_for_replay(data: TelemetryData):
    print(f"Received: driver={data.driver_number}, speed={data.speed}, throttle={data.throttle}, rpm={data.rpm} timestamp={data.timestamp}")
    write_telemetry(data.model_dump())
    return {"status": "ok"}

@app.post("/location")
def receive_location_for_replay(data: LocationData):
    payload = data.model_dump()
    write_location(payload)
    manager.broadcast_from_thread(payload)
    return {"status": "ok"}

@app.get("/track")
def get_track(session_key: int = 11245, driver_number: int = 10):
    track = fetch_track(session_key, driver_number)
    if not track["points"]:
        raise HTTPException(status_code=404, detail=f"No track data for session {session_key}")
    return track

@app.websocket("/ws/location")
async def location_socket(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)