# Clean Stream Ripper - 1-Click Windows App Installer
$appName = "Clean Stream Ripper"
$installDir = "$env:LOCALAPPDATA\Programs\$appName"
$sourceDir = "$PSScriptRoot\dist\Clean Stream Ripper"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   INSTALLING CLEAN STREAM RIPPER AS A WINDOWS APP" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Installing to: $installDir`n" -ForegroundColor Gray

# 1. Ensure target directory exists
if (!(Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir -Force | Out-Null
}

# 2. Copy application files and ensure icon.ico exists at root
Write-Host "Copying application binaries and assets..." -ForegroundColor Gray
robocopy $sourceDir $installDir /E /NP /R:2 /W:1 | Out-Null

$iconSource = "$PSScriptRoot\icon.ico"
$iconDest = "$installDir\icon.ico"
if (Test-Path $iconSource) {
    Copy-Item $iconSource $iconDest -Force
}

$exePath = "$installDir\Clean Stream Ripper.exe"

# 3. Create Windows Start Menu Shortcut with embedded icon
Write-Host "Registering in Windows Start Menu..." -ForegroundColor Gray
$wscript = New-Object -ComObject WScript.Shell
$startMenuPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\$appName.lnk"
if (Test-Path $startMenuPath) { Remove-Item $startMenuPath -Force }

$shortcut = $wscript.CreateShortcut($startMenuPath)
$shortcut.TargetPath = $exePath
$shortcut.WorkingDirectory = $installDir
$shortcut.IconLocation = "$iconDest,0"
$shortcut.Description = "Personal YouTube & Media Stream Ripper"
$shortcut.Save()

# 4. Create Desktop Shortcut with 3D Icon
Write-Host "Creating Desktop app icon..." -ForegroundColor Gray
$desktopPath = "$([Environment]::GetFolderPath('Desktop'))\$appName.lnk"
if (Test-Path $desktopPath) { Remove-Item $desktopPath -Force }

$desktopShortcut = $wscript.CreateShortcut($desktopPath)
$desktopShortcut.TargetPath = $exePath
$desktopShortcut.WorkingDirectory = $installDir
$desktopShortcut.IconLocation = "$iconDest,0"
$desktopShortcut.Description = "Personal YouTube & Media Stream Ripper"
$desktopShortcut.Save()

# 5. Register in Windows "Installed Apps" (Settings -> Apps -> Installed Apps)
Write-Host "Registering in Windows Installed Apps list..." -ForegroundColor Gray
$regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\$appName"
New-Item -Path $regPath -Force | Out-Null
Set-ItemProperty -Path $regPath -Name "DisplayName" -Value $appName
Set-ItemProperty -Path $regPath -Name "DisplayIcon" -Value "$iconDest,0"
Set-ItemProperty -Path $regPath -Name "DisplayVersion" -Value "1.0.0"
Set-ItemProperty -Path $regPath -Name "Publisher" -Value "Clean Apps"
Set-ItemProperty -Path $regPath -Name "InstallLocation" -Value $installDir
Set-ItemProperty -Path $regPath -Name "UninstallString" -Value "powershell.exe -ExecutionPolicy Bypass -File `"$installDir\uninstall.ps1`""

# Copy uninstaller script to installation directory
Copy-Item "$PSScriptRoot\uninstall.ps1" "$installDir\uninstall.ps1" -Force

# 6. Flush Windows Shell Icon Cache so the new 3D icon shows immediately
Write-Host "Flushing Windows Shell icon cache..." -ForegroundColor Gray
try {
    $code = @"
    using System;
    using System.Runtime.InteropServices;
    public class ShellNotifier {
        [DllImport("shell32.dll")]
        public static extern void SHChangeNotify(int wEventId, int uFlags, IntPtr dwItem1, IntPtr dwItem2);
    }
"@
    Add-Type -TypeDefinition $code -Language CSharp
    [ShellNotifier]::SHChangeNotify(0x08000000, 0, [IntPtr]::Zero, [IntPtr]::Zero)
} catch {
    ie4uinit.exe -show 2>$null
}

Write-Host "`n============================================================" -ForegroundColor Green
Write-Host "   INSTALLATION COMPLETE!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host " Clean Stream Ripper is now installed with your 3D icon:" -ForegroundColor White
Write-Host " * Windows Start Menu: Search 'Clean Stream Ripper' (with 3D icon)" -ForegroundColor Gray
Write-Host " * Desktop: Glossy 3D App Icon is on your desktop" -ForegroundColor Gray
Write-Host " * Windows Settings: Visible in 'Installed Apps'" -ForegroundColor Gray
Write-Host "============================================================`n" -ForegroundColor Green
