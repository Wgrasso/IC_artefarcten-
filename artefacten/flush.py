# %%

import matplotlib.pyplot as plt
'''
Model with function to load artefact data from Excel .xls and .xlsx files and splits 
data in separate vectors to process. Written for KT3401 - Assignment Artefact Detection
'''
# #%% Clear system
# from IPython import get_ipython
# # Clear all variables (IPython/Jupyter)
# get_ipython().magic('reset -sf')
# import matplotlib.pyplot as plt
# # Close all figures
# plt.close('all')
# import os
# # Clear the console
# os.system('cls' if os.name == 'nt' else 'clear')

#%% Import modules
import pandas as pd
import numpy as np 
import os

def read_Artefacts(path, folder, filename, fs):
    """
    Inputs: 
    path: string to the path with data folders
    folder: string with the name of the folder with the dataset
    filename: string with name of the file, incl. extension
    fs: sampling rate (in Hz)

    Outputs: 
    t: time vector based on length of signal (to use instead of Time)
    ABP, CVP: vectors of arterial blood pressure and central venous pressure, with same length as t
    """
    filepath = os.path.join(path, folder, filename)
    print(f"Attempting to read file at: {filepath}")  # Debug print statement
    # Read the Excel file
    try:
        raw = pd.read_excel(filepath, sheet_name=0, header=None)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return None, None, None
    raw = pd.read_excel(filepath, sheet_name=0, header=None)
    
    # Skip the first two rows
    raw = raw.iloc[2:, :]
    
    # Convert the data to a numpy array
    data = raw.to_numpy()
    
    # Allocate imported array to column variable names
    ABP = pd.to_numeric(data[:, 1], errors = 'coerce')
    CVP = pd.to_numeric(data[:, 2], errors = 'coerce')
    
    # Create time vector
    t = np.arange(1/fs, len(ABP)/fs + 1/fs, 1/fs)

    return t, ABP, CVP






# %%
if __name__ == "__main__":

# Load data
    from config import DATA_PATH, FS, FILES
    path = DATA_PATH
    folder = "Flush"
    filename = FILES["Flush"][0]
    fs = FS
    filenames = FILES["Flush"]


    t, ABP, CVP = read_Artefacts(path, folder, filename, fs)

# %%
    if t is not None and CVP is not None:
        plt.plot(t, CVP, label='CVP')
        plt.plot(t, ABP, label='ABP')
        plt.xlabel('Time (s)')
        plt.ylabel('Pressure (mmHg)')
        plt.legend()
        plt.show()
    else:
        print("Unable to plot because the data could not be loaded.")

# %%
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

# %%
