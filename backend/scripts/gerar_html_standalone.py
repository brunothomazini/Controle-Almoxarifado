#!/usr/bin/env python3
import json, sqlite3
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent.parent.parent
DB = BASE / "backend" / "data" / "almoxarifado.db"
OUT = BASE / "almoxarifado-consulta.html"

conn = sqlite3.connect(str(DB))
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT id, nome FROM categorias ORDER BY nome")
categorias = [r["nome"] for r in cur.fetchall()]

cur.execute("SELECT id, nome FROM categorias")
cat_map = {r["id"]: r["nome"] for r in cur.fetchall()}

cur.execute(
    "SELECT i.codigo,i.nome,i.nome_comercial,i.fabricante,i.categoria_id,"
    "i.quantidade_atual,i.unidade_medida,i.solicitar_por_email,i.tipo_controle,i.status "
    "FROM itens i ORDER BY i.nome"
)
itens = []
for r in cur.fetchall():
    row = dict(r)
    cn = cat_map.get(row["categoria_id"], "N/A")
    tc = (row["tipo_controle"] or "").lower()
    if cn == "Informatica":
        ped = "solicitar para o setor de Informatica"
    elif tc == "almoxarifado":
        ped = "Almox"
    elif row["solicitar_por_email"]:
        ped = "e-mail padronizados@fob.usp.br"
    else:
        ped = "Almox"
    itens.append({
        "codigo": row["codigo"], "nome": row["nome"],
        "nome_comercial": row["nome_comercial"] or "-",
        "fabricante": row["fabricante"] or "-",
        "categoria": cn,
        "quantidade_disponivel": row["quantidade_atual"],
        "unidade": row["unidade_medida"],
        "status": str.lower(row["status"] or "DISPONIVEL"),
        "pedidos_info": ped,
    })
conn.close()

total = len(itens)
disp = sum(1 for i in itens if i["status"] == "disponivel")
cat_opts = "\n".join(f"<option value=\"{c}\">{c}</option>" for c in categorias)
hoje = datetime.now().strftime("%d/%m/%Y")

data_obj = {
    "total": total,
    "total_categorias": len(categorias),
    "total_disponiveis": disp,
    "total_indisponiveis": total - disp,
    "categorias": categorias,
    "itens": itens
}
data_json = json.dumps(data_obj, ensure_ascii=False)

cat_opts_js = "\\n".join(f"<option value=\"{c}\">{c}</option>" for c in categorias)

