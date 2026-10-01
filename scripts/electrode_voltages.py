"""Calculate seven electrode potentials and optionally write Elmer boundary blocks.

No mesh IDs are inferred from STL triangle numbers. Boundary IDs must come from
an inspected Elmer mesh and be supplied explicitly.
"""
import argparse
import csv
import io
import json
import math
from pathlib import Path

NAMES = ['cathode', 'electrode_1', 'electrode_2', 'electrode_3',
         'electrode_4', 'electrode_5', 'anode']


def potentials(config):
    vc, va = config['cathode_V'], config['anode_V']
    positions = config['positions']
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
           for v in [vc, va, *positions]):
        raise ValueError('Voltages and positions must be finite numbers')
    if vc == va:
        raise ValueError('Cathode and anode potentials must differ')
    if len(positions) != 7:
        raise ValueError('Exactly seven positions required, ordered cathode to anode')
    differences = [b-a for a, b in zip(positions, positions[1:])]
    if not (all(d > 0 for d in differences) or all(d < 0 for d in differences)):
        raise ValueError('Positions must be strictly monotonic along the drift axis')
    unit = config['position_unit']
    if unit not in ('mm', 'cm', 'm', 'relative'):
        raise ValueError('position_unit must be mm, cm, m, or relative')
    return [(name, pos, vc+(va-vc)*(pos-positions[0])/(positions[-1]-positions[0]))
            for name, pos in zip(NAMES, positions)]


def boundary_blocks(rows, mapping):
    if set(mapping) != set(NAMES):
        raise ValueError('Boundary map must contain exactly the seven electrode names')
    seen = set()
    blocks = ['! Generated electrode Dirichlet conditions; potentials in V.',
              '! Include once in the Elmer solver input. BC numbers 1-7 are reserved.']
    for i, (name, _, voltage) in enumerate(rows, 1):
        ids = mapping[name]
        if not isinstance(ids, list) or not ids:
            raise ValueError(f'{name}: supply a nonempty list of actual Elmer boundary IDs')
        for boundary in ids:
            if type(boundary) is not int or boundary <= 0 or boundary in seen:
                raise ValueError(f'{name}: boundary IDs must be positive, unique integers')
            seen.add(boundary)
        blocks.extend([f'Boundary Condition {i}', f'  Name = "{name}"',
                       f'  Target Boundaries({len(ids)}) = ' + ' '.join(map(str, ids)),
                       f'  Potential = {voltage:.12g}', 'End', ''])
    return '\n'.join(blocks)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config', type=Path)
    parser.add_argument('--output', type=Path, help='CSV voltage table (otherwise stdout)')
    parser.add_argument('--boundary-map', type=Path, help='JSON electrode name -> Elmer boundary IDs')
    parser.add_argument('--sif', type=Path, help='Output Elmer boundary-condition include file')
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text())
        rows = potentials(config)
        if bool(args.boundary_map) != bool(args.sif):
            raise ValueError('--boundary-map and --sif must be supplied together')
        sif = boundary_blocks(rows, json.loads(args.boundary_map.read_text())) if args.sif else None
        targets = [p for p in (args.output, args.sif) if p]
        if len({p.resolve() for p in targets}) != len(targets):
            raise ValueError('CSV and SIF output paths must differ')
        for path in targets:
            if path.exists():
                raise ValueError(f'Output already exists: {path}')
        text = io.StringIO()
        writer = csv.writer(text)
        writer.writerow(['electrode', 'position_' + config['position_unit'], 'potential_V'])
        writer.writerows((n, f'{p:.12g}', f'{v:.12g}') for n, p, v in rows)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text.getvalue())
        else:
            print(text.getvalue(), end='')
        if args.sif:
            args.sif.parent.mkdir(parents=True, exist_ok=True)
            args.sif.write_text(sif)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f'Error: {error}\n')


if __name__ == '__main__':
    main()
