#include <Garfield/ComponentConstant.hh>
#include <Garfield/ComponentElmer.hh>
#include <Garfield/Medium.hh>

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>

namespace fs = std::filesystem;
using Config = std::map<std::string, double>;

Config ReadConfig(const fs::path& path) {
  std::ifstream input(path);
  if (!input) throw std::runtime_error("Cannot read config: " + path.string());
  const Config keys{{"x_min", 0}, {"x_max", 0}, {"y_min", 0}, {"y_max", 0},
                    {"z_min", 0}, {"z_max", 0}, {"nx", 0}, {"ny", 0},
                    {"nz", 0}, {"v_cathode", 0}, {"v_anode", 0}};
  Config cfg;
  std::string line;
  unsigned lineNumber = 0;
  while (std::getline(input, line)) {
    ++lineNumber;
    line = line.substr(0, line.find('#'));
    if (line.find_first_not_of(" \t\r") == std::string::npos) continue;
    const auto eq = line.find('=');
    if (eq != std::string::npos) line[eq] = ' ';
    std::istringstream stream(line);
    std::string key, extra;
    double value;
    if (eq == std::string::npos || !(stream >> key >> value) ||
        (stream >> extra) || !std::isfinite(value) || !keys.count(key) ||
        !cfg.emplace(key, value).second) {
      throw std::runtime_error("Invalid/duplicate config entry at line " +
                               std::to_string(lineNumber));
    }
  }
  for (const auto& entry : keys) {
    if (!cfg.count(entry.first)) throw std::runtime_error("Missing key: " + entry.first);
  }
  for (const std::string axis : {"x", "y", "z"}) {
    if (cfg.at(axis + "_max") <= cfg.at(axis + "_min"))
      throw std::runtime_error("Invalid bounds for " + axis);
    const double n = cfg.at("n" + axis);
    if (n < 2 || n > 1000 || n != std::floor(n))
      throw std::runtime_error("Grid counts must be integers in [2, 1000]");
  }
  if (cfg.at("nx") * cfg.at("ny") * cfg.at("nz") > 10000000)
    throw std::runtime_error("Grid exceeds 10 million points");
  if (cfg.at("v_cathode") == cfg.at("v_anode"))
    throw std::runtime_error("Reference voltage difference must be nonzero");
  return cfg;
}

