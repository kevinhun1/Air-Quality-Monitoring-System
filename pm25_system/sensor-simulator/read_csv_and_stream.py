<<<<<<< HEAD
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
=======
#!/usr/bin/env python3
"""
CSV -> FastAPI streamer.

CSV format expected (header row):
timestamp,pm25

Example timestamp: 2025-01-01T15:01:23
"""
import time
import csv
import requests
import os
from datetime import datetime
from requests.exceptions import RequestException

# CONFIG — edit these
API_URL = "http://localhost:8000/api/readings/"   # ensure trailing slash matches your router
CSV_PATH = "sensor.csv"                            # path to CSV produced by your embedded device
POLL_INTERVAL = 2.0                                # seconds between polling the CSV for new rows
MAX_RETRIES = 5
BACKOFF_FACTOR = 1.5                               # exponential backoff multiplier
TIMEOUT = 6                                        # request timeout in seconds

# If you want to use the uploaded file path (note: that's a .docx in your workspace),
# you could replace CSV_PATH with the absolute path:
# CSV_PATH = "/mnt/data/Proposal Document_fin.docx"
# (Only do that if your embedded device actually writes CSV to that path.)

def iso_parse(s):
    """Parse timestamp string to ISO-like format accepted by pydantic/datetime."""
    # Try flexible parsing; if already ISO, this will be ok
    try:
        return datetime.fromisoformat(s)
    except Exception:
        # Fallback: try common formats
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
            try:
                return datetime.strptime(s, fmt)
            except Exception:
                continue
    raise ValueError(f"Unrecognized timestamp format: {s}")


def post_reading(payload):
    """POST a single reading with retries and exponential backoff."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.post(API_URL, json=payload, timeout=TIMEOUT)
            r.raise_for_status()
            return r.json()
        except RequestException as e:
            wait = (BACKOFF_FACTOR ** (attempt - 1))
            print(f"[WARN] POST failed (attempt {attempt}/{MAX_RETRIES}): {e}. retrying in {wait:.1f}s")
            time.sleep(wait)
    # If we get here, all retries failed
    print("[ERROR] All retries failed for payload:", payload)
    return None


def stream_csv(csv_path):
    """
    Poll the CSV file and POST any new rows.
    It tracks the number of lines processed to avoid duplicates.
    """
    last_line_count = 0

    # Create file if missing (prevents crash)
    if not os.path.exists(csv_path):
        open(csv_path, "a").close()

    print(f"[INFO] Streaming from {csv_path} -> {API_URL}")
    while True:
        try:
            with open(csv_path, "r", newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except Exception as e:
            print(f"[ERROR] Failed to read CSV: {e}. Will retry in {POLL_INTERVAL}s")
            time.sleep(POLL_INTERVAL)
            continue

        total = len(rows)
        if total > last_line_count:
            new_rows = rows[last_line_count:]
            print(f"[INFO] Found {len(new_rows)} new rows")
            for row in new_rows:
                # Expecting keys: 'timestamp' and 'pm25' (case-insensitive)
                # Normalize keys
                row_keys = {k.strip().lower(): v.strip() for k, v in row.items()}
                if "timestamp" not in row_keys or "pm25" not in row_keys:
                    print("[WARN] Skipping row with unexpected columns:", row)
                    continue

                try:
                    ts = iso_parse(row_keys["timestamp"]).isoformat()
                    pm25 = float(row_keys["pm25"])
                except Exception as e:
                    print("[WARN] Invalid row data, skipping:", row, "error:", e)
                    continue

                payload = {
                    "timestamp": ts,
                    "pm25_value": pm25
                }

                resp = post_reading(payload)
                if resp is not None:
                    print("[OK] Sent reading:", payload, "response id:", resp.get("reading_id"))
                else:
                    # If posting failed after retries, you may choose to log and continue.
                    print("[ERROR] Failed to send reading after retries:", payload)

            last_line_count = total
        # else: no new rows

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    try:
        stream_csv(CSV_PATH)
    except KeyboardInterrupt:
        print("\n[INFO] Streamer stopped by user")
>>>>>>> b229d0647d56508b389d6ee36e830a7999909258
