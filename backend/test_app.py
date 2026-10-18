import pytest
from fastapi.testclient import TestClient
from main import app, sensors_db, alerts_db, ml_engine
from ml_engine import AcousticMLEngine

client = TestClient(app)

def test_ml_engine_normal_noise():
    engine = AcousticMLEngine(high_freq_threshold=2.0, sustain_frames=3)
    # Give normal noise where low_freq > high_freq
    is_anomaly1 = engine.analyze_audio_features("sensor_test", 50.0, 10.0)
    is_anomaly2 = engine.analyze_audio_features("sensor_test", 60.0, 15.0)
    is_anomaly3 = engine.analyze_audio_features("sensor_test", 55.0, 12.0)
    
    assert is_anomaly1 == False
    assert is_anomaly2 == False
    assert is_anomaly3 == False
    assert engine.sensor_state["sensor_test"] == 0

def test_ml_engine_anomaly_detection():
    engine = AcousticMLEngine(high_freq_threshold=2.0, sustain_frames=3)
    # Sequence of noises with high high_freq_power (hiss)
    assert not engine.analyze_audio_features("sensor_leak", 10.0, 50.0) # frame 1
    assert not engine.analyze_audio_features("sensor_leak", 12.0, 55.0) # frame 2
    # Frame 3 triggers the anomaly
    assert engine.analyze_audio_features("sensor_leak", 11.0, 60.0)

def test_ingest_data_normal():
    # Clear the DBs for clean test
    sensors_db.clear()
    alerts_db.clear()
    
    payload = {
        "sensor_id": "SNSR-TEST-1",
        "low_freq_power": 60.5,
        "high_freq_power": 12.2,
        "timestamp": "2026-04-06T12:00:00.000Z"
    }
    response = client.post("/ingest", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "received"
    assert response.json()["anomaly_detected"] == False
    
    assert "SNSR-TEST-1" in sensors_db
    assert sensors_db["SNSR-TEST-1"]["status"] == "normal"
    assert len(alerts_db) == 0

def test_ingest_data_leak():
    sensors_db.clear()
    alerts_db.clear()
    ml_engine.sensor_state.clear() # Reset global engine state
    
    payload = {
        "sensor_id": "SNSR-TEST-2",
        "low_freq_power": 10.0,
        "high_freq_power": 50.0,
        "timestamp": "2026-04-06T12:05:00.000Z"
    }
    
    # Send multiple to trigger the sustain frames (3)
    client.post("/ingest", json=payload)
    client.post("/ingest", json=payload)
    response = client.post("/ingest", json=payload)
    
    assert response.status_code == 200
    assert response.json()["anomaly_detected"] == True
    assert sensors_db["SNSR-TEST-2"]["status"] == "leak_detected"
    assert len(alerts_db) >= 1
    assert alerts_db[0]["severity"] == "CRITICAL"

def test_get_sensors():
    response = client.get("/sensors")
    assert response.status_code == 200
    assert "sensors" in response.json()
    assert isinstance(response.json()["sensors"], list)

def test_get_alerts():
    response = client.get("/alerts")
    assert response.status_code == 200
    assert "alerts" in response.json()
    assert isinstance(response.json()["alerts"], list)
