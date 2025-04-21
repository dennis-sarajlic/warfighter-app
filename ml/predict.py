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
stress_model_path = os.path.join(base_dir, 'stress_holder.pkl')
fatigue_model_path = os.path.join(base_dir, 'fatigue_holder.pkl')

# Import trained models
with open(stress_model_path, 'rb') as f:
    stress_model = pickle.load(f)

with open(fatigue_model_path, 'rb') as f:
    fatigue_model = pickle.load(f)

def make_prediction(ppg_signal, gsr_signal):
    
    # Get features
    mean_hr, lf_hf_ratio, sdnn, rmssd, ap_en = process_ppg(ppg_signal)
    mean_scl, ns_scr = process_gsr(gsr_signal)

    # Create feature array for prediction
    features = np.array([[ns_scr, lf_hf_ratio, rmssd, sdnn, mean_hr, ap_en]])

    # Generate predictions
    stress_prediction = stress_model.predict(features)
    fatigue_prediction = fatigue_model.predict(features)

    return stress_prediction, fatigue_prediction