# Super-FRS GEM-TPC field-cage simulation

C++17 / Garfield++ project for inspecting the drift-cage electric field.
CPU operation is sufficient; CUDA is not required.

**Status:** project foundation. The supplied CAD mesh and Gmsh inspection source
are in [geometry/](geometry/README.md). Geometry units, electrode assignments
and operating voltages remain to be confirmed.
`config/uniform.cfg` is an artificial validation fixture, not the
Super-FRS detector. No detector field-uniformity prediction is provided yet.

## Get the project and build (Debian 13)

For a fresh checkout:

```bash
git clone --branch setup/garfield-project https://github.com/ikeshel/sfrs-gem-tpc-fc-sim.git
cd sfrs-gem-tpc-fc-sim
```

For an existing checkout, commit or stash your edits before switching branches:

```bash
git fetch origin
git switch setup/garfield-project
git pull --ff-only
```

All commands below run from the repository root.

Install ROOT and Garfield++ first; see [Debian setup](docs/debian.md).
Use the compiler/C++ standard supported by your ROOT installation.

```bash
source $HOME/garfieldpp/install/share/Garfield/setupGarfield.sh
cmake -S . -B build -DCMAKE_PREFIX_PATH=$HOME/garfieldpp/install
cmake --build build -j4
ctest --test-dir build --output-on-failure
```

The project links the installed `Garfield::Garfield` CMake target. It does not
download dependencies or require a graphical session. Python 3 is used for validation and plotting; use `-DBUILD_TESTING=OFF` to omit
the build-time validation tests. Adjust the Garfield++ install path above if needed.

## Uniform validation

```bash
./build/tpc-field uniform config/uniform.cfg results/uniform.csv
```

`config/uniform.cfg` is editable: its bounds and voltages define your uniform
field run. This mode does not solve electrodes, fringe fields or space charge.
The field is Ez = (v_cathode - v_anode)/(z_max - z_min).

CTest uses a separate fixed file, `tests/fixtures/uniform.cfg`, with -1000 V at
z = 0 cm and 0 V at z = 10 cm. Its expected Ez is -100 V/cm. Editing the run
configuration does not change that regression test. After pulling this change:

```bash
cmake -S . -B build -DCMAKE_PREFIX_PATH="$HOME/garfieldpp/install"
cmake --build build -j4
ctest --test-dir build --output-on-failure
```

CTest writes temporary CSVs; it does not refresh `results/uniform.csv`. After
changing simulation settings, generate a new CSV and plot that file:

```bash
./build/tpc-field uniform config/uniform.cfg results/uniform_updated.csv
python3 scripts/plot_field_zx_zy.py results/uniform_updated.csv --style both
```

Choose another output name if this CSV already exists.

## Visualize the field and sampling mesh

Install plotting dependencies:

```bash
sudo apt install python3-numpy python3-matplotlib
```

After generating `results/uniform.csv`, display both central slices with colored
sampling cells and electric-field arrows:

```bash
python3 scripts/plot_field_zx_zy.py results/uniform.csv --style both
```

Other views:

```bash
# Sampling mesh only, shared field-magnitude color scale on both planes
python3 scripts/plot_field_zx_zy.py results/uniform.csv --style mesh
# Arrows and sample points, without colored cells
python3 scripts/plot_field_zx_zy.py results/uniform.csv --style arrows
# Single x-z slice at y = 0 cm
python3 scripts/plot_field.py results/uniform.csv --y 0
# Potential and Ez along x = y = 0
python3 scripts/plot_uniformity.py results/uniform.csv
# Save on a remote/headless machine without opening a window
python3 scripts/plot_field_zx_zy.py results/uniform.csv --style both --no-show --output results/field_mesh.png
```

The zx view is the x-z plane at `--y` (default 0 cm); zy is the y-z plane
at `--x` (default 0 cm). These must be sampled coordinates, not interpolated
planes. Use `--view zx` or `--view zy` for one plane. All scripts accept
`--help`, an input CSV, `--output` and `--no-show`. The original misspelled
`plot_univormity.py` remains as a compatibility entry point.

Colors show the full field magnitude; equal-length arrows show the direction
of the field projected into each plane, not electron trajectories. Missing or
invalid samples remain blank. Cells are centered on CSV sample coordinates,
with edges halfway between neighbors; the outer cells extend half a spacing
past the sampled range. This is a **sampling grid, not the finite-element mesh**.
No interpolation across missing points is performed. PNGs default to the input
CSV directory and are replaced when rerunning the same plot command.

The initial grid is deliberately coarse (3 x 3 x 11). For a denser display,
copy the config, increase nx/ny/nz, and write a new CSV:

```bash
cp config/uniform.cfg config/uniform_dense.cfg
# Edit nx = 21, ny = 21 and nz = 101 in this copy.
nano config/uniform_dense.cfg
./build/tpc-field uniform config/uniform_dense.cfg results/uniform_dense.csv
python3 scripts/plot_field_zx_zy.py results/uniform_dense.csv --style mesh
```

