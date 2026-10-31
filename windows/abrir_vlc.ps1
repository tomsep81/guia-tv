# Abre en VLC un canal elegido en la Guia TV.
# Recibe enlaces del tipo: guiatv-vlc://abrir?u=<url>&r=<referrer>&a=<user-agent>
param([string]$Enlace)

Add-Type -AssemblyName System.Windows.Forms

function Mostrar-Error([string]$mensaje) {
    [System.Windows.Forms.MessageBox]::Show($mensaje, 'Guia TV') | Out-Null
}

function Leer-Parametros([string]$texto) {
    $resultado = @{}
    $partes = $texto.Split([char]'?', 2)
    if ($partes.Count -lt 2) { return $resultado }
    foreach ($par in $partes[1].Split([char]'&')) {
        $clave_valor = $par.Split([char]'=', 2)
        if ($clave_valor.Count -eq 2) {
            $resultado[$clave_valor[0]] = [Uri]::UnescapeDataString($clave_valor[1].Replace('+', ' '))
        }
    }
    return $resultado
}

function Buscar-VLC {
    foreach ($clave in 'HKLM:\SOFTWARE\VideoLAN\VLC', 'HKLM:\SOFTWARE\WOW6432Node\VideoLAN\VLC') {
        $datos = Get-ItemProperty -Path $clave -ErrorAction SilentlyContinue
        if ($datos) {
            $candidatos = @($datos.'(default)')
            if ($datos.InstallDir) { $candidatos += Join-Path $datos.InstallDir 'vlc.exe' }
            foreach ($ruta in $candidatos) {
                if ($ruta -and (Test-Path $ruta -PathType Leaf)) { return $ruta }
            }
        }
    }
    foreach ($ruta in "$env:ProgramFiles\VideoLAN\VLC\vlc.exe", "${env:ProgramFiles(x86)}\VideoLAN\VLC\vlc.exe") {
        if (Test-Path $ruta -PathType Leaf) { return $ruta }
    }
    return $null
}

$p = Leer-Parametros $Enlace
$url = $p['u']
if (-not $url -or $url -notmatch '^https?://[^\s"]+$') {
    Mostrar-Error "El enlace del canal no es valido:`n$Enlace"
    exit 1
}

$vlc = Buscar-VLC
if (-not $vlc) {
    Mostrar-Error 'No se encontro VLC. Instalalo desde https://www.videolan.org y vuelve a intentarlo.'
    exit 1
}

# --one-instance: si VLC ya esta abierto, cambia de canal en la misma ventana
$argumentos = @('--one-instance', "`"$url`"")
if ($p['r'] -and $p['r'] -notmatch '"') { $argumentos += "`":http-referrer=$($p['r'])`"" }
if ($p['a'] -and $p['a'] -notmatch '"') { $argumentos += "`":http-user-agent=$($p['a'])`"" }

# Reserva de video: VLC acumula 3 segundos antes de reproducir (menos cortes)
$argumentos += '":network-caching=3000"'

Start-Process -FilePath $vlc -ArgumentList ($argumentos -join ' ')