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

# 2. Copy application files
Write-Host "Copying application binaries and assets..." -ForegroundColor Gray
robocopy $sourceDir $installDir /E /NP /R:2 /W:1 | Out-Null

$exePath = "$installDir\Clean Stream Ripper.exe"
$iconPath = "$installDir\icon.ico"

# 3. Create Windows Start Menu Shortcut
Write-Host "Registering in Windows Start Menu..." -ForegroundColor Gray
$wscript = New-Object -ComObject WScript.Shell
$startMenuPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\$appName.lnk"
$shortcut = $wscript.CreateShortcut($startMenuPath)
$shortcut.TargetPath = $exePath
$shortcut.WorkingDirectory = $installDir
$shortcut.IconLocation = "$iconPath,0"
$shortcut.Description = "Personal YouTube & Media Stream Ripper"
$shortcut.Save()

# 4. Create Desktop Shortcut with 3D Icon
Write-Host "Creating Desktop app icon..." -ForegroundColor Gray
$desktopPath = "$([Environment]::GetFolderPath('Desktop'))\$appName.lnk"
$desktopShortcut = $wscript.CreateShortcut($desktopPath)
$desktopShortcut.TargetPath = $exePath
$desktopShortcut.WorkingDirectory = $installDir
$desktopShortcut.IconLocation = "$iconPath,0"
$desktopShortcut.Description = "Personal YouTube & Media Stream Ripper"
$desktopShortcut.Save()

# 5. Register in Windows "Installed Apps" (Settings -> Apps -> Installed Apps)
Write-Host "Registering in Windows Installed Apps list..." -ForegroundColor Gray
$regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\$appName"
New-Item -Path $regPath -Force | Out-Null
Set-ItemProperty -Path $regPath -Name "DisplayName" -Value $appName
Set-ItemProperty -Path $regPath -Name "DisplayIcon" -Value $iconPath
Set-ItemProperty -Path $regPath -Name "DisplayVersion" -Value "1.0.0"
Set-ItemProperty -Path $regPath -Name "Publisher" -Value "Clean Apps"
Set-ItemProperty -Path $regPath -Name "InstallLocation" -Value $installDir
Set-ItemProperty -Path $regPath -Name "UninstallString" -Value "powershell.exe -ExecutionPolicy Bypass -File `"$installDir\uninstall.ps1`""

# Copy uninstaller script to installation directory
Copy-Item "$PSScriptRoot\uninstall.ps1" "$installDir\uninstall.ps1" -Force

Write-Host "`n============================================================" -ForegroundColor Green
Write-Host "   INSTALLATION COMPLETE!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host " Clean Stream Ripper is now an officially installed Windows program:" -ForegroundColor White
Write-Host " * Windows Start Menu: Press the Windows Key and type 'Clean Stream Ripper'" -ForegroundColor Gray
Write-Host " * Desktop: 3D App Icon is on your desktop" -ForegroundColor Gray
Write-Host " * Windows Settings: Visible in 'Installed Apps' with 1-click uninstall" -ForegroundColor Gray
Write-Host "============================================================`n" -ForegroundColor Green