Existing simulation CSV files are protected against overwrite: choose a new
output filename for another run. Refining this sampling grid does not refine
an imported FEM solution.

## Display the full sampled field in 3D

```bash
python3 scripts/plot_field_3d.py results/uniform.csv
# Use your newly generated CSV after changing configuration:
python3 scripts/plot_field_3d.py results/updated.csv
# Save without opening a window:
python3 scripts/plot_field_3d.py results/uniform.csv --no-show --output results/field_3d.png
```

Drag in the Matplotlib window to rotate the view. Colored points indicate |E|;
black arrows show 3D field direction at equal length. Axis proportions preserve
physical dimensions. Invalid samples are excluded. Above 2,000 valid samples,
the plot displays evenly spaced rows to keep interaction responsive; increase
`--max-arrows` to show more (the title reports the displayed count). The color
scale and spatial bounds use all valid samples. `--elev` and `--azim` set the
initial view angle in degrees. PNG exports are static and replaced on rerun.

This shows the sampled field volume, not the STL, tetrahedral mesh or electron
trajectories. The uniform example will show parallel arrows throughout.

## View the geometry or actual FEM mesh

```bash
sudo apt install gmsh
gmsh geometry/gmsh/GEM_TPC.geo
```

This opens the supplied STL triangle mesh, which has no field solution. In
Gmsh's visibility/options controls, enable surface faces and surface edges.
Once an actual volume mesh has been generated, open its `.msh` file in Gmsh
and enable volume edges to inspect its tetrahedra. For field colors on the
actual solver mesh, export the Elmer solution as VTU, open it in ParaView,
choose **Surface With Edges**, and select the exported potential or electric
field array. Neither a solved cage mesh nor VTU output exists in this project
yet. The STL alone cannot display a cage electric field.

## Seven-electrode potentials

The new [seven-electrode setup](docs/electrodes.md) implements cathode -200 V,
five shaping electrodes, and anode +4000 V. For provisional equal spacing:

```bash
python3 scripts/electrode_voltages.py config/electrodes.json
```

This gives -200, 500, 1200, 1900, 2600, 3300 and 4000 V. The script can also
write Elmer boundary conditions after actual mesh boundary IDs are supplied.
`GEM_TPC_v1.stl` is included; its units are mm. Electrode identification and
volume meshing remain necessary before solving the physical cage field.
See the linked guide for unequal spacing and the Elmer commands.

## Import a solved cage field

Workflow: geometry/mesh in Gmsh, electrostatics in Elmer, then Garfield++ field
inspection. See [geometry and field-map requirements](docs/geometry.md).

```bash
./build/tpc-field elmer config/cage.cfg results/cage.csv fieldmaps/cage mm 0
```

This is a template: create `config/cage.cfg` and the map from the real detector
first. Copy the example config and set the sampling bounds and resolution.
The final argument is the **zero-based Garfield material index** of the gas;
`mm` specifies only the source mesh unit. Config and CSV coordinates are always
**cm**, potential **V**, field **V/cm**. The drift axis is z.

In map mode, config potentials and z bounds define only the nominal comparison
field Ez0 = (V_cathode - V_anode)/(z_max - z_min); they do not modify the solution.
For that comparison, z bounds must correspond to the physical electrode positions.

CSV contains potential, Ex/Ey/Ez, Etrans/|Ez|, signed (Ez-Ez0)/Ez0 and status.
Only finite samples with status 0 in the selected medium enter the summary.
Invalid samples remain as `nan`; Etrans/|Ez| is also `nan` when Ez is zero.
Excluded points are counted; exit code 2 means no valid samples. Sampling includes
endpoints, which may lie outside the map. Check coverage before interpreting extrema.
Existing output files are not overwritten.

The medium is a sampling marker, not an assumed gas mixture or transport model.
Electron drift, diffusion, gain, magnetic fields, weighting fields and signals
are outside this initial implementation.

## Validation status

Built and tested on macOS with AppleClang 21, ROOT 6.36.02 and Garfield++
revision `60c55ca309c1d8734127e26a16548c9ddc496ba5` (CPU, GSL enabled).
Both CTest cases pass: uniform potential/field checks and a synthetic Elmer
tetrahedron checking interpolation, mm-to-cm conversion and out-of-map handling.
The latter is an analytic importer fixture, not a mesh solved by Elmer.
The user also verified the build, both CTest cases and the uniform run on
Debian 13 with GNU 14.2.0. A real detector field map remains to be validated.

## References

- [Garfield++](https://garfieldpp.web.cern.ch/)
- [Gmsh/Elmer tutorial](https://garfieldpp.web.cern.ch/tutorials/pdf/garfield_elmer_doc.pdf)

The repository retains its GPL-3.0 license; see [LICENSE](LICENSE).
