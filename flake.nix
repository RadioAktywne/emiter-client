{
  description = "emiter-client";

  inputs.nixpkgs.url = "https://github.com/NixOS/nixpkgs/archive/nixos-26.05.tar.gz";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];

      forAllSystems = f:
        builtins.listToAttrs (map (s: { name = s; value = f s; }) systems);

      devShellFor = system:
        let pkgs = import nixpkgs { inherit system; };
        in pkgs.mkShellNoCC {
          packages = [
            (pkgs.python3.withPackages (ps: [ ps.pyqt5 ps.requests ]))
            pkgs.socat     
            pkgs.docker
            pkgs.pulseaudio 
            pkgs.procps
            pkgs.coreutils
            pkgs.util-linux 
            pkgs.qt5.qtbase.bin
          ];

          shellHook = ''
            export QT_PLUGIN_PATH="${pkgs.qt5.qtbase.bin}/lib/qt-${pkgs.qt5.qtbase.version}/plugins"
          '';
        };
    in {
      devShells = forAllSystems (system: {
        default = devShellFor system;
      });
    };
}
