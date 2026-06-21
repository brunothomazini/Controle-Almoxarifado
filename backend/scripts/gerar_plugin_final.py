#!/usr/bin/env python3
import base64
from pathlib import Path

html_path = Path(__file__).resolve().parent.parent.parent / "almoxarifado-consulta.html"
html = html_path.read_text(encoding="utf-8")
b64 = base64.b64encode(html.encode("utf-8")).decode("ascii")
print(f"HTML: {len(html)} bytes, Base64: {len(b64)} chars")

out = Path(__file__).resolve().parent.parent.parent / "plugins" / "almoxarifado-plugin" / "almoxarifado-consulta.php"
out.parent.mkdir(parents=True, exist_ok=True)

php = f"""<?php
/**
 * Plugin Name: Almoxarifado - Consulta Pública
 * Description: Consulta de estoque do almoxarifado - FOB/USP
 * Version: 1.0
 */

function almoxarifado_consulta() {{
    return base64_decode("{b64}");
}}
add_shortcode('almoxarifado', 'almoxarifado_consulta');
"""
out.write_text(php, encoding="utf-8")
print(f"Plugin gerado: {out} ({len(php)} bytes)")
