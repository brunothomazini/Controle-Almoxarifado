#!/usr/bin/env python3
"""Generate a WordPress-friendly version with inline everything."""
import json, sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "data" / "almoxarifado.db"
OUT = Path(__file__).resolve().parent.parent.parent / "almoxarifado-wordpress.html"

conn = sqlite3.connect(str(DB))
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT id, nome FROM categorias ORDER BY nome")
categorias = [{"id": r["id"], "nome": r["nome"]} for r in cur.fetchall()]
cat_map = {c["id"]: c["nome"] for c in categorias}

cur.execute(
    "SELECT i.codigo,i.nome,i.nome_comercial,i.fabricante,i.categoria_id,"
    "i.quantidade_atual,i.unidade_medida,i.solicitar_por_email,"
    "i.tipo_controle,i.status FROM itens i ORDER BY i.nome"
)
itens = []
for r in cur.fetchall():
    row = dict(r)
    cat_nome = cat_map.get(row["categoria_id"], "N/A")
    tc = (row["tipo_controle"] or "").lower()
    if cat_nome == "Informatica":
        pedidos_info = "solicitar para o setor de Informatica"
    elif tc == "almoxarifado":
        pedidos_info = "Almox"
    elif row["solicitar_por_email"]:
        pedidos_info = "e-mail padronizados@fob.usp.br"
    else:
        pedidos_info = "Almox"
    itens.append({
        "codigo": row["codigo"], "nome": row["nome"],
        "nome_comercial": row["nome_comercial"] or "-",
        "fabricante": row["fabricante"] or "-",
        "categoria": cat_nome,
        "quantidade_disponivel": row["quantidade_atual"] or 0,
        "unidade": row["unidade_medida"] or "un",
        "status": (row["status"] or "DISPONIVEL").lower(),
        "pedidos_info": pedidos_info,
    })
conn.close()

total = len(itens)
disp = sum(1 for i in itens if i["status"] == "disponivel")
dados = {
    "total": total, "total_categorias": len(categorias),
    "total_disponiveis": disp, "total_indisponiveis": total - disp,
    "categorias": [c["nome"] for c in categorias],
    "itens": itens,
}
data_json = json.dumps(dados, ensure_ascii=False)

cat_options = "\n".join(f"<option value=\"{c}\">{c}</option>" for c in dados["categorias"])

