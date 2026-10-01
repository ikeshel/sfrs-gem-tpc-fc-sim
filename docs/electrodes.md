# Seven-electrode voltage distribution

The confirmed polarity is **cathode -200 V, anode +4000 V**. Five shaping
electrodes lie between them. `config/electrodes.json` is the voltage source
configuration; STL coordinates are confirmed to be mm. The drift axis and
actual electrode positions/boundary identities still need to be established.

Equal spacing is an explicit provisional model, encoded as relative positions
0 through 6. It gives:

| Electrode | V |
| --- | ---: |
| cathode | -200 |
| electrode_1 | 500 |
| electrode_2 | 1200 |
| electrode_3 | 1900 |
| electrode_4 | 2600 |
| electrode_5 | 3300 |
| anode | 4000 |

Print or export the table (Python standard library only):

```bash
python3 scripts/electrode_voltages.py config/electrodes.json
python3 scripts/electrode_voltages.py config/electrodes.json --output geometry/generated/voltages.csv
```

For unequal gaps, replace `positions` with the seven measured positions in
cathode-to-anode order and set `position_unit` to `mm`, `cm` or `m`. Positions
may increase or decrease but must be strictly monotonic. Voltage interpolation
is V_i = V_c + (V_a - V_c)*(s_i - s_c)/(s_a - s_c). This specifies a linear
boundary-potential distribution; it does not guarantee a uniform field near
finite electrodes or dielectric interfaces.

## Apply to Elmer

Open the supplied geometry:

```bash
gmsh geometry/gmsh/GEM_TPC_v1.geo
```

Identify the seven electrode surfaces, construct the gas/dielectric domains,
mesh and convert to Elmer. Then copy the boundary template:

```bash
cp config/elmer/boundaries.template.json config/elmer/boundaries.json
```

Fill each list with the actual boundary IDs **in the converted Elmer mesh**.
An electrode may cover several boundary IDs. Never use STL triangle numbers
or assume the physical IDs survived conversion without checking. Empty lists
are deliberately rejected; duplicate IDs across electrodes are also rejected.

```bash
python3 scripts/electrode_voltages.py config/electrodes.json \
  --boundary-map config/elmer/boundaries.json \
  --sif geometry/generated/electrode_boundaries.sif
```

Include the generated blocks once in the complete Elmer solver input:

```text
Include "electrode_boundaries.sif"
```

Place that include alongside the solver input in its working directory, or
use the correct path. The include reserves Boundary Condition numbers 1-7;
other boundary-condition blocks must use different numbers. It supplies only
fixed-potential boundary blocks, not a complete solver input or gas mesh.
The complete electrostatic model must still define bodies, permittivities,
solver settings, remaining boundaries and output. Re-solve when voltages change,
then import the result using the README's `tpc-field elmer` command.

The generator refuses to overwrite existing files. Choose fresh output names
or intentionally remove old generated files before regeneration.

## Uniform approximation

`config/uniform.cfg` now uses the confirmed endpoint polarity; its existing
sampling dimensions are retained. This independent ideal-field mode has **no
intermediate electrode geometry** and does not read `electrodes.json`.
With its present z length of 10 cm, Ez = -420 V/cm. Regenerate a new CSV:

```bash
./build/tpc-field uniform config/uniform.cfg results/seven_electrode_ideal.csv
python3 scripts/plot_field_3d.py results/seven_electrode_ideal.csv
```

That plot is an ideal approximation only. The new STL has not yet been used to
solve the physical cage field. Do not interpret it as a seven-electrode FEM result.
