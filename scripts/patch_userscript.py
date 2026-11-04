"""Parchea el userScript.js compilado de TizenTube para una version propia.

Hace, con verificacion estricta (cada paso exige exactamente una coincidencia):
  1. Quita las secciones "Apoyar" y "Redes sociales" de los ajustes (enlaces del autor).
  2. Oculta el menu del actualizador y apaga el chequeo de versiones (default,
     arranque y funcion de consulta a la API de GitHub).
  3. Reemplaza el nombre visible "TizenTube Cobalt" / "TizenTube" por la marca.
     No toca identificadores internos en minuscula (window.h5vcc.tizentube, ids).
  4. Antepone un aviso de licencia GPL-3.0 y atribucion al autor original.

Uso: python3 -I patch_userscript.py <entrada.js> <salida.js> <Marca> [<icono-ajustes.png>]
"""
import re
import sys

src, dst, brand = sys.argv[1:4]
t = open(src, encoding="utf-8").read()
orig_len = len(t)


def once(pattern, repl, text, flags=0, label=""):
    n = len(re.findall(pattern, text, flags))
    assert n == 1, f"[{label}] se esperaba 1 coincidencia y hay {n}"
    return re.sub(pattern, lambda m: repl(m) if callable(repl) else repl, text, count=1, flags=flags)


# 1) Secciones "Apoyar" + "Redes sociales": son los dos primeros elementos del arreglo de ajustes
a = t.index('{name:ga("settings.supportTT.title")')
b = t.index('{name:ga("settings.options.adBlock")')
assert a < b and t[a - 1] == "[" and t[b - 1] == ",", "limites inesperados de las secciones"
removed = t[a:b]
assert "supportTT" in removed and "socialMedia" in removed and "buymeacoffee" in removed
for o, c in ("{}", "[]", "()"):
    assert removed.count(o) == removed.count(c), f"tramo desbalanceado {o}{c}: no es un corte limpio"
assert removed.count('settings.options.socialMedia.title') == 1 and removed.count('settings.supportTT.title') == 2
t = t[:a] + t[b:]

# 2) Actualizador
t = once(r'window\.h5vcc&&window\.h5vcc\.tizentube\?(\{name:ga\("settings\.options\.updater\.title"\))',
         lambda m: "!1?" + m.group(1), t, label="menu updater")
t = once(r'(window\.h5vcc&&window\.h5vcc\.tizentube&&)\w+\("enableUpdater"\)',
         lambda m: m.group(1) + "!1", t, label="chequeo al arrancar")
t = once(r"enableUpdater:!0", "enableUpdater:!1", t, label="default enableUpdater")
t = once(r"(function \w+\(e\)\{)(var t=window\.h5vcc\.tizentube\.GetVersion\(\),i=Math\.floor\(Date\.now\(\)/1e3\);fetch\(\"https://api\.github\.com/)",
         lambda m: m.group(1) + "return;" + m.group(2), t, label="funcion de consulta")
t = once(r"https://api\.github\.com/repos/reisxd/TizenTubeCobalt/releases/latest", "about:blank", t, label="url api")

# 2b) Credito visible bajo el titulo de los ajustes ("Hecho por ... (reisxd)"): se vacia.
#     La atribucion queda en el aviso de licencia (paso 4) y en el README del repositorio.
n_made = len(re.findall(r'madeByText:"(?:[^"\\]|\\.)*"', t))
assert n_made >= 30, f"madeByText: se esperaban >=30 traducciones y hay {n_made}"
t = re.sub(r'madeByText:"(?:[^"\\]|\\.)*"', 'madeByText:""', t)


# 2c) Textos huerfanos de la seccion "Apoyar" (ya no se muestran): se eliminan los bloques supportTT:{...}
def _block_end(s, start):
    """Indice del '}' que cierra el '{' en `start`, respetando strings JS."""
    depth, i, q = 0, start, None
    while i < len(s):
        ch = s[i]
        if q:
            if ch == "\\":
                i += 1
            elif ch == q:
                q = None
        elif ch in "\"'`":
            q = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise AssertionError("bloque sin cerrar")


