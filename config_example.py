# ============================================================
#  CONFIG TEMPLATE
# ============================================================
#
#  HOE TE GEBRUIKEN / HOW TO USE
#  ──────────────────────────────
#
#  Stap 1:  Kopieer dit bestand naar config.py
#             cp config_example.py config.py
#
#  Stap 2:  Open config.py en vervang PASTE_YOUR_PATH_HERE
#           met het pad naar JOUW data map.
#
#  Stap 3:  Klaar! config.py staat in .gitignore, dus jouw
#           persoonlijke pad wordt nooit naar git gepusht.
#
# ============================================================
#
#  NIEUW BESTAND TOEVOEGEN
#  ───────────────────────
#
#  Stel: je hebt een nieuw databestand "D07Flush.xlsx" in de
#  map "Flush". Dan doe je het volgende:
#
#  Stap 1:  Open JOUW config.py (niet config_example.py!)
#
#  Stap 2:  Zoek de juiste map in het FILES woordenboek.
#           Bijvoorbeeld voor Flush:
#
#             "Flush": [
#                 "D01Flush.xlsx",
#                 "D03Flush.xlsx",
#                 ...
#                 "D07Flush.xlsx",    # <-- voeg hier toe
#             ],
#
#  Stap 3:  Sla op. Het programma pakt automatisch alle
#           bestanden uit de lijst.
#
#  NIEUWE MAP TOEVOEGEN
#  ────────────────────
#
#  Stap 1:  Voeg de mapnaam toe aan FOLDERS:
#
#             FOLDERS = {
#                 ...
#                 "NieuweMap": "NieuweMap",
#             }
#
#  Stap 2:  Voeg de bestanden toe aan FILES:
#
#             FILES = {
#                 ...
#                 "NieuweMap": [
#                     "D01Nieuw.xlsx",
#                 ],
#             }
#
#  LET OP: Als je wilt dat teamgenoten dezelfde bestanden
#  gebruiken, werk dan config_EXAMPLE.py bij en push die
#  naar git. Iedereen kopieert het opnieuw naar config.py.
#
# ============================================================

# ----- JOUW DATA PAD -----
# Plak het volledige pad naar de map met alle data mappen.
# Gebruik een raw string r"..." zodat backslashes werken.
#
# Voorbeelden:
#   r"C:\Users\Mila den Hollander\OneDrive - Delft University of Technology\Bureaublad\KT3405 Intensive care en computer simulatie\KT3401_AFdata_2025"
#   r"C:\Users\HP\OneDrive - Delft University of Technology\KT3405\Artefactdetectie"
#   r"/Users/jouwnaam/Documents/KT3401_AFdata_2025"

DATA_PATH = r"PASTE_YOUR_PATH_HERE"

# ----- SAMPLEFREQUENTIE -----
FS = 100

# ----- DATA MAPPEN -----
# De namen van de submappen in jouw DATA_PATH.
# Pas alleen aan als jouw mapnamen anders zijn.

FOLDERS = {
    "Calibratie":      "Calibratie",
    "Flush":           "Flush",
    "Gasbel":          "Gasbel",
    "Slinger":         "Slinger",
    "Transducer_hoog": "Transducer_hoog",
    "Infuus_op_CVD":   "Infuus_op_CVD",
}

# ----- DATA BESTANDEN PER MAP -----
# Lijst van .xlsx bestanden per artefacttype.
# Voeg toe of verwijder bestandsnamen naar wens.

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