# Minified JS for initialisation (will go inside SVG onload)
# Everything on one line so it fits in an attribute
js_funcs = (
    "var d=JSON.parse(document.getElementById('_d').textContent),"
    "I=d.itens,C=d.categorias,P=50,p=1,F=[];"
    "var _s=document.getElementById('_scat');"
    "_s.innerHTML='<option value=\"\">Todas as categorias</option>';"
    "for(var _i=0;_i<C.length;_i++){var _o=document.createElement('option');"
    "_o.value=C[_i];_o.textContent=C[_i];_s.appendChild(_o);}"
    "function _b(s){"
    "var m={disponivel:['Disponivel','#e8f5e9','#2e7d32','#4caf50'],"
    "emprestado:['Emprestado','#fff3e0','#e65100','#ff9800'],"
    "manutencao:['Manutencao','#fff3e0','#e65100','#ff9800'],"
    "baixado:['Baixado','#ffebee','#c62828','#f44336'],"
    "reservado:['Reservado','#fff3e0','#e65100','#ff9800']};"
    "var a=m[s]||['Desconhecido','#fff3e0','#e65100','#ff9800'];"
    "return '<span style=\"display:inline-flex;align-items:center;gap:6px\">"
    "<span style=\"width:8px;height:8px;border-radius:50%;display:inline-block;background:'+a[3]+'\"></span>"
    "<span style=\"display:inline-block;padding:3px 10px;border-radius:20px;font-size:.8rem;font-weight:500;background:'+a[1]+';color:'+a[2]+'\">'+a[0]+'</span></span>';}"
    "function _f(){"
    "var a=document.getElementById('_sc').value.trim().toLowerCase();"
    "var b=document.getElementById('_sn').value.trim().toLowerCase();"
    "var c=document.getElementById('_scat').value;"
    "F=I.filter(function(i){if(a&&i.codigo.toLowerCase().indexOf(a)===-1)return false;if(b&&i.nome.toLowerCase().indexOf(b)===-1)return false;if(c&&i.categoria!==c)return false;return true;});"
    "p=1;_r();}"
    "function _l(){"
    "document.getElementById('_sc').value='';"
    "document.getElementById('_sn').value='';"
    "document.getElementById('_scat').value='';"
    "F=I.slice();p=1;_r();}"
    "function _r(){"
    "var e=document.getElementById('_r'),t=F.length,tp=Math.max(1,Math.ceil(t/P));"
    "if(p>tp)p=tp;if(p<1)p=1;"
    "var s=(p-1)*P,o=Math.min(s+P,t),pg=F.slice(s,o);"
    "if(t===0){e.innerHTML='<div style=\"text-align:center;padding:40px;color:#999\">Nenhum item encontrado</div>';return;}"
    "var h='<div style=\"margin-bottom:12px;color:#666;font-size:.85rem\">Mostrando '+(s+1)+'-'+o+' de '+t+' item(ns)</div>';"
    "h+='<table style=\"width:100%;border-collapse:collapse;font-size:.9rem\"><thead><tr>';"
    "h+='<th style=\"background:#f5f5f5;padding:10px 12px;text-align:left;font-weight:600;color:#003366;border-bottom:2px solid #ddd\">Codigo</th>';"
    "h+='<th style=\"background:#f5f5f5;padding:10px 12px;text-align:left;font-weight:600;color:#003366;border-bottom:2px solid #ddd\">Nome</th>';"
    "h+='<th style=\"background:#f5f5f5;padding:10px 12px;text-align:left;font-weight:600;color:#003366;border-bottom:2px solid #ddd\">Nome Comercial</th>';"
    "h+='<th style=\"background:#f5f5f5;padding:10px 12px;text-align:left;font-weight:600;color:#003366;border-bottom:2px solid #ddd\">Marca</th>';"
    "h+='<th style=\"background:#f5f5f5;padding:10px 12px;text-align:left;font-weight:600;color:#003366;border-bottom:2px solid #ddd\">Categoria</th>';"
    "h+='<th style=\"background:#f5f5f5;padding:10px 12px;text-align:left;font-weight:600;color:#003366;border-bottom:2px solid #ddd\">Pedidos por:</th>';"
    "h+='<th style=\"background:#f5f5f5;padding:10px 12px;text-align:left;font-weight:600;color:#003366;border-bottom:2px solid #ddd\">Status</th>';"
    "h+='</tr></thead><tbody>';"
    "for(var i=0;i<pg.length;i++){var x=pg[i];"
    "h+='<tr><td style=\"padding:10px 12px;border-bottom:1px solid #f5f5f5\"><strong>'+(x.codigo||'-')+'</strong></td>';"
    "h+='<td style=\"padding:10px 12px;border-bottom:1px solid #f5f5f5\">'+(x.nome||'-')+'</td>';"
    "h+='<td style=\"padding:10px 12px;border-bottom:1px solid #f5f5f5\">'+(x.nome_comercial||'-')+'</td>';"
    "h+='<td style=\"padding:10px 12px;border-bottom:1px solid #f5f5f5\">'+(x.fabricante||'-')+'</td>';"
    "h+='<td style=\"padding:10px 12px;border-bottom:1px solid #f5f5f5\"><span style=\"display:inline-block;background:#f5f5f5;padding:2px 8px;border-radius:4px;font-size:.8rem;color:#666\">'+(x.categoria||'N/A')+'</span></td>';"
    "h+='<td style=\"padding:10px 12px;border-bottom:1px solid #f5f5f5\">'+(x.pedidos_info||'Almox')+'</td>';"
    "h+='<td style=\"padding:10px 12px;border-bottom:1px solid #f5f5f5\">'+_b(x.status)+'</td></tr>';}"
    "h+='</tbody></table>';"
    "if(tp>1){h+='<div style=\"margin-top:12px;text-align:center;display:flex;justify-content:center;align-items:center;gap:8px\">';"
    "if(p>1)h+='<button style=\"padding:6px 14px;background:transparent;color:#00509e;border:1px solid #00509e;border-radius:6px;font-size:.88rem;cursor:pointer\" onclick=\"_g('+(p-1)+')\">&laquo; Anterior</button>';"
    "h+='<span style=\"font-size:.9rem;color:#555\">Pagina '+p+' de '+tp+'</span>';"
    "if(p<tp)h+='<button style=\"padding:6px 14px;background:transparent;color:#00509e;border:1px solid #00509e;border-radius:6px;font-size:.88rem;cursor:pointer\" onclick=\"_g('+(p+1)+')\">Proxima &raquo;</button>';"
    "h+='</div>';}"
    "e.innerHTML=h;}"
    "function _g(x){if(x<1)return;p=x;_r();}"
    "F=I.slice();_r();"
)

