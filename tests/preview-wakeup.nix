{ lib, runCommand, pkg-config, qt6, stdenv }:

runCommand "kaltsit-isolated-greeter-preview" {
  nativeBuildInputs = [ pkg-config stdenv.cc ];
  buildInputs = [ qt6.qtbase qt6.qtdeclarative ];
  meta = {
    description = "Guarded wake-up for a native greeter running with --testing in private KWin";
    platforms = [ "x86_64-linux" ];
    license = lib.licenses.mit;
  };
} ''
  mkdir -p "$out/lib"
  c++ -std=c++17 -fPIC -shared ${./preview-wakeup.cpp} -o "$out/lib/kaltsit-preview-wakeup.so" $(pkg-config --cflags --libs Qt6Core Qt6Gui Qt6Quick)
''
