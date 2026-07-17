# Publica a pagina Almoxarifado no WordPress
# Uso: .\publicar_wp.ps1
# Antes: $env:WP_USER = 'seu-usuario'; $env:WP_PASS = 'sua-senha'

$DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
python "$DIR\backend\scripts\publicar_wp_direto.py"
