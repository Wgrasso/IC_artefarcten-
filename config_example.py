# ============================================================
#  CONFIG — Kopieer dit bestand naar config.py
#           en vul jouw pad in bij DATA_PATH
# ============================================================
#
#  Stap 1:  Kopieer dit bestand:
#             cp config_example.py config.py
#
#  Stap 2:  Vervang het pad hieronder met jouw eigen pad.
#
#  Stap 3:  Klaar!
#
# ============================================================

# Vervang hieronder met JOUW pad:
#
#   Mila:   r"C:\Users\Mila den Hollander\OneDrive - Delft University of Technology\Bureaublad\KT3405 Intensive care en computer simulatie\KT3401_AFdata_2025"
#   HP:     r"C:\Users\HP\OneDrive - Delft University of Technology\KT3405\Artefactdetectie"
#   Wouter: r"C:\Users\wpggr\..."

DATA_PATH = r"C:\Users\JOUWNAAM\pad\naar\KT3401_AFdata_2025"

FS = 100

# Mapnamen in je DATA_PATH
FOLDERS = {
    "Calibratie":      "Calibratie",
    "Flush":           "Flush",
    "Gasbel":          "Gasbel",
    "Slinger":         "Slinger",
    "Transducer_hoog": "Transducer_hoog",
    "Infuus_op_CVD":   "Infuus_op_CVD",
}

# Bestanden per map — voeg nieuwe bestanden toe aan de juiste lijst
FILES = {
    "Calibratie": [
        "D01Cal.xlsx",
        "D04Cal.xlsx",
    ],
    "Flush": [
        "D01Flush.xlsx",
        "D03Flush.xlsx",
        "D04Flush_ABP.xlsx",
        "D05Flush_ABP.xlsx",
        "D06Flush.xlsx",
    ],
    "Gasbel": [
        "D01Gasbel_Flush.xlsx",
        "D04Gasbel_Flush_Slinger.xlsx",
    ],
    "Slinger": [
        "D01Slinger.xlsx",
        "D02Slinger.xlsx",
        "D03Slinger.xlsx",
        "D05Slinger.xlsx",
        "D06Slinger.xlsx",
    ],
    "Transducer_hoog": [
        "D03Transd_hoog.xlsx",
    ],
    "Infuus_op_CVD": [
        "D04Inf-op-CVP.xlsx",
    ],
}
