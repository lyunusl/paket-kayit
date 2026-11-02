#requires -Version 5.1
<#
Paket Kayıt kurulumu - Developed by AugeLab. Copyright (c) 2026 AugeLab. MIT License (see LICENSE).

AugeLab Studio yoksa resmi kurulum dosyasını AugeLab sunucusundan indirir, SHA-256 ile doğrular
ve sessizce kurar. Ardından Paket Kayıt bloklarını ve senaryosunu yerleştirir, masaüstü
kısayollarını ekler ve Studio'yu açar. Lisans etkinleştirme kullanıcıya bırakılır.

  -DryRun  Hiçbir şey indirmeden ya da değiştirmeden yapılacakları listeler.
  -Yes     Studio kurulumu için onay sormaz.
#>
[CmdletBinding()]
param([switch]$DryRun, [switch]$Yes)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$config = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'studio-installer.json') -Raw | ConvertFrom-Json
$installDir = Join-Path $env:LOCALAPPDATA 'Programs\AugeLab Studio'
$blocksDir = Join-Path $env:APPDATA 'AugeLab Studio\marketplace\custom_blocks'
$docsDir = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'PaketKayit'
$desktop = [Environment]::GetFolderPath('Desktop')
$uiUrl = 'http://127.0.0.1:8080/'

function Step([string]$Text) { Write-Host ''; Write-Host ('> ' + $Text) -ForegroundColor Yellow }
function Info([string]$Text) { Write-Host ('  ' + $Text) }

function Find-Studio {
    $dirs = @($installDir)
    foreach ($base in @($env:LOCALAPPDATA, $env:ProgramFiles, ${env:ProgramFiles(x86)})) {
        if ($base) { $dirs += Join-Path $base 'Programs\AugeLab Studio'; $dirs += Join-Path $base 'AugeLab Studio' }
    }
    foreach ($hive in @('HKCU:', 'HKLM:')) {
        foreach ($view in @('Software', 'Software\WOW6432Node')) {
            $reg = Get-ItemProperty -LiteralPath "$hive\$view\Microsoft\Windows\CurrentVersion\Uninstall\AugeLab Studio" -ErrorAction SilentlyContinue
            if ($reg -and $reg.InstallLocation) { $dirs += $reg.InstallLocation }
        }
    }
    foreach ($dir in $dirs | Where-Object { $_ } | Select-Object -Unique) {
        $exe = Join-Path $dir $config.executable
        if (Test-Path -LiteralPath $exe -PathType Leaf) { return $exe }
    }
    return $null
}

# A failed install leaves the launcher behind without Studio's Python packages.
function Test-StudioComplete([string]$Exe) {
    return (Test-Path -LiteralPath (Join-Path (Split-Path -Parent $Exe) 'Python\Lib\site-packages\studio'))
}

# Studio's silent installer can only add the Visual C++ runtime when it runs elevated.
function Test-VCRuntime {
    $reg = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64' -ErrorAction SilentlyContinue
    return (($reg -and $reg.Installed -eq 1) -or (Test-Path -LiteralPath (Join-Path $env:windir 'System32\msvcp140.dll')))
}

# Downloads a Microsoft redistributable, checks Microsoft's signature and installs it elevated.
function Install-MicrosoftRedist([string]$Url, [string]$FileName, [string]$Label, [string]$Dll) {
    $cache = Join-Path $env:LOCALAPPDATA 'AugeLab\paket-kayit-setup'
    [void][IO.Directory]::CreateDirectory($cache)
    $file = Join-Path $cache $FileName
    Info "$Label indiriliyor..."
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $Url -OutFile $file -UseBasicParsing
    $sig = Get-AuthenticodeSignature -FilePath $file
    if ($sig.Status -ne 'Valid' -or $sig.SignerCertificate.Subject -notmatch 'O=Microsoft Corporation') {
        Remove-Item -LiteralPath $file -Force
        throw "$Label kurulum dosyası Microsoft imzalı değil. Hiçbir şey çalıştırılmadı."
    }
    Info 'Kuruluyor (Windows yönetici izni isteyecek, "Evet" deyin)...'
    try {
        $proc = Start-Process -FilePath $file -ArgumentList '/install /quiet /norestart' -Verb RunAs -PassThru -Wait
    } catch {
        throw "Yönetici izni verilmediği için $Label kurulamadı. Kurulumu tekrar çalıştırıp izin isteğine ""Evet"" deyin."
    }
    # 1638: a newer version is already installed; 3010: installed, restart recommended
    if ($proc.ExitCode -notin 0, 1638, 3010) { throw "$Label kurulumu $($proc.ExitCode) koduyla bitti." }
    if (-not (Test-Path -LiteralPath (Join-Path $env:windir "System32\$Dll"))) { throw "$Label kuruldu görünüyor ama $Dll bulunamadı." }
    Info "$Label kuruldu."
}

