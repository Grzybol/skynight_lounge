param(
    [string]$AtlasPath = 'frontend/apps/poc/static/assets/sprites/symbolsStatic/symbolsStatic.png',
    [string]$BackgroundPath = 'frontend/apps/poc/static/assets/backgrounds/mine_base_drawn.png',
    [Parameter(Mandatory = $true)]
    [string]$ComfyInputDirectory
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$resolvedAtlas = (Resolve-Path -LiteralPath $AtlasPath).Path
$resolvedBackground = (Resolve-Path -LiteralPath $BackgroundPath).Path
$resolvedInput = (Resolve-Path -LiteralPath $ComfyInputDirectory).Path

$frames = [ordered]@{
    H1  = [System.Drawing.Rectangle]::new(0, 0, 200, 200)
    H2  = [System.Drawing.Rectangle]::new(200, 0, 200, 200)
    H3  = [System.Drawing.Rectangle]::new(400, 0, 200, 200)
    L1  = [System.Drawing.Rectangle]::new(200, 200, 200, 200)
    L2  = [System.Drawing.Rectangle]::new(400, 200, 200, 200)
    L3  = [System.Drawing.Rectangle]::new(600, 200, 200, 200)
    L4  = [System.Drawing.Rectangle]::new(0, 400, 200, 200)
    W   = [System.Drawing.Rectangle]::new(200, 400, 200, 200)
    S   = [System.Drawing.Rectangle]::new(600, 400, 200, 200)
    M2  = [System.Drawing.Rectangle]::new(0, 600, 200, 200)
    M4  = [System.Drawing.Rectangle]::new(200, 600, 200, 200)
    M5  = [System.Drawing.Rectangle]::new(400, 600, 200, 200)
    M7  = [System.Drawing.Rectangle]::new(600, 600, 200, 200)
    M10 = [System.Drawing.Rectangle]::new(0, 800, 200, 200)
}

$atlas = [System.Drawing.Image]::FromFile($resolvedAtlas)
try {
    foreach ($entry in $frames.GetEnumerator()) {
        $canvas = [System.Drawing.Bitmap]::new(1024, 1024)
        $graphics = [System.Drawing.Graphics]::FromImage($canvas)
        try {
            $graphics.Clear([System.Drawing.Color]::FromArgb(238, 238, 238))
            $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
            $destination = [System.Drawing.Rectangle]::new(112, 112, 800, 800)
            $graphics.DrawImage($atlas, $destination, $entry.Value, [System.Drawing.GraphicsUnit]::Pixel)
            $outputPath = Join-Path $resolvedInput "garden_$($entry.Key)_source.png"
            $canvas.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
            Write-Output $outputPath
        }
        finally {
            $graphics.Dispose()
            $canvas.Dispose()
        }
    }
}
finally {
    $atlas.Dispose()
}

$background = [System.Drawing.Image]::FromFile($resolvedBackground)
try {
    $backgroundOutput = Join-Path $resolvedInput 'garden_background_source.png'
    $background.Save($backgroundOutput, [System.Drawing.Imaging.ImageFormat]::Png)
    Write-Output $backgroundOutput
}
finally {
    $background.Dispose()
}
