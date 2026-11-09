{ lib, stdenvNoCC, python3 }:

stdenvNoCC.mkDerivation {
  pname = "kaltsit-sddm";
  version = "1.5.0";
  src = ./sddm;
  nativeBuildInputs = [ python3 ];
  buildPhase = ''
    python3 build-palette.py ${./share/color-schemes/KaltsitMedicalGreen.colors} Palette.js
  '';
  installPhase = ''
    theme="$out/share/sddm/themes/KaltsitMedicalGreen"
    mkdir -p "$theme" "$out/share/doc/kaltsit-sddm"
    cp Main.qml metadata.desktop theme.conf Palette.js "$theme/"
    cp ${./share/wallpapers/KaltsitMedicalGreen/contents/images/3840x2160.jpg} "$theme/background.jpg"
    cp ${./CREDITS.md} "$out/share/doc/kaltsit-sddm/CREDITS.md"
    cp -r ${./LICENSES} "$out/share/doc/kaltsit-sddm/LICENSES"
    cp ${./LICENSE} "$out/share/doc/kaltsit-sddm/LICENSE"
  '';
  meta = {
    description = "Experimental opt-in Medical Green SDDM theme (Qt 6)";
    platforms = [ "x86_64-linux" ];
    # The code is MIT; the existing wallpaper retains separate rights.
    # This complete package is not all-free. See unchanged CREDITS and LICENSES.
    license = lib.licenses.unfree;
  };
}
