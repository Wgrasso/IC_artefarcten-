import numpy as np
import pandas as pd
from scipy.signal import find_peaks


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


def _rolling_amplitude(signaal, window_samples):
    """
    Lokale amplitude schatting: rolling (max - min).
    """
    s = pd.Series(np.asarray(signaal, dtype=float))
    roll_max = s.rolling(window=window_samples, center=True).max()
    roll_min = s.rolling(window=window_samples, center=True).min()
    amp = (roll_max - roll_min).bfill().ffill().to_numpy()
    return amp


def _rolling_peak_sharpness(signaal, fs, window_samples):
    """
    Lokale piekscherpte via gemiddelde prominences van systolische pieken.
    """
    signaal = np.asarray(signaal, dtype=float)
    peaks, props = find_peaks(
        signaal,
        prominence=max(1e-6, float(np.std(signaal) * 0.1)),
        distance=max(1, int(0.3 * fs)),
    )
    sharp = np.zeros(len(signaal), dtype=float)
    if len(peaks) == 0:
        return sharp
    prom = np.asarray(props.get("prominences", np.zeros(len(peaks))), dtype=float)
    point_series = pd.Series(0.0, index=np.arange(len(signaal)))
    point_series.iloc[peaks] = prom
    sharp = (
        point_series
        .rolling(window=window_samples, center=True)
        .mean()
        .bfill()
        .ffill()
        .to_numpy()
    )
    return sharp


def _detect_flush_mask(signaal, fs, threshold_offset, slope_threshold, min_samples):
    """
    Simpele flushschatting op hoge absolute waarde of snelle stijgsnelheid.
    """
    signaal = np.asarray(signaal, dtype=float)
    amplitude_mask = signaal > (float(np.mean(signaal)) + float(threshold_offset))
    slope_mask = np.concatenate(([False], np.abs(np.diff(signaal)) > float(slope_threshold)))
    flush_mask = _maak_minimale_duur_mask(amplitude_mask | slope_mask, min_samples=min_samples)
    return flush_mask


def _require_flush_before(mask, flush_mask):
    """
    Houd detectie alleen waar er eerder flush in het signaal is gezien.
    """
    if len(mask) != len(flush_mask):
        return mask
    flush_seen = np.cumsum(flush_mask.astype(int)) > 0
    return mask & flush_seen


def _detect_gasbel_1_signaal(signaal, t, fs, amp_window_s,
                             baseline_s, drop_fraction, sharp_drop_fraction,
                             gasbel_min_samples, merge_gap,
                             flush_threshold_offset, flush_slope_threshold, flush_min_samples):
    """
    Detecteer gasbel in één signaal.
    """
    signaal = np.asarray(signaal, dtype=float)

    amplitude = _rolling_amplitude(signaal, window_samples=max(3, int(amp_window_s * fs)))
    afwijkingen = amplitude.copy()

    if len(amplitude) == 0:
        leeg = np.zeros(len(t), dtype=bool)
        return leeg, np.array([]), np.array([]), afwijkingen

    window_samples = max(3, int(amp_window_s * fs))
    sharpness = _rolling_peak_sharpness(signaal, fs=fs, window_samples=window_samples)

    baseline_samples = max(1, int(baseline_s * fs))
    baseline_amp = float(np.mean(amplitude[:baseline_samples]))
    baseline_sharp = float(np.mean(sharpness[:baseline_samples]))
    amp_drempel = baseline_amp * (1.0 - float(drop_fraction))
    sharp_drempel = baseline_sharp * (1.0 - float(sharp_drop_fraction))

    # Gasbel: amplitude omlaag + piekscherpte omlaag.
    gasbel_mask = (amplitude < amp_drempel) & (sharpness < sharp_drempel)

    # Vereis dat er eerder een flush is geweest.
    flush_mask = _detect_flush_mask(
        signaal=signaal,
        fs=fs,
        threshold_offset=flush_threshold_offset,
        slope_threshold=flush_slope_threshold,
        min_samples=flush_min_samples,
    )
    gasbel_mask = _require_flush_before(gasbel_mask, flush_mask)
    gasbel_mask = _maak_minimale_duur_mask(gasbel_mask, gasbel_min_samples)

    # Eerste en laatste sample uitzetten
    if len(gasbel_mask) > 1:
        gasbel_mask[0] = False
        gasbel_mask[-1] = False

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
    artefact_rows = []

    binair_ABP, start_ABP, eind_ABP, afwijkingen_ABP = _detect_gasbel_1_signaal(
        signaal=ABP,
        t=t,
        fs=fs,
        amp_window_s=1.0,
        baseline_s=8.0,
        drop_fraction=0.35,
        sharp_drop_fraction=0.30,
        gasbel_min_samples=300,
        merge_gap=0.5,
        flush_threshold_offset=75.0,
        flush_slope_threshold=20.0,
        flush_min_samples=20,
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
