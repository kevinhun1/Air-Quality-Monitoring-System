import csv
import time
import requests

API_URL = "http://localhost:8000/api/readings"

def stream_from_csv(csv_file_path):
    with open(csv_file_path, "r") as f:
        reader = csv.DictReader(f)

        for row in reader:
            payload = {
                "timestamp": row["timestamp"],
                "pm25_value": float(row["pm25"])
            }

            response = requests.post(API_URL, json=payload)
            print(response.json())

            time.sleep(2)  # simulate real-time streaming

if __name__ == "__main__":
    stream_from_csv("sensor.csv")
