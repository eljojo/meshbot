{ pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python312;
  lib = pkgs.lib;

  # Fetching specific version of bleak
  bleak = python.pkgs.buildPythonPackage rec {
    pname = "bleak";
    version = "0.21.1";

    src = python.pkgs.fetchPypi {
      inherit pname version;
      sha256 = "sha256-7EoaJ3L7MVuZLLqhFTBwx+JpaKUrDicnA19EOhr1wY8";
      #sha256 = lib.fakeSha256;
    };

    format = "pyproject";
    nativeBuildInputs = [ pkgs.poetry python.pkgs.poetry-core ];

    propagatedBuildInputs = [
      python.pkgs.setuptools
      python.pkgs.wheel
      python.pkgs.pyserial
      python.pkgs.requests
      python.pkgs.dbus-fast
    ];

    meta = with pkgs.lib; {
      description = "Bluetooth Low Energy platform Agnostic Client for Python";
      homepage = "https://github.com/hbldh/bleak";
      license = licenses.mit;
    };
  };

  protobuf = pkgs.python312Packages.buildPythonPackage rec {
    pname = "protobuf";
    version = "5.26.0";

    src = pkgs.python312Packages.fetchPypi {
      inherit pname version;

      #sha256 = lib.fakeSha256;
      sha256 = "sha256-gvWHDXTJmt3+QVJ3e9+BaCRLnPCsZfjszwRd36nYDZs";
    };

    preBuild = ''
      mkdir -p google/_upb
    '';

    propagatedBuildInputs = [
      pkgs.python312Packages.setuptools
      pkgs.python312Packages.wheel
    ];

    meta = with lib; {
      description = "Protocol Buffers - Google's data interchange format";
      homepage = "https://github.com/protocolbuffers/protobuf";
      license = licenses.bsd3;
    };
  };

  print_color = python.pkgs.buildPythonPackage rec {
    pname = "print-color";
    version = "0.4.6";

    src = pkgs.fetchFromGitHub {
      owner = "xy3";
      repo = "print-color";
      rev = "0b29d6f1931a741c6a8adeeb6c3b55681b26bf6c"; 
      sha256 = "sha256-Zmok898pDtRv65CKec3viXTnzB3rPSeGQXfbxSDR5eI"; 
      #sha256 = lib.fakeSha256;
    };

    format = "pyproject";
    propagatedBuildInputs = [
      python.pkgs.setuptools
    ];

    nativeBuildInputs = [
      python.pkgs.pip
      python.pkgs.wheel
      python.pkgs.pytest
      pkgs.poetry python.pkgs.poetry-core
    ];

    doCheck = false; # Disable check phase as we install pytest manually

    meta = with lib; {
      description = "A simple color printing library for Python";
      homepage = "https://pypi.org/project/print-color/";
      license = licenses.mit;
    };
  };

  meshtastic = python.pkgs.buildPythonApplication rec {
    pname = "meshtastic";
    version = "2.3.14";

    src = python.pkgs.fetchPypi {
      inherit pname version;
      sha256 = "sha256-dnhe7m3+uMlf5QHhWUTJKA6N2rZpBlyEi/BOzSnGcUw";
    };

    format = "pyproject";
    nativeBuildInputs = [ pkgs.poetry python.pkgs.poetry-core ];

    propagatedBuildInputs = [
      python.pkgs.setuptools
      python.pkgs.wheel
      bleak  # Use specific version of bleak
      python.pkgs.dotmap
      python.pkgs.pexpect
      protobuf 
      python.pkgs.pyparsing
      python.pkgs.pypubsub
      python.pkgs.pyqrcode
      python.pkgs.pyserial
      python.pkgs.pyyaml
      python.pkgs.requests
      python.pkgs.tabulate
      python.pkgs.webencodings
      print_color
    ];

    meta = with pkgs.lib; {
      description = "Meshtastic project for mesh networking.";
      homepage = "https://meshtastic.org";
      license = licenses.gpl3;
    };
  };
in
pkgs.mkShell {
  buildInputs = [
    python
    meshtastic
    pkgs.sqlite
    pkgs.python312Packages.packaging
  ];
}
