"""Display sampled 3D electric field; this does not solve or display a FEM mesh."""
import argparse
from pathlib import Path
import numpy as np
from field_csv import load_field_csv


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', nargs='?', default='results/uniform.csv')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--no-show', action='store_true')
    parser.add_argument('--max-arrows', type=int, default=2000,
                        help='Uniformly subsample valid rows above this count (default: 2000)')
    parser.add_argument('--elev', type=float, default=25)
    parser.add_argument('--azim', type=float, default=-60)
    args = parser.parse_args()
    if args.max_arrows < 1:
        parser.error('--max-arrows must be positive')
    import matplotlib
    if args.no_show:
        matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize
    try:
        data = load_field_csv(args.input)
        keys = ['x_mm', 'y_mm', 'z_mm', 'Ex_V_per_cm', 'Ey_V_per_cm', 'Ez_V_per_cm', 'status']
        if not data.size or not set(keys).issubset(data.dtype.names or ()):
            raise ValueError('Empty CSV or missing required tpc-field columns')
        valid = data['status'] == 0
        for key in keys[:-1]:
            valid &= np.isfinite(data[key])
        values = data[valid]
        if not values.size:
            raise ValueError('No valid field samples')
        position = np.column_stack([values[k] for k in keys[:3]])
        vectors = np.column_stack([values[k] for k in keys[3:6]])
        magnitude = np.linalg.norm(vectors, axis=1)
        lo, hi = magnitude.min(), magnitude.max()
        if np.isclose(lo, hi):
            pad = max(abs(lo)*.01, 1e-6)
            lo, hi = max(0, lo-pad), hi+pad
        norm = Normalize(lo, hi)
        indices = np.linspace(0, len(values)-1, min(len(values), args.max_arrows), dtype=int)
        p, v, mag = position[indices], vectors[indices], magnitude[indices]
        spans = np.ptp(position, axis=0)
        positive_spans = spans[spans > 0]
        base = positive_spans.min() if positive_spans.size else 1.
        steps = [np.diff(np.unique(position[:, i])) for i in range(3)]
        spacing = [d.min() for d in steps if d.size]
        length = .4 * min(spacing) if spacing else .1 * base
        fig = plt.figure(figsize=(10, 8), constrained_layout=True)
        ax = fig.add_subplot(111, projection='3d')
        points = ax.scatter(*p.T, c=mag, cmap='viridis', norm=norm, s=15, depthshade=False)
        nonzero = mag > 0
        # Equal arrow lengths encode direction; colors encode full magnitude.
        ax.quiver(*p[nonzero].T, *v[nonzero].T, length=length,
                  normalize=True, pivot='middle', color='black', linewidth=.6)
        limits = np.column_stack((position.min(axis=0), position.max(axis=0)))
        widths = np.maximum(spans, .1*base) + 2*length
        centers = limits.mean(axis=1)
        for setter, center, width in zip([ax.set_xlim, ax.set_ylim, ax.set_zlim], centers, widths):
            setter(center-width/2, center+width/2)
        ax.set_box_aspect(widths)
        ax.set(xlabel='x [mm]', ylabel='y [mm]', zlabel='z [mm]')
        ax.view_init(elev=args.elev, azim=args.azim)
        ax.set_title(f'{Path(args.input).name}: sampled 3D electric field\n'
                     f'{len(indices)} of {len(values)} valid samples displayed; arrows show direction')
        fig.colorbar(points, ax=ax, label='|E| [V/cm]', shrink=.7, pad=.1)
        output = args.output or Path(args.input).with_name(Path(args.input).stem + '_3d.png')
        if output.resolve() == Path(args.input).resolve():
            raise ValueError('Output must differ from input CSV')
        output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output, dpi=180)
        print(f'Saved {output}; valid samples {len(values)}/{len(data)}; displayed {len(indices)}')
        if not args.no_show:
            plt.show()
        plt.close(fig)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f'Error: {error}\n')


if __name__ == '__main__':
    main()
