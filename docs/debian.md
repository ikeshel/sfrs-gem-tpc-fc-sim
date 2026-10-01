# Debian 13 setup

Run these instructions on the Debian host. A Debian build has not yet been
verified here. No CUDA toolkit or NVIDIA GPU is required.

```bash
sudo apt update
sudo apt install build-essential gfortran cmake git libgsl-dev python3
```

Install [ROOT 6](https://root.cern.ch/install/) for a distribution/compiler
compatible with Debian 13; do not assume Ubuntu binaries are compatible.

```bash
source /path/to/root/bin/thisroot.sh
root-config --version
root-config --cxx
```

If Garfield++ is already installed, use it. Otherwise, in your dependencies directory:

```bash
git clone https://gitlab.cern.ch/garfield/garfieldpp.git
# Revision used to check this project's initial interfaces.
git -C garfieldpp checkout 60c55ca309c1d8734127e26a16548c9ddc496ba5
cmake -S garfieldpp -B garfieldpp/build \
  -DCMAKE_INSTALL_PREFIX="$PWD/garfieldpp/install" \
  -DGARFIELD_WITH_CUDA=OFF \
  -DGARFIELD_WITH_EXAMPLES=OFF \
  -DGARFIELD_WITH_TESTS=OFF
cmake --build garfieldpp/build -j4
cmake --install garfieldpp/build
source garfieldpp/install/share/Garfield/setupGarfield.sh
```

Follow the README using the absolute install directory as `CMAKE_PREFIX_PATH`.
If ROOT is not found, initialize it first or pass `-DROOT_DIR=/path/to/root/cmake`.
Use a fresh build directory after changing compiler or ROOT installations.
Gmsh and Elmer are needed for producing cage maps, not the uniform fixture.
