import matplotlib
matplotlib.use("Agg")  # Important pour Azure
import pandas as pd
import numpy as np
from scipy.stats import ks_2samp
import json
import os
from datetime import datetime

def detect_drift(reference_file, production_file, threshold=0.05, output_dir="drift_reports"):
    os.makedirs(output_dir, exist_ok=True)
    # Chargement des données
    ref = pd.read_csv(reference_file)
    prod = pd.read_csv(production_file)
    
    results = {}
    # Comparaison colonne par colonne
    for col in ref.columns:
        if col != "Exited" and col in prod.columns:
            # Test de Kolmogorov-Smirnov
            stat, p = ks_2samp(ref[col].dropna(), prod[col].dropna())
            results[col] = {
                "p_value": float(p),
                "statistic": float(stat),
                "drift_detected": bool(p < threshold)
            }
            
    return results