{ lib, stdenvNoCC, kdePackages, baseTheme, videoFile ? null, posterFile ? null }:

stdenvNoCC.mkDerivation {
  pname = "kaltsit-motion";
  version = "1.3.0";
  src = ./motion;
  dontBuild = true;
  propagatedUserEnvPkgs = [ kdePackages.qtmultimedia ];
  installPhase = ''
    mkdir -p "$out/share/plasma/wallpapers"
    cp -a wallpaper "$out/share/plasma/wallpapers/org.xinyan.kaltsit.medicalgreen.motion"
    mkdir -p "$out/share/wallpapers/KaltsitMedicalGreenMotion/contents/images"
    cp ${if posterFile != null then lib.escapeShellArg "${posterFile}" else
      "${baseTheme}/share/wallpapers/KaltsitMedicalGreen/contents/images/3840x2160.jpg"} \
      "$out/share/wallpapers/KaltsitMedicalGreenMotion/contents/images/poster.jpg"
    substituteInPlace "$out/share/plasma/wallpapers/org.xinyan.kaltsit.medicalgreen.motion/contents/ui/Defaults.js" \
      --replace-fail '@DEFAULT_VIDEO@' '${if videoFile == null then "" else "file://${videoFile}"}'
    # Make native QML imports discoverable through the installed profile.
    mkdir -p "$out/lib/qt-6/qml" "$out/lib/qt-6/plugins"
    ln -s ${kdePackages.qtmultimedia}/lib/qt-6/qml/QtMultimedia "$out/lib/qt-6/qml/QtMultimedia"
    ln -s ${kdePackages.qtmultimedia}/lib/qt-6/plugins/multimedia "$out/lib/qt-6/plugins/multimedia"
  '';
  meta = {
    description = "Optional silent local video wallpaper for Medical Green";
    platforms = [ "x86_64-linux" ];
    license = lib.licenses.unfree;
  };
}
