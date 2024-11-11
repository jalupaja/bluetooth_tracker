{ pkgs ? import <nixpkgs> {} }:

# Define the environment
pkgs.mkShell {
  buildInputs = [
		pkgs.python312
		pkgs.python312Packages.pybluez
  ];

  shellHook = "source .venv/bin/activate";
}
