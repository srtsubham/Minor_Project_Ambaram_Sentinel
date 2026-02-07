import os

import numpy as np
import torch
import torch.nn as nn

MODEL_PATH = os.path.join("models", "cyclone_model.pth")


class CyclonePredictor(nn.Module):
    def __init__(self):
        super(CyclonePredictor, self).__init__()
        self.fc1 = nn.Linear(5, 16)
        self.fc2 = nn.Linear(16, 8)
        self.fc3 = nn.Linear(8, 1)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = self.fc3(x)
        return x


class WeatherAI:
    def __init__(self):
        self.model = CyclonePredictor()
        self.loaded = False

        if os.path.exists(MODEL_PATH):
            try:
                self.model.load_state_dict(torch.load(MODEL_PATH))
                self.model.eval()
                self.loaded = True
                print(f"AI Model loaded from {MODEL_PATH}")
            except Exception as e:
                print(f"Model load failed: {e}")
        else:
            print(f"Model file not found at {MODEL_PATH}")

    def predict(self, lat, lon, bt, insolation, moisture):
        if not self.loaded:
            return None

        input_data = torch.tensor(
            [[lat, lon, bt, insolation, moisture]], dtype=torch.float32
        )

        with torch.no_grad():
            prediction = self.model(input_data).item()

        intensity_shift = prediction
        next_lat = lat + (0.1 * abs(intensity_shift))
        next_lon = lon - (0.1 * abs(intensity_shift))

        return {
            "predicted_intensity": 100 + intensity_shift,
            "next_lat": next_lat,
            "next_lon": next_lon,
            "risk_score": max(0, min(100, (prediction * 10) + 50)),
        }
