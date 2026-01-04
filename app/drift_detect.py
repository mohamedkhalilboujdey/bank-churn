import matplotlib
matplotlib.use("Agg")  # OBLIGATOIRE pour Docker / Azure

import pandas as pd
import numpy as np
from scipy.stats import ks_2samp
import json
import os
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

def detect_drift(reference_file, production_file, threshold=0.05, output_dir="drift_reports"):
    os.makedirs(output_dir, exist_ok=True)

    ref = pd.read_csv(reference_file)
    prod = pd.read_csv(production_file)

    results = {}

    for col in ref.columns:
        if col != "Exited" and col in prod.columns:
            stat, p = ks_2samp(ref[col].dropna(), prod[col].dropna())
            results[col] = {
                "p_value": float(p),
                "statistic": float(stat),
                "drift_detected": bool(p < threshold)
            }

    report_path = f"{output_dir}/drift_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)

    return results