int main(int argc, char** argv) {
  try {
    if (argc == 2 && std::string(argv[1]) == "--help") {
      std::cout << "Usage:\n  tpc-field uniform CONFIG OUTPUT.csv\n"
                   "  tpc-field elmer CONFIG OUTPUT.csv MAP_DIR UNIT MATERIAL_INDEX\n"
                   "UNIT: mm, cm, or m (mesh coordinates only). MATERIAL_INDEX: zero-based.\n"
                   "Config/sample coordinates are always cm; fields V/cm; potentials V.\n";
      return 0;
    }
    if (argc < 2) throw std::runtime_error("Use --help for usage");
    const std::string mode = argv[1];
    if (!((mode == "uniform" && argc == 4) || (mode == "elmer" && argc == 7)))
      throw std::runtime_error("Invalid arguments; use --help");
    const Config cfg = ReadConfig(argv[2]);
    const double ez0 = (cfg.at("v_cathode") - cfg.at("v_anode")) /
                       (cfg.at("z_max") - cfg.at("z_min"));
    // A marker for the selected sampling material, NOT a gas transport model.
    Garfield::Medium samplingMedium;
    samplingMedium.EnableDrift();
    std::unique_ptr<Garfield::Component> field;
    if (mode == "uniform") {
      auto uniform = std::make_unique<Garfield::ComponentConstant>();
      uniform->SetArea(cfg.at("x_min"), cfg.at("y_min"), cfg.at("z_min"),
                       cfg.at("x_max"), cfg.at("y_max"), cfg.at("z_max"));
      uniform->SetMedium(&samplingMedium);
      uniform->SetElectricField(0, 0, ez0);
      uniform->SetPotential(0, 0, cfg.at("z_min"), cfg.at("v_cathode"));
      field = std::move(uniform);
      std::cout << "UNIFORM VALIDATION FIXTURE: no cage electrodes or fringe fields.\n";
    } else {
      const fs::path dir = argv[4];
      const std::string unit = argv[5];
      if (unit != "mm" && unit != "cm" && unit != "m")
        throw std::runtime_error("Mesh unit must be mm, cm, or m");
      const std::string index = argv[6];
      if (index.empty() || index.find_first_not_of("0123456789") != std::string::npos)
        throw std::runtime_error("Material index must be a nonnegative integer");
      const auto material = std::stoul(index);
      for (const auto* file : {"mesh.header", "mesh.elements", "mesh.nodes",
                               "dielectrics.dat", "out.result"}) {
        if (!fs::is_regular_file(dir / file))
          throw std::runtime_error("Missing map file: " + (dir / file).string());
      }
      auto elmer = std::make_unique<Garfield::ComponentElmer>();
      if (!elmer->Initialise((dir / "mesh.header").string(),
                             (dir / "mesh.elements").string(),
                             (dir / "mesh.nodes").string(),
                             (dir / "dielectrics.dat").string(),
                             (dir / "out.result").string(), unit))
        throw std::runtime_error("Elmer field-map initialization failed");
      if (material >= elmer->GetNumberOfMaterials())
        throw std::runtime_error("Material index outside map material list");
      elmer->SetMedium(material, &samplingMedium);
      elmer->DriftMedium(material);
      field = std::move(elmer);
    }
    const fs::path output = argv[3];
    if (fs::exists(output)) throw std::runtime_error("Output already exists: " + output.string());
    if (output.has_parent_path()) fs::create_directories(output.parent_path());
    std::ofstream csv(output);
    if (!csv) throw std::runtime_error("Cannot write output");
    csv << "x_cm,y_cm,z_cm,potential_V,Ex_V_per_cm,Ey_V_per_cm,Ez_V_per_cm,"
           "Etrans_over_abs_Ez,delta_Ez_over_Ez0,status\n" << std::setprecision(17);
    const auto coordinate = [&](const std::string& axis, int i) {
      return cfg.at(axis + "_min") + i * (cfg.at(axis + "_max") - cfg.at(axis + "_min")) /
             (cfg.at("n" + axis) - 1);
    };
    std::size_t valid = 0, invalid = 0;
    double maxDeviation = 0;
    const double nan = std::numeric_limits<double>::quiet_NaN();
    for (int ix = 0; ix < cfg.at("nx"); ++ix)
      for (int iy = 0; iy < cfg.at("ny"); ++iy)
        for (int iz = 0; iz < cfg.at("nz"); ++iz) {
          const double x = coordinate("x", ix), y = coordinate("y", iy), z = coordinate("z", iz);
          double ex = nan, ey = nan, ez = nan, v = nan;
          Garfield::Medium* medium = nullptr;
          int status = -99;
          field->ElectricField(x, y, z, ex, ey, ez, v, medium, status);
          const bool ok = status == 0 && medium == &samplingMedium &&
                          std::isfinite(ex) && std::isfinite(ey) && std::isfinite(ez) && std::isfinite(v);
          double transverse = nan, deviation = nan;
          if (ok) {
            ++valid;
            transverse = ez != 0 ? std::hypot(ex, ey) / std::abs(ez) : nan;
            deviation = (ez - ez0) / ez0;
            maxDeviation = std::max(maxDeviation, std::abs(deviation));
          } else {
            ++invalid;
            ex = ey = ez = v = nan;
            if (status == 0) status = -99;
          }
          csv << x << ',' << y << ',' << z << ',' << v << ',' << ex << ',' << ey << ','
              << ez << ',' << transverse << ',' << deviation << ',' << status << '\n';
        }
    csv.close();
    if (!csv) throw std::runtime_error("Failed while writing output");
    std::cout << "Reference Ez = " << ez0 << " V/cm; valid samples = " << valid
              << "; excluded samples = " << invalid << '\n';
    if (valid) std::cout << "Max |(Ez-Ez0)/Ez0| over valid samples = " << maxDeviation << '\n';
    // Invalid points remain explicitly marked in CSV, never interpreted as zero field.
    return valid ? 0 : 2;
  } catch (const std::exception& error) {
    std::cerr << "Error: " << error.what() << '\n';
    return 1;
  }
}
