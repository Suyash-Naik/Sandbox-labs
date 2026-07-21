"""CLI interface for binned-plot tool."""

import argparse
import json
from pathlib import Path
import sys
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from binned_plot.binned_plotter import BinnedIntensityPlotter


def parse_treatment_map(raw_arg: Optional[str]) -> Dict[str, List[int]]:
    """Parse treatment map from JSON string or file path."""
    if not raw_arg:
        return {}
    path = Path(raw_arg)
    if path.is_file():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    try:
        return json.loads(raw_arg)
    except json.JSONDecodeError as err:
        raise ValueError(
            f"Invalid --treatment-map value '{raw_arg}'. Must be valid JSON string or path to JSON file."
        ) from err


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for binned-plot CLI."""
    parser = argparse.ArgumentParser(
        prog="binned-plot",
        description="Process and plot bio-image intensity time-series data across experimental conditions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process raw CSV files from a directory and generate plots
  binned-plot -i ./data/csv_folder -o ./output -pd -mp --treatment-map '{"Control":[1,2],"Treatment":[3,4]}'

  # Process explicit file list
  binned-plot -i file1.csv file2.csv -o ./output -pd -mp --treatment-map map.json

  # Plot from an existing binned_intensity_data.csv file
  binned-plot -i ./output/binned_intensity_data.csv -o ./output -mp
""",
    )

    parser.add_argument(
        "-i",
        "--input",
        nargs="+",
        required=True,
        metavar="PATH",
        help="Input CSV file(s) or directory containing intensity CSV files.",
    )
    parser.add_argument(
        "-o",
        "--output-folder",
        required=True,
        metavar="DIR",
        help="Output directory path to store processed CSVs and generated plots.",
    )
    parser.add_argument(
        "-pd",
        "--process-data",
        action="store_true",
        help="Flag to process raw intensity CSV files and produce binned_intensity_data.csv.",
    )
    parser.add_argument(
        "-mp",
        "--make-plot",
        action="store_true",
        help="Flag to render and save treatment average/SEM plots.",
    )
    parser.add_argument(
        "-tm",
        "--treatment-map",
        metavar="JSON_OR_PATH",
        help="JSON string or path to JSON file mapping treatment names to position IDs, e.g. '{\"Control\":[1,2]}'.",
    )
    parser.add_argument(
        "--timeframe",
        type=float,
        default=120.0,
        help="Frame interval time in seconds (default: 120.0).",
    )
    parser.add_argument(
        "--start-hpf",
        type=float,
        default=4.0,
        help="Initial start time in hours post fertilization (default: 4.0).",
    )
    parser.add_argument(
        "--bin-step",
        type=float,
        default=0.5,
        help="Time bin duration step in hours (default: 0.5).",
    )
    parser.add_argument(
        "--bin-start",
        type=float,
        default=4.0,
        help="Binning start time in hpf (default: 4.0).",
    )
    parser.add_argument(
        "--bin-end",
        type=float,
        default=10.0,
        help="Binning end time in hpf (default: 10.0).",
    )
    parser.add_argument(
        "--plot-param",
        default="Mean",
        help="Column name in raw CSV files to aggregate (default: 'Mean').",
    )
    parser.add_argument(
        "--title",
        default=None,
        help="Custom title for the generated plot.",
    )
    return parser


def main(args: Optional[List[str]] = None) -> int:
    """Main CLI execution wrapper."""
    parser = build_parser()
    parsed_args = parser.parse_args(args)

    if not parsed_args.process_data and not parsed_args.make_plot:
        print("Error: Must specify at least one action flag: --process-data (-pd) or --make-plot (-mp).", file=sys.stderr)
        parser.print_help()
        return 1

    output_dir = Path(parsed_args.output_folder)
    output_dir.mkdir(parents=True, exist_ok=True)

    input_paths: List[Path] = []
    for item in parsed_args.input:
        p = Path(item)
        if p.is_dir():
            input_paths.extend(sorted(p.glob("*.csv")))
        elif p.is_file():
            input_paths.append(p)
        else:
            print(f"Warning: Input path '{item}' not found.", file=sys.stderr)

    bin_edges = np.arange(parsed_args.bin_start, parsed_args.bin_end + 1e-6, parsed_args.bin_step)
    treatment_map = parse_treatment_map(parsed_args.treatment_map)

    plotter = BinnedIntensityPlotter(
        intensity_files=input_paths,
        bin_edges=bin_edges,
        save_folder=output_dir,
        treatment_map=treatment_map,
        timeframe=parsed_args.timeframe,
        start_hpf=parsed_args.start_hpf,
    )

    if parsed_args.process_data:
        if not input_paths:
            print("Error: No input CSV files found for processing.", file=sys.stderr)
            return 1
        print(f"Processing {len(input_paths)} CSV file(s)...")
        plotter.process_data(plotparam=parsed_args.plot_param)
        print(f"Binned intensity data saved to '{output_dir / 'binned_intensity_data.csv'}'.")

    if parsed_args.make_plot:
        binned_file = output_dir / "binned_intensity_data.csv"
        if not parsed_args.process_data:
            if binned_file.is_file():
                df = pd.read_csv(binned_file)
                plotter.import_data(df)
            elif len(input_paths) == 1 and input_paths[0].name.endswith(".csv"):
                df = pd.read_csv(input_paths[0])
                plotter.import_data(df)
            else:
                print(f"Error: Could not locate binned intensity file at '{binned_file}'. Run with -pd first.", file=sys.stderr)
                return 1

        plotter.plot_data(title=parsed_args.title)
        print(f"Plot saved to '{output_dir / 'binned_intensity_plot.png'}'.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
