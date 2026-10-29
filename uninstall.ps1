# Clean Stream Ripper - Windows Uninstaller
$appName = "Clean Stream Ripper"
$installDir = "$env:LOCALAPPDATA\Programs\$appName"
$startMenuPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\$appName.lnk"
$desktopPath = "$([Environment]::GetFolderPath('Desktop'))\$appName.lnk"
$regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\$appName"

Write-Host "Uninstalling $appName..." -ForegroundColor Cyan

Stop-Process -Name "Clean Stream Ripper" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

Remove-Item -Path $startMenuPath -Force -ErrorAction SilentlyContinue
Remove-Item -Path $desktopPath -Force -ErrorAction SilentlyContinue
Remove-Item -Path $regPath -Recurse -Force -ErrorAction SilentlyContinue

# Self-removal of install directory
Start-Process powershell -ArgumentList "-NoProfile -Command `"Start-Sleep -Seconds 1; Remove-Item -Path '$installDir' -Recurse -Force -ErrorAction SilentlyContinue`"" -WindowStyle Hidden

Write-Host "$appName has been cleanly removed from your system." -ForegroundColor Green
