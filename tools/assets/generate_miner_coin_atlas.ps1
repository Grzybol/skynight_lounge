param(
	[string]$OutputDirectory = ""
)

Add-Type -AssemblyName System.Drawing

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
	$OutputDirectory = Join-Path $repoRoot "frontend\apps\poc\static\assets\sprites\minerCoin"
}

$outputPath = [System.IO.Path]::GetFullPath($OutputDirectory)
[System.IO.Directory]::CreateDirectory($outputPath) | Out-Null

$cellSize = 256
$columns = 6
$rows = 2
$frameCount = 12
$atlasWidth = $cellSize * $columns
$atlasHeight = $cellSize * $rows

$bitmap = [System.Drawing.Bitmap]::new(
	$atlasWidth,
	$atlasHeight,
	[System.Drawing.Imaging.PixelFormat]::Format32bppArgb
)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$graphics.Clear([System.Drawing.Color]::Transparent)

$ink = [System.Drawing.ColorTranslator]::FromHtml("#3A1C22")
$shadow = [System.Drawing.ColorTranslator]::FromHtml("#6E351F")
$ochre = [System.Drawing.ColorTranslator]::FromHtml("#D98B2B")
$gold = [System.Drawing.ColorTranslator]::FromHtml("#F2C35B")
$highlight = [System.Drawing.ColorTranslator]::FromHtml("#FFE7A0")

$inkPen = [System.Drawing.Pen]::new($ink, 8)
$innerPen = [System.Drawing.Pen]::new($shadow, 5)
$detailPen = [System.Drawing.Pen]::new($ink, 7)
$highlightPen = [System.Drawing.Pen]::new($highlight, 5)
$shadowBrush = [System.Drawing.SolidBrush]::new($shadow)
$ochreBrush = [System.Drawing.SolidBrush]::new($ochre)
$goldBrush = [System.Drawing.SolidBrush]::new($gold)

for ($index = 0; $index -lt $frameCount; $index++) {
	$column = $index % $columns
	$row = [Math]::Floor($index / $columns)
	$centerX = ($column * $cellSize) + ($cellSize / 2)
	$centerY = ($row * $cellSize) + ($cellSize / 2)

	$angle = (2 * [Math]::PI * $index) / $frameCount
	$faceFactor = [Math]::Abs([Math]::Cos($angle))
	$coinWidth = [Math]::Max(22, 190 * $faceFactor)
	$coinHeight = 190
	$x = $centerX - ($coinWidth / 2)
	$y = $centerY - ($coinHeight / 2)

	$rimOffset = [Math]::Max(5, 13 * $faceFactor)
	$graphics.FillEllipse($shadowBrush, $x + $rimOffset, $y + 7, $coinWidth, $coinHeight)
	$graphics.FillEllipse($ochreBrush, $x, $y, $coinWidth, $coinHeight)
	$graphics.DrawEllipse($inkPen, $x, $y, $coinWidth, $coinHeight)

	if ($coinWidth -gt 44) {
		$insetX = [Math]::Max(8, 15 * $faceFactor)
		$graphics.FillEllipse(
			$goldBrush,
			$x + $insetX,
			$y + 16,
			$coinWidth - (2 * $insetX),
			$coinHeight - 32
		)
		$graphics.DrawEllipse(
			$innerPen,
			$x + $insetX,
			$y + 16,
			$coinWidth - (2 * $insetX),
			$coinHeight - 32
		)
	}

	if ($coinWidth -gt 96) {
		$markScale = [Math]::Min(1, $coinWidth / 190)
		$handleHalf = 47 * $markScale
		$headHalf = 34 * $markScale
		$graphics.DrawLine(
			$detailPen,
			$centerX - $handleHalf,
			$centerY + 42,
			$centerX + $handleHalf,
			$centerY - 42
		)
		$graphics.DrawLine(
			$detailPen,
			$centerX + $handleHalf,
			$centerY + 42,
			$centerX - $handleHalf,
			$centerY - 42
		)
		$graphics.DrawArc(
			$detailPen,
			$centerX - $headHalf - 20,
			$centerY - 64,
			($headHalf * 2) + 40,
			42,
			195,
			150
		)
		$graphics.DrawArc(
			$detailPen,
			$centerX - $headHalf - 20,
			$centerY - 64,
			($headHalf * 2) + 40,
			42,
			15,
			150
		)
	}

	if ($coinWidth -gt 34) {
		$graphics.DrawArc(
			$highlightPen,
			$x + [Math]::Max(7, 12 * $faceFactor),
			$y + 10,
			[Math]::Max(12, $coinWidth - [Math]::Max(14, 24 * $faceFactor)),
			$coinHeight - 20,
			205,
			82
		)
	}
}

$pngPath = Join-Path $outputPath "minerCoin.png"
$bitmap.Save($pngPath, [System.Drawing.Imaging.ImageFormat]::Png)

$frames = [ordered]@{}
for ($index = 0; $index -lt $frameCount; $index++) {
	$name = "{0}.png" -f ($index + 1)
	$frames[$name] = [ordered]@{
		frame = [ordered]@{
			x = ($index % $columns) * $cellSize
			y = [Math]::Floor($index / $columns) * $cellSize
			w = $cellSize
			h = $cellSize
		}
		rotated = $false
		trimmed = $false
		spriteSourceSize = [ordered]@{ x = 0; y = 0; w = $cellSize; h = $cellSize }
		sourceSize = [ordered]@{ w = $cellSize; h = $cellSize }
	}
}

$atlas = [ordered]@{
	frames = $frames
	animations = [ordered]@{
		coin = 1..$frameCount | ForEach-Object { "$_.png" }
	}
	meta = [ordered]@{
		app = "Miner's Fortune deterministic atlas generator"
		version = "1.0"
		image = "minerCoin.png"
		format = "RGBA8888"
		size = [ordered]@{ w = $atlasWidth; h = $atlasHeight }
		scale = "1"
	}
}

$jsonPath = Join-Path $outputPath "minerCoin.json"
$atlas | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $jsonPath -Encoding utf8

$graphics.Dispose()
$bitmap.Dispose()
$inkPen.Dispose()
$innerPen.Dispose()
$detailPen.Dispose()
$highlightPen.Dispose()
$shadowBrush.Dispose()
$ochreBrush.Dispose()
$goldBrush.Dispose()

Write-Output "Generated $pngPath"
Write-Output "Generated $jsonPath"
