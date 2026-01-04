from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import joblib
import numpy as np
import logging
import os
import traceback
from opencensus.ext.azure.log_exporter import AzureLogHandler
from app.models import CustomerFeatures, PredictionResponse, HealthResponse
from app.drift_detect import detect_drift

# -------------------------------------------------
# Logging & Application Insights
# -------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bank-churn-api")

APPINSIGHTS_CONN = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
if APPINSIGHTS_CONN:
    try:
        handler = AzureLogHandler(connection_string=APPINSIGHTS_CONN)
        logger.addHandler(handler)
        logger.info("Application Insights connecté avec succès")
    except Exception as e:
        logger.error(f"Echec connexion App Insights: {e}")
else:
    logger.warning("Application Insights non configuré")

# -------------------------------------------------
# Initialisation FastAPI
# -------------------------------------------------
app = FastAPI(title="Bank Churn Prediction API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_PATH = os.getenv("MODEL_PATH", "model/churn_model.pkl")
model = None

@app.on_event("startup")
async def load_model():
    global model
    try:
        model = joblib.load(MODEL_PATH)
        logger.info(f"Modèle chargé depuis {MODEL_PATH}")
    except Exception as e:
        logger.error(f"Erreur chargement modèle : {e}")
        model = None

# -------------------------------------------------
# Endpoints
# -------------------------------------------------
@app.get("/health", response_model=HealthResponse)
def health():
    if model is None:
        raise HTTPException(status_code=503, detail="Modèle non chargé")
    return {"status": "healthy", "model_loaded": True}

@app.post("/predict", response_model=PredictionResponse)
def predict(features: CustomerFeatures):
    if model is None:
        raise HTTPException(status_code=503, detail="Modèle indisponible")
    try:
        input_data = np.array([[ 
            features.CreditScore, features.Age, features.Tenure, features.Balance,
            features.NumOfProducts, features.HasCrCard, features.IsActiveMember,
            features.EstimatedSalary, features.Geography_Germany, features.Geography_Spain
        ]])
        
        proba = model.predict_proba(input_data)[0][1]
        prediction = int(proba > 0.5)
        risk = "Low" if proba < 0.3 else "Medium" if proba < 0.7 else "High"
        
        # Envoi du log à Azure
        logger.info("prediction", extra={"custom_dimensions": {
            "event_type": "prediction",
            "probability": float(proba),
            "risk_level": risk
        }})
        
        return {"churn_probability": round(float(proba), 4), "prediction": prediction, "risk_level": risk}
    except Exception as e:
        logger.error(f"Erreur prediction : {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/drift/check", tags=["Monitoring"])
def check_drift(threshold: float = 0.05):
    try:
        # Note: En production réelle, on utiliserait un Blob Storage
        # Ici on simule avec les fichiers locaux pour le workshop
        if not os.path.exists("data/production_data.csv"):
             return {"status": "no_data", "message": "Pas de données de prod générées"}

        results = detect_drift(
            reference_file="data/bank_churn.csv",
            production_file="data/production_data.csv",
            threshold=threshold
        )
        
        drifted = [f for f, r in results.items() if r["drift_detected"]]
        drift_pct = len(drifted) / len(results) * 100
        
        logger.warning("drift_detection", extra={"custom_dimensions": {
            "event_type": "drift_detection",
            "drift_percentage": drift_pct,
            "features_drifted": len(drifted)
        }})
        
        return {"status": "success", "features_drifted": len(drifted), "details": results}
    except Exception as e:
        logger.error(f"Erreur drift : {e}")
        raise HTTPException(status_code=500, detail=str(e))