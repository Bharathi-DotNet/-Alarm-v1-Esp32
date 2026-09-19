$ErrorActionPreference='Stop'
$project=Split-Path $PSScriptRoot -Parent
$env:EM_CONFIG=Join-Path $PSScriptRoot 'em-config.py'
New-Item -ItemType Directory -Force -Path (Join-Path $project '.pio\host') | Out-Null
& 'C:\Users\Bharathi\.platformio\penv\Scripts\python.exe' 'C:\Program Files\dotnet\packs\Microsoft.NET.Runtime.Emscripten.3.1.56.Sdk.win-x64\9.0.5\tools\emscripten\em++.py' -std=c++17 "-I$PSScriptRoot\stubs" "$PSScriptRoot\lifecycle_tests.cpp" -o "$project\.pio\host\lifecycle_tests.js" -sENVIRONMENT=node -sSINGLE_FILE=1
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
& 'C:\Program Files\nodejs\node.exe' "$project\.pio\host\lifecycle_tests.js"
exit $LASTEXITCODE
