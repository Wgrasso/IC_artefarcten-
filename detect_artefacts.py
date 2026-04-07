import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import FS
from artefacten.calibratie import functie_calibratie
from artefacten.flush import functie_flush
from artefacten.gasbel import functie_gasbel
from artefacten.infuus import functie_CVD
from artefacten.slinger import functie_slinger
from artefacten.transducer import functie_transducer


EXPECTED_COLUMNS = ["Starttijd", "Eindtijd", "Naam van het artefact", "Signaal"]
ARTEFACT_COLORS = {
    "Calibratie": "#1f77b4",
    "Flush": "#ff7f0e",
    "Gasbel": "#2ca02c",
    "Slinger": "#d62728",
    "Transducer Hoog": "#9467bd",
    "Infuus op CVD": "#8c564b",
}


def load_artefact_excel(filepath: Path, fs: int):
    """Load ABP/CVP from the expected KT3401 Excel format."""
    raw = pd.read_excel(filepath, sheet_name=0, header=None)
    raw = raw.iloc[2:, :]
    if raw.empty or raw.shape[1] < 3:
        raise ValueError(
            "Expected KT3401 Excel format with ABP in column B and CVP in column C."
        )
    data = raw.to_numpy()

    ABP = pd.to_numeric(data[:, 1], errors="coerce")
    CVP = pd.to_numeric(data[:, 2], errors="coerce")
    ABP = pd.Series(ABP).interpolate(limit_direction="both").bfill().ffill().to_numpy()
    CVP = pd.Series(CVP).interpolate(limit_direction="both").bfill().ffill().to_numpy()
    t = np.arange(1 / fs, len(ABP) / fs + 1 / fs, 1 / fs)
    return t, ABP, CVP


def normalize_result(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize detector output to one shared schema."""
    if df is None or df.empty:
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

    out = df.copy()
    if "Naam" in out.columns and "Naam van het artefact" not in out.columns:
        out = out.rename(columns={"Naam": "Naam van het artefact"})

    for col in EXPECTED_COLUMNS:
        if col not in out.columns:
            out[col] = ""

    out = out[EXPECTED_COLUMNS]
    out["Starttijd"] = pd.to_numeric(out["Starttijd"], errors="coerce").round(2)
    out["Eindtijd"] = pd.to_numeric(out["Eindtijd"], errors="coerce").round(2)
    out = out.dropna(subset=["Starttijd", "Eindtijd"])
    return out


def run_all_detectors(t, ABP, CVP, fs: int) -> pd.DataFrame:
    """Run every detector and combine all artefact intervals."""
    frames = []

    df_calibratie = functie_calibratie(t, ABP, CVP)
    frames.append(normalize_result(df_calibratie))

    df_flush, _, _ = functie_flush(t, ABP, CVP, fs=fs)
    frames.append(normalize_result(df_flush))

    df_gasbel, _, _, _, _ = functie_gasbel(t, ABP, CVP, fs=fs)
    frames.append(normalize_result(df_gasbel))

    df_slinger, _, _, _, _ = functie_slinger(t, ABP, CVP, fs=fs)
    frames.append(normalize_result(df_slinger))

    df_transducer = functie_transducer(t, ABP, CVP)
    frames.append(normalize_result(df_transducer))

    df_cvd = functie_CVD(t, ABP, CVP)
    frames.append(normalize_result(df_cvd))

    combined = pd.concat(frames, ignore_index=True)
    if combined.empty:
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

    return combined.sort_values(by=["Starttijd", "Eindtijd", "Naam van het artefact"]).reset_index(drop=True)


def plot_signals_and_artefacts(t, ABP, CVP, results: pd.DataFrame, title: str):
    """Plot ABP/CVP and highlight detected artefact intervals."""
    fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
    fig.suptitle(title)

    axes[0].plot(t, ABP, color="black", linewidth=1.0, label="ABP")
    axes[0].set_ylabel("ABP (mmHg)")
    axes[0].grid(alpha=0.3)
    axes[0].legend(loc="upper right")

    axes[1].plot(t, CVP, color="black", linewidth=1.0, label="CVP")
    axes[1].set_ylabel("CVP (mmHg)")
    axes[1].set_xlabel("Tijd (s)")
    axes[1].grid(alpha=0.3)
    axes[1].legend(loc="upper right")

    if not results.empty:
        used_labels = set()
        for _, row in results.iterrows():
            start = float(row["Starttijd"])
            eind = float(row["Eindtijd"])
            artefact_name = str(row["Naam van het artefact"])
            signaal = str(row["Signaal"])
            color = ARTEFACT_COLORS.get(artefact_name, "#7f7f7f")
            interval_label = f"{artefact_name} ({start:.2f}-{eind:.2f}s)"
            label = interval_label if interval_label not in used_labels else None
            if label:
                used_labels.add(interval_label)

            if signaal.upper() == "ABP":
                axes[0].axvspan(start, eind, color=color, alpha=0.25, label=label)
            elif signaal.upper() == "CVP":
                axes[1].axvspan(start, eind, color=color, alpha=0.25, label=label)
            else:
                axes[0].axvspan(start, eind, color=color, alpha=0.15, label=label)
                axes[1].axvspan(start, eind, color=color, alpha=0.15, label=None)

        handles0, labels0 = axes[0].get_legend_handles_labels()
        handles1, labels1 = axes[1].get_legend_handles_labels()
        if len(labels0) > 1:
            axes[0].legend(loc="upper right", fontsize=8)
        if len(labels1) > 1:
            axes[1].legend(loc="upper right", fontsize=8)

    plt.tight_layout()
    plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Run all artefact detectors on one Excel file."
    )
    parser.add_argument("excel_file", help="Path to input Excel file (.xlsx)")
    parser.add_argument(
        "--output",
        default="",
        help="Optional output CSV path. If omitted, only prints results.",
    )
    parser.add_argument(
        "--fs",
        type=int,
        default=FS,
        help=f"Sampling rate in Hz (default from config.py: {FS})",
    )
    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Do not show signal plot with highlighted artefacts.",
    )
    args = parser.parse_args()
    if args.fs <= 0:
        parser.error("--fs must be a positive integer")

    filepath = Path(args.excel_file).expanduser().resolve()
    if not filepath.exists():
        raise FileNotFoundError(f"Input file not found: {filepath}")

    t, ABP, CVP = load_artefact_excel(filepath, fs=args.fs)
    results = run_all_detectors(t, ABP, CVP, fs=args.fs)

    print(f"\nDetected {len(results)} artefact interval(s) in: {filepath.name}")
    if results.empty:
        print("No artefacts detected.")
    else:
        print(results.to_string(index=False))

    if args.output:
        outpath = Path(args.output).expanduser().resolve()
        results.to_csv(outpath, index=False)
        print(f"\nSaved combined results to: {outpath}")

    if not args.no_plot:
        plot_title = f"Artefact detectie - {filepath.name}"
        plot_signals_and_artefacts(t, ABP, CVP, results, plot_title)


if __name__ == "__main__":
    main()
