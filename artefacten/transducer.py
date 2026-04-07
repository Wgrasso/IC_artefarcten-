import numpy as np
import pandas as pd
from scipy.signal import find_peaks


def _pieken_naar_segmenten(t, piek_idx, padding_s=0.1, max_gap_s=0.5):
    """
    Groepeer pieken tot losse segmenten op basis van tijdsgap.
    """
    if len(piek_idx) == 0:
        return []

    piek_t = np.asarray(t)[piek_idx]
    starts = [piek_t[0]]
    einden = [piek_t[0]]

    for i in range(1, len(piek_t)):
        if (piek_t[i] - einden[-1]) <= max_gap_s:
            einden[-1] = piek_t[i]
        else:
            starts.append(piek_t[i])
            einden.append(piek_t[i])

    segmenten = []
    for s, e in zip(starts, einden):
        start_t = max(0.0, float(s) - padding_s)
        eind_t = min(float(t[-1]), float(e) + padding_s)
        segmenten.append((start_t, eind_t))
    return segmenten


def functie_transducer(t, ABP, CVP):
    artefacten_uit_transducer = []

    # --- ABP Detectie ---
    abp_smooth = pd.Series(ABP).rolling(window=11, center=True).mean().bfill().ffill().values
    cvp_smooth = pd.Series(CVP).rolling(window=11, center=True).mean().bfill().ffill().values
    threshold_ABP = np.mean(ABP) - 21

    # Zoek pieken in het omgekeerde signaal (dalen in origineel)
    peaks_ABP, _ = find_peaks(-abp_smooth, height=-threshold_ABP)

    for start_t, eind_t in _pieken_naar_segmenten(t, peaks_ABP, padding_s=0.1, max_gap_s=0.5):
        # Hou alleen voldoende lange foutblokken over.
        if (eind_t - start_t) > 10:
            artefacten_uit_transducer.append([f"{start_t:.2f}", f"{eind_t:.2f}", "Transducer Hoog", "ABP"])

    # --- CVP Detectie ---
    threshold_CVP = np.mean(CVP) - 10
    peaks_CVP, _ = find_peaks(-cvp_smooth, height=-threshold_CVP)

    for start_t_cvp, eind_t_cvp in _pieken_naar_segmenten(t, peaks_CVP, padding_s=0.1, max_gap_s=0.5):
        if (eind_t_cvp - start_t_cvp) > 10:
            artefacten_uit_transducer.append([f"{start_t_cvp:.2f}", f"{eind_t_cvp:.2f}", "Transducer Hoog", "CVP"])

    return pd.DataFrame(artefacten_uit_transducer, columns=['Starttijd', 'Eindtijd', 'Naam', 'Signaal'])
