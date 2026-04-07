# %%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from readArtefacts import read_Artefacts


def functie_CVD(t, ABP, CVP):
    artefacten_uit_CVD = []
   
    # MATLAB: mmCVP = movmean(CVP, [20 20]) -> Lijn stabiliseren
    # Venster van 41 samples (20 voor, 20 na + de huidige sample)
    cvp_series = pd.Series(CVP)
    mmCVP = cvp_series.rolling(window=41, center=True).mean().bfill().ffill().values
   
    # MATLAB: findpeaks(mmCVP, 'MinPeakHeight', 20)
    # Zoek indexen waar de druk boven de 20 mmHg uitkomt
    peak_indices, _ = find_peaks(mmCVP, height=20)
   
    if len(peak_indices) > 0:
        # MATLAB logica: Pak alles tussen de eerste en laatste gevonden piek
        min_idx = peak_indices[0]
        max_idx = peak_indices[-1]
       
        # Controleer of het interval lang genoeg is (MATLAB loop met nummer_CVD >= 900)
        # 900 samples bij 100Hz is 9 seconden.
        if (max_idx - min_idx) >= 900:
            start_t = t[min_idx]
            eind_t = t[max_idx]
            artefacten_uit_CVD.append([f"{start_t:.2f}", f"{eind_t:.2f}", "Infuus op CVD", "CVP"])
   
    return pd.DataFrame(artefacten_uit_CVD, columns=['Starttijd', 'Eindtijd', 'Naam', 'Signaal'])


# --- Instellingen voor de test ---
from config import DATA_PATH, FS
path = DATA_PATH
folder = 'Infuus_op_CVD'
filename = 'D04Inf-op-CVP.xlsx'
fs = FS


# 1. Data inladen
t, ABP, CVP = read_Artefacts(path, folder, filename, fs)


# 2. Detectie uitvoeren
df_results = functie_CVD(t, ABP, CVP)


# 3. Resultaten printen
print("\nGedetecteerde Artefacten (Infuus op CVD):")
print(df_results)


# 4. Plotten (Hergebruik de logica van je vorige script)
def plot_infuus(t, ABP, CVP, df_results):
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(t, CVP, label='CVP (CVD)', color='black', linewidth=0.7)
    ax.set_ylabel('Druk (mmHg)')
    ax.set_xlabel('Tijd (s)')
    ax.set_title(f'Detectie Infuus op CVD: {filename}')
   
    for _, row in df_results.iterrows():
        start, eind = float(row['Starttijd']), float(row['Eindtijd'])
        ax.fill_between([start, eind], ax.get_ylim()[0], ax.get_ylim()[1],
                         color='red', alpha=0.3, label='Infuus gedetecteerd')
        ax.scatter([start, eind], [ax.get_ylim()[1]]*2, color='red', marker='*', s=100)
   
    plt.legend()
    plt.show()


if not df_results.empty:
    plot_infuus(t, ABP, CVP, df_results)




