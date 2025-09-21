{ pkgs }: {
  deps = [
    pkgs.python311Full
    pkgs.python311Packages.pip
    pkgs.uv # if available; Replit often supports uv
    pkgs.ffmpeg
  ];
}
