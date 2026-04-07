import numpy as np
import pandas as pd
from scipy.signal import find_peaks


def functie_transducer(t, ABP, CVP):
    artefacten_uit_transducer = []

    # --- ABP Detectie ---
    abp_smooth = pd.Series(ABP).rolling(window=11, center=True).mean().bfill().ffill().values
    cvp_smooth = pd.Series(CVP).rolling(window=11, center=True).mean().bfill().ffill().values
    threshold_ABP = np.mean(ABP) - 21

    # Zoek pieken in het omgekeerde signaal (dalen in origineel)
    peaks_ABP, _ = find_peaks(-abp_smooth, height=-threshold_ABP)

    if len(peaks_ABP) > 0:
        start_t = max(0, t[peaks_ABP[0]] - 0.3)
        eind_t = min(t[-1], t[peaks_ABP[-1]] + 0.3 + 2.0)

        if (eind_t - start_t) > 10:
            artefacten_uit_transducer.append([f"{start_t:.2f}", f"{eind_t:.2f}", "Transducer Hoog", "ABP"])

    # --- CVP Detectie ---
    threshold_CVP = np.mean(CVP) - 10
    peaks_CVP, _ = find_peaks(-CVP, height=-threshold_CVP)

    if len(peaks_CVP) > 0:
        start_t_cvp = max(0, t[peaks_CVP[0]] - 0.3)
        eind_t_cvp = min(t[-1], t[peaks_CVP[-1]] + 0.3 + 2.0)

        if (eind_t_cvp - start_t_cvp) > 10:
            artefacten_uit_transducer.append([f"{start_t_cvp:.2f}", f"{eind_t_cvp:.2f}", "Transducer Hoog", "CVP"])

    return pd.DataFrame(artefacten_uit_transducer, columns=['Starttijd', 'Eindtijd', 'Naam', 'Signaal'])
