"""Validate potential, E=-grad(V), and input failure handling."""
import csv
import math
from pathlib import Path
import subprocess
import sys
import tempfile

executable, config = sys.argv[1:]
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    output = tmp / "field.csv"
    subprocess.run([executable, "uniform", config, str(output)], check=True)
    with output.open() as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 99
    for row in rows:
        z = float(row["z_cm"])
        assert int(row["status"]) == 0
        assert math.isclose(float(row["potential_V"]), -1000 + 100 * z, abs_tol=1e-10)
        assert math.isclose(float(row["Ez_V_per_cm"]), -100, abs_tol=1e-10)
        assert float(row["Ex_V_per_cm"]) == float(row["Ey_V_per_cm"]) == 0
        assert float(row["Etrans_over_abs_Ez"]) == 0
        assert float(row["delta_Ez_over_Ez0"]) == 0
    for a, b in zip(rows[:10], rows[1:11]):
        gradient = (float(b["potential_V"]) - float(a["potential_V"])) / (
            float(b["z_cm"]) - float(a["z_cm"]))
        assert math.isclose(-gradient, float(a["Ez_V_per_cm"]), abs_tol=1e-10)
    assert subprocess.run([executable, "uniform", config, str(output)]).returncode != 0
    bad = tmp / "bad.cfg"
    bad.write_text(Path(config).read_text().replace("nz = 11", "nz = 1"))
    assert subprocess.run([executable, "uniform", str(bad), str(tmp / "bad.csv")]).returncode != 0
    assert subprocess.run([executable, "elmer", config, str(tmp / "map.csv"),
                           str(tmp / "missing"), "mm", "0"]).returncode != 0
print("Uniform potential, field sign, sampling, and failure checks passed.")
