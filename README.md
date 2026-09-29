# Super-FRS GEM-TPC field-cage simulation

C++17 / Garfield++ project for inspecting the drift-cage electric field.
CPU operation is sufficient; CUDA is not required.

**Status:** project foundation. Detector geometry and operating voltages are
pending. `config/uniform.cfg` is an artificial validation fixture, not the
Super-FRS detector. No detector field-uniformity prediction is provided yet.

## Build

Install ROOT and Garfield++ first; see [Debian setup](docs/debian.md).
Use the compiler/C++ standard supported by your ROOT installation.

```bash
source /path/to/garfield-install/share/Garfield/setupGarfield.sh
cmake -S . -B build -DCMAKE_PREFIX_PATH=/path/to/garfield-install
cmake --build build -j4
ctest --test-dir build --output-on-failure
```

The project links the installed `Garfield::Garfield` CMake target. It does not
download dependencies or require a graphical session. Python 3 is used only for
the validation test; use `-DBUILD_TESTING=OFF` to omit it.

## Uniform validation

```bash
./build/tpc-field uniform config/uniform.cfg results/uniform.csv
```

The artificial example spans z = 0 to 10 cm, with -1000 V at the cathode and
0 V at the anode: Ez = -100 V/cm and V(z) = -1000 + 100 z V.
It verifies sampling and E = -grad(V), not electrodes, fringe fields or space charge.

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
Debian 13 and a real detector field map remain to be validated.

## References

- [Garfield++](https://garfieldpp.web.cern.ch/)
- [Gmsh/Elmer tutorial](https://garfieldpp.web.cern.ch/tutorials/pdf/garfield_elmer_doc.pdf)

The repository retains its GPL-3.0 license; see [LICENSE](LICENSE).
