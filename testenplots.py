import argparse
from pathlib import Path

from config import FS
from detect_artefacts import (
    load_artefact_excel,
    plot_signals_and_artefacts,
    run_all_detectors,
)


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

        for excel_file in excel_files:
            print(f"Processing: {excel_file.name}")
            t, ABP, CVP = load_artefact_excel(excel_file, fs=fs)
            results = run_all_detectors(t, ABP, CVP, fs=fs)
            title = f"{folder.name} - {excel_file.name}"
            # Blocks until plot window is closed, then continues to next file.
            plot_signals_and_artefacts(t, ABP, CVP, results, title)


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
