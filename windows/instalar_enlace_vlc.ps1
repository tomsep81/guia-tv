# Registra en Windows los enlaces "guiatv-vlc://" de la Guia TV,
# para que el boton "Ver en VLC" abra el canal en VLC.
# Solo afecta a tu usuario y no necesita permisos de administrador.
#
# Para desinstalar:  Remove-Item 'HKCU:\Software\Classes\guiatv-vlc' -Recurse

$script = Join-Path $PSScriptRoot 'abrir_vlc.ps1'
if (-not (Test-Path $script)) {
    Write-Host "No se encontro $script" -ForegroundColor Red
    exit 1
}

$powershell = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$comando = "`"$powershell`" -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$script`" `"%1`""

$base = 'HKCU:\Software\Classes\guiatv-vlc'
New-Item -Path $base -Value 'URL:Guia TV - abrir en VLC' -Force | Out-Null
New-ItemProperty -Path $base -Name 'URL Protocol' -Value '' -PropertyType String -Force | Out-Null
New-Item -Path "$base\shell\open\command" -Value $comando -Force | Out-Null

Write-Host 'Listo: los botones "Ver en VLC" de la guia ya abren VLC.' -ForegroundColor Green
Write-Host "Comando registrado: $comando"