import numpy as np
import pandas as pd
from scipy.signal import spectrogram
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

    start_tijden = t[start_idx]
    eind_tijden = t[eind_idx]

    return start_tijden, eind_tijden


def _voeg_dichte_segmenten_samen(start_tijden, eind_tijden, min_gap):
    """
    Voeg segmenten samen als de tussenruimte <= min_gap seconden is.
    """
    if len(start_tijden) == 0:
        return np.array([]), np.array([])

    nieuwe_starts = [start_tijden[0]]
    nieuwe_einden = [eind_tijden[0]]

    for i in range(1, len(start_tijden)):
        if start_tijden[i] - nieuwe_einden[-1] <= min_gap:
            nieuwe_einden[-1] = eind_tijden[i]
        else:
            nieuwe_starts.append(start_tijden[i])
            nieuwe_einden.append(eind_tijden[i])

    return np.array(nieuwe_starts), np.array(nieuwe_einden)


def _projecteer_bins_naar_samples(values_bins, tijden_bins, t):
    """
    Projecteer spectrogram-binwaarden stapvormig naar de sample-tijdas.
    Geen lineaire interpolatie om kunstmatige "bruggen" te vermijden.
    """
    values_bins = np.asarray(values_bins)
    tijden_bins = np.asarray(tijden_bins, dtype=float)
    t = np.asarray(t, dtype=float)

    if len(values_bins) == 0 or len(tijden_bins) == 0:
        return np.zeros(len(t), dtype=float)
    if len(values_bins) != len(tijden_bins):
        raise ValueError("values_bins en tijden_bins moeten even lang zijn.")

    # Grenzen tussen bins = midden tussen opeenvolgende spectrogramtijden.
    grenzen = np.empty(len(tijden_bins) + 1, dtype=float)
    grenzen[0] = -np.inf
    grenzen[-1] = np.inf
    if len(tijden_bins) > 1:
        grenzen[1:-1] = (tijden_bins[:-1] + tijden_bins[1:]) / 2.0

    idx = np.searchsorted(grenzen, t, side="right") - 1
    idx = np.clip(idx, 0, len(values_bins) - 1)
    return values_bins[idx]


def _gemiddelde_piekamplitude_per_bin(signaal, fs, resolution):
    """
    Bepaal per spectrogram-bin de gemiddelde piekamplitude (prominence).
    """
    x = np.asarray(signaal, dtype=float)
    bin_len = max(3, int(resolution * fs))
    n_bins = int(np.ceil(len(x) / bin_len))
    out = np.zeros(n_bins, dtype=float)

    for i in range(n_bins):
        start = i * bin_len
        end = min(len(x), (i + 1) * bin_len)
        seg = x[start:end]
        if len(seg) < 3:
            out[i] = 0.0
            continue
        peaks, props = find_peaks(seg, prominence=0)
        if len(peaks) == 0:
            out[i] = 0.0
            continue
        prom = np.asarray(props.get("prominences", []), dtype=float)
        out[i] = float(np.mean(prom)) if len(prom) else 0.0
    return out


def _robuuste_hoge_drempel(values, k):
    values = np.asarray(values, dtype=float)
    med = float(np.median(values))
    mad = float(np.median(np.abs(values - med)))
    scale = mad if mad > 1e-12 else float(np.std(values) + 1e-12)
    return med + float(k) * scale