n_support = 0
pos = 0
while True:
    k = t.find("supportTT:{", pos)
    if k == -1:
        break
    end = _block_end(t, k + len("supportTT:"))
    # quitar tambien una coma contigua para no dejar `,,` ni `{,`
    if t[end + 1] == ",":
        t = t[:k] + t[end + 2:]
    elif t[k - 1] == ",":
        t = t[:k - 1] + t[end + 1:]
    else:
        t = t[:k] + t[end + 1:]
    n_support += 1
    pos = k
assert n_support >= 30, f"supportTT: se esperaban >=30 bloques y hay {n_support}"

# 2d) Imagen de la entrada de ajustes (opcional, 4to argumento): se embebe como data URI PNG
#     en lugar del escudo que el original pide a gstatic.com.
icon_png = sys.argv[4] if len(sys.argv) > 4 else None
if icon_png:
    import base64
    raw = open(icon_png, "rb").read()
    assert raw[:8] == b"\x89PNG\r\n\x1a\n", "el icono de ajustes debe ser PNG"
    uri = "data:image/png;base64," + base64.b64encode(raw).decode()
    t = once(r"https://www\.gstatic\.com/ytlr/img/parent_code\.png", uri, t, label="icono de ajustes")

# 2e) Recarga del inicio (SOFT_RELOAD_PAGE) con 1,5 s de espera (de inmediato deja el feed vacio) + dialogo de
#     salida al tocar "Atras" dos veces + filtro ampliado de anuncios del inicio.
EXIT_JS = r"""
try{var __bl=0,__bd=null,__bs=0,__bk=[27,4,461,10009];
function __bc(){if(__bd){__bd.remove();__bd=null}}
function __bx(){__bc();try{PO({signalAction:{signal:"EXIT_APP"}})}catch(e){}setTimeout(function(){try{window.close()}catch(e){}},900)}
function __bh(){var b=__bd.querySelectorAll("button");for(var i=0;i<b.length;i++){b[i].style.background=i===__bs?"#e50914":"#333";b[i].style.outline=i===__bs?"3px solid #fff":"none"}}
function __bo(){__bc();__bs=0;__bd=document.createElement("div");
__bd.style.cssText="position:fixed;left:0;top:0;right:0;bottom:0;background:rgba(0,0,0,.75);z-index:2147483647;display:flex;align-items:center;justify-content:center;font-family:sans-serif";
__bd.innerHTML='<div style="background:#1c1c1c;color:#fff;padding:40px 56px;border-radius:16px;text-align:center"><div style="font-size:34px;margin-bottom:28px">¿Cerrar BRAND?</div><button style="font-size:28px;color:#fff;border:0;border-radius:10px;padding:14px 40px;margin:0 12px">Cerrar app</button><button style="font-size:28px;color:#fff;border:0;border-radius:10px;padding:14px 40px;margin:0 12px">Cancelar</button></div>';
document.body.appendChild(__bd);__bh()}
document.addEventListener("keydown",function(e){var k=e.keyCode;
if(__bd){if(k===37||k===39||k===38||k===40){__bs=__bs?0:1;__bh()}else if(k===13||k===32){__bs===0?__bx():__bc()}else if(__bk.indexOf(k)>=0){__bc()}
e.preventDefault();e.stopImmediatePropagation();return}
if(__bk.indexOf(k)>=0){var n=Date.now();if(n-__bl<1200){__bl=0;__bo();e.preventDefault();e.stopImmediatePropagation()}else{__bl=n}}},true)}catch(e){}
"""


def _reload(m):
    po = re.search(r'(\w+)\(\{signalAction:\{signal:"SOFT_RELOAD_PAGE"', m.group(2)).group(1)
    js = EXIT_JS.replace("PO", po).replace("BRAND", brand).replace("\n", "")
    import os
    d = os.environ.get("RELOAD_DELAY_MS", "1500")
    if d == "0":  # igual que el original: recarga inmediata
        return '%s("reloadHomeOnStartup")&&%s;%s' % (m.group(1), m.group(2), js)
    return '%s("reloadHomeOnStartup")&&setTimeout(()=>{%s},%s);%s' % (m.group(1), m.group(2), d, js)


t = once(r'(\w+)\("reloadHomeOnStartup"\)&&(\(\w+\("launchToOnStartup"\)\?\w+\(JSON\.parse\(\w+\("launchToOnStartup"\)\)\):\w+\(\{signalAction:\{signal:"SOFT_RELOAD_PAGE"\}\}\)\))',
         _reload, t, label="recarga al iniciar con espera")
