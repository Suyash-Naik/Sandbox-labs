# Binned Plotter (`binned-plot`)

`binned-plot` is a Python utility module for loading, time-binning, aggregating, and visualizing fluorescence or bio-image intensity data from multi-position experimental CSV files.

## Features

 Designed for taking in a dataset from a experiment with a time collected dataset across different samples (`Pos`)

- **Robust Metadata Extraction**: Parses date and position numbers dynamically (`Pos01`, `Pos002`, etc.) using regex.
- **Time Binning**: Converts frame numbers to hours post fertilization (hpf) and bins intensity metrics across specified time intervals.
- **Treatment Aggregation**: Automatically groups positions by experimental condition (e.g. `Control`, `K4K8MO`) and computes Mean & Standard Error of the Mean (SEM).
- **Dynamic Treatment Support**: `import_data()` dynamically detects treatment conditions from imported datasets without hardcoded treatment names.
- **Modern Packaging**: Compatible with `pip` / `uv` for seamless installation.

---

## Installation

Install in editable mode locally:

```bash
pip install -e .
```

Or using `uv`:

```bash
uv pip install -e .
```

---

## Usage Example

```python
import numpy as np
from pathlib import Path
from BinnedPlotter import BinnedIntensityPlotter

# 1. Define input CSV files and treatment groupings
csv_files = [
    "data/20250526_Pos003_intensity.csv",
    "data/20250526_Pos005_intensity.csv",
    "data/20250526_Pos006_intensity.csv",
]

treatment_map = {
    "Control": [3, 5],
    "K4K8MO": [6]
}

# 2. Define bin edges in hpf (e.g. from 4.0 to 10.0 hpf in 0.5h steps)
bin_edges = np.arange(4.0, 10.5, 0.5)

# 3. Instantiate plotter
plotter = BinnedIntensityPlotter(
    intensity_files=csv_files,
    bin_edges=bin_edges,
    save_folder="./output",
    treatment_map=treatment_map,
    timeframe=120.0,  # 120 seconds per frame
    start_hpf=4.0     # imaging began at 4.0 hpf
)

# 4. Process raw CSV data and export binned table
binned_df = plotter.process_data(plotparam="Mean")

# 5. Generate and save plot
fig = plotter.plot_data(title="Fluorescence Intensity vs Time (hpf)")
```

---

## Re-importing Pre-binned Data

If you already have a `binned_intensity_data.csv` exported:

```python
import pandas as pd
from BinnedPlotter import BinnedIntensityPlotter

binned_df = pd.read_csv("./output/binned_intensity_data.csv")

plotter = BinnedIntensityPlotter([], [], "./output", {}, timeframe=120.0)
plotter.import_data(binned_df)
fig = plotter.plot_data()
```
