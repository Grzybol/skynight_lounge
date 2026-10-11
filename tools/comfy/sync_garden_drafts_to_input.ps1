param(
    [Parameter(Mandatory = $true)]
    [string]$ComfyOutputDirectory,
    [Parameter(Mandatory = $true)]
    [string]$ComfyInputDirectory
)

$ErrorActionPreference = 'Stop'
$resolvedOutput = (Resolve-Path -LiteralPath $ComfyOutputDirectory).Path
$resolvedInput = (Resolve-Path -LiteralPath $ComfyInputDirectory).Path
$source = Join-Path $resolvedOutput 'slot_garden\static_drafts'
$target = Join-Path $resolvedInput 'slot_garden\static_drafts'

if (-not (Test-Path -LiteralPath $source)) {
    throw "Garden draft output directory does not exist: $source"
}

New-Item -ItemType Directory -Path $target -Force | Out-Null
Get-ChildItem -LiteralPath $source -Filter '*_drawn_*.png' | ForEach-Object {
    $destination = Join-Path $target $_.Name
    Copy-Item -LiteralPath $_.FullName -Destination $destination -Force
    Write-Output $destination
}