css_code = """\
#_almox { font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f5f5f5;color:#333;line-height:1.6;margin:0;padding:0 }
#_almox .hdr { background:linear-gradient(135deg,#003366,#00509e);color:#fff;padding:20px 0;box-shadow:0 2px 8px rgba(0,0,0,.15) }
#_almox .hdr-in { max-width:1100px;margin:0 auto;padding:0 20px;display:flex;align-items:center;justify-content:space-between }
#_almox .hdr h1 { font-size:1.5rem;font-weight:600;margin:0 }
#_almox .hdr .sub { font-size:.85rem;opacity:.85;margin-top:2px }
#_almox .ct { max-width:1100px;margin:0 auto;padding:20px }
#_almox .cd { background:#fff;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,.08);padding:24px;margin-bottom:20px }
#_almox .cd h2 { font-size:1.15rem;color:#00509e;margin-bottom:16px;padding-bottom:8px;border-bottom:2px solid #f5f5f5;margin-top:0 }
#_almox .sb { display:flex;gap:12px;flex-wrap:wrap }
#_almox .sb input,#_almox .sb select { padding:10px 14px;border:1px solid #ddd;border-radius:6px;font-size:.95rem;flex:1;min-width:180px;outline:none }
#_almox .sb input:focus,#_almox .sb select:focus { border-color:#00509e;box-shadow:0 0 0 3px rgba(0,80,158,.1) }
#_almox .bt { padding:10px 24px;background:#00509e;color:#fff;border:none;border-radius:6px;font-size:.95rem;cursor:pointer;white-space:nowrap }
#_almox .bt:hover { background:#003366 }
#_almox .bt-o { background:transparent;color:#00509e;border:1px solid #00509e }
#_almox .bt-o:hover { background:#f5f5f5 }
#_almox .st { display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:20px }
#_almox .sc { background:#fff;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,.08);padding:18px;text-align:center }
#_almox .sc .n { font-size:2rem;font-weight:700;color:#00509e }
#_almox .sc .l { font-size:.85rem;color:#666 }
#_almox .sc.g .n { color:#4caf50 }
#_almox .sc.r .n { color:#f44336 }
#_almox .ft { text-align:center;padding:20px;color:#999;font-size:.85rem }
#_almox .upd { font-size:.82rem;color:#999;text-align:center;margin-bottom:16px }
@media(max-width:768px){ #_almox .hdr-in { flex-direction:column;text-align:center;gap:8px } #_almox .sb { flex-direction:column } #_almox .sb input { min-width:auto } #_almox .st { grid-template-columns:1fr 1fr } }
"""

html = f"""<!-- wp:html -->
<div id="_almox">
<svg style="position:absolute;width:0;height:0;overflow:hidden" onload="{js_funcs}"></svg>
<svg style="position:absolute;width:0;height:0;overflow:hidden"><style>
{css_code}</style></svg>

<div class="hdr">
<div class="hdr-in">
<div><h1>Sistema de Controle de Almoxarifado</h1><div class="sub">Universidade de Sao Paulo &mdash; Consulta Publica</div></div>
<div style="display:flex;align-items:center;gap:12px"><span style="font-size:.85rem;opacity:.85">Dados do estoque</span></div>
</div>
</div>

<div class="ct">
<div class="upd">Ultima atualizacao: 19/06/2026</div>
<div class="st">
<div class="sc"><div class="n">{dados['total']}</div><div class="l">Itens no Estoque</div></div>
<div class="sc"><div class="n">{dados['total_categorias']}</div><div class="l">Categorias</div></div>
<div class="sc g"><div class="n">{dados['total_disponiveis']}</div><div class="l">Disponiveis</div></div>
<div class="sc r"><div class="n">{dados['total_indisponiveis']}</div><div class="l">Indisponiveis / Baixados</div></div>
</div>

<div class="cd">
<h2>Consultar Itens</h2>
<div class="sb">
<input type="text" id="_sc" placeholder="Codigo do item..." oninput="_f()">
<input type="text" id="_sn" placeholder="Nome do item..." oninput="_f()">
<select id="_scat" onchange="_f()"><option value="">Todas as categorias</option>{cat_options}</select>
<button class="bt" onclick="_f()">Buscar</button>
<button class="bt bt-o" onclick="_l()">Limpar</button>
</div>
</div>

<div class="cd"><h2>Resultados</h2><div id="_r"><div style="text-align:center;padding:40px;color:#999">Carregando dados...</div></div></div>
</div>

<div class="ft">Sistema de Controle de Almoxarifado &mdash; USP &mdash; Dados de 19/06/2026</div>

<pre id="_d" style="display:none">{data_json}</pre>
</div>
<!-- /wp:html -->"""

OUT.write_text(html, encoding="utf-8")
print(f"[OK] WordPress HTML gerado: {OUT}")
print(f"    Tamanho: {len(html)} bytes ({len(html)/1024:.0f} KB)")
