import numpy as np
import pandas as pd
from scipy.signal import find_peaks


def functie_CVD(t, ABP, CVP):
    artefacten_uit_CVD = []

    # Smooth CVP met moving average (venster van 41 samples)
    cvp_series = pd.Series(CVP)
    mmCVP = cvp_series.rolling(window=41, center=True).mean().bfill().ffill().values

    # Zoek pieken boven 20 mmHg
    peak_indices, _ = find_peaks(mmCVP, height=20)

    if len(peak_indices) > 0:
        min_idx = peak_indices[0]
        max_idx = peak_indices[-1]

        # Alleen als interval >= 900 samples (9 seconden)
        if (max_idx - min_idx) >= 900:
            start_t = t[min_idx]
            eind_t = t[max_idx]
            artefacten_uit_CVD.append([f"{start_t:.2f}", f"{eind_t:.2f}", "Infuus op CVD", "CVP"])

    return pd.DataFrame(artefacten_uit_CVD, columns=['Starttijd', 'Eindtijd', 'Naam', 'Signaal'])
