{ pkgs }: {
  deps = [
    pkgs.playwright
    pkgs.python311Full
    pkgs.python311Packages.pip
    pkgs.python311Packages.fastapi
    pkgs.python311Packages.uvicorn
    pkgs.python311Packages.pymongo
    pkgs.python311Packages.openai
    pkgs.python311Packages.httpx
    pkgs.python311Packages.python-dotenv
    pkgs.python311Packages.pytz
  ];
}
