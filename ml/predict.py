import pickle
import sys
import os
import numpy as np
import warnings
warnings.filterwarnings("ignore")

# Navigate to the directory of script.py by going up one directory and then into sub_directory
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))

from processing import process_ppg, process_gsr

# Construct full paths to the model files
base_dir = os.path.dirname(__file__)
stress_model_path = os.path.join(base_dir, 'stress_model.pkl')

# Import trained models
with open(stress_model_path, 'rb') as f:
    stress_model = pickle.load(f)

def make_prediction(ppg_signal, gsr_signal):
    
    # Get features
    mean_hr, lf_hf_ratio, sdnn, rmssd, ap_en = process_ppg(ppg_signal)
    mean_scl, ns_scr, tvsymp_mean = process_gsr(gsr_signal)

    # Create feature array for prediction
    features = np.array([[tvsymp_mean, lf_hf_ratio, rmssd, sdnn, mean_hr, ap_en]])

    print(mean_hr, lf_hf_ratio, sdnn, rmssd, ap_en, tvsymp_mean)

    # Generate predictions
    stress_prediction = stress_model.predict(features)
    stress_proba = stress_model.predict_proba(features)[0][1]

    return stress_prediction, stress_proba