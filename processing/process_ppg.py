import numpy as np
from scipy.signal import butter, filtfilt, find_peaks, welch
from scipy.interpolate import CubicSpline
from antropy import app_entropy

def process_ppg(ppg, sf=25):
    # --- Bandpass filter: 0.5 - 8 Hz ---
    b, a = butter(2, [0.5 / (sf / 2), 8 / (sf / 2)], btype='band')
    ppg_filtered = filtfilt(b, a, ppg)

    # --- Peak detection ---
    min_peak_distance = int(round(sf * 0.3))
    peaks, _ = find_peaks(ppg_filtered, distance=min_peak_distance, prominence=0.2)
    peak_times = peaks / sf

    # --- NN intervals ---
    nn_intervals = np.diff(peak_times)

    # --- Time-domain HRV features ---
    sdnn = np.std(nn_intervals)
    rmssd = np.sqrt(np.mean(np.diff(nn_intervals) ** 2))

    # --- Instantaneous HR and interpolation ---
    fs_hrv = 4
    hr_values = 60 / nn_intervals
    mean_hr = np.mean(hr_values)

    hr_time = np.arange(peak_times[0], peak_times[-1], 1 / fs_hrv)
    cs = CubicSpline(peak_times[1:], hr_values)
    hr_interp = cs(hr_time)

    # --- Frequency-domain HRV (Welch) ---
    f, pxx = welch(hr_interp - np.mean(hr_interp), fs=fs_hrv, nperseg=256, noverlap=128, nfft=1024)

    lf_band = (f > 0.04) & (f < 0.15)
    hf_band = (f > 0.15) & (f < 0.4)

    hrv_lf = np.trapz(pxx[lf_band], f[lf_band])
    hrv_hf = np.trapz(pxx[hf_band], f[hf_band])
    lf_hf_ratio = hrv_lf / hrv_hf if hrv_hf != 0 else np.inf

    # --- Approximate Entropy ---
    ap_en = app_entropy(hr_interp)

    return mean_hr, lf_hf_ratio, sdnn, rmssd, ap_en