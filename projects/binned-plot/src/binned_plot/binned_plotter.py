"""BinnedIntensityPlotter module for processing and plotting binned intensity data.

This module reads intensity data from CSV files, bins the data based on specified bin edges,
and plots the binned data with treatment-specific statistics (mean and SEM).
"""

from pathlib import Path
import re
from typing import Dict, List, Union, Optional, Sequence
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


class BinnedIntensityPlotter:
    """Class to load, bin, and visualize bio-image intensity time-series data across experimental conditions."""

    def __init__(
        self,
        intensity_files: Sequence[Union[str, Path]],
        bin_edges: Sequence[float],
        save_folder: Union[str, Path],
        treatment_map: Dict[str, List[int]],
        timeframe: float,
        start_hpf: float = 4.0,
    ) -> None:
        """Initialize the BinnedIntensityPlotter.

        Args:
            intensity_files: List of file paths to raw intensity CSV files.
            bin_edges: Bin boundaries for time binning (in hpf).
            save_folder: Path to directory where output data/plots will be saved.
            treatment_map: Dictionary mapping treatment names to position numbers,
                e.g. {"Control": [3, 5], "K4K8MO": [6, 7, 9]}.
            timeframe: Frame interval in seconds.
            start_hpf: Initial start time in hours post fertilization (default 4.0).
        """
        self.intensity_files = [Path(f) for f in intensity_files]
        self.bin_edges = np.asanyarray(bin_edges)
        self.save_folder = Path(save_folder)
        self.treatment_map = treatment_map
        self.timeframe = float(timeframe)
        self.start_hpf = float(start_hpf)

        self.intensity_data = pd.DataFrame()
        self.binned_intensity_data = pd.DataFrame()
        self.treatment_indices: Dict[str, List[str]] = {k: [] for k in treatment_map}

    def get_treatment(self, pos_number: int) -> Optional[str]:
        """Return the treatment name for a given position number."""
        for treatment, pos_list in self.treatment_map.items():
            if pos_number in pos_list:
                return treatment
        return None

    def process_data(self, plotparam: str = "Mean") -> pd.DataFrame:
        """Read intensity files, assign treatments, bin data, and save binned results.

        Args:
            plotparam: Column name in input CSVs to aggregate (default: 'Mean').

        Returns:
            DataFrame containing binned intensity data across all treatments and positions.
        """
        if len(self.bin_edges) < 2:
            raise ValueError("bin_edges must contain at least two boundary values.")

        bin_centers = 0.5 * (self.bin_edges[1:] + self.bin_edges[:-1])
        if "Time (hpf)" not in self.binned_intensity_data.columns:
            self.binned_intensity_data["Time (hpf)"] = bin_centers

        dfs_to_concat = []

        for file_path in self.intensity_files:
            file_name = file_path.name
            date = file_name.split("_")[0]

            pos_match = re.search(r"Pos(\d+)", file_name, re.IGNORECASE)
            if not pos_match:
                print(f"Warning: Could not extract position number from '{file_name}'. Skipping.")
                continue

            pos_str = pos_match.group(1)
            pos_number = int(pos_str)
            treatment = self.get_treatment(pos_number)
            if treatment is None:
                print(f"Treatment not found for position {pos_number} in file '{file_path}'. Skipping.")
                continue

            data = pd.read_csv(file_path)
            data["Label"] = f"{date}_Pos{pos_str}"
            data["Treatment"] = treatment

            frame_col = data.columns[0]
            if frame_col.strip() == "" or "unnamed" in frame_col.lower():
                frame_idx = data[frame_col]
            elif "frame" in [c.lower() for c in data.columns]:
                frame_idx = data[[c for c in data.columns if c.lower() == "frame"][0]]
            else:
                frame_idx = data.iloc[:, 0]

            data["Time"] = (frame_idx - 1) * (self.timeframe / 3600.0) + self.start_hpf
            dfs_to_concat.append(data)

            binned_groups = data.groupby(
                pd.cut(data["Time"], bins=self.bin_edges, include_lowest=True),
                observed=False,
            )[plotparam].mean()

            bin_averages = binned_groups.to_numpy()
            col_name = f"{treatment}_{plotparam}_{date}_Pos{pos_str}"

            if col_name not in self.binned_intensity_data.columns:
                self.binned_intensity_data[col_name] = bin_averages
                self.treatment_indices[treatment].append(col_name)
            else:
                print(f"Column '{col_name}' already exists in binned intensity data. Skipping.")

        if dfs_to_concat:
            self.intensity_data = pd.concat(dfs_to_concat, ignore_index=True)

        cols = ["Time (hpf)"] + [c for c in self.binned_intensity_data.columns if c != "Time (hpf)"]
        self.binned_intensity_data = self.binned_intensity_data[cols]

        self.save_folder.mkdir(parents=True, exist_ok=True)
        self.binned_intensity_data.to_csv(self.save_folder / "binned_intensity_data.csv", index=False)
        return self.binned_intensity_data

    def import_data(self, binned_intdf: pd.DataFrame) -> None:
        """Import pre-processed binned intensity data from a DataFrame.

        Args:
            binned_intdf: DataFrame containing binned intensity data with 'Time (hpf)' column.
        """
        if "Time (hpf)" not in binned_intdf.columns:
            raise ValueError("DataFrame must contain 'Time (hpf)' column.")

        self.binned_intensity_data = binned_intdf.copy()

        for col in self.binned_intensity_data.columns:
            if col == "Time (hpf)":
                continue
            treatment_name = col.split("_")[0]
            if treatment_name not in self.treatment_indices:
                self.treatment_indices[treatment_name] = []
            if col not in self.treatment_indices[treatment_name]:
                self.treatment_indices[treatment_name].append(col)

    def plot_data(
        self,
        title: Optional[str] = None,
        colors: Optional[Dict[str, str]] = None,
        save_plot_name: Optional[str] = "binned_intensity_plot.png",
    ) -> plt.Figure:
        """Plot binned intensity mean and standard error of the mean (SEM) for each treatment.

        Args:
            title: Optional plot title.
            colors: Dict mapping treatment names to hex/named colors.
            save_plot_name: Output filename to save plot within save_folder.

        Returns:
            Matplotlib Figure object.
        """
        fig, ax = plt.subplots(figsize=(7, 5.3), dpi=100)

        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)

        time_vals = self.binned_intensity_data["Time (hpf)"]

        default_colors = ["#83bb03", "#ff7f00", "#1f77b4", "#e377c2", "#9467bd"]
        color_map = colors or {}

        for i, (treatment, cols) in enumerate(self.treatment_indices.items()):
            if not cols:
                continue

            treatment_cols = [c for c in cols if c in self.binned_intensity_data.columns]
            if not treatment_cols:
                continue

            treatment_data = self.binned_intensity_data[treatment_cols]
            mean_vals = treatment_data.mean(axis=1)
            sem_vals = treatment_data.sem(axis=1)

            color = color_map.get(treatment, default_colors[i % len(default_colors)])

            ax.plot(time_vals, mean_vals, label=treatment, color=color, linewidth=2)
            ax.fill_between(
                time_vals,
                mean_vals - sem_vals,
                mean_vals + sem_vals,
                color=color,
                alpha=0.3,
            )

        ax.set_xlabel("Time (hpf)")
        ax.set_ylabel("Intensity")
        if title:
            ax.set_title(title)
        ax.legend(frameon=False)

        self.save_folder.mkdir(parents=True, exist_ok=True)
        if save_plot_name:
            fig.savefig(self.save_folder / save_plot_name, dpi=300, bbox_inches="tight")

        return fig
