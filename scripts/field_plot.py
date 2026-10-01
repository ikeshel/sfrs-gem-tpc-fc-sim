"""Shared CSV plotting: retain missing/invalid samples as holes, never zero fields."""
import argparse
from pathlib import Path
import numpy as np
from field_csv import load_field_csv


def main(default_view="both", line=False):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", default="results/uniform.csv")
    parser.add_argument("--output", type=Path, help="Output file; both planes append _zx and _zy to its stem")
    parser.add_argument("--no-show", action="store_true", help="Save without a GUI")
    parser.add_argument("--x", type=float, default=0, help="x coordinate for zy slice / line [mm]")
    parser.add_argument("--y", type=float, default=0, help="y coordinate for zx slice / line [mm]")
    parser.add_argument("--view", choices=["zx", "zy", "both"], default=default_view)
    parser.add_argument("--style", choices=["arrows", "mesh", "both"], default="both")
    args = parser.parse_args()
    import matplotlib
    if args.no_show:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize

    figures = []
    try:
        data = load_field_csv(args.input)
        keys = ["x_mm", "y_mm", "z_mm", "potential_V", "Ex_V_per_cm", "Ey_V_per_cm", "Ez_V_per_cm", "status"]
        if not data.size or not set(keys).issubset(data.dtype.names or ()):
            raise ValueError("Empty CSV or missing required tpc-field columns")
        if not all(np.isfinite(data[k]).all() for k in keys[:3]):
            raise ValueError("Nonfinite sample coordinates")
        valid = data["status"] == 0
        for key in keys[3:7]:
            valid &= np.isfinite(data[key])
        if not valid.any():
            raise ValueError("No valid field samples")
        near = lambda values, target: np.isclose(values, target, rtol=0, atol=1e-9)
        if line:
            samples = data[near(data["x_mm"], args.x) & near(data["y_mm"], args.y)]
            if not samples.size:
                raise ValueError("No samples on requested line; choose sampled --x and --y coordinates")
            samples = np.sort(samples, order="z_mm")
            if len(np.unique(samples["z_mm"])) != len(samples):
                raise ValueError("Duplicate line coordinates")
            fig, axes = plt.subplots(2, 1, sharex=True, figsize=(7, 6), constrained_layout=True)
            for ax, key, label in zip(axes, ["potential_V", "Ez_V_per_cm"], ["Potential [V]", "Ez [V/cm]"]):
                values = samples[key].copy()
                values[(samples["status"] != 0) | ~np.isfinite(values)] = np.nan
                if not np.isfinite(values).any():
                    raise ValueError("No valid samples on requested line")
                ax.plot(samples["z_mm"], values, "o-")
                ax.set_ylabel(label)
                ax.grid(alpha=.3)
            axes[-1].set_xlabel("z [mm]")
            fig.suptitle(f"{Path(args.input).name}: x={args.x:g}, y={args.y:g} mm")
            figures.append((fig, None, "field_line.png"))
        else:
            planes = []
            for view, fixed, target, horizontal, component in [
                ("zx", "y_mm", args.y, "x_mm", "Ex_V_per_cm"),
                ("zy", "x_mm", args.x, "y_mm", "Ey_V_per_cm")]:
                if args.view not in (view, "both"):
                    continue
                mask = near(data[fixed], target)
                if not mask.any() or not valid[mask].any():
                    raise ValueError(f"No valid samples on {view} slice at {fixed}={target}; choose a sampled coordinate")
                sample = data[mask]
                h, z = np.unique(sample[horizontal]), np.unique(sample["z_mm"])
                if len(h) < 2 or len(z) < 2:
                    raise ValueError("Each plane requires at least two coordinates along each axis")
                ih, iz = np.searchsorted(h, sample[horizontal]), np.searchsorted(z, sample["z_mm"])
                if len(set(zip(ih, iz))) != len(sample):
                    raise ValueError("Duplicate plane coordinates")
                grids = []
                for values in [np.hypot(np.hypot(sample["Ex_V_per_cm"], sample["Ey_V_per_cm"]), sample["Ez_V_per_cm"]), sample[component], sample["Ez_V_per_cm"]]:
                    grid = np.full((len(z), len(h)), np.nan)
                    grid[iz, ih] = np.where(valid[mask], values, np.nan)
                    grids.append(np.ma.masked_invalid(grid))
                planes.append((h, z, grids, horizontal[0], f"{view}: {fixed[0]} = {target:g} mm"))
            magnitudes = np.concatenate([p[2][0].compressed() for p in planes])
            lo, hi = magnitudes.min(), magnitudes.max()
            if np.isclose(lo, hi):
                pad = max(abs(lo)*.01, 1e-6)
                lo, hi = max(0, lo-pad), hi+pad
            norm = Normalize(lo, hi)
            for h, z, (mag, eh, ez), label, title in planes:
                fig, ax = plt.subplots(figsize=(7, 8), constrained_layout=True)
                if args.style in ("mesh", "both"):
                    colors = ax.pcolormesh(h, z, mag, shading="nearest", cmap="viridis", norm=norm,
                                          edgecolors="0.6", linewidth=.4)
                else:
                    hh, zz = np.meshgrid(h, z)
                    colors = ax.scatter(hh, zz, c=mag, cmap="viridis", norm=norm, s=35)
                if args.style in ("arrows", "both"):
                    projected = np.ma.sqrt(eh**2 + ez**2)
                    denominator = np.ma.masked_where(projected == 0, projected)
                    length = .4*min(np.diff(h).min(), np.diff(z).min())
                    ax.quiver(h, z, eh/denominator, ez/denominator, angles="xy", scale_units="xy",
                              scale=1/length, pivot="mid", color="black")
                ax.set(xlabel=f"{label} [mm]", ylabel="z [mm]", title=title, aspect="equal")
                fig.colorbar(colors, ax=ax, label="|E| [V/cm]", shrink=.8)
                fig.suptitle(f"{Path(args.input).name}: sampling grid (not FEM mesh)\nArrows: projected direction; blank cells: invalid/missing")
                view = "zx" if label == "x" else "zy"
                figures.append((fig, view, f"field_{view}_{args.style}.png"))
        outputs = []
        for fig, view, default_output in figures:
            output = args.output or Path(args.input).parent / default_output
            if args.output and len(figures) > 1:
                output = output.with_name(f"{output.stem}_{view}{output.suffix or '.png'}")
            if output.resolve() == Path(args.input).resolve():
                raise ValueError("Output must differ from input CSV")
            outputs.append((fig, output))
        for fig, output in outputs:
            output.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(output, dpi=180)
            print(f"Saved {output}; CSV valid samples: {valid.sum()}/{len(data)}")
        if not args.no_show:
            plt.show()
        for fig, _, _ in figures:
            plt.close(fig)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
