{
  description = "emiter-client: PyQt5 GUI for Emiter streaming";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        python = pkgs.python3;
        pythonEnv = python.withPackages (ps: with ps; [
          pyqt5
          requests
        ]);
      in {
        packages.default = pkgs.stdenv.mkDerivation {
          pname = "emiter-client";
          version = "0.1.0";
          src = ./.;
          buildInputs = [
            pythonEnv
            pkgs.liquidsoap
            pkgs.socat
            pkgs.qt5.qtbase
            pkgs.qt5.qtx11extras
          ];
          installPhase = ''
            mkdir -p $out
            cp -r * $out/
          '';
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonEnv
            pkgs.liquidsoap
            pkgs.socat
            pkgs.qt5.qttools
            pkgs.qt5.qtbase
            pkgs.qt5.qtx11extras
            pkgs.xorg.libX11
            pkgs.xorg.libxcb
            pkgs.xorg.xcbutil
            pkgs.xorg.xcbutilwm
            pkgs.xorg.xcbutilimage
            pkgs.xorg.xcbutilkeysyms
            pkgs.xorg.xcbutilrenderutil
          ];
          shellHook = ''
            export PYTHONPATH=${pythonEnv}/${python.sitePackages}
            export QT_QPA_PLATFORM_PLUGIN_PATH=${pkgs.qt5.qtbase.bin}/lib/qt-${pkgs.qt5.qtbase.version}/plugins
            export QT_PLUGIN_PATH=${pkgs.qt5.qtbase.bin}/lib/qt-${pkgs.qt5.qtbase.version}/plugins
            echo "Development shell for emiter-client"
            echo "Liquidsoap version: $(liquidsoap --version)"
          '';
        };
      }
    );
}