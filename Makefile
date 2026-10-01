# Run from the repository root. Initialize ROOT/Garfield++ in your shell first.
.DEFAULT_GOAL := all

GARFIELD_PREFIX ?= $(HOME)/garfieldpp/install
BUILD_DIR ?= build
JOBS ?= 4
CONFIG ?= config/uniform.cfg
OUTPUT ?= results/new_setup.csv

.PHONY: all configure build test run

all: run

configure:
	cmake -S . -B "$(BUILD_DIR)" -DCMAKE_PREFIX_PATH="$(GARFIELD_PREFIX)"

build: configure
	cmake --build "$(BUILD_DIR)" -j$(JOBS)

test: build
	ctest --test-dir "$(BUILD_DIR)" --output-on-failure

# The dependency chain keeps configure/build/test/run ordered even with make -j.
# Existing CSVs are protected by tpc-field; choose OUTPUT=... for another run.
run: test
	"$(BUILD_DIR)/tpc-field" uniform "$(CONFIG)" "$(OUTPUT)"
