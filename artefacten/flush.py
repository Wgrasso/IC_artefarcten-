import numpy as np
import pandas as pd


def maak_minimale_duur_mask(signaal, threshold, min_samples):
    """
    Houd alleen stukken over waar het signaal minstens min_samples
    aaneengesloten boven de threshold ligt.
    """
    boven = signaal > threshold
    mask = np.zeros_like(boven, dtype=bool)

    teller = 0
    for i, val in enumerate(boven):
        if val:
            teller += 1
        else:
            if teller >= min_samples:
                mask[i - teller:i] = True
            teller = 0

    if teller >= min_samples:
        mask[len(boven) - teller:len(boven)] = True

    return mask


def vind_segmenten(mask, t):
    """
    Zet een boolean mask om naar start- en eindtijden.
    """
    mask = np.asarray(mask, dtype=int)
    padded = np.concatenate(([0], mask, [0]))
    diff_mask = np.diff(padded)

    start_idx = np.where(diff_mask == 1)[0]
    eind_idx = np.where(diff_mask == -1)[0] - 1

    start_tijden = t[start_idx]
    eind_tijden = t[eind_idx]

    return start_tijden, eind_tijden


def functie_flush(t, ABP, CVP, fs=100):
    """
    Detecteert flush-artefacten in ABP en CVP.
    Output is een pandas DataFrame met:
    Starttijd, Eindtijd, Naam van het artefact, Signaal
    """
    artefact_rows = []

    # Flush in ABP
    threshold_abp = np.mean(ABP) + 75
    binair_ABP = maak_minimale_duur_mask(ABP, threshold_abp, min_samples=70)
    start_abp, eind_abp = vind_segmenten(binair_ABP, t)

    for s, e in zip(start_abp, eind_abp):
        artefact_rows.append([round(float(s), 2), round(float(e), 2), "Flush", "ABP"])

    # Flush in CVP
    threshold_cvp = np.mean(CVP) + 75
    binair_CVP = maak_minimale_duur_mask(CVP, threshold_cvp, min_samples=100)
    start_cvp, eind_cvp = vind_segmenten(binair_CVP, t)

    for s, e in zip(start_cvp, eind_cvp):
        artefact_rows.append([round(float(s), 2), round(float(e), 2), "Flush", "CVP"])

    artefacten_uit_flush = pd.DataFrame(
        artefact_rows,
        columns=["Starttijd", "Eindtijd", "Naam van het artefact", "Signaal"]
    )

    return artefacten_uit_flush, binair_ABP, binair_CVP
