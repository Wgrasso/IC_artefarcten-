import numpy as np
import pandas as pd


def functie_calibratie(t, ABP, CVP):
    results = []

    def vind_calibratie_intervals(signaal, t, marge, naam, signaal_naam):
        if signaal is None or t is None:
            return []

        # Zoek alle indices waar het signaal rond 0 ligt
        is_rond_nul = (signaal > -marge) & (signaal < marge)

        # Filter: Alleen reeksen van minimaal 400 samples (4 seconden) tellen mee
        binaire_vector = np.zeros(len(signaal))

        # Rolling window check
        valid_blocks = pd.Series(is_rond_nul).rolling(window=400).sum() == 400

        if valid_blocks.any():
            for i in np.where(valid_blocks)[0]:
                binaire_vector[i-399:i+1] = 1

        # Veiligheid: als >80% calibratie -> waarschijnlijk fout bestand
        if np.sum(binaire_vector) > 0.8 * len(t):
            return []

        # Start- en eindtijden vinden
        diff_vec = np.diff(np.insert(binaire_vector.astype(int), 0, 0))
        starts = t[diff_vec == 1]
        einden = t[diff_vec == -1] if len(t[diff_vec == -1]) > 0 else [t[-1]]

        intervals = []
        for s, e in zip(starts, einden):
            intervals.append([f"{s:.2f}", f"{e:.2f}", naam, signaal_naam])

        return intervals

    # Uitvoeren voor ABP en CVP
    results.extend(vind_calibratie_intervals(ABP, t, 15, "Calibratie", "ABP"))
    results.extend(vind_calibratie_intervals(CVP, t, 5, "Calibratie", "CVP"))

    return pd.DataFrame(results, columns=['Starttijd', 'Eindtijd', 'Naam', 'Signaal'])
