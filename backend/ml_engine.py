class AcousticMLEngine:
    def __init__(self, high_freq_threshold=2.5, sustain_frames=3):
        """
        Mock ML Engine for Acoustic Leak Detection.
        high_freq_threshold: Ratio of high frequency (hiss) over low frequency (rumble).
        sustain_frames: How many consecutive frames the hiss must be detected to trigger an anomaly.
        """
        self.high_freq_threshold = high_freq_threshold
        self.sustain_frames = sustain_frames
        
        # State tracking per sensor: sensor_id -> consecutive_anomalous_frames
        self.sensor_state = {}

    def analyze_audio_features(self, sensor_id: str, low_freq_power: float, high_freq_power: float) -> bool:
        """
        Takes processed audio metrics (power in different bands).
        Returns True if a leak (hiss) is detected, False otherwise.
        """
        if sensor_id not in self.sensor_state:
            self.sensor_state[sensor_id] = 0

        # Prevent division by zero
        low_freq_power = max(low_freq_power, 0.01)
        ratio = high_freq_power / low_freq_power

        # If ratio exceeds threshold, it's a hiss
        if ratio > self.high_freq_threshold:
            self.sensor_state[sensor_id] += 1
        else:
            # Drop the consecutive frame count if normal noise
            self.sensor_state[sensor_id] = max(0, self.sensor_state[sensor_id] - 1)

        # Trigger if sustained
        if self.sensor_state[sensor_id] >= self.sustain_frames:
            return True
        return False
