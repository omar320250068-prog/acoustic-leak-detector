from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn
from ml_engine import AcousticMLEngine
import datetime

app = FastAPI(title="Acoustic Leak Detection System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ml_engine = AcousticMLEngine(high_freq_threshold=2.0)

class SensorData(BaseModel):
    sensor_id: str
    low_freq_power: float
    high_freq_power: float
    timestamp: str

# In-memory database of sensors and alerts
sensors_db: Dict[str, Any] = {}
alerts_db: List[Dict[str, Any]] = []

@app.post("/ingest")
async def ingest_sensor_data(data: SensorData):
    # Process through ML engine
    is_anomaly = ml_engine.analyze_audio_features(
        data.sensor_id, 
        data.low_freq_power, 
        data.high_freq_power
    )

    # Update sensor state
    sensors_db[data.sensor_id] = {
        "sensor_id": data.sensor_id,
        "last_seen": data.timestamp,
        "status": "leak_detected" if is_anomaly else "normal",
        "low_freq": data.low_freq_power,
        "high_freq": data.high_freq_power
    }

    # Generate alert if anomalous and not immediately recorded
    if is_anomaly:
        alert = {
            "sensor_id": data.sensor_id,
            "timestamp": data.timestamp,
            "severity": "CRITICAL",
            "message": "High-frequency hiss detected! Probable micro-leak."
        }
        # Avoid duplicate consecutive alerts (basic throttling)
        if not alerts_db or alerts_db[-1]["sensor_id"] != data.sensor_id or alerts_db[-1]["timestamp"] != data.timestamp:
           alerts_db.append(alert)

    return {"status": "received", "anomaly_detected": is_anomaly}

@app.get("/sensors")
async def get_sensors():
    return {"sensors": list(sensors_db.values())}

@app.get("/alerts")
async def get_alerts():
    recent_alerts: List[Dict[str, Any]] = alerts_db[-20:]  # type: ignore[index]
    return {"alerts": recent_alerts}  # Return last 20 alerts

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
