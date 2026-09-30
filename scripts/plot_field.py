import csv
import numpy as np
import matplotlib.pyplot as plt

with open("results/uniform.csv") as f:
    rows = [
        r for r in csv.DictReader(f)
        if abs(float(r["y_cm"])) < 1e-9
        and int(r["status"]) == 0
    ]

x = np.array([float(r["x_cm"]) for r in rows])
z = np.array([float(r["z_cm"]) for r in rows])
ex = np.array([float(r["Ex_V_per_cm"]) for r in rows])
ey = np.array([float(r["Ey_V_per_cm"]) for r in rows])
ez = np.array([float(r["Ez_V_per_cm"]) for r in rows])
magnitude = np.sqrt(ex**2 + ey**2 + ez**2)

fig, ax = plt.subplots(figsize=(6, 8))
points = ax.scatter(x, z, c=magnitude, cmap="viridis", s=90)
fig.colorbar(points, ax=ax, label="|E| [V/cm]")

# Normalize projected arrows to show direction.
projected = np.hypot(ex, ez)
ux = np.divide(ex, projected, out=np.zeros_like(ex), where=projected > 0)
uz = np.divide(ez, projected, out=np.zeros_like(ez), where=projected > 0)
ax.quiver(x, z, ux, uz, angles="xy",
          scale_units="xy", scale=2, pivot="mid", color="black")

ax.set(xlabel="x [cm]", ylabel="z [cm]",
       title="Electric field at y = 0\nUniform validation example")
ax.set_aspect("equal")
ax.margins(0.2)
fig.tight_layout()
fig.savefig("results/field_arrows.png", dpi=180)
plt.show()