# Studio's own installer fails to add the Visual C++ runtime on a clean Windows, so install it first.
function Install-VCRuntime {
    Install-MicrosoftRedist 'https://aka.ms/vs/17/release/vc_redist.x64.exe' 'vc_redist.x64.exe' 'Microsoft Visual C++ çalışma zamanı' 'msvcp140.dll'
}

# zbar (pyzbar) is the barcode engine behind AugeLab's Barcode Reader block; current Studio installs lack it.
$pyzbarWheel = @{
    url    = 'https://files.pythonhosted.org/packages/0a/e2/1c6a8e94197612dbdfc51eab8dfb674168829885fac2c4f50ac8366c25ca/pyzbar-0.1.9-py2.py3-none-win_amd64.whl'
    sha256 = '13e3ee5a2f3a545204a285f41814d5c0db571967e8d4af8699a03afc55182a9c'
}

# Run in a separate process: with $ErrorActionPreference = 'Stop', a Python traceback on stderr would abort the setup.
function Test-Zbar([string]$Python) {
    $proc = Start-Process -FilePath $Python -ArgumentList '-I', '-c', '"import pyzbar.pyzbar"' -WindowStyle Hidden -PassThru -Wait
    return ($proc.ExitCode -eq 0)
}

function Install-Zbar([string]$Python) {
    # Studio ships pyzbar, but zbar's DLL needs the Visual C++ 2013 runtime, which a clean Windows lacks;
    # without it Studio cannot load pyzbar and drops its own Barcode Reader block as well.
    if (-not (Test-Path -LiteralPath (Join-Path $env:windir 'System32\msvcr120.dll'))) {
        Install-MicrosoftRedist 'https://aka.ms/highdpimfc2013x64enu' 'vcredist2013_x64.exe' 'Microsoft Visual C++ 2013 çalışma zamanı' 'msvcr120.dll'
        if (Test-Zbar $Python) { return }
    }
    $cache = Join-Path $env:LOCALAPPDATA 'AugeLab\paket-kayit-setup'
    [void][IO.Directory]::CreateDirectory($cache)
    $wheel = Join-Path $cache 'pyzbar-0.1.9-win_amd64.zip'
    Info 'zbar (pyzbar) indiriliyor...'
    Invoke-WebRequest -Uri $pyzbarWheel.url -OutFile $wheel -UseBasicParsing
    if ((Get-FileHash -LiteralPath $wheel -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pyzbarWheel.sha256) {
        Remove-Item -LiteralPath $wheel -Force
        throw 'pyzbar paketi doğrulanamadı (SHA-256 uyuşmuyor).'
    }
    $unpack = Join-Path $cache 'pyzbar-unpacked'
    if (Test-Path -LiteralPath $unpack) { Remove-Item -LiteralPath $unpack -Recurse -Force }
    Expand-Archive -LiteralPath $wheel -DestinationPath $unpack -Force
    $sitePackages = Join-Path (Split-Path -Parent $Python) 'Lib\site-packages'
    Copy-Item -Path (Join-Path $unpack '*') -Destination $sitePackages -Recurse -Force
}

function Test-StudioRunning([string]$Exe) {
    $dir = (Split-Path -Parent $Exe).TrimEnd('\') + '\'
    $procs = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.ExecutablePath -and $_.ExecutablePath.StartsWith($dir, [StringComparison]::OrdinalIgnoreCase) }
    return [bool]$procs
}

function Assert-Hash([string]$Path) {
    $stream = [IO.File]::OpenRead($Path)
    $sha = [Security.Cryptography.SHA256]::Create()
    try { $actual = [BitConverter]::ToString($sha.ComputeHash($stream)).Replace('-', '').ToLowerInvariant() }
    finally { $stream.Dispose(); $sha.Dispose() }
    if ($actual -ne $config.sha256) {
        throw 'Indirilen Studio kurulum dosyası doğrulanamadı (SHA-256 uyuşmuyor). Hiçbir şey çalıştırılmadı. Paket Kayıt paketinin güncel sürümünü indirin.'
    }
}

function Get-StudioInstaller {
    $uri = [Uri]$config.url
    if ($uri.Scheme -ne 'https' -or $uri.Host -ne 'studio-desktop-application.s3.eu-central-1.amazonaws.com') {
        throw 'Studio kurulum dosyası yalnızca AugeLab sunucusundan indirilebilir.'
    }
    $cache = Join-Path $env:LOCALAPPDATA 'AugeLab\paket-kayit-setup'
    [void][IO.Directory]::CreateDirectory($cache)
    $target = Join-Path $cache ('AugeLab-Ai-Studio-' + $config.sha256 + '.exe')
    if (Test-Path -LiteralPath $target -PathType Leaf) { Assert-Hash $target; return $target }
    $partial = Join-Path $cache ([Guid]::NewGuid().ToString('N') + '.partial')
    Add-Type -AssemblyName System.Net.Http
    $handler = [Net.Http.HttpClientHandler]::new()
    $handler.AllowAutoRedirect = $false
    $client = [Net.Http.HttpClient]::new($handler)
    $client.Timeout = [TimeSpan]::FromSeconds(900)
    $response = $null
    try {
        Info 'İndiriliyor...'
        $response = $client.GetAsync($uri).GetAwaiter().GetResult()
        [void]$response.EnsureSuccessStatusCode()
        $file = [IO.File]::Create($partial)
        try { [void]$response.Content.CopyToAsync($file).GetAwaiter().GetResult() } finally { $file.Dispose() }
        Assert-Hash $partial
        Move-Item -LiteralPath $partial -Destination $target -Force
        return $target
    } finally {
        if (Test-Path -LiteralPath $partial) { Remove-Item -LiteralPath $partial -Force }
        if ($response) { $response.Dispose() }
        $client.Dispose()
    }
}

if ($env:OS -ne 'Windows_NT' -or -not [Environment]::Is64BitOperatingSystem -or $env:PROCESSOR_ARCHITECTURE -eq 'ARM64') {
    throw 'Paket Kayıt kurulumu 64 bit Windows gerektirir.'
}

Write-Host 'Paket Kayıt kurulumu  ·  Developed by AugeLab' -ForegroundColor White
if ($DryRun) { Write-Host '(Deneme modu: hiçbir şey indirilmeyecek ya da değiştirilmeyecek.)' -ForegroundColor DarkGray }

Step 'AugeLab Studio'
$studio = Find-Studio
$repair = $false
if ($studio -and -not (Test-StudioComplete $studio)) {
    Info "Yarım kalmış bir Studio kurulumu bulundu: $studio"
    if ((Split-Path -Parent $studio).TrimEnd('\') -ne $installDir.TrimEnd('\')) {
        throw "Yarım kurulum beklenmeyen bir klasörde. Studio'yu Windows Ayarlar > Uygulamalar'dan kaldırıp kurulumu tekrar çalıştırın."
    }
    $repair = $true
    $studio = $null
}
if ($studio) {
    Info "Kurulu: $studio"
} else {
    $needAdmin = -not (Test-VCRuntime)
    if ($repair) { Info 'Studio yeniden kurulacak.' } else { Info 'Bulunamadı. Resmi kurulum dosyası AugeLab sunucusundan indirilip doğrulanacak ve sessizce kurulacak.' }
    Info 'Bu işlem birkaç dakika sürebilir.'
    if ($needAdmin) {
        Info 'Bu bilgisayarda Microsoft Visual C++ çalışma zamanı yok; önce o kurulacak.'
        Info 'Windows bir kez yönetici izni isteyecek, "Evet" deyin.'
    }
    if (-not $DryRun) {
        if (-not $Yes) {
            $answer = Read-Host '  Devam edilsin mi? (E/H)'
            if ($answer -notmatch '^[EeYy]') { Info 'Kurulum iptal edildi.'; exit 1 }
        }
        if ((Test-Path -LiteralPath $installDir) -and -not $repair) {
            throw "Hedef klasör var ama içinde Studio bulunamadı: $installDir. Klasörü kontrol edin ya da Studio'yu onarın."
        }
        if ($needAdmin) { Install-VCRuntime }
        $setup = Get-StudioInstaller
        Info 'Studio kuruluyor...'
        $proc = Start-Process -FilePath $setup -ArgumentList ('--silent --install-dir "' + $installDir + '" --start-menu-shortcut') -WindowStyle Hidden -PassThru -Wait
        if ($proc.ExitCode -ne 0) {
            throw "Studio kurulumu $($proc.ExitCode) koduyla bitti. Ayrıntılar: %TEMP%\augelab-installer-startup.log"
        }
        $studio = Find-Studio
        if (-not $studio -or -not (Test-StudioComplete $studio)) { throw 'Kurulum bitti ama Studio eksik görünüyor. Ayrıntılar: %TEMP%\augelab-installer-startup.log' }
        Info "Kuruldu: $studio"
    }
}

Step 'Barkod okuyucu (zbar)'
if ($studio) {
    $studioPython = Join-Path (Split-Path -Parent $studio) 'Python\python.exe'
    if (Test-Zbar $studioPython) {
        Info 'Kurulu.'
    } else {
        Info 'zbar barkod motoru çalışmıyor. Gereken Microsoft Visual C++ 2013 çalışma zamanı kurulacak (Windows yönetici izni isteyecek);'
        Info 'gerekirse PyPI''daki resmi pyzbar paketi (SHA-256 doğrulamalı) Studio''ya eklenecek.'
        if (-not $DryRun) {
            try {
                Install-Zbar $studioPython
                if (Test-Zbar $studioPython) { Info 'Kuruldu.' } else { throw 'pyzbar yüklendi ama çalışmıyor.' }
            } catch {
                Write-Warning ("zbar kurulamadı: " + $_.Exception.Message + " Barkodlar OpenCV ile okunacak; okuma daha zayıf olabilir.")
            }
        }
    }
}

Step 'Paket Kayıt blokları'
$blocks = @(Get-ChildItem -Path (Join-Path $root 'custom_blocks') -Filter '*.py')
Info ("{0} blok -> {1}" -f $blocks.Count, $blocksDir)
if (-not $DryRun) {
    New-Item -ItemType Directory -Force $blocksDir | Out-Null
    $blocks | Copy-Item -Destination $blocksDir -Force
}

Step 'Senaryo'
$pmod = Join-Path $root 'scenario\PaketKayit.pmod'
if (Test-Path -LiteralPath $pmod) {
    Info "-> $docsDir\PaketKayit.pmod"
    if (-not $DryRun) {
        New-Item -ItemType Directory -Force $docsDir | Out-Null
        Copy-Item -LiteralPath $pmod -Destination $docsDir -Force
    }
} else {
    Write-Warning 'scenario\PaketKayit.pmod bulunamadı; bu paket eksik.'
}

Step 'Masaüstü kısayolları'
Info '"Paket Kayıt - Studio" ve "Paket Kayıt - Ekran"'
if (-not $DryRun) {
    if ($studio) {
        $shell = New-Object -ComObject WScript.Shell
        $link = $shell.CreateShortcut((Join-Path $desktop 'Paket Kayıt - Studio.lnk'))
        $link.TargetPath = $studio
        $link.WorkingDirectory = Split-Path -Parent $studio
        $link.Save()
    }
    Set-Content -LiteralPath (Join-Path $desktop 'Paket Kayıt - Ekran.url') -Value ("[InternetShortcut]`r`nURL=" + $uiUrl) -Encoding ASCII
}

Step 'Studio'
if ($studio -and (Test-StudioRunning $studio)) {
    Info 'Zaten açık.'
} elseif ($studio) {
    Info 'Açılıyor.'
    if (-not $DryRun) { Start-Process -FilePath $studio -WorkingDirectory (Split-Path -Parent $studio) | Out-Null }
}

Write-Host ''
Write-Host 'Kurulum tamamlandı. İlk kullanım:' -ForegroundColor Green
Info '1. Studio lisans ekranı açılırsa account.augelab.com hesabınızdaki doğrulama kodunu girip VERIFY''a basın. (Yalnızca ilk sefer.)'
Info "2. Studio'da File > Open ile '$docsDir\PaketKayit.pmod' dosyasını açın ve Run > Run'a basın."
Info "3. Paket Kayıt ekranı tarayıcıda açılır. Masaüstündeki 'Paket Kayıt - Ekran' kısayolu da aynı adresi açar."
