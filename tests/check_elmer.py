"""Synthetic quadratic tetrahedron: verify import, mm->cm and field gradient.

This hand-generated analytic fixture tests the importer, not the Elmer solver.
"""
import csv
import math
from pathlib import Path
import subprocess
import sys
import tempfile

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    vertices = [(0, 0, 0), (10, 0, 0), (0, 10, 0), (0, 0, 10)]
    nodes = vertices + [tuple((vertices[a][i] + vertices[b][i]) / 2 for i in range(3))
                        for a, b in [(0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3)]]
    (root / "mesh.header").write_text("10 1 0\n1\n510 1\n")
    (root / "mesh.elements").write_text("1 1 510 1 2 3 4 5 6 7 8 9 10\n")
    (root / "mesh.nodes").write_text("".join(
        f"{i} -1 {x} {y} {z}\n" for i, (x, y, z) in enumerate(nodes, 1)))
    (root / "dielectrics.dat").write_text("1\n1 1.0\n")
    (root / "out.result").write_text("Perm:\n" + "".join(f"{i}\n" for i in range(1, 11)) +
                                     "".join(f"{-100 + 10*z}\n" for x, y, z in nodes))
    cfg = root / "sample.cfg"
    cfg.write_text("x_min_mm=1\nx_max_mm=2\ny_min_mm=1\ny_max_mm=2\n"
                   "z_min_mm=1\nz_max_mm=2\nnx=2\nny=2\nnz=2\n"
                   "v_cathode=-90\nv_anode=-80\n")
    output = root / "field.csv"
    subprocess.run([sys.argv[1], "elmer", str(cfg), str(output), str(root), "mm", "0"], check=True)
    with output.open() as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 8
    for row in rows:
        assert int(row["status"]) == 0
        assert math.isclose(float(row["potential_V"]), -100 + 10 * float(row["z_mm"]), abs_tol=1e-8)
        assert math.isclose(float(row["Ez_V_per_cm"]), -100, abs_tol=1e-8)
        assert abs(float(row["Ex_V_per_cm"])) < 1e-8
        assert abs(float(row["Ey_V_per_cm"])) < 1e-8
    # Sampling entirely outside the mesh must fail rather than report zero field.
    cfg.write_text(cfg.read_text().replace("x_min_mm=1", "x_min_mm=20").replace("x_max_mm=2", "x_max_mm=30"))
    assert subprocess.run([sys.argv[1], "elmer", str(cfg), str(root / "outside.csv"),
                           str(root), "mm", "0"]).returncode == 2
print("Elmer analytic import, unit conversion, field gradient and coverage checks passed.")
