# %%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import spectrogram, find_peaks
from readArtefacts import read_Artefacts


def functie_transducer(t, ABP, CVP):
    artefacten_uit_transducer = []
   
    # --- ABP Detectie ---
    # MATLAB: movmean(ABP, [5 5]) -> Python: pandas rolling mean
    cvp_smooth = pd.Series(CVP).rolling(window=11, center=True).mean().bfill().ffill().values
    threshold_ABP = np.mean(ABP) - 21
   
    # Zoek pieken in het omgekeerde signaal (MATLAB: findpeaks(-signaal, 'MinPeakHeight', -threshold))
    peaks_ABP, _ = find_peaks(-abp_smooth, height=-threshold_ABP)
   
    if len(peaks_ABP) > 0:
        # We pakken de globale start en eind op basis van de eerste/laatste piek (zoals je MATLAB code)
        start_t = max(0, t[peaks_ABP[0]] - 0.3) # 30 samples bij 100Hz is 0.3s
        eind_t = min(t[-1], t[peaks_ABP[-1]] + 0.3 + 2.0) # +2s marge uit je code
       
        if (eind_t - start_t) > 10: # Alleen intervallen > 10 seconden [cite: 111]
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




# --- Instellingen voor de test ---
if __name__ == "__main__":
    from config import DATA_PATH, FS
    path = DATA_PATH
    folder = 'Transducer_hoog'
    filename = 'D03Transd_hoog.xlsx'
    fs = FS


    # 1. Data inladen
    t, ABP, CVP = read_Artefacts(path, folder, filename, fs)


    # 2. Transducer detectie uitvoeren
    df_results = functie_transducer(t, ABP, CVP)


    # 3. Resultaat tonen (verplicht formaat voor de opdracht) [cite: 320, 328]
    print("\nGedetecteerde Artefacten:")
    print(df_results)


def plot_artefacten(t, ABP, CVP, df_results):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
   
    # --- Plot ABP ---
    ax1.plot(t, ABP, label='ABP', color='blue', linewidth=0.7)
    ax1.set_ylabel('Druk (mmHg)')
    ax1.set_title(f'Artefactdetectie: {filename}')
   
    # --- Plot CVP ---
    ax2.plot(t, CVP, label='CVP', color='black', linewidth=0.7)
    ax2.set_ylabel('Druk (mmHg)')
    ax2.set_xlabel('Tijd (s)')


    # --- Markeer de artefacten uit de tabel ---
    for _, row in df_results.iterrows():
        start = float(row['Starttijd'])
        eind = float(row['Eindtijd'])
        signaal = row['Signaal']
       
        if signaal == 'ABP':
            ax1.fill_between([start, eind], ax1.get_ylim()[0], ax1.get_ylim()[1],
                             color='red', alpha=0.3, label='Artefact gedetecteerd')
            # Optioneel: voeg sterretjes toe zoals in de opdracht
            ax1.scatter([start, eind], [ax1.get_ylim()[1]]*2, color='red', marker='*', s=100)
           
        elif signaal == 'CVP':
            ax2.fill_between([start, eind], ax2.get_ylim()[0], ax2.get_ylim()[1],
                             color='red', alpha=0.3)
            ax2.scatter([start, eind], [ax2.get_ylim()[1]]*2, color='red', marker='*', s=100)


    ax1.legend(loc='upper right')
    plt.tight_layout()
    plt.show()


# Roep de functie aan na je detectie







