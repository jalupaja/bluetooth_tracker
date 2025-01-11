{ pkgs ? import <nixpkgs> {} }:

# Define the environment
pkgs.mkShell {
  buildInputs = with pkgs;[
    python312
    python312Packages.pybluez

    python312Packages.rich
    python312Packages.matplotlib
    pkgs.python312Packages.numpy

    # pkgs.python312Packages.pandas
    # pkgs.python312Packages.tabulate
  ];

  shellHook = "source .venv/bin/activate";
}
