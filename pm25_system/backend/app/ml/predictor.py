import pickle
import os

# Try to import numpy; if unavailable, we'll fallback to threshold logic
try:
    import numpy as np
except Exception:
    np = None

# Try to load a trained model if present
model = None
model_path = os.path.join("app", "ml", "model.pkl")
if os.path.exists(model_path):
    try:
        with open(model_path, "rb") as f:
            model = pickle.load(f)
    except Exception:
        model = None

# Define risk categories (keep consistent with training labels if using a model)
RISK_LABELS = {
    0: "Low",
    1: "Moderate",
    2: "Unhealthy",
    3: "Very Unhealthy",
    4: "Hazardous"
}


def _threshold_classify(pm25_value: float) -> str:
    """Fallback classifier using simple PM2.5 thresholds (µg/m3).
    These thresholds are approximate and suitable for development when a model
    or numpy is not available.
    """
    try:
        v = float(pm25_value)
    except Exception:
        return "Unknown"

    if v <= 12.0:
        return "Low"
    if v <= 35.4:
        return "Moderate"
    if v <= 55.4:
        return "Unhealthy"
    if v <= 150.4:
        return "Very Unhealthy"
    return "Hazardous"


def classify_pm25(pm25_value: float) -> str:
    """Classify PM2.5 either using the loaded model (if available) or a
    simple threshold fallback.
    """
    # If model is available and numpy is present, use model prediction
    if model is not None and np is not None:
        try:
            arr = np.array([[float(pm25_value)]])
            prediction = model.predict(arr)[0]
            return RISK_LABELS.get(prediction, "Unknown")
        except Exception:
            # fall through to threshold fallback
            pass

    # Fallback
    return _threshold_classify(pm25_value)
