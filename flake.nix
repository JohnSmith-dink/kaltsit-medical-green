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
      nixosBase = nixpkgs.lib.nixosSystem {
        inherit system;
        modules = [ ./nixos-module.nix {
          nixpkgs.pkgs = pkgs;
          system.stateVersion = "26.05";
        } ];
      };
      evalNixos = settings: (nixosBase.extendModules { modules = [ settings ]; }).config;
      nixosOff = nixosBase.config;
      nixosOn = evalNixos { programs.kaltsit-sddm.enable = true; };
      nixosPlasma = evalNixos {
        programs.kaltsit-sddm.enable = true;
        services.desktopManager.plasma6.enable = true;
      };
      nixosCustom = evalNixos {
        programs.kaltsit-sddm.enable = true;
        services.desktopManager.plasma6.enable = true;
        services.displayManager.sddm.theme = "existing-user-theme";
      };
      nixosDisabledCustom = evalNixos { services.displayManager.sddm.theme = "existing-user-theme"; };
      # An existing text fixture is sufficient for option evaluation; no private font enters the flake.
      nixosFont = evalNixos { programs.kaltsit-sddm = { enable = true; fontFile = ./LICENSE; }; };
      nixosFontDisabled = evalNixos { programs.kaltsit-sddm.fontFile = ./LICENSE; };
      nixosModuleCheck = assert !nixosOff.programs.kaltsit-sddm.enable;
        assert nixosOff.programs.kaltsit-sddm.fontFile == null;
        assert nixosOn.programs.kaltsit-sddm.fontFile == null;
        assert nixosOn.fonts.packages == nixosOff.fonts.packages;
        assert nixosFontDisabled.fonts.packages == nixosOff.fonts.packages;
        assert builtins.length nixosFont.fonts.packages == builtins.length nixosOff.fonts.packages + 1;
        assert builtins.any (p: (p.fontSource or null) == (builtins.path { path = ./LICENSE; name = "OPPO-Sans-4.0.ttf"; }) && p.preferLocalBuild && !p.allowSubstitutes) nixosFont.fonts.packages;
        assert nixosOff.services.displayManager.sddm.theme == "";
        assert nixosOff.services.displayManager.sddm.extraPackages == [ ];
        assert !(builtins.any (p: (p.pname or "") == "kaltsit-sddm") nixosOff.environment.systemPackages);
        assert nixosOn.services.displayManager.sddm.theme == "KaltsitMedicalGreen";
        assert !nixosOn.services.displayManager.sddm.enable;
        assert nixosOn.services.displayManager.sddm.extraPackages == [ ];
        assert builtins.elem sddmTheme nixosOn.environment.systemPackages;
        assert nixosPlasma.services.displayManager.sddm.theme == "KaltsitMedicalGreen";
        assert nixosCustom.services.displayManager.sddm.theme == "existing-user-theme";
        assert nixosDisabledCustom.services.displayManager.sddm.theme == "existing-user-theme";
        pkgs.runCommand "kaltsit-nixos-module-check" { } "echo 'SDDM NixOS module assertions passed' > $out";
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
      nixosModules.default = import ./nixos-module.nix;
      checks.${system} = {
        inherit theme motion;
        home-module = homeModuleCheck;
        sddm = sddmTheme;
        nixos-module = nixosModuleCheck;
      };
      devShells.${system}.default = pkgs.mkShell {
        packages = [ (pkgs.python3.withPackages (packages: [ packages.pillow ])) ];
        PYTHONDONTWRITEBYTECODE = "1";
      };
    };
}
