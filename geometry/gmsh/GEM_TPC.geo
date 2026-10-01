// Surface inspection entry point; not an electrostatic volume mesh.
// Coordinates are preserved. Confirm STL units before defining solver geometry.
Merge StrCat(CurrentDirectory, "../stl/GEM_TPC.stl");

Mesh.SurfaceEdges = 1;
Mesh.SurfaceFaces = 1;

// Next: identify electrodes and dielectric/gas interfaces, define closed
// volumes and physical groups, then generate an Elmer-compatible mesh.
// Do not assume the enclosed CAD solid is the gas volume.
//+
SetFactory("Built-in");
//+
SetFactory("OpenCASCADE");
