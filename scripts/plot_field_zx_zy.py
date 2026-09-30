
import csv
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

with open("results/uniform.csv") as f:
    rows = [r for r in csv.DictReader(f) if int(r["status"]) == 0]

data = {
    k: np.array([float(r[k]) for r in rows])
    for k in ("x_cm", "y_cm", "z_cm",
              "Ex_V_per_cm", "Ey_V_per_cm", "Ez_V_per_cm")
}
x, y, z = (data[k] for k in ("x_cm", "y_cm", "z_cm"))
ex, ey, ez = (data[k] for k in
              ("Ex_V_per_cm", "Ey_V_per_cm", "Ez_V_per_cm"))
magnitude = np.sqrt(ex**2 + ey**2 + ez**2)

lo, hi = magnitude.min(), magnitude.max()
if np.isclose(lo, hi):
    padding = max(abs(lo) * 0.01, 1e-6)
    lo, hi = lo - padding, hi + padding
norm = Normalize(lo, hi)

fig, axes = plt.subplots(
    1, 2, figsize=(10, 8), sharey=True, layout="constrained"
)

planes = [
    (x, ex, np.isclose(y, 0), "x", "x–z plane (y = 0)"),
    (y, ey, np.isclose(x, 0), "y", "y–z plane (x = 0)"),
]

for ax, (horizontal, eh, mask, label, title) in zip(axes, planes):
    if not mask.any():
        raise SystemExit(f"No samples for {title}")

    h, zz = horizontal[mask], z[mask]
    eh, ezz = eh[mask], ez[mask]
    projected = np.hypot(eh, ezz)
    uh = np.divide(eh, projected, out=np.zeros_like(eh),
                   where=projected > 0)
    uz = np.divide(ezz, projected, out=np.zeros_like(ezz),
                   where=projected > 0)

    points = ax.scatter(h, zz, c=magnitude[mask],
                        cmap="viridis", norm=norm, s=90)
    ax.quiver(h, zz, uh, uz, angles="xy", scale_units="xy",
              scale=2, pivot="mid", color="black")
    ax.set(xlabel=f"{label} [cm]", title=title)
    ax.set_aspect("equal")
    ax.margins(0.2)
    ax.grid(alpha=0.25)

axes[0].set_ylabel("z [cm]")
fig.colorbar(points, ax=axes, label="|E| [V/cm]", shrink=0.8)
fig.suptitle("Uniform-field validation — arrows show projected direction")
fig.savefig("results/field_zx_zy.png", dpi=180)
plt.show()