t = once(r'(sectionListRenderer\.contents\.filter\((\w+)=>)!\2\.adSlotRenderer\)',
         lambda m: m.group(1) + '!%s.adSlotRenderer&&!Object.keys(%s).some(k=>/^ad[A-Z]|[Mm]asthead/.test(k)))' % (m.group(2), m.group(2)),
         t, label="filtro de anuncios del inicio")

# 2e-bis) Limpieza generica de anuncios en el feed: en cada respuesta JSON se quitan de los arreglos los elementos
#     que son anuncios (adSlotRenderer, masthead, "Patrocinado"/"Sponsored" en mosaicos). Solo con AdBlock activado.
ADCLEAN = r"""function __ma(it){var ks=Object.keys(it),i,k,v,k2;for(i=0;i<ks.length;i++){k=ks[i];if(/^ad[A-Z]|[Mm]asthead|promotedSparkles/.test(k))return!0;v=it[k];if(v&&typeof v==="object"&&!Array.isArray(v)){for(k2 in v){if(/^adSlot|^adLayout|^inFeedAd|^tvAdRenderer/.test(k2))return!0}}}
if(it.tileRenderer||it.lockupViewModel||it.shelfRenderer===void 0&&it.richItemRenderer){try{return/"(Patrocinado|Sponsored|Publicidad|Anuncio)"|adSlotRenderer|inFeedAdLayout|tvAdRenderer/.test(JSON.stringify(it))}catch(e){}}return!1}
function __mz(o,d){if(!o||typeof o!=="object"||(d=d||0)>14)return;if(Array.isArray(o)){for(var i=o.length-1;i>=0;i--){var it=o[i];if(it&&typeof it==="object"&&!Array.isArray(it)&&__ma(it)){o.splice(i,1)}else __mz(it,d+1)}}else{for(var k in o)__mz(o[k],d+1)}}
"""
t = once(r'(var (\w+)=JSON\.parse;JSON\.parse=function\(\)\{var (\w+)=\2\.apply\(this,arguments\);)',
         lambda m: ADCLEAN.replace("\n", "") + m.group(1) + 'try{if(Ma("enableAdBlock"))__mz(%s)}catch(_e){}' % m.group(3),
         t, label="limpieza de anuncios")
# Ma = lector de config: se resuelve por nombre en el codigo minificado

# 2f) Rendimiento: se apagan las funciones mas pesadas (una sola vez; despues se pueden volver a prender en Ajustes).
#     DeArrow (consulta de red por cada miniatura), previsualizaciones de video, aviso de bienvenida y avisos de SponsorBlock.
t = once(r'(try\{(\w+)=JSON\.parse\(window\.localStorage\[(\w+)\]\)\}catch\(e\)\{console\.warn\("Config read failed:",e\),\2=(\w+)\})',
         lambda m: m.group(1) + (';try{if(!window.localStorage["myv-perf1"]){var __mP={enableDeArrow:!1,enablePreviews:!1,showWelcomeToast:!1,enableSponsorBlockToasts:!1};'
                                 'for(var __mK in __mP){%s[__mK]=__mP[__mK]}window.localStorage[%s]=JSON.stringify(%s);window.localStorage["myv-perf1"]="1"}}catch(e){}' % (m.group(2), m.group(3), m.group(2))),
         t, label="rendimiento")
for k_ in ("enableDeArrow", "enablePreviews", "showWelcomeToast", "enableSponsorBlockToasts"):
    t = once(k_ + r":!0,", k_ + ":!1,", t, label="default " + k_)

# 3) Marca visible
before = len(re.findall("TizenTube", t))
t = t.replace("TizenTube Cobalt", brand).replace("TizenTube", brand)

# 4) Aviso de licencia y atribucion
header = ("/*! %s - version derivada de TizenTube (c) Reis Can (reisxd), GPL-3.0-only. "
          "Fuente original: https://github.com/reisxd/TizenTube . Esta copia modifica textos visibles "
          "y desactiva el actualizador integrado. */\n" % brand)
t = header + t

open(dst, "w", encoding="utf-8").write(t)
print(f"ok: {orig_len} -> {len(t)} bytes | secciones quitadas: 2 | 'TizenTube' reemplazados: {before} | marca: {brand}")
