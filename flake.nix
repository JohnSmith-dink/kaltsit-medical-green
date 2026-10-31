{
  description = "Kal'tsit Medical Green — a reversible KDE Plasma 6 desktop theme";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs {
        inherit system;
        config.allowUnfreePredicate = package: (package.pname or "") == "kaltsit-theme";
      };
      theme = pkgs.callPackage ./package.nix { };
      app = {
        type = "app";
        program = "${theme}/bin/kaltsit-theme";
        meta.description = theme.meta.description;
      };
    in {
      packages.${system} = {
        default = theme;
        kaltsit-theme = theme;
      };

      apps.${system} = {
        default = app;
        kaltsit-theme = app;
      };

      homeManagerModules.default = import ./home-manager.nix;
      checks.${system}.theme = theme;
      devShells.${system}.default = pkgs.mkShell {
        packages = [ (pkgs.python3.withPackages (packages: [ packages.pillow ])) ];
        PYTHONDONTWRITEBYTECODE = "1";
      };
    };
}
