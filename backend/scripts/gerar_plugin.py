#!/usr/bin/env python3
"""Generate a WordPress plugin with embedded data."""
import json, sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "data" / "almoxarifado.db"
OUT = Path(__file__).resolve().parent.parent.parent / "plugins" / "almoxarifado-plugin" / "almoxarifado-consulta.php"

conn = sqlite3.connect(str(DB))
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT id, nome FROM categorias ORDER BY nome")
categorias = [r["nome"] for r in cur.fetchall()]

cur.execute(
    "SELECT i.codigo,i.nome,i.nome_comercial,i.fabricante,i.categoria_id,"
    "i.quantidade_atual,i.unidade_medida,i.solicitar_por_email,i.tipo_controle,i.status "
    "FROM itens i ORDER BY i.nome"
)

cats_map = {}
cur2 = conn.cursor()  # fresh cursor for cat names
cur2.execute("SELECT id, nome FROM categorias")
for r in cur2:
    cats_map[r["id"]] = r["nome"]

itens = []
for r in cur.fetchall():
    row = dict(r)
    cat_nome = cats_map.get(row["categoria_id"], "N/A")
    tc = (row["tipo_controle"] or "").lower()
    if cat_nome == "Informatica":
        ped = "solicitar para o setor de Informatica"
    elif tc == "almoxarifado":
        ped = "Almox"
    elif row["solicitar_por_email"]:
        ped = "e-mail padronizados@fob.usp.br"
    else:
        ped = "Almox"
    itens.append({
        "c": row["codigo"], "n": row["nome"],
        "nc": row["nome_comercial"] or "-",
        "f": row["fabricante"] or "-",
        "cat": cat_nome,
        "q": row["quantidade_atual"] or 0,
        "u": row["unidade_medida"] or "un",
        "s": str.lower(row["status"] or "DISPONIVEL"),
        "p": ped,
    })
conn.close()

total = len(itens)
disp = sum(1 for i in itens if i["s"] == "disponivel")
data_json = json.dumps({"itens": itens, "cats": categorias}, ensure_ascii=False)

cat_options = "\n".join(f"<option value=\"{c}\">{c}</option>" for c in categorias)

