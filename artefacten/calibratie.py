import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def functie_calibratie(t, ABP, CVP):
    results = []
   
    # Helper functie voor de logica die voor beide signalen hetzelfde is
    def vind_calibratie_intervals(signaal, t, marge, naam, signaal_naam):
        # EXTRA VEILIGHEID: voorkom crash als signaal None is
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
       
        # Veiligheid: als >80% calibratie → waarschijnlijk fout bestand
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


# ==============================
# PLOT FUNCTIE
# ==============================
def plot_artefacten(t, ABP, CVP, df_results):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
   
    # --- Plot ABP ---
    ax1.plot(t, ABP, label='ABP', color='blue', linewidth=0.7)
    ax1.set_ylabel('Druk (mmHg)')
   
    # --- Plot CVP ---
    ax2.plot(t, CVP, label='CVP', color='black', linewidth=0.7)
    ax2.set_ylabel('Druk (mmHg)')
    ax2.set_xlabel('Tijd (s)')


    # --- Markeer artefacten ---
    for _, row in df_results.iterrows():
        start = float(row['Starttijd'])
        eind = float(row['Eindtijd'])
        signaal = row['Signaal']
       
        if signaal == 'ABP':
            ax1.fill_between([start, eind], ax1.get_ylim()[0], ax1.get_ylim()[1],
                             color='red', alpha=0.3)
            ax1.scatter([start, eind], [ax1.get_ylim()[1]]*2,
                        color='red', marker='*', s=100)
           
        elif signaal == 'CVP':
            ax2.fill_between([start, eind], ax2.get_ylim()[0], ax2.get_ylim()[1],
                             color='red', alpha=0.3)
            ax2.scatter([start, eind], [ax2.get_ylim()[1]]*2,
                        color='red', marker='*', s=100)

    ax1.legend(loc='upper right')
    plt.tight_layout()
    plt.show()


# ==============================
# TESTCODE (BELANGRIJK!)
# ==============================
if __name__ == "__main__":

    from readArtefacts import read_Artefacts

    # --- Instellingen ---
    path = r'C:\Users\Mila den Hollander\OneDrive - Delft University of Technology\Bureaublad\KT3405 Intensive care en computer simulatie\KT3401_AFdata_2025'
    folder = 'Calibratie'
    filename = 'D04Cal.xlsx'
    fs = 100

    # 1. Inladen
    t, ABP, CVP = read_Artefacts(path, folder, filename, fs)

    # DEBUG check
    print("Check None:", t is None, ABP is None, CVP is None)

    # 2. Detectie
    df_cal = functie_calibratie(t, ABP, CVP)

    # 3. Printen
    print("\nGedetecteerde Calibraties:")
    print(df_cal)

    # 4. Plotten
    plot_artefacten(t, ABP, CVP, df_cal)