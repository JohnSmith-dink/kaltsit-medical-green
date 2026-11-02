# Test VM only. Never import this fixture into a physical-machine configuration.
{ pkgs, lib, ... }:
{
  imports = [ ../nixos-module.nix ];
  networking.hostName = "sddm-test";
  system.stateVersion = "26.05";
  nixpkgs.config.allowUnfreePredicate = package: (package.pname or "") == "kaltsit-sddm";
  programs.kaltsit-sddm.enable = true;
  services.xserver.enable = true;
  services.displayManager.sddm = {
    enable = true;
    package = pkgs.kdePackages.sddm;
    wayland.enable = false;
    settings.General.InputMethod = "";
  };
  services.xserver.desktopManager.xterm.enable = true;
  services.displayManager.defaultSession = "xterm";
  users.users.tester = {
    isNormalUser = true;
    initialPassword = "wallpaper-test"; # Public, disposable VM fixture only.
  };
  fonts.packages = [ pkgs.noto-fonts-cjk-sans ];
  environment.systemPackages = [ pkgs.xdotool pkgs.xorg.xprop ];
  virtualisation.vmVariant = {
    virtualisation = {
      memorySize = 2048;
      cores = 2;
      graphics = true;
      resolution = { x = 1280; y = 800; };
      useNixStoreImage = true;
      sharedDirectories = lib.mkForce { };
      restrictNetwork = true;
      useHostCerts = false;
    };
  };
}
