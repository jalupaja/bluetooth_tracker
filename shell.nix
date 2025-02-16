{ pkgs ? import <nixpkgs> {} }:

# Define the environment
pkgs.mkShell {
  buildInputs = with pkgs;[
    python312
    python312Packages.sqlalchemy
    python312Packages.bleak
    python312Packages.pybluez

    python312Packages.pyyaml
    pkgs.python312Packages.numpy
    pkgs.python312Packages.pandas

    python312Packages.rich
    python312Packages.matplotlib
  ];

  # shellHook = "source .venv/bin/activate";
}
