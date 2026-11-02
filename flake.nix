{
  description = "Kal'tsit Medical Green — a reversible KDE Plasma 6 desktop theme";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs {
        inherit system;
        config.allowUnfreePredicate = package: builtins.elem (package.pname or "") [ "kaltsit-theme" "kaltsit-motion" "kaltsit-sddm" ];
      };
      theme = pkgs.callPackage ./package.nix { };
      motion = pkgs.callPackage ./motion.nix { baseTheme = theme; };
      sddmTheme = pkgs.callPackage ./sddm.nix { };
      # Evaluate the real module with a small Home Manager option harness.
      # No new input or second nixpkgs; this exercises lazy defaults and mkIf.
      evalHome = settings: (pkgs.lib.evalModules {
        specialArgs = { inherit pkgs; };
        modules = [ ./home-manager.nix ({ lib, ... }: {
          options.home.packages = lib.mkOption { type = lib.types.listOf lib.types.package; default = [ ]; };
          options.xdg.configFile = lib.mkOption { type = lib.types.attrsOf lib.types.anything; default = { }; };
        }) settings ];
      }).config;
      homeOff = evalHome { };
      homeMotion = evalHome { programs.kaltsit-theme.motion.enable = true; };
      customBase = pkgs.runCommand "kaltsit-custom-base-fixture" { } "mkdir -p $out";
      homeCustom = evalHome { programs.kaltsit-theme = {
        package = customBase;
        motion.enable = true;
        motion.videoFile = ./LICENSE;
      }; };
      homePoster = evalHome { programs.kaltsit-theme.motion = {
        enable = true;
        posterFile = ./share/wallpapers/KaltsitMedicalGreen/contents/images/3840x2160.jpg;
      }; };
      homeModuleCheck = assert homeOff.home.packages == [ ];
        assert homeOff.xdg.configFile == { };
        assert !homeOff.programs.kaltsit-theme.motion.enable;
        assert homeOff.programs.kaltsit-theme.motion.videoFile == null;
        assert homeOff.programs.kaltsit-theme.motion.posterFile == null;
        assert !homeMotion.programs.kaltsit-theme.enable;
        assert builtins.length homeMotion.home.packages == 1;
        assert (builtins.head homeMotion.home.packages).pname == "kaltsit-motion";
        assert homeMotion.xdg.configFile == { };
        assert pkgs.lib.hasInfix (builtins.unsafeDiscardStringContext "file://${./LICENSE}") (builtins.head homeCustom.home.packages).installPhase;
        assert pkgs.lib.hasInfix (builtins.unsafeDiscardStringContext "${customBase}/share/wallpapers") (builtins.head homeCustom.home.packages).installPhase;
        assert pkgs.lib.hasInfix (builtins.unsafeDiscardStringContext "${./share/wallpapers/KaltsitMedicalGreen/contents/images/3840x2160.jpg}") (builtins.head homePoster.home.packages).installPhase;
        assert motion ? override;
        assert (motion.override { videoFile = ./LICENSE; }).version == motion.version;
        pkgs.runCommand "kaltsit-home-module-check" { } "echo 'Home Manager motion assertions passed' > $out";
      app = {
        type = "app";
        program = "${theme}/bin/kaltsit-theme";
        meta.description = theme.meta.description;
      };
    in {
      packages.${system} = {
        default = theme;
        kaltsit-theme = theme;
        kaltsit-motion = motion;
        kaltsit-sddm = sddmTheme;
        # Optional input for native greeter previews in a private compositor.
        preview-wakeup = pkgs.callPackage ./tests/preview-wakeup.nix { };
      };

      apps.${system} = {
        default = app;
        kaltsit-theme = app;
      };

      homeManagerModules.default = import ./home-manager.nix;
      checks.${system} = { inherit theme motion; home-module = homeModuleCheck; sddm = sddmTheme; };
      devShells.${system}.default = pkgs.mkShell {
        packages = [ (pkgs.python3.withPackages (packages: [ packages.pillow ])) ];
        PYTHONDONTWRITEBYTECODE = "1";
      };
    };
}
