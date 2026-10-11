param(
	[string]$OutputDirectory = ""
)

Add-Type -AssemblyName System.Drawing

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
	$OutputDirectory = Join-Path $repoRoot "frontend\apps\poc\static\assets\sprites\gardenToken"
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

$ink = [System.Drawing.ColorTranslator]::FromHtml("#294221")
$shadow = [System.Drawing.ColorTranslator]::FromHtml("#7B5727")
$ochre = [System.Drawing.ColorTranslator]::FromHtml("#D79A31")
$gold = [System.Drawing.ColorTranslator]::FromHtml("#F4CA56")
$highlight = [System.Drawing.ColorTranslator]::FromHtml("#FFF0A6")
$leaf = [System.Drawing.ColorTranslator]::FromHtml("#4F8B3E")
$leafLight = [System.Drawing.ColorTranslator]::FromHtml("#83B94C")
$center = [System.Drawing.ColorTranslator]::FromHtml("#70421D")

$inkPen = [System.Drawing.Pen]::new($ink, 8)
$innerPen = [System.Drawing.Pen]::new($shadow, 5)
$detailPen = [System.Drawing.Pen]::new($ink, 6)
$highlightPen = [System.Drawing.Pen]::new($highlight, 5)
$shadowBrush = [System.Drawing.SolidBrush]::new($shadow)
$ochreBrush = [System.Drawing.SolidBrush]::new($ochre)
$goldBrush = [System.Drawing.SolidBrush]::new($gold)
$leafBrush = [System.Drawing.SolidBrush]::new($leaf)
$leafLightBrush = [System.Drawing.SolidBrush]::new($leafLight)
$centerBrush = [System.Drawing.SolidBrush]::new($center)

for ($index = 0; $index -lt $frameCount; $index++) {
	$column = $index % $columns
	$row = [Math]::Floor($index / $columns)
	$centerX = ($column * $cellSize) + ($cellSize / 2)
	$centerY = ($row * $cellSize) + ($cellSize / 2)

	$angle = (2 * [Math]::PI * $index) / $frameCount
	$faceFactor = [Math]::Abs([Math]::Cos($angle))
	$tokenWidth = [Math]::Max(22, 190 * $faceFactor)
	$tokenHeight = 190
	$x = $centerX - ($tokenWidth / 2)
	$y = $centerY - ($tokenHeight / 2)

	$rimOffset = [Math]::Max(5, 13 * $faceFactor)
	$graphics.FillEllipse($shadowBrush, $x + $rimOffset, $y + 7, $tokenWidth, $tokenHeight)
	$graphics.FillEllipse($ochreBrush, $x, $y, $tokenWidth, $tokenHeight)
	$graphics.DrawEllipse($inkPen, $x, $y, $tokenWidth, $tokenHeight)

	if ($tokenWidth -gt 44) {
		$insetX = [Math]::Max(8, 15 * $faceFactor)
		$graphics.FillEllipse(
			$goldBrush,
			$x + $insetX,
			$y + 16,
			$tokenWidth - (2 * $insetX),
			$tokenHeight - 32
		)
		$graphics.DrawEllipse(
			$innerPen,
			$x + $insetX,
			$y + 16,
			$tokenWidth - (2 * $insetX),
			$tokenHeight - 32
		)
	}

	if ($tokenWidth -gt 104) {
		$markScale = [Math]::Min(1, $tokenWidth / 190)
		$petalWidth = 24 * $markScale
		$petalHeight = 53

		for ($petal = 0; $petal -lt 8; $petal++) {
			$petalAngle = (2 * [Math]::PI * $petal) / 8
			$petalX = $centerX + ([Math]::Cos($petalAngle) * 39 * $markScale) - ($petalWidth / 2)
			$petalY = $centerY + ([Math]::Sin($petalAngle) * 39) - ($petalHeight / 2)
			$graphics.FillEllipse($ochreBrush, $petalX, $petalY, $petalWidth, $petalHeight)
			$graphics.DrawEllipse($detailPen, $petalX, $petalY, $petalWidth, $petalHeight)
		}

		$coreSize = 49 * $markScale
		$graphics.FillEllipse($centerBrush, $centerX - ($coreSize / 2), $centerY - 25, $coreSize, 50)
		$graphics.DrawEllipse($detailPen, $centerX - ($coreSize / 2), $centerY - 25, $coreSize, 50)

		$leafWidth = 34 * $markScale
		$graphics.FillEllipse($leafBrush, $centerX + 29, $centerY + 31, $leafWidth, 22)
		$graphics.DrawEllipse($detailPen, $centerX + 29, $centerY + 31, $leafWidth, 22)
		$graphics.FillEllipse($leafLightBrush, $centerX - 62, $centerY + 33, $leafWidth, 20)
		$graphics.DrawEllipse($detailPen, $centerX - 62, $centerY + 33, $leafWidth, 20)
	}

	if ($tokenWidth -gt 34) {
		$graphics.DrawArc(
			$highlightPen,
			$x + [Math]::Max(7, 12 * $faceFactor),
			$y + 10,
			[Math]::Max(12, $tokenWidth - [Math]::Max(14, 24 * $faceFactor)),
			$tokenHeight - 20,
			205,
			82
		)
	}
}

$pngPath = Join-Path $outputPath "gardenToken.png"
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
		app = "Garden Bounty deterministic token atlas generator"
		version = "1.0"
		image = "gardenToken.png"
		format = "RGBA8888"
		size = [ordered]@{ w = $atlasWidth; h = $atlasHeight }
		scale = "1"
	}
}

$jsonPath = Join-Path $outputPath "gardenToken.json"
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
$leafBrush.Dispose()
$leafLightBrush.Dispose()
$centerBrush.Dispose()

Write-Output "Generated $pngPath"
Write-Output "Generated $jsonPath"
