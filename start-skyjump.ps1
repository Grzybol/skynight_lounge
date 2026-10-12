# SkyJump local launcher. Called by START.bat. Keep this window open while playing.
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Frontend = Join-Path $Root 'frontend'
$App = Join-Path $Frontend 'apps\poc'
$PixiPkg = Join-Path $Frontend 'packages\pixi-svelte'
$PixiDist = Join-Path $PixiPkg 'dist\index.js'
$ViteCmd = Join-Path $Frontend 'node_modules\.bin\vite.cmd'
$ViteCache = Join-Path ([System.IO.Path]::GetTempPath()) 'slot-game-poc-vite-cache'
$PnpmHome = Join-Path $env:LOCALAPPDATA 'SkyJump'
$PnpmCmd = Join-Path $PnpmHome 'node_modules\.bin\pnpm.cmd'
$PnpmVersion = '10.5.0'
$UrlPath = '/dev-preview'
$PreferredPorts = @(3010, 4010)

function Write-Step($message) {
	Write-Host ""
	Write-Host "==> $message" -ForegroundColor Cyan
}

function Fail($message) {
	Write-Host ""
	Write-Host $message -ForegroundColor Red
	Write-Host ""
	Write-Host "Zrob zrzut tego okna i wyslij go osobie, ktora Ci przekazala gre." -ForegroundColor Yellow
	exit 1
}

function Add-NodeToPath {
	$candidates = @(
		"$env:ProgramFiles\nodejs",
		"${env:ProgramFiles(x86)}\nodejs",
		"$env:LOCALAPPDATA\Programs\nodejs"
	)
	foreach ($dir in $candidates) {
		if (Test-Path (Join-Path $dir 'node.exe')) {
			$env:Path = "$dir;$env:Path"
			return
		}
	}
}

function Get-NodeExe {
	$cmd = Get-Command node -ErrorAction SilentlyContinue
	if ($cmd) { return $cmd.Source }
	Add-NodeToPath
	$cmd = Get-Command node -ErrorAction SilentlyContinue
	if ($cmd) { return $cmd.Source }
	return $null
}

function Test-PortFree([int]$port) {
	try {
		$listener = [System.Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, $port)
		$listener.Start()
		$listener.Stop()
		return $true
	} catch {
		return $false
	}
}

function Test-GameUp([int]$port) {
	try {
		$res = Invoke-WebRequest -Uri "http://127.0.0.1:$port$UrlPath" -UseBasicParsing -TimeoutSec 2
		return $res.StatusCode -ge 200 -and $res.StatusCode -lt 500
	} catch {
		return $false
	}
}

function Open-Game([int]$port) {
	$url = "http://localhost:$port$UrlPath"
	Write-Host "Otwieram gre: $url" -ForegroundColor Green
	Start-Process $url | Out-Null
}

function Test-PixiBuilt {
	return (Test-Path -LiteralPath $PixiDist)
}

function Test-ViteInstalled {
	return (Test-Path -LiteralPath $ViteCmd)
}

function Get-ListenPids([int]$port) {
	$ids = @()
	try {
		$ids = @(
			Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction Stop |
				Select-Object -ExpandProperty OwningProcess -Unique
		)
	} catch {
		$escaped = [regex]::Escape([string]$port)
		netstat -ano | ForEach-Object {
			if ($_ -match "[:.]$escaped\s+\S+\s+\S+\s+LISTENING\s+(\d+)") {
				$ids += [int]$Matches[1]
			}
		}
	}
	return @($ids | Where-Object { $_ -gt 4 } | Select-Object -Unique)
}

function Stop-ListenPort([int]$port) {
	foreach ($procId in (Get-ListenPids $port)) {
		try {
			Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
		} catch { }
	}
	Start-Sleep -Milliseconds 400
}

function Get-PnpmPath {
	# Never call npm/npx from frontend/: Node 24 npm rejects this repo's pnpm .npmrc.
	if (Test-Path -LiteralPath $PnpmCmd) { return $PnpmCmd }

	$npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
	if (-not $npm) { $npm = Get-Command npm -ErrorAction SilentlyContinue }
	if (-not $npm) { Fail "Nie znalazlem npm (powinien byc razem z Node.js)." }

	Write-Step "Pobieram pnpm $PnpmVersion (jednorazowo, potrzebny internet)..."
	New-Item -ItemType Directory -Force -Path $PnpmHome | Out-Null
	$here = Get-Location
	try {
		# Install outside the repo so npm never reads frontend/.npmrc.
		Set-Location -LiteralPath $PnpmHome
		$oldEap = $ErrorActionPreference
		$ErrorActionPreference = 'Continue'
		& $npm.Source install "pnpm@$PnpmVersion" --no-fund --no-audit
		$code = $LASTEXITCODE
		$ErrorActionPreference = $oldEap
		if ($code -ne 0 -or -not (Test-Path -LiteralPath $PnpmCmd)) {
			throw "npm install pnpm exit $code"
		}
	} catch {
		Fail @"
Nie moge pobrac pnpm.
Sprawdz internet i kliknij START.bat jeszcze raz.
Szczegoly: $($_.Exception.Message)
"@
	} finally {
		Set-Location -LiteralPath $here
	}
	return $PnpmCmd
}

function Invoke-Pnpm {
	param([Parameter(ValueFromRemainingArguments = $true)][string[]]$PnpmArgs)
	# Never call npm/npx from frontend/: Node 24's npm rejects this repo's pnpm .npmrc.
	$exe = Get-PnpmPath
	$oldEap = $ErrorActionPreference
	$ErrorActionPreference = 'Continue'
	# Out-Host keeps pnpm logs visible without turning them into the return code.
	& $exe @PnpmArgs | Out-Host
	$code = $LASTEXITCODE
	$ErrorActionPreference = $oldEap
	if ($null -eq $code) { return 0 }
	return $code
}

