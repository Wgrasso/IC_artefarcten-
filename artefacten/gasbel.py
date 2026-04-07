import numpy as np
import pandas as pd
from scipy.signal import spectrogram


def _maak_minimale_duur_mask(mask, min_samples):
    """
    Houd alleen stukken over waar minstens min_samples opeenvolgende True's zitten.
    """
    mask = np.asarray(mask, dtype=bool)
    output = np.zeros_like(mask, dtype=bool)

    teller = 0
    for i, val in enumerate(mask):
        if val:
            teller += 1
        else:
            if teller >= min_samples:
                output[i - teller:i] = True
            teller = 0

    if teller >= min_samples:
        output[len(mask) - teller:len(mask)] = True

    return output


def _vind_segmenten(mask, t):
    """
    Zet boolean mask om naar start- en eindtijden.
    """
    mask = np.asarray(mask, dtype=int)
    padded = np.concatenate(([0], mask, [0]))
    dmask = np.diff(padded)

    start_idx = np.where(dmask == 1)[0]
    eind_idx = np.where(dmask == -1)[0] - 1

    return t[start_idx], t[eind_idx]


def _voeg_segmenten_samen(start_tijden, eind_tijden, min_gap):
    """
    Voeg segmenten samen als tussenruimte <= min_gap.
    """
    if len(start_tijden) == 0:
        return np.array([]), np.array([])

    starts = [start_tijden[0]]
    einden = [eind_tijden[0]]

    for i in range(1, len(start_tijden)):
        if start_tijden[i] - einden[-1] <= min_gap:
            einden[-1] = eind_tijden[i]
        else:
            starts.append(start_tijden[i])
            einden.append(eind_tijden[i])

    return np.array(starts), np.array(einden)


def _spectrogram_afwijking(signaal, fs, resolution, frange):
    """
    Bereken spectrogrammaat in gekozen frequentiegebied en interpoleer naar lengte van signaal.
    """
    frequenties, tijden, Sxx = spectrogram(
        signaal,
        fs=fs,
        nperseg=int(resolution * fs),
        noverlap=0,
        nfft=int(resolution * fs),
        scaling="spectrum",
        mode="magnitude"
    )

    geselecteerd = (frequenties >= frange[0]) & (frequenties <= frange[1])

    if np.sum(geselecteerd) == 0:
        return np.zeros(len(signaal)), np.array([])

    out = np.mean(np.abs(Sxx[geselecteerd, :]), axis=0)

    afwijkingen = np.interp(
        np.linspace(0, 1, len(signaal)),
        np.linspace(0, 1, len(out)),
        out
    )

    return afwijkingen, out


def _detect_flush_mask(signaal, t, threshold_offset, min_samples):
    """
    Eenvoudige flush-detectie om flushgebieden uit de gasbelmask te halen.
    """
    threshold = np.mean(signaal) + threshold_offset
    piek_mask = signaal > threshold
    flush_mask = _maak_minimale_duur_mask(piek_mask, min_samples=min_samples)
    return flush_mask


def _detect_gasbel_1_signaal(signaal, t, fs, resolution, frange,
                             threshold_factor, flush_offset,
                             flush_min_samples, gasbel_min_samples,
                             max_fraction, merge_gap):
    """
    Detecteer gasbel in één signaal.
    """
    signaal = np.asarray(signaal, dtype=float)

    afwijkingen, out = _spectrogram_afwijking(signaal, fs, resolution, frange)

    if len(out) == 0:
        leeg = np.zeros(len(t), dtype=bool)
        return leeg, np.array([]), np.array([]), afwijkingen

    gem = np.mean(out)
    drempel = gem * threshold_factor

    # Gasbel = lagere spectrogramenergie
    afwijking_mask = afwijkingen < drempel

    # Flush apart schatten en verwijderen
    flush_mask = _detect_flush_mask(
        signaal=signaal,
        t=t,
        threshold_offset=flush_offset,
        min_samples=flush_min_samples
    )

    gasbel_mask = afwijking_mask & (~flush_mask)

    # Minimale duur afdwingen
    gasbel_mask = _maak_minimale_duur_mask(gasbel_mask, gasbel_min_samples)

    # Eerste en laatste sample uitzetten
    if len(gasbel_mask) > 1:
        gasbel_mask[0] = False
        gasbel_mask[-1] = False

    # Weggooien als bijna heel signaal positief is
    if np.sum(gasbel_mask) > max_fraction * len(t):
        gasbel_mask = np.zeros(len(t), dtype=bool)

    start_tijden, eind_tijden = _vind_segmenten(gasbel_mask, t)
    start_tijden, eind_tijden = _voeg_segmenten_samen(start_tijden, eind_tijden, merge_gap)

    # Mask opnieuw opbouwen na samenvoegen
    nieuw_mask = np.zeros(len(t), dtype=bool)
    for s, e in zip(start_tijden, eind_tijden):
        nieuw_mask[(t >= s) & (t <= e)] = True

    return nieuw_mask, start_tijden, eind_tijden, afwijkingen


def functie_gasbel(t, ABP, CVP, fs=100):
    """
    Detecteer gasbelartefacten alleen in ABP.
    """
    resolution = 0.5
    frange = (5, 20)

    artefact_rows = []

    binair_ABP, start_ABP, eind_ABP, afwijkingen_ABP = _detect_gasbel_1_signaal(
        signaal=ABP,
        t=t,
        fs=fs,
        resolution=resolution,
        frange=frange,
        threshold_factor=0.65,
        flush_offset=75,
        flush_min_samples=20,
        gasbel_min_samples=300,
        max_fraction=0.7,
        merge_gap=2.0
    )

    for s, e in zip(start_ABP, eind_ABP):
        artefact_rows.append([round(float(s), 2), round(float(e), 2), "Gasbel", "ABP"])

    binair_CVP = np.zeros(len(t), dtype=bool)
    afwijkingen_CVP = np.zeros(len(t))

    artefacten_uit = pd.DataFrame(
        artefact_rows,
        columns=["Starttijd", "Eindtijd", "Naam van het artefact", "Signaal"]
    )

    return artefacten_uit, binair_ABP, binair_CVP, afwijkingen_ABP, afwijkingen_CVP
