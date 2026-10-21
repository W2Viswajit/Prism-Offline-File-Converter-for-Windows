param([Parameter(Mandatory=$true)][string]$Compiler)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$dist = Join-Path $projectRoot 'dist'
$build = Join-Path $projectRoot 'build'
& $python -m PyInstaller --noconfirm --distpath $dist --workpath $build (Join-Path $PSScriptRoot 'Prism.spec')
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed; no installer was compiled.' }
& $Compiler "/DBuildDir=$dist\Prism" "/DOutputDir=$dist" (Join-Path $PSScriptRoot 'Prism.iss')
if ($LASTEXITCODE -ne 0) { throw 'Inno Setup compilation failed.' }
Write-Output "Installer: $dist\Prism-0.1.3-Setup-x64.exe"