function Install-Frontend {
	Write-Step "Sprawdzam / dopinam zaleznosci (kolejne uruchomienie jest krotsze)..."
	Set-Location -LiteralPath $Frontend
	$code = Invoke-Pnpm install
	Set-Location -LiteralPath $Root
	if ($code -ne 0) {
		Fail "Instalacja zaleznosci nie wyszla (kod $code). Sprawdz internet i sprobuj ponownie."
	}
	if (-not (Test-ViteInstalled)) {
		Fail "Brak Vite po instalacji. Usun folder frontend\node_modules i kliknij START.bat jeszcze raz."
	}
}

function Build-PixiSvelte {
	if (Test-PixiBuilt) { return }
	Write-Step "Buduje silnik Pixi (pixi-svelte). To jest normalne przy pierwszym starcie..."
	if (Test-Path -LiteralPath $ViteCache) {
		Remove-Item -LiteralPath $ViteCache -Recurse -Force -ErrorAction SilentlyContinue
	}
	Set-Location -LiteralPath $Frontend
	$code = Invoke-Pnpm --filter pixi-svelte build
	Set-Location -LiteralPath $Root
	if ($code -ne 0 -or -not (Test-PixiBuilt)) {
		Fail "Nie udalo sie zbudowac pixi-svelte. Sprawdz internet i kliknij START.bat jeszcze raz."
	}
}

function Sync-SvelteKit {
	$sk = Join-Path $Frontend 'node_modules\.bin\svelte-kit.cmd'
	if (-not (Test-Path -LiteralPath $sk)) { return }
	Write-Step "Przygotowuje SvelteKit..."
	Set-Location -LiteralPath $App
	$oldEap = $ErrorActionPreference
	$ErrorActionPreference = 'Continue'
	& $sk sync | Out-Null
	$ErrorActionPreference = $oldEap
	Set-Location -LiteralPath $Root
}

Set-Location -LiteralPath $Root
Write-Host ""
Write-Host "  SKYJUMP  -  lokalny tester" -ForegroundColor White
Write-Host "  Nie zamykaj tego okna, dopoki grasz." -ForegroundColor DarkGray

$node = Get-NodeExe
if (-not $node) {
	Write-Host ""
	Write-Host "Brak Node.js. Otwieram strone instalacji." -ForegroundColor Yellow
	Start-Process 'https://nodejs.org/en/download' | Out-Null
	Fail @"
Zainstaluj Node.js LTS (przycisk na srodku strony):
  1. Pobierz instalator Windows
  2. Klikaj Next (zostaw 'Add to PATH')
  3. ZAMKNIJ to okno i kliknij START.bat jeszcze raz
"@
}

Write-Step "Node.js: $(& $node -v)"

if (-not (Test-Path -LiteralPath $Frontend)) {
	Fail "Nie widze folderu frontend. Uruchom START.bat z katalogu gry, nie z Pulpitu ze skrotu do innego miejsca."
}

if (Test-PixiBuilt) {
	foreach ($port in $PreferredPorts) {
		if (Test-GameUp $port) {
			Write-Step "Gra juz dziala na porcie $port."
			Open-Game $port
			Write-Host "Mozesz zamknac to okno." -ForegroundColor DarkGray
			exit 0
		}
	}
} else {
	foreach ($port in $PreferredPorts) {
		if (-not (Test-PortFree $port)) {
			Write-Step "Port $port trzyma niedokonczony start. Zamykam go..."
			Stop-ListenPort $port
		}
	}
}

if (-not (Test-ViteInstalled) -or -not (Test-PixiBuilt)) {
	Install-Frontend
}
Build-PixiSvelte
Sync-SvelteKit

foreach ($port in $PreferredPorts) {
	if (-not (Test-PortFree $port) -and -not (Test-GameUp $port)) {
		Write-Step "Port $port jest zajety przez stary proces. Zamykam go..."
		Stop-ListenPort $port
	}
}

$port = $null
foreach ($candidate in $PreferredPorts) {
	if (Test-PortFree $candidate) {
		$port = $candidate
		break
	}
	if ((Test-GameUp $candidate) -and (Test-PixiBuilt)) {
		Open-Game $candidate
		exit 0
	}
}
if (-not $port) {
	Fail "Porty 3010 i 4010 sa zajete. Zamknij inne okna 'SkyJump' / 'vite' i sprobuj ponownie."
}

Write-Step "Startuje gre na porcie $port..."
$opener = $null
try {
	$opener = Start-Job -ScriptBlock {
		param($url)
		Start-Sleep -Seconds 6
		for ($i = 0; $i -lt 30; $i++) {
			try {
				Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2 | Out-Null
				Start-Process $url | Out-Null
				return
			} catch {
				Start-Sleep -Seconds 2
			}
		}
	} -ArgumentList "http://127.0.0.1:$port$UrlPath"
} catch {
	$opener = $null
}

Write-Host "Przegladarka otworzy sie sama, gdy gra bedzie gotowa." -ForegroundColor Green
Write-Host "Adres: http://localhost:$port$UrlPath" -ForegroundColor Green
Write-Host ""

Set-Location -LiteralPath $App
& $ViteCmd --host 0.0.0.0 --port $port
$code = $LASTEXITCODE
if ($opener) {
	try { Stop-Job $opener -ErrorAction SilentlyContinue; Remove-Job $opener -Force -ErrorAction SilentlyContinue } catch { }
}
if ($code -ne 0) { exit $code }
