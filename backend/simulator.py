
import time
import random
import requests
import datetime

INGEST_URL = "http://localhost:8000/ingest"

# 5 simulated sensors along a pipeline
SENSORS = [
    "SNSR-NORTH-01",
    "SNSR-NORTH-02",
    "SNSR-EAST-01",
    "SNSR-EAST-02",
    "SNSR-WEST-01"
]

def generate_normal_city_noise():
    # Traffic rumbling, distant construction
    return {
        "low_freq_power": random.uniform(20.0, 80.0), # Lots of bass/rumble
        "high_freq_power": random.uniform(5.0, 15.0)  # Minimal high freq
    }

def generate_leak_hiss():
    # Penetrating high frequency hiss of escaping gas
    return {
        "low_freq_power": random.uniform(10.0, 30.0), # Regular background
        "high_freq_power": random.uniform(60.0, 100.0) # Spike in high freq
    }

def run_simulation():
    print("Starting pipeline acoustic sensor simulation...")
    
    # Introduce a leak randomly
    leaking_sensor = None
    leak_duration: int = 0
    
    while True:
        try:
            # Chance to start a leak if one isn't happening
            if not leaking_sensor and random.random() < 0.05:
                leaking_sensor = random.choice(SENSORS)
                leak_duration = random.randint(10, 30) # Persist for 10-30 iterations
                print(f"*** SIMULATING LEAK ON {leaking_sensor} ***")
            
            for sensor in SENSORS:
                if sensor == leaking_sensor:
                    audio_profile = generate_leak_hiss()
                    leak_duration -= 1  # type: ignore[operator]
                    if leak_duration <= 0:
                        leaking_sensor = None
                        print(f"*** SIMULATED LEAK FIXED ON {sensor} ***")
                else:
                    audio_profile = generate_normal_city_noise()
                
                payload = {
                    "sensor_id": sensor,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "low_freq_power": audio_profile["low_freq_power"],
                    "high_freq_power": audio_profile["high_freq_power"]
                }
                
                # Send to backend
                res = requests.post(INGEST_URL, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    if data.get("anomaly_detected"):
                        print(f"[{sensor}] Backend flagged ANOMALY!")
                else:
                     print(f"Error connecting to backend: {res.status_code}")
                     
            time.sleep(1) # Send data every second
        except Exception as e:
            print(f"Simulation error (is backend running?): {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_simulation()
