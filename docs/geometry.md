# Geometry and field-map contract

Supply a drawing/CAD file with:

- Active shape/dimensions, drift axis and origin, with units.
- Cathode/readout locations, shapes and voltages.
- Strip/wire count, pitch, width/diameter, thickness and end spacing.
- Divider potentials or resistor values and their connections.
- Insulator dimensions/permittivities and nearby grounded structures.
- Relevant openings, supports and feedthroughs.
- Fiducial volume and required field-uniformity tolerance.

State electrostatic boundary conditions and whether space charge is neglected.
Refine near gaps/edges and compare successive meshes. Use realistic edge radii
when evaluating peak surface fields.

## Import format

The initial importer uses **3D second-order, 10-node tetrahedra** through
`ComponentElmer`. It does not import 2D or axisymmetric meshes. If the drawing
permits a reduced model, add the appropriate importer first.

Place these files from the same solution together:

```text
fieldmaps/cage/
  mesh.header
  mesh.elements
  mesh.nodes
  dielectrics.dat
  out.result
```

`out.result` must use the Elmer potential format supported by Garfield++, not
a VTU visualization export. `dielectrics.dat` contains the material count,
then material number / relative permittivity rows in mesh material order.
For a one-material ideal gas domain:

```text
1
1 1.0
```

The corresponding CLI material index is 0 (zero-based). Check the importer log
for material assignments and coordinate units. Provide the full solved map;
this application does not impose periodicity or mirror symmetry.

Generated maps/results are git-ignored. Version the geometry source, solver
inputs and parameter choices when available. Changing sampling-config voltages
does not re-solve Elmer; recompute the map when boundary conditions change.
