import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from config import FS
from detect_artefacts import (
    ARTEFACT_COLORS,
    load_artefact_excel,
    run_all_detectors,
)


def _plot_folder_as_subplots(folder: Path, excel_files, fs: int) -> None:
    n = len(excel_files)
    fig, axes = plt.subplots(
        nrows=n,
        ncols=2,
        figsize=(18, max(3 * n, 6)),
        sharex=False,
        squeeze=False,
    )
    fig.suptitle(f"Batch: {folder.name}", fontsize=14)
    gebruikte_artefacten = set()

    for i, excel_file in enumerate(excel_files):
        print(f"Processing: {excel_file.name}")
        t, ABP, CVP = load_artefact_excel(excel_file, fs=fs)
        results = run_all_detectors(t, ABP, CVP, fs=fs)

        ax_abp = axes[i, 0]
        ax_cvp = axes[i, 1]

        ax_abp.plot(t, ABP, color="black", linewidth=0.9)
        ax_cvp.plot(t, CVP, color="black", linewidth=0.9)

        ax_abp.set_title(f"{excel_file.name} - ABP", fontsize=9)
        ax_cvp.set_title(f"{excel_file.name} - CVP", fontsize=9)
        ax_abp.set_ylabel("mmHg")
        ax_cvp.set_ylabel("mmHg")
        ax_abp.set_xlabel("Tijd (s)")
        ax_cvp.set_xlabel("Tijd (s)")
        ax_abp.grid(alpha=0.25)
        ax_cvp.grid(alpha=0.25)

        if not results.empty:
            for _, row in results.iterrows():
                start = float(row["Starttijd"])
                end = float(row["Eindtijd"])
                artefact_name = str(row["Naam van het artefact"])
                signaal = str(row["Signaal"]).upper()
                color = ARTEFACT_COLORS.get(artefact_name, "#7f7f7f")
                gebruikte_artefacten.add(artefact_name)

                if signaal == "ABP":
                    ax_abp.axvspan(start, end, color=color, alpha=0.25)
                elif signaal == "CVP":
                    ax_cvp.axvspan(start, end, color=color, alpha=0.25)
                else:
                    ax_abp.axvspan(start, end, color=color, alpha=0.15)
                    ax_cvp.axvspan(start, end, color=color, alpha=0.15)

    if gebruikte_artefacten:
        legenda_handles = [
            Patch(facecolor=ARTEFACT_COLORS.get(name, "#7f7f7f"), edgecolor="none", alpha=0.25, label=name)
            for name in sorted(gebruikte_artefacten)
        ]
        fig.legend(
            handles=legenda_handles,
            loc="upper center",
            ncol=min(4, len(legenda_handles)),
            fontsize=9,
            frameon=True,
            bbox_to_anchor=(0.5, 0.99),
        )

    plt.tight_layout()
    plt.show()


def run_folder_batches(base_dir: Path, fs: int) -> None:
    subfolders = sorted([p for p in base_dir.iterdir() if p.is_dir()])
    if not subfolders:
        print(f"No subfolders found in: {base_dir}")
        return

    for folder in subfolders:
        excel_files = sorted(folder.glob("*.xlsx"))
        if not excel_files:
            continue

        print("\n" + "=" * 70)
        print(f"Batch: {folder.name} ({len(excel_files)} file(s))")
        print("=" * 70)
        _plot_folder_as_subplots(folder, excel_files, fs=fs)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Show detector plots grouped by subfolder batches."
    )
    parser.add_argument(
        "--base-dir",
        default="KT3401_AFdata_2025",
        help="Root folder containing artefact subfolders with .xlsx files.",
    )
    parser.add_argument(
        "--fs",
        type=int,
        default=FS,
        help=f"Sampling rate in Hz (default from config.py: {FS}).",
    )
    args = parser.parse_args()

    if args.fs <= 0:
        parser.error("--fs must be a positive integer")

    base_dir = Path(args.base_dir).expanduser().resolve()
    if not base_dir.exists() or not base_dir.is_dir():
        raise FileNotFoundError(f"Base directory not found: {base_dir}")

    run_folder_batches(base_dir, fs=args.fs)


if __name__ == "__main__":
    main()
