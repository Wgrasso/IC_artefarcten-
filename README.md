# ICU Artifact Detection

Detecting artifacts in intensive care patient monitoring data (arterial blood pressure and related signals). Built for the Intensive Care course in the Clinical Technology BSc at TU Delft.

## What it does

- `detect_artefacts.py` - main artifact detection pipeline (calibration, flush, air bubble, transducer height events)
- `readArtefacts.py` - reading and labeling recorded artifact data
- `testenplots.py` - visualization of detected artifacts
- `transducerhoog.ipynb` - transducer height analysis
- `algemene_code.ipynb` - general exploration

## Data

Clinical waveform recordings. Data paths are configured via `config.py` - copy `config_example.py` and set your own path.

## Approach

Rule-based detection plus a decision tree classifier on signal features, tuned per artifact type.

Group project with fellow Clinical Technology students.