html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Almoxarifado - Consulta Pública</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:Roboto,'Segoe UI',Arial,sans-serif;background:#e9e9e9;color:#444;line-height:1.6;min-height:100vh}}
#a-r .hdr{{background:linear-gradient(135deg,#055e6f,#1094ab);color:#fff;padding:20px 0}}
#a-r .hdr-in{{max-width:1100px;margin:0 auto;padding:0 20px;display:flex;align-items:center;justify-content:space-between}}
#a-r .hdr h1{{font-size:1.5rem;font-weight:600}}
#a-r .hdr .sub{{font-size:.85rem;opacity:.85;margin-top:2px}}
#a-r .ct{{max-width:1100px;margin:0 auto;padding:20px}}
#a-r .cd{{background:#fff;border-radius:10px;box-shadow:0 2px 16px rgba(0,0,0,.07);padding:24px;margin-bottom:20px}}
#a-r .cd h2{{font-size:1.15rem;color:#1094ab;margin-bottom:16px;padding-bottom:8px;border-bottom:2px solid #e9e9e9}}
#a-r .sb{{display:flex;gap:12px;flex-wrap:wrap}}
#a-r .sb input,#a-r .sb select{{padding:10px 14px;border:2px solid #ddd;border-radius:8px;font-size:.95rem;flex:1;min-width:180px;outline:none;transition:border-color .2s}}
#a-r .sb input:focus,#a-r .sb select:focus{{border-color:#1094ab;box-shadow:0 0 0 3px rgba(16,148,171,.12)}}
#a-r .bt{{display:inline-flex;align-items:center;justify-content:center;padding:10px 24px;background:#1094ab;color:#fff;border:none;border-radius:8px;font-size:.95rem;font-weight:500;cursor:pointer;white-space:nowrap;text-decoration:none;transition:background .2s}}
#a-r .bt:hover{{background:#055e6f}}
#a-r .bt-o{{background:transparent;color:#1094ab;border:2px solid #1094ab}}
#a-r .bt-o:hover{{background:#f0fafc}}
#a-r .st{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:20px}}
#a-r .sc{{background:#fff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,.07);padding:18px;text-align:center}}
#a-r .sc .n{{font-size:2rem;font-weight:700;color:#1094ab}}
#a-r .sc .l{{font-size:.85rem;color:#666}}
#a-r .sc.g .n{{color:#4caf50}}
#a-r .sc.r .n{{color:#f44336}}
#a-r .ft{{text-align:center;padding:20px;color:#999;font-size:.85rem}}
#a-r .upd{{font-size:.82rem;color:#999;text-align:center;margin-bottom:16px}}
#a-r .res-wrap{{overflow-x:auto;width:100%}}
#a-r table{{width:100%;border-collapse:collapse;font-size:.9rem;min-width:700px}}
#a-r th{{background:#f5f5f5;padding:12px 14px;text-align:left;font-weight:600;color:#055e6f;border-bottom:2px solid #ddd;white-space:nowrap}}
#a-r td{{padding:12px 14px;border-bottom:1px solid #eee;vertical-align:middle;white-space:nowrap}}
#a-r tr:hover td{{background:#fafafa}}
#a-r .inf{{margin-bottom:12px;color:#666;font-size:.85rem}}
#a-r .pag{{margin-top:16px;text-align:center;display:flex;justify-content:center;align-items:center;gap:8px;flex-wrap:wrap}}
#a-r .pag .bt{{padding:8px 18px;font-size:.88rem}}
#a-r .pag span{{font-size:.9rem;color:#555}}
#a-r .tag{{display:inline-block;background:#e8f0fe;padding:3px 10px;border-radius:20px;font-size:.78rem;color:#055e6f;font-weight:500}}
#a-r .si{{display:inline-flex;align-items:center;gap:6px}}
#a-r .sg{{display:inline-block;padding:3px 10px;border-radius:20px;font-size:.78rem;font-weight:500}}
#a-r .emp{{text-align:center;padding:60px 20px;color:#999}}
@media(max-width:768px){{#a-r .hdr-in{{flex-direction:column;text-align:center;gap:8px}}#a-r .sb{{flex-direction:column}}#a-r .sb input{{min-width:auto}}#a-r .st{{grid-template-columns:1fr 1fr}}#a-r th,#a-r td{{padding:8px 10px;font-size:.82rem}}}}
</style>
</head>
<body>
<div id="a-r">
<div class="hdr"><div class="hdr-in"><div><h1>Sistema de Controle de Almoxarifado</h1><div class="sub">Universidade de São Paulo &mdash; Consulta Pública</div></div></div></div>
<div class="ct">
<div class="upd">Última atualização: {hoje}</div>
<div class="st">
<div class="sc"><div class="n">{total}</div><div class="l">Itens no Estoque</div></div>
<div class="sc"><div class="n">{len(categorias)}</div><div class="l">Categorias</div></div>
<div class="sc g"><div class="n">{disp}</div><div class="l">Disponíveis</div></div>
<div class="sc r"><div class="n">{total - disp}</div><div class="l">Indisponíveis</div></div>
</div>
<div class="cd">
<h2>Consultar Itens</h2>
<div class="sb">
<input type="text" id="s_c" placeholder="Código..." oninput="r()">
<input type="text" id="s_n" placeholder="Nome do item..." oninput="r()">
<select id="s_t" onchange="r()"><option value="">Todas as categorias</option>{cat_opts}</select>
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
<pre id="d" style="display:none">{data_json}</pre>
<script>
var _d=JSON.parse(document.getElementById('d').textContent);
var I=_d.itens,C=_d.categorias,P=50,p=1,F=[];
var _t=document.getElementById('s_t');
_t.innerHTML='<option value="">Todas as categorias</option>';
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

OUT.write_text(html, encoding="utf-8")
print(f"OK: {OUT} ({len(html)} bytes, {total} itens)")
