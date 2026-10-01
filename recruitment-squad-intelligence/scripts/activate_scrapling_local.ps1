$ErrorActionPreference = 'Stop'

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$SourceRoot = (Resolve-Path (Join-Path $ProjectRoot 'vendor\Scrapling-0.4.15')).Path
$PythonExe = Join-Path $ProjectRoot '.venv-scrapling\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $PythonExe)) {
    throw "Scrapling project interpreter not found: $PythonExe"
}

$SitePackages = (& $PythonExe -c "import site; print(site.getsitepackages()[0])").Trim()
$PthPath = Join-Path $SitePackages 'scrapling_local_source.pth'
$BootstrapLine = "import sys; sys.path.insert(0, r'$SourceRoot')"
Set-Content -LiteralPath $PthPath -Value $BootstrapLine -Encoding ascii

$Probe = & $PythonExe -c "import scrapling; print(scrapling.__version__); print(scrapling.__file__)"
Write-Output "Scrapling version: $($Probe[0])"
Write-Output "Scrapling source: $($Probe[1])"
if (-not $Probe[1].StartsWith($SourceRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'Scrapling did not load from the local source directory.'
}
