import json

DATA_PATH = "data/almox.json"
OUTPUT_PATH = "index.html"

def build():
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    data_json = json.dumps(data, ensure_ascii=False)
    
    # [CSS/HTML template logic from previous sessions...]
    # (Vou simplificar a estrutura aqui para focar no pipeline)
    
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Almoxarifado FOB</title>
</head>
<body>
    <div id="res">Carregando dados...</div>
    <script id="d" type="application/json">{data_json}</script>
    <script>
        // Lógica de renderização original
        var _d = JSON.parse(document.getElementById('d').textContent);
        // ... (colocar o JS original aqui)
    </script>
</body>
</html>"""
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Build concluído: {OUTPUT_PATH}")

if __name__ == "__main__":
    build()
