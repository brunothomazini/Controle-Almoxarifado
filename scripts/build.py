import json, re

# Caminhos ajustados para execução a partir da raiz (onde o GitHub Actions roda)
DATA_PATH = "data/almox.json"
OUTPUT_PATH = "index.html"

def build():
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data_obj = json.load(f)
    
    data_json = json.dumps(data_obj, ensure_ascii=False)
    
    # CSS completo
    css = """*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Roboto,'Segoe UI',Arial,sans-serif;background:#e9e9e9;color:#444;line-height:1.6;min-height:100vh}
#a-r .hdr{background:linear-gradient(135deg,#055e6f,#1094ab);color:#fff;padding:20px 0}
#a-r .hdr-in{max-width:1100px;margin:0 auto;padding:0 20px;display:flex;align-items:center;justify-content:space-between}
#a-r .hdr h1{font-size:1.5rem;font-weight:600}
#a-r .hdr .sub{font-size:.85rem;opacity:.85;margin-top:2px}
#a-r .ct{max-width:1100px;margin:0 auto;padding:20px}
#a-r .upd{text-align:right;font-size:.8rem;color:#777;margin-bottom:8px}
#a-r .st{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin-bottom:20px}
#a-r .sc{background:#fff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,.05);padding:16px;text-align:center}
#a-r .sc .n{font-size:1.8rem;font-weight:700;color:#055e6f}
#a-r .sc.g .n{color:#2e7d32}
#a-r .sc.r .n{color:#c62828}
#a-r .sc .l{font-size:.75rem;text-transform:uppercase;letter-spacing:.5px;color:#888;margin-top:2px}
#a-r .cd{background:#fff;border-radius:10px;box-shadow:0 2px 16px rgba(0,0,0,.07);padding:24px;margin-bottom:20px}
#a-r .cd h2{font-size:1.1rem;color:#055e6f;margin-bottom:14px;font-weight:600}
#a-r .sb{display:flex;flex-wrap:wrap;gap:8px}
#a-r .sb input,#a-r .sb select{flex:1;min-width:160px;padding:8px 12px;border:1px solid #ddd;border-radius:6px;font-size:.85rem;outline:none;transition:border .2s}
#a-r .sb input:focus,#a-r .sb select:focus{border-color:#1094ab}
#a-r .bt{display:inline-block;padding:8px 18px;border-radius:6px;text-decoration:none;font-size:.85rem;font-weight:600;cursor:pointer;background:#055e6f;color:#fff;border:none;transition:opacity .2s}
#a-r .bt:hover{opacity:.85}
#a-r .bt-o{background:transparent;color:#055e6f;border:1px solid #055e6f}
#a-r .inf{font-size:.85rem;color:#666;margin-bottom:12px}
#a-r table{width:100%;border-collapse:collapse;font-size:.85rem}
#a-r th{background:#f5f5f5;padding:10px 8px;text-align:left;font-weight:600;color:#444;border-bottom:2px solid #ddd}
#a-r td{padding:8px;border-bottom:1px solid #eee}
#a-r tr:hover td{background:#fafafa}
#a-r .tag{display:inline-block;background:#e0f7fa;color:#055e6f;border-radius:4px;padding:2px 8px;font-size:.78rem;font-weight:500}
#a-r .si{display:inline-flex;align-items:center;gap:5px}
#a-r .sg{display:inline-block;padding:1px 8px;border-radius:4px;font-size:.78rem;font-weight:500}
#a-r .pag{display:flex;align-items:center;justify-content:center;gap:12px;margin-top:16px;font-size:.85rem}
#a-r .emp{text-align:center;padding:40px;color:#888;font-size:.95rem}
#a-r .ft{text-align:center;padding:16px;font-size:.78rem;color:#999}
@media(max-width:600px){#a-r .st{grid-template-columns:repeat(2,1fr)} #a-r .sb input,#a-r .sb select{min-width:100%}}

html,body{height:100%}
#a-r{max-width:1100px;margin:0 auto;padding:0;min-height:100vh;display:flex;flex-direction:column}
#a-r .ct{flex:1}"""

    # HTML com o JSON embutido
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Almoxarifado - Consulta Pública</title>
<style>{css}</style>
</head>
<body>
<div id="a-r">
<div class="hdr"><div class="hdr-in"><div><h1>Sistema de Controle de Almoxarifado</h1><div class="sub">Universidade de S&atilde;o Paulo &mdash; Consulta P&uacute;blica</div></div></div></div>
<div class="ct">
<div class="upd">&Uacute;ltima atualiza&ccedil;&atilde;o: 2026-07-16</div>
<div class="st">
<div class="sc"><div class="n">{data_obj['total']}</div><div class="l">Itens no Estoque</div></div>
<div class="sc"><div class="n">{data_obj['total_categorias']}</div><div class="l">Categorias</div></div>
<div class="sc g"><div class="n">{data_obj['total_disponiveis']}</div><div class="l">Dispon&iacute;veis</div></div>
<div class="sc r"><div class="n">{data_obj['total_indisponiveis']}</div><div class="l">Indispon&iacute;veis</div></div>
</div>
<div class="cd">
<h2>Consultar Itens</h2>
<div class="sb">
<input type="text" id="s_c" placeholder="C&oacute;digo..." oninput="r()">
<input type="text" id="s_n" placeholder="Nome do item..." oninput="r()">
<select id="s_t" onchange="r()"><option value="">Todas as categorias</option></select>
<a class="bt" href="javascript:r()">Buscar</a>
<a class="bt bt-o" href="javascript:l()">Limpar</a>
</div>
</div>
<div class="cd">
<h2>Resultados</h2>
<div id="res"><div class="emp">Carregando dados...</div></div>
</div>
</div>
<div class="ft">Sistema de Controle de Almoxarifado &mdash; FOB/USP</div>
</div>
<script id="d" type="application/json">{data_json}</script>
<script>
var _d=JSON.parse(document.getElementById('d').textContent);
var I=_d.itens,C=_d.categorias,P=50,p=1,F=[];
var _t=document.getElementById('s_t');
for(var i=0;i<C.length;i++){{var o=document.createElement('option');o.value=C[i];o.textContent=C[i];_t.appendChild(o);}}
function b(s){{var m={{disponivel:['Disponivel','#e8f5e9','#2e7d32','#4caf50'],emprestado:['Emprestado','#fff3e0','#e65100','#ff9800'],manutencao:['Manutencao','#fff3e0','#e65100','#ff9800'],baixado:['Baixado','#ffebee','#c62828','#f44336'],reservado:['Reservado','#fff3e0','#e65100','#ff9800']}};var a=m[s]||['Desconhecido','#fff3e0','#e65100','#ff9800'];return '<span class="si"><span style="width:9px;height:9px;border-radius:50%;display:inline-block;background:'+a[3]+'"></span><span class="sg" style="background:'+a[1]+';color:'+a[2]+'">'+a[0]+'</span></span>';}}
function r(){{var a=document.getElementById('s_c').value.trim().toLowerCase();var b=document.getElementById('s_n').value.trim().toLowerCase();var c=document.getElementById('s_t').value;F=I.filter(function(i){{if(a&&i.codigo.toLowerCase().indexOf(a)===-1)return false;if(b&&i.nome.toLowerCase().indexOf(b)===-1)return false;if(c&&i.categoria!==c)return false;return true;}});p=1;render();}}
function l(){{document.getElementById('s_c').value='';document.getElementById('s_n').value='';document.getElementById('s_t').value='';F=I.slice();p=1;render();}}
function render(){{var e=document.getElementById('res'),t=F.length,tp=Math.max(1,Math.ceil(t/P));if(p>tp)p=tp;if(p<1)p=1;var s=(p-1)*P,o=Math.min(s+P,t),pg=F.slice(s,o);if(t===0){{e.innerHTML='<div class="emp">Nenhum item encontrado</div>';return;}}var h='<div class="inf">Mostrando '+(s+1)+'-'+o+' de '+t+' item(ns)</div><table><thead><tr><th>Codigo</th><th>Nome</th><th>Nome Comercial</th><th>Marca</th><th>Categoria</th><th>Pedidos por:</th><th>Status</th></tr></thead><tbody>';for(var i=0;i<pg.length;i++){{var x=pg[i];h+='<tr><td><strong>'+(x.codigo||'-')+'</strong></td><td>'+(x.nome||'-')+'</td><td>'+(x.nome_comercial||'-')+'</td><td>'+(x.fabricante||'-')+'</td><td><span class="tag">'+(x.categoria||'N/A')+'</span></td><td>'+(x.pedidos_info||'Almox')+'</td><td>'+b(x.status)+'</td></tr>';}}h+='</tbody></table>';if(tp>1){{h+='<div class="pag">';if(p>1)h+='<a class="bt bt-o" href="javascript:g('+(p-1)+')">&laquo; Anterior</a>';h+='<span>Pagina '+p+' de '+tp+'</span>';if(p<tp)h+='<a class="bt bt-o" href="javascript:g('+(p+1)+')">Proxima &raquo;</a>';h+='</div>';}}e.innerHTML=h;}}
function g(x){{if(x<1)return;p=x;render();}}
F=I.slice();render();
</script>
</body>
</html>"""
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Build concluído: {OUTPUT_PATH}")

if __name__ == "__main__":
    build()
