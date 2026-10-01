# Detector geometry sources

`stl/GEM_TPC.stl` is the supplied CAD surface mesh, copied without modification.
`gmsh/GEM_TPC.geo` is the source entry point for opening that mesh in Gmsh:

```bash
gmsh geometry/gmsh/GEM_TPC.geo
```

This imports the existing triangulated surface for inspection. It does not yet
define the gas volume, electrode potentials, dielectric properties or physical
groups, and does not produce a solved Garfield++ field map.

## Source metadata

- Original filename: `GEM_TPC.stl`
- Format: binary STL
- Triangle count: 4,696
- Size: 234,884 bytes
- SHA-256: `fe31fb22de3dd7aa07297de1d7839b6cda3c5ce5ec492ed7981c8befcec583a6`
- Units: **unconfirmed**; STL does not encode length units.
- Coordinates: original CAD coordinates, with no rescaling or rotation.
- Drift axis: unconfirmed; do not assume the CAD z axis is the drift axis.

Bounding box in the original, unspecified units:

| Axis | Minimum | Maximum |
| --- | ---: | ---: |
| x | -200.296204 | 200.296204 |
| y | -50 | 50 |
| z | -96 | 0 |

The uniform-field example's cm units and z drift axis are independent of this
CAD file. Confirm units, orientation, electrode identities and operating
voltages before connecting this geometry to the simulation.

Keep source STL and Gmsh scripts here. Put generated meshes under
`geometry/generated/` and solved Elmer maps under `fieldmaps/`; both are ignored
by Git. See [the field-map contract](../docs/geometry.md) for solver requirements.

## Version 1 geometry

`stl/GEM_TPC_v1.stl` is the new source (unchanged binary STL, 4,844 triangles,
242,284 bytes). Its units are confirmed **mm**; its bounds are the same as the
original table above. The drift axis and electrode surface identities remain
unconfirmed. Open `gmsh/GEM_TPC_v1.geo` for surface inspection.

SHA-256: `2b36fe768172f63f447001ef013ba81da596866ad0b7d7dc330c6d7effea541a`.

See [seven-electrode setup](../docs/electrodes.md) for potentials.
