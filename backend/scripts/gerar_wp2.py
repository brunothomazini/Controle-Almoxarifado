#!/usr/bin/env python3
"""Generate a WordPress-friendly version - direct approach (no SVG tricks)."""
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

html = f"""<!-- wp:html -->
<style>
#a-r .hdr {{ background:linear-gradient(135deg,#003366,#00509e);color:#fff;padding:20px 0;box-shadow:0 2px 8px rgba(0,0,0,.15) }}
#a-r .hdr-in {{ max-width:1100px;margin:0 auto;padding:0 20px;display:flex;align-items:center;justify-content:space-between }}
#a-r .hdr h1 {{ font-size:1.5rem;font-weight:600;margin:0 }}
#a-r .hdr .sub {{ font-size:.85rem;opacity:.85;margin-top:2px }}
#a-r .ct {{ max-width:1100px;margin:0 auto;padding:20px }}
#a-r .cd {{ background:#fff;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,.08);padding:24px;margin-bottom:20px }}
#a-r .cd h2 {{ font-size:1.15rem;color:#00509e;margin-bottom:16px;padding-bottom:8px;border-bottom:2px solid #f5f5f5;margin-top:0 }}
#a-r .sb {{ display:flex;gap:12px;flex-wrap:wrap }}
#a-r .sb input,#a-r .sb select {{ padding:10px 14px;border:1px solid #ddd;border-radius:6px;font-size:.95rem;flex:1;min-width:180px;outline:none }}
#a-r .sb input:focus,#a-r .sb select:focus {{ border-color:#00509e;box-shadow:0 0 0 3px rgba(0,80,158,.1) }}
#a-r .bt {{ display:inline-block;padding:10px 24px;background:#00509e;color:#fff;border:none;border-radius:6px;font-size:.95rem;cursor:pointer;white-space:nowrap;text-decoration:none }}
#a-r .bt:hover {{ background:#003366 }}
#a-r .bt-o {{ background:transparent;color:#00509e;border:1px solid #00509e }}
#a-r .bt-o:hover {{ background:#f5f5f5 }}
#a-r .st {{ display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:20px }}
#a-r .sc {{ background:#fff;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,.08);padding:18px;text-align:center }}
#a-r .sc .n {{ font-size:2rem;font-weight:700;color:#00509e }}
#a-r .sc .l {{ font-size:.85rem;color:#666 }}
#a-r .sc.g .n {{ color:#4caf50 }}
#a-r .sc.r .n {{ color:#f44336 }}
#a-r .ft {{ text-align:center;padding:20px;color:#999;font-size:.85rem }}
#a-r .upd {{ font-size:.82rem;color:#999;text-align:center;margin-bottom:16px }}
#a-r table {{ width:100%;border-collapse:collapse;font-size:.9rem }}
#a-r th {{ background:#f5f5f5;padding:10px 12px;text-align:left;font-weight:600;color:#003366;border-bottom:2px solid #ddd }}
#a-r td {{ padding:10px 12px;border-bottom:1px solid #f5f5f5 }}
#a-r .inf {{ margin-bottom:12px;color:#666;font-size:.85rem }}
#a-r .pag {{ margin-top:12px;text-align:center;display:flex;justify-content:center;align-items:center;gap:8px }}
#a-r .pag .bt {{ padding:6px 14px;font-size:.88rem }}
#a-r .pag span {{ font-size:.9rem;color:#555 }}
#a-r .tag {{ display:inline-block;background:#f5f5f5;padding:2px 8px;border-radius:4px;font-size:.8rem;color:#666 }}
#a-r .si {{ display:inline-flex;align-items:center;gap:6px }}
#a-r .sg {{ display:inline-block;padding:3px 10px;border-radius:20px;font-size:.8rem;font-weight:500 }}
#a-r .emp {{ text-align:center;padding:40px;color:#999 }}
@media(max-width:768px){{ #a-r .hdr-in {{ flex-direction:column;text-align:center;gap:8px }} #a-r .sb {{ flex-direction:column }} #a-r .sb input {{ min-width:auto }} #a-r .st {{ grid-template-columns:1fr 1fr }} }}
</style>
<div id="a-r" style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f5f5f5;color:#333;line-height:1.6">

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
<input type="text" id="s_c" placeholder="Codigo do item..." oninput="r()">
<input type="text" id="s_n" placeholder="Nome do item..." oninput="r()">
<select id="s_t" onchange="r()"><option value="">Todas as categorias</option>{cat_options}</select>
<a class="bt" href="javascript:r()">Buscar</a>
<a class="bt bt-o" href="javascript:l()">Limpar</a>
</div>
</div>

<div class="cd"><h2>Resultados</h2><div id="res"><div class="emp">Carregando dados...</div></div></div>
</div>

<div class="ft">Sistema de Controle de Almoxarifado &mdash; USP &mdash; Dados de 19/06/2026</div>

<pre id="d" style="display:none">{data_json}</pre>

<script>
var _d=JSON.parse(document.getElementById('d').textContent);
var I=_d.itens,C=_d.categorias,P=50,p=1,F=[];
var _t=document.getElementById('s_t');
_t.innerHTML='<option value="">Todas as categorias</option>';
for(var i=0;i<C.length;i++){{var o=document.createElement('option');o.value=C[i];o.textContent=C[i];_t.appendChild(o);}}
function b(s){{var m={{disponivel:['Disponivel','#e8f5e9','#2e7d32','#4caf50'],emprestado:['Emprestado','#fff3e0','#e65100','#ff9800'],manutencao:['Manutencao','#fff3e0','#e65100','#ff9800'],baixado:['Baixado','#ffebee','#c62828','#f44336'],reservado:['Reservado','#fff3e0','#e65100','#ff9800']}};var a=m[s]||['Desconhecido','#fff3e0','#e65100','#ff9800'];return '<span class="si"><span style="width:8px;height:8px;border-radius:50%;display:inline-block;background:'+a[3]+'"></span><span class="sg" style="background:'+a[1]+';color:'+a[2]+'">'+a[0]+'</span></span>';}}
function r(){{var a=document.getElementById('s_c').value.trim().toLowerCase();var b=document.getElementById('s_n').value.trim().toLowerCase();var c=document.getElementById('s_t').value;F=I.filter(function(i){{if(a&&i.codigo.toLowerCase().indexOf(a)===-1)return false;if(b&&i.nome.toLowerCase().indexOf(b)===-1)return false;if(c&&i.categoria!==c)return false;return true;}});p=1;render();}}
function l(){{document.getElementById('s_c').value='';document.getElementById('s_n').value='';document.getElementById('s_t').value='';F=I.slice();p=1;render();}}
function render(){{var e=document.getElementById('res'),t=F.length,tp=Math.max(1,Math.ceil(t/P));if(p>tp)p=tp;if(p<1)p=1;var s=(p-1)*P,o=Math.min(s+P,t),pg=F.slice(s,o);if(t===0){{e.innerHTML='<div class="emp">Nenhum item encontrado</div>';return;}}var h='<div class="inf">Mostrando '+(s+1)+'-'+o+' de '+t+' item(ns)</div><table><thead><tr><th>Codigo</th><th>Nome</th><th>Nome Comercial</th><th>Marca</th><th>Categoria</th><th>Pedidos por:</th><th>Status</th></tr></thead><tbody>';for(var i=0;i<pg.length;i++){{var x=pg[i];h+='<tr><td><strong>'+(x.codigo||'-')+'</strong></td><td>'+(x.nome||'-')+'</td><td>'+(x.nome_comercial||'-')+'</td><td>'+(x.fabricante||'-')+'</td><td><span class="tag">'+(x.categoria||'N/A')+'</span></td><td>'+(x.pedidos_info||'Almox')+'</td><td>'+b(x.status)+'</td></tr>';}}h+='</tbody></table>';if(tp>1){{h+='<div class="pag">';if(p>1)h+='<a class="bt bt-o" href="javascript:g('+(p-1)+')">&laquo; Anterior</a>';h+='<span>Pagina '+p+' de '+tp+'</span>';if(p<tp)h+='<a class="bt bt-o" href="javascript:g('+(p+1)+')">Proxima &raquo;</a>';h+='</div>';}}e.innerHTML=h;}}
function g(x){{if(x<1)return;p=x;render();}}
F=I.slice();render();
</script>
</div>
<!-- /wp:html -->"""

OUT.write_text(html, encoding="utf-8")
print(f"[OK] WP HTML gerado: {OUT}")
print(f"    Tamanho: {len(html)} bytes ({len(html)/1024:.0f} KB)")
