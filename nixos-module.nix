{ config, lib, pkgs, ... }:
let cfg = config.programs.kaltsit-sddm;
in
{
  options.programs.kaltsit-sddm.enable = lib.mkEnableOption
    "the experimental Medical Green SDDM theme resources and theme selection";
  options.programs.kaltsit-sddm.fontFile = lib.mkOption {
    type = with lib.types; nullOr path;
    default = null;
    description = "Optional local OPPO Sans 4.0 TTF supplied by the user. The project does not distribute or download this font.";
  };

  config = lib.mkIf cfg.enable {
    environment.systemPackages = [ (pkgs.callPackage ./sddm.nix { }) ];
    # Plasma sets mkDefault "breeze" (1000). Win over that default while keeping
    # ordinary explicit user settings (100) authoritative. Do not enable SDDM.
    services.displayManager.sddm.theme = lib.mkOverride 900 "KaltsitMedicalGreen";
    fonts.packages = lib.mkIf (cfg.fontFile != null) [
      (pkgs.runCommandLocal "kaltsit-sddm-user-font" {
        # types.path also accepts absolute strings; explicitly import either form.
        fontSource = builtins.path { path = cfg.fontFile; name = "OPPO-Sans-4.0.ttf"; };
      } ''
        install -Dm444 "$fontSource" "$out/share/fonts/truetype/OPPO-Sans-4.0.ttf"
      '')
    ];
    # QtQuick/Controls.Basic/Layouts are already in SDDM's qtdeclarative closure.
    # No extraPackages are needed, and authentication settings remain untouched.
  };
}