php_code = """<?php
/**
 * Plugin Name: Almoxarifado - Consulta Publica
 * Description: Consulta de estoque do almoxarifado - FOB/USP
 * Version: 1.0
 */

function almoxarifado_consulta() {
    $html = '<style>
#alm{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f5f5f5;color:#333;line-height:1.6}
#alm .hdr{background:linear-gradient(135deg,#003366,#00509e);color:#fff;padding:20px 0;box-shadow:0 2px 8px rgba(0,0,0,.15)}
#alm .hdr-in{max-width:1100px;margin:0 auto;padding:0 20px;display:flex;align-items:center;justify-content:space-between}
#alm .hdr h1{font-size:1.5rem;font-weight:600;margin:0}
#alm .hdr .sub{font-size:.85rem;opacity:.85;margin-top:2px}
#alm .ct{max-width:1100px;margin:0 auto;padding:20px}
#alm .cd{background:#fff;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,.08);padding:24px;margin-bottom:20px}
#alm .cd h2{font-size:1.15rem;color:#00509e;margin-bottom:16px;padding-bottom:8px;border-bottom:2px solid #f5f5f5;margin-top:0}
#alm .sb{display:flex;gap:12px;flex-wrap:wrap}
#alm .sb input,#alm .sb select{padding:10px 14px;border:1px solid #ddd;border-radius:6px;font-size:.95rem;flex:1;min-width:180px;outline:none}
#alm .sb input:focus,#alm .sb select:focus{border-color:#00509e;box-shadow:0 0 0 3px rgba(0,80,158,.1)}
#alm .bt{display:inline-block;padding:10px 24px;background:#00509e;color:#fff;border:none;border-radius:6px;font-size:.95rem;cursor:pointer;white-space:nowrap;text-decoration:none}
#alm .bt:hover{background:#003366}
#alm .bt-o{background:transparent;color:#00509e;border:1px solid #00509e}
#alm .bt-o:hover{background:#f5f5f5}
#alm .st{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:20px}
#alm .sc{background:#fff;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,.08);padding:18px;text-align:center}
#alm .sc .n{font-size:2rem;font-weight:700;color:#00509e}
#alm .sc .l{font-size:.85rem;color:#666}
#alm .sc.g .n{color:#4caf50}
#alm .sc.r .n{color:#f44336}
#alm .ft{text-align:center;padding:20px;color:#999;font-size:.85rem}
#alm .upd{font-size:.82rem;color:#999;text-align:center;margin-bottom:16px}
#alm table{width:100%;border-collapse:collapse;font-size:.9rem}
#alm th{background:#f5f5f5;padding:10px 12px;text-align:left;font-weight:600;color:#003366;border-bottom:2px solid #ddd}
#alm td{padding:10px 12px;border-bottom:1px solid #f5f5f5}
#alm .inf{margin-bottom:12px;color:#666;font-size:.85rem}
#alm .pag{margin-top:12px;text-align:center;display:flex;justify-content:center;align-items:center;gap:8px}
#alm .pag .bt{padding:6px 14px;font-size:.88rem}
#alm .pag span{font-size:.9rem;color:#555}
#alm .tag{display:inline-block;background:#f5f5f5;padding:2px 8px;border-radius:4px;font-size:.8rem;color:#666}
#alm .si{display:inline-flex;align-items:center;gap:6px}
#alm .emp{text-align:center;padding:40px;color:#999}
@media(max-width:768px){#alm .hdr-in{flex-direction:column;text-align:center;gap:8px}#alm .sb{flex-direction:column}#alm .sb input{min-width:auto}#alm .st{grid-template-columns:1fr 1fr}}
<\/style>
<div id="alm">
<div class="hdr"><div class="hdr-in"><div><h1>Sistema de Controle de Almoxarifado</h1><div class="sub">Universidade de Sao Paulo &mdash; Consulta Publica</div></div></div></div>
<div class="ct">
<div class="upd">Ultima atualizacao: """ + datetime.now().strftime("%d/%m/%Y") + """</div>
<div class="st">
<div class="sc"><div class="n">""" + str(total) + """</div><div class="l">Itens no Estoque</div></div>
<div class="sc"><div class="n">""" + str(len(categorias)) + """</div><div class="l">Categorias</div></div>
<div class="sc g"><div class="n">""" + str(disp) + """</div><div class="l">Disponiveis</div></div>
<div class="sc r"><div class="n">""" + str(total - disp) + """</div><div class="l">Indisponiveis / Baixados</div></div>
</div>
<div class="cd"><h2>Consultar Itens</h2><div class="sb">
<input type="text" id="alm_sc" placeholder="Codigo..." oninput="alm_f()">
<input type="text" id="alm_sn" placeholder="Nome do item..." oninput="alm_f()">
<select id="alm_t" onchange="alm_f()"><option value="">Todas as categorias</option>""" + cat_options + """</select>
<a class="bt" href="javascript:alm_f()">Buscar</a>
<a class="bt bt-o" href="javascript:alm_l()">Limpar</a>
</div></div>
<div class="cd"><h2>Resultados</h2><div id="alm_r"><div class="emp">Carregando dados...</div></div></div>
</div>
<div class="ft">Sistema de Controle de Almoxarifado &mdash; USP</div>
</div>
<script>
var almD=""" + data_json + """;
var almI=almD.itens,almC=almD.cats,almP=50,alm_p=1,almF=[];
var almS=document.getElementById("alm_t");
almS.innerHTML="<option value=\"\">Todas as categorias</option>";
for(var i=0;i<almC.length;i++){var o=document.createElement("option");o.value=almC[i];o.textContent=almC[i];almS.appendChild(o);}
function alm_b(s){var m={disponivel:["Disponivel","#e8f5e9","#2e7d32","#4caf50"],emprestado:["Emprestado","#fff3e0","#e65100","#ff9800"],manutencao:["Manutencao","#fff3e0","#e65100","#ff9800"],baixado:["Baixado","#ffebee","#c62828","#f44336"],reservado:["Reservado","#fff3e0","#e65100","#ff9800"]};var a=m[s]||["Desconhecido","#fff3e0","#e65100","#ff9800"];return "<span style=\"display:inline-flex;align-items:center;gap:6px\"><span style=\"width:8px;height:8px;border-radius:50%;display:inline-block;background:"+a[3]+"\"></span><span style=\"display:inline-block;padding:3px 10px;border-radius:20px;font-size:.8rem;font-weight:500;background:"+a[1]+";color:"+a[2]+"\">"+a[0]+"</span></span>";}
function alm_f(){var a=document.getElementById("alm_sc").value.trim().toLowerCase();var b=document.getElementById("alm_sn").value.trim().toLowerCase();var c=document.getElementById("alm_t").value;almF=almI.filter(function(i){if(a&&i.c.toLowerCase().indexOf(a)===-1)return false;if(b&&i.n.toLowerCase().indexOf(b)===-1)return false;if(c&&i.cat!==c)return false;return true;});alm_p=1;alm_r();}
function alm_l(){document.getElementById("alm_sc").value="";document.getElementById("alm_sn").value="";document.getElementById("alm_t").value="";almF=almI.slice();alm_p=1;alm_r();}
function alm_r(){var e=document.getElementById("alm_r"),t=almF.length,tp=Math.max(1,Math.ceil(t/almP));if(alm_p>tp)alm_p=tp;if(alm_p<1)alm_p=1;var s=(alm_p-1)*almP,o=Math.min(s+almP,t),pg=almF.slice(s,o);if(t===0){e.innerHTML="<div class=\"emp\">Nenhum item encontrado</div>";return;}var h="<div class=\"inf\">Mostrando "+(s+1)+"-"+o+" de "+t+" item(ns)</div><table><thead><tr><th>Codigo</th><th>Nome</th><th>Nome Comercial</th><th>Marca</th><th>Categoria</th><th>Pedidos por:</th><th>Status</th></tr></thead><tbody>";for(var i=0;i<pg.length;i++){var x=pg[i];h+="<tr><td><strong>"+(x.c||"-")+"</strong></td><td>"+(x.n||"-")+"</td><td>"+(x.nc||"-")+"</td><td>"+(x.f||"-")+"</td><td><span class=\"tag\">"+(x.cat||"N/A")+"</span></td><td>"+(x.p||"Almox")+"</td><td>"+alm_b(x.s)+"</td></tr>";}h+="</tbody></table>";if(tp>1){h+="<div class=\"pag\">";if(alm_p>1)h+="<a class=\"bt bt-o\" href=\"javascript:alm_g("+(alm_p-1)+')\">&laquo; Anterior</a>";h+="<span>Pagina "+alm_p+" de "+tp+"</span>";if(alm_p<tp)h+="<a class=\"bt bt-o\" href=\"javascript:alm_g("+(alm_p+1)+')\">Proxima &raquo;</a>";h+="</div>";}e.innerHTML=h;}
function alm_g(x){if(x<1)return;alm_p=x;alm_r();}
almF=almI.slice();alm_r();
<\/script>';

    return $html;
}
add_shortcode('almoxarifado', 'almoxarifado_consulta');
""";

import os
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(php_code, encoding="utf-8")
print(f"[OK] Plugin gerado: {OUT}")
print(f"    Tamanho: {len(php_code)} bytes ({len(php_code)/1024:.0f} KB)")
