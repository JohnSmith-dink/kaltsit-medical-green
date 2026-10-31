{ lib, stdenvNoCC, makeWrapper, python3, dbus, systemd, kdePackages }:

let
  python = python3.withPackages (packages: [ packages.pillow ]);
in
stdenvNoCC.mkDerivation {
  pname = "kaltsit-theme";
  version = "1.1.0-dev.2";
  src = lib.cleanSourceWith {
    src = ./.;
    filter = path: type:
      let name = baseNameOf path;
      in lib.cleanSourceFilter path type
        && !(builtins.elem name [ "__pycache__" "dist" "build" "result" ])
        && !(lib.hasPrefix "result-" name)
        && !(lib.hasSuffix ".pyc" name);
  };
  nativeBuildInputs = [ makeWrapper ];
  dontBuild = true;
  doCheck = true;

  checkPhase = ''
    runHook preCheck
    PYTHONDONTWRITEBYTECODE=1 ${python}/bin/python3 -m unittest discover -s tests -v
    runHook postCheck
  '';

  installPhase = ''
    runHook preInstall
    mkdir -p "$out/share" "$out/libexec" "$out/bin" "$out/share/doc/kaltsit-theme"
    cp -a share/. "$out/share/"
    cp -a docs previews "$out/share/doc/kaltsit-theme/"
    cp -a LICENSES "$out/share/doc/kaltsit-theme/"
    cp README.md README.en.md LICENSE CREDITS.md CHANGELOG.md "$out/share/doc/kaltsit-theme/"
    cp tools/kaltsit_theme.py "$out/libexec/kaltsit_theme.py"
    makeWrapper ${python}/bin/python3 "$out/bin/kaltsit-theme" \
      --add-flags "$out/libexec/kaltsit_theme.py" \
      --add-flags "--data-dir $out/share" \
      --suffix PATH : ${lib.makeBinPath [ dbus systemd kdePackages.kconfig kdePackages.plasma-workspace kdePackages.qttools ]} \
      --prefix XDG_DATA_DIRS : "$out/share:${kdePackages.breeze}/share:${kdePackages.breeze-icons}/share:${kdePackages.breeze-gtk}/share"
    runHook postInstall
  '';

  meta = {
    description = "Kal'tsit Medical Green theme for KDE Plasma 6, with explicit apply and restore";
    platforms = [ "x86_64-linux" ];
    # Code and bundled assets have different licenses. Existing character
    # artwork and cursor assets retain their original rights; see LICENSES
    # and CREDITS.md. The complete distribution is not an all-free package.
    license = lib.licenses.unfree;
    mainProgram = "kaltsit-theme";
  };
}
