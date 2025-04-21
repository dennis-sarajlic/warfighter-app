import numpy as np
from scipy.signal import butter, filtfilt, medfilt, firwin, resample, hilbert
from scipy.stats import zscore
from .cvxEDA import cvxEDA 


def zcd(signal):

    return np.where(np.diff(np.sign(signal)))[0]

def process_gsr(eda, sf=25):
    # --- Preprocessing ---
    bfir = firwin(35, cutoff=1/(round(sf/2)), window='hamming')  # FIR filter of order 34
    eda_filtered = filtfilt(bfir, [1], medfilt(eda, kernel_size=round(sf)))
    eda_filtered = resample(eda_filtered, 8 * len(eda_filtered) // sf)
    fs = 8

    # --- Derive SCL and NS-SCR ---
    mean_eda = np.mean(eda_filtered)
    std_eda = np.std(eda_filtered)
    phasic, phasic_drivers, tonic, *_ = cvxEDA(zscore(eda_filtered), delta=1/fs)
    phasic = phasic * std_eda
    tonic = tonic * std_eda + mean_eda

    mean_scl = np.mean(tonic)

    # Estimate NS-SCRs per minute using zero-crossings
    eda_phasic_driver = phasic_drivers
    duration_minutes = len(eda_phasic_driver) / (fs * 60)
    zero_crossings = zcd(eda_phasic_driver - 0.05)
    ns_scr = (len(zero_crossings) / 2) / duration_minutes

    return mean_scl, ns_scr