def _slinger_detectie_1_signaal(signaal, t, fs, frange, resolution,
                                drempel_k, min_samples,
                                max_fraction, merge_gap,
                                peak_ratio_min, min_peak_amplitude):
    """
    Detecteer slinger in één signaal met spectrogram.
    """
    signaal = np.asarray(signaal, dtype=float)

    # Spectrogram
    frequenties, tijden, Sxx = spectrogram(
        signaal,
        fs=fs,
        nperseg=int(resolution * fs),
        noverlap=0,
        nfft=int(resolution * fs),
        scaling="spectrum",
        mode="magnitude"
    )

    # Kies interessante frequenties
    geselecteerd = (frequenties >= frange[0]) & (frequenties <= frange[1])

    if np.sum(geselecteerd) == 0:
        leeg_mask = np.zeros(len(t), dtype=bool)
        return leeg_mask, np.array([]), np.array([]), np.zeros(len(t))

    geselecteerde_power = np.abs(Sxx[geselecteerd, :])
    out = np.mean(geselecteerde_power, axis=0)
    afwijkingen = _projecteer_bins_naar_samples(out, tijden, t)
    mean_peak_amp_bins = _gemiddelde_piekamplitude_per_bin(signaal, fs, resolution)
    if len(mean_peak_amp_bins) != len(out):
        # Veilig alignen als afronding net anders uitvalt.
        mean_peak_amp_bins = np.interp(
            np.linspace(0, 1, len(out)),
            np.linspace(0, 1, len(mean_peak_amp_bins)),
            mean_peak_amp_bins,
        )

    # Robuuste threshold + spectrale piekdominantie
    drempelwaarde = _robuuste_hoge_drempel(out, drempel_k)
    mean_power = np.mean(geselecteerde_power, axis=0) + 1e-12
    peak_power = np.max(geselecteerde_power, axis=0)
    peak_ratio = peak_power / mean_power
    mask_bins = (
        (out > drempelwaarde)
        & (peak_ratio >= peak_ratio_min)
        & (mean_peak_amp_bins > float(min_peak_amplitude))
    )

    # Minimale duur afdwingen op spectrogram-niveau.
    # min_samples slaat op samples van het originele signaal.
    if len(tijden) > 1:
        dt_spec = float(np.median(np.diff(tijden)))
    else:
        dt_spec = float(resolution)
    min_duur_s = float(min_samples) / float(fs)
    min_bins = max(1, int(np.ceil(min_duur_s / dt_spec)))
    mask_bins = _maak_minimale_duur_mask(mask_bins, min_bins)

    # Verwerp als "bijna alles" positief is
    if np.sum(mask_bins) > max_fraction * len(mask_bins):
        mask_bins = np.zeros(len(mask_bins), dtype=bool)

    # Segmenten bepalen op spectrogramtijd-as.
    start_tijden, eind_tijden = _vind_segmenten(mask_bins, tijden)

    # Segmenten samenvoegen als ze dicht bij elkaar liggen
    start_tijden, eind_tijden = _voeg_dichte_segmenten_samen(
        start_tijden, eind_tijden, min_gap=merge_gap
    )

    # Maak sample-mask opnieuw op basis van samengevoegde segmenten.
    nieuwe_mask = np.zeros(len(t), dtype=bool)
    for s, e in zip(start_tijden, eind_tijden):
        nieuwe_mask[(t >= s) & (t <= e)] = True

    return nieuwe_mask, start_tijden, eind_tijden, afwijkingen


def functie_slinger(t, ABP, CVP, fs=100):
    """
    Detecteer slingerartefacten in ABP en CVP met spectrogramanalyse.

    Output:
        artefacten_uit : pandas DataFrame
        binair_ABP : boolean mask voor ABP
        binair_CVP : boolean mask voor CVP
        afwijkingen_ABP : geïnterpoleerde spectrogrammaat voor ABP
        afwijkingen_CVP : geïnterpoleerde spectrogrammaat voor CVP
    """
    resolution = 1.0
    frange = (5, 20)

    artefact_rows = []

    # ABP
    binair_ABP, start_ABP, eind_ABP, afwijkingen_ABP = _slinger_detectie_1_signaal(
        signaal=ABP,
        t=t,
        fs=fs,
        frange=frange,
        resolution=resolution,
        drempel_k=3.0,
        min_samples=350,
        max_fraction=0.6,
        merge_gap=0.5,
        peak_ratio_min=1.8,
        min_peak_amplitude=3.0
    )

    for s, e in zip(start_ABP, eind_ABP):
        artefact_rows.append([round(float(s), 2), round(float(e), 2), "Slinger", "ABP"])

    # CVP
    binair_CVP, start_CVP, eind_CVP, afwijkingen_CVP = _slinger_detectie_1_signaal(
        signaal=CVP,
        t=t,
        fs=fs,
        frange=frange,
        resolution=resolution,
        drempel_k=3.0,
        min_samples=350,
        max_fraction=0.7,
        merge_gap=0.3,
        peak_ratio_min=1.9,
        min_peak_amplitude=3.0
    )

    for s, e in zip(start_CVP, eind_CVP):
        artefact_rows.append([round(float(s), 2), round(float(e), 2), "Slinger", "CVP"])

    artefacten_uit = pd.DataFrame(
        artefact_rows,
        columns=["Starttijd", "Eindtijd", "Naam van het artefact", "Signaal"]
    )

    return artefacten_uit, binair_ABP, binair_CVP, afwijkingen_ABP, afwijkingen_CVP
