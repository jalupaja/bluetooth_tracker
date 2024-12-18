{ pkgs ? import <nixpkgs> {} }:

# Define the environment
pkgs.mkShell {
  buildInputs = [
		pkgs.python312
		pkgs.python312Packages.pybluez

		# pkgs.python312Packages.numpy
		# pkgs.python312Packages.pandas
		# pkgs.python312Packages.tabulate
  ];

  shellHook = "source .venv/bin/activate";
}
