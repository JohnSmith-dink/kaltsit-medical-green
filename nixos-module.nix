{ config, lib, pkgs, ... }:
{
  options.programs.kaltsit-sddm.enable = lib.mkEnableOption
    "the experimental Medical Green SDDM theme resources and theme selection";

  config = lib.mkIf config.programs.kaltsit-sddm.enable {
    environment.systemPackages = [ (pkgs.callPackage ./sddm.nix { }) ];
    # Plasma sets mkDefault "breeze" (1000). Win over that default while keeping
    # ordinary explicit user settings (100) authoritative. Do not enable SDDM.
    services.displayManager.sddm.theme = lib.mkOverride 900 "KaltsitMedicalGreen";
    # QtQuick/Controls.Basic/Layouts are already in SDDM's qtdeclarative closure.
    # No extraPackages are needed, and authentication settings remain untouched.
  };
}
