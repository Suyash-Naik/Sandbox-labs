"""Script to generate synthetic sample intensity data for testing binned-plot."""

from pathlib import Path
import numpy as np
import pandas as pd


def generate_sample_data():
    sample_dir = Path(__file__).parent / "sample_data"
    sample_dir.mkdir(exist_ok=True)

    date_str = "20260723"
    positions = {
        "Pos001": {"base": 100, "slope": 15, "noise": 5},   # Control
        "Pos002": {"base": 105, "slope": 14, "noise": 6},   # Control
        "Pos003": {"base": 100, "slope": 35, "noise": 8},   # K4K8MO
        "Pos004": {"base": 95,  "slope": 32, "noise": 7},   # K4K8MO
    }

    # 180 frames (e.g. 120s interval = 6 hours of imaging, 4.0 to 10.0 hpf)
    frames = np.arange(1, 181)

    for pos, params in positions.items():
        time_hours = (frames - 1) * (120 / 3600.0)
        # Synthetic intensity curve with some noise
        mean_intensity = params["base"] + params["slope"] * time_hours + np.random.normal(0, params["noise"], len(frames))
        std_intensity = np.random.uniform(5, 12, len(frames))

        df = pd.DataFrame({
            " ": frames,  # Frame index column
            "Mean": np.round(mean_intensity, 2),
            "StdDev": np.round(std_intensity, 2),
            "Min": np.round(mean_intensity - 15, 2),
            "Max": np.round(mean_intensity + 15, 2),
        })

        filename = f"{date_str}_{pos}_intensity.csv"
        file_path = sample_dir / filename
        df.to_csv(file_path, index=False)
        print(f"Generated sample file: {file_path}")

    print(f"\nAll sample files created successfully in '{sample_dir}'.")


if __name__ == "__main__":
    generate_sample_data()
