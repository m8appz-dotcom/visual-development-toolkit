$ProgressPreference='SilentlyContinue'
$ErrorActionPreference='Stop'
$runtimeRoot='D:\visual-development-toolkit'
$cacheSource=Join-Path $env:USERPROFILE '.codex\plugins\cache\modding-lab'
$cacheTarget=Join-Path $runtimeRoot 'codex-plugin-cache\modding-lab'
if ([IO.Path]::GetFullPath($cacheSource) -ne 'C:\Users\kenny\.codex\plugins\cache\modding-lab') { throw 'Unexpected source cache path' }
if (-not [IO.Path]::GetFullPath($cacheTarget).StartsWith('D:\visual-development-toolkit\')) { throw 'Unexpected destination cache path' }
$bytes=0;$files=0
if (Test-Path -LiteralPath $cacheSource) {
    $sourceItem=Get-Item -LiteralPath $cacheSource -Force
    if ($sourceItem.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Existing cache link requires separate inspection' }
    if (Test-Path -LiteralPath $cacheTarget) { throw 'Destination already exists; preserve it and inspect before retry' }
    $entries=Get-ChildItem -LiteralPath $cacheSource -Recurse -Force
    if ($entries | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }) { throw 'Cache contains links' }
    $originals=@($entries | Where-Object { -not $_.PSIsContainer })
    $bytes=($originals | Measure-Object Length -Sum).Sum;$files=$originals.Count
    New-Item -ItemType Directory -Force -Path (Split-Path $cacheTarget -Parent) | Out-Null
    Copy-Item -LiteralPath $cacheSource -Destination $cacheTarget -Recurse -Force
    foreach ($file in $originals) {
        $relative=$file.FullName.Substring($cacheSource.Length).TrimStart('\')
        $copy=Join-Path $cacheTarget $relative
        if ((Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $copy -Algorithm SHA256).Hash) { throw 'Cache copy verification failed' }
    }
    # Only the exact, verified task-specific cache is removed after preserving its copy.
    if ((Resolve-Path -LiteralPath $cacheSource).Path -ne 'C:\Users\kenny\.codex\plugins\cache\modding-lab') { throw 'Resolved source changed' }
    Remove-Item -LiteralPath $cacheSource -Recurse -Force
} else {
    New-Item -ItemType Directory -Force -Path $cacheTarget | Out-Null
}
New-Item -ItemType Junction -Path $cacheSource -Target $cacheTarget | Out-Null
$link=Get-Item -LiteralPath $cacheSource -Force
if (-not ($link.Attributes -band [IO.FileAttributes]::ReparsePoint) -or $link.Target -ne $cacheTarget) { throw 'Cache junction verification failed' }
[ordered]@{source=$cacheSource;target=$cacheTarget;files=$files;bytes=$bytes;copyVerified=$true;junctionVerified=$true} | ConvertTo-Json | Set-Content -Encoding utf8 -LiteralPath ($runtimeRoot+'\reports\cache-migration.json')
$env:TEMP=$runtimeRoot+'\temp';$env:TMP=$env:TEMP
Set-Location -LiteralPath $runtimeRoot
$install=codex plugin add game-modding-toolkit@modding-lab --json
if ($LASTEXITCODE -ne 0) { throw 'Plugin install failed after cache relocation' }
$install | Set-Content -Encoding utf8 -LiteralPath ($runtimeRoot+'\logs\plugin-install.json')
$install
