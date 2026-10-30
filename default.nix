{ pkgs ? import <nixpkgs> {
    config.allowUnfreePredicate = package: (package.pname or "") == "kaltsit-theme";
  }
}:

pkgs.callPackage ./package.nix { }
