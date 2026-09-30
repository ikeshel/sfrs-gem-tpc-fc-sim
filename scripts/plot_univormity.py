import csv
import matplotlib.pyplot as plt

with open("results/uniform.csv") as f:
    rows = list(csv.DictReader(f))

# Select the central line x = y = 0.
rows = sorted(
    [r for r in rows
     if abs(float(r["x_cm"])) < 1e-9
     and abs(float(r["y_cm"])) < 1e-9],
    key=lambda r: float(r["z_cm"])
)

z = [float(r["z_cm"]) for r in rows]
v = [float(r["potential_V"]) for r in rows]
ez = [float(r["Ez_V_per_cm"]) for r in rows]

fig, axes = plt.subplots(2, 1, sharex=True, figsize=(7, 6))
axes[0].plot(z, v, "o-")
axes[0].set_ylabel("Potential [V]")
axes[1].plot(z, ez, "o-")
axes[1].set_ylabel("Ez [V/cm]")
axes[1].set_xlabel("z [cm]")
for ax in axes:
    ax.grid(True)
fig.suptitle("Uniform-field validation — not the cage model")
fig.tight_layout()
fig.savefig("results/uniform.png", dpi=180)
plt.show()

