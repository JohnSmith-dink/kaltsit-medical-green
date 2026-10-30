{ config, lib, pkgs, ... }:

let
  cfg = config.programs.kaltsit-theme;
in
{
  options.programs.kaltsit-theme = {
    enable = lib.mkEnableOption "the Kal'tsit Medical Green Plasma theme and switching commands";

    package = lib.mkOption {
      type = lib.types.package;
      default = pkgs.callPackage ./package.nix { };
      defaultText = lib.literalExpression "pkgs.callPackage ./package.nix { }";
      description = ''
        Theme package to install. The complete package includes assets with
        separate rights and is marked unfree. The supplied package set must
        allow kaltsit-theme, or this option can use the flake package output.
      '';
    };
  };

  # No activation hook or session service: switching is an explicit action.
  config = lib.mkIf cfg.enable {
    home.packages = [ cfg.package pkgs.kdePackages.breeze-gtk ];
  };
}
