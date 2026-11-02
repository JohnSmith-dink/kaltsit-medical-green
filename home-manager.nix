{ config, lib, pkgs, ... }:

let
  cfg = config.programs.kaltsit-theme;
in
{
  options.programs.kaltsit-theme = {
    enable = lib.mkEnableOption "the Kal'tsit Medical Green Plasma theme and switching commands";

    ghosttyThemeFile = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = ''
        Install the Ghostty theme in its user theme directory. This does not
        modify Ghostty's configuration; declarative users can set
        programs.ghostty.settings.theme = "Kaltsit Medical Green" separately.
      '';
    };

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
    motion = {
      enable = lib.mkEnableOption "the optional local video wallpaper resources";
      videoFile = lib.mkOption {
        type = lib.types.nullOr lib.types.path;
        default = null;
        description = "Optional local video copied into the Nix store; null selects it later in wallpaper settings.";
      };
      posterFile = lib.mkOption {
        type = lib.types.nullOr lib.types.path;
        default = null;
        description = "Optional still image; null uses the existing package option's wallpaper.";
      };
    };
  };

  # No activation hook or session service: switching is an explicit action.
  config = lib.mkMerge [ (lib.mkIf cfg.enable {
    home.packages = [ cfg.package pkgs.kdePackages.breeze-gtk ];
    xdg.configFile."ghostty/themes/Kaltsit Medical Green" = lib.mkIf cfg.ghosttyThemeFile {
      source = "${cfg.package}/share/ghostty/themes/Kaltsit Medical Green";
    };
  }) (lib.mkIf cfg.motion.enable {
    home.packages = [ (pkgs.callPackage ./motion.nix {
      baseTheme = cfg.package;
      inherit (cfg.motion) videoFile posterFile;
    }) ];
  }) ];
}
