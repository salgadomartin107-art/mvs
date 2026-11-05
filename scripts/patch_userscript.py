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
t = re.sub(r'madeByText:"(?:[^"\\]|\\.)*"', 'madeByText:"%s"' % __import__("os").environ.get("COVER_LABEL", ""), t)


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
if icon_png and icon_png.startswith("https://"):
    # icono por URL (mantiene el script liviano)
    t = once(r"https://www\.gstatic\.com/ytlr/img/parent_code\.png", icon_png, t, label="icono de ajustes (URL)")
elif icon_png:
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
var bx=document.createElement("div");bx.style.cssText="background:#1c1c1c;color:#fff;padding:40px 56px;border-radius:16px;text-align:center";
var q=document.createElement("div");q.style.cssText="font-size:34px;margin-bottom:28px";q.textContent="\u00bfCerrar BRAND?";bx.appendChild(q);
var tt=["Cerrar app","Cancelar"];for(var i=0;i<2;i++){var bt=document.createElement("button");bt.style.cssText="font-size:28px;color:#fff;border:0;border-radius:10px;padding:14px 40px;margin:0 12px";bt.textContent=tt[i];bx.appendChild(bt)}
__bd.appendChild(bx);document.body.appendChild(__bd);__bh()}
document.addEventListener("keydown",function(e){var k=e.keyCode;
if(__bd){if(k===37||k===39||k===38||k===40){__bs=__bs?0:1;__bh()}else if(k===13||k===32){__bs===0?__bx():__bc()}else if(__bk.indexOf(k)>=0){__bc()}
e.preventDefault();e.stopImmediatePropagation();return}
if(__bk.indexOf(k)>=0){var n=Date.now();if(n-__bl<1200){__bl=0;__bo();e.preventDefault();e.stopImmediatePropagation()}else{__bl=n}}},true)}catch(e){}
"""


DIAG_JS = r"""setTimeout(function(){try{var D=window.__myvD||{},c=document.getElementById("__myv_cover"),r=c?c.getBoundingClientRect():null,tp=document.elementFromPoint(640,360),s="rs:"+D.rs+" b0:"+D.b+" ap:"+D.ap+" dt:"+(Date.now()-(D.t0||0))+" el:"+(c?1:0)+(r?" "+Math.round(r.width)+"x"+Math.round(r.height):"")+" top:"+(tp?(tp.id||tp.tagName):"-")+" ch:"+(document.body?document.body.children.length:-1);PO({openPopupAction:{popupType:"TOAST",popup:{overlayToastRenderer:{title:{simpleText:"MyouVTube "+LABEL},subtitle:{simpleText:s}}}}})}catch(e){}},1200);"""


def _reload(m):
    po = re.search(r'(\w+)\(\{signalAction:\{signal:"SOFT_RELOAD_PAGE"', m.group(2)).group(1)
    js = EXIT_JS.replace("PO", po).replace("BRAND", brand).replace("\n", "")
    import os
    d = os.environ.get("RELOAD_DELAY_MS", "1500")
    if d == "0":  # igual que el original: recarga inmediata
        dg = DIAG_JS.replace("PO", po).replace("LABEL", '"%s"' % __import__("os").environ.get("COVER_LABEL", "")).replace("\n", "")
    return 'window.__myvReloaded=1;%s;%s%s' % (m.group(2), dg, js)
    return '%s("reloadHomeOnStartup")&&setTimeout(()=>{window.__myvReloaded=1;%s},%s);%s' % (m.group(1), m.group(2), d, js)


t = once(r'(\w+)\("reloadHomeOnStartup"\)&&(\(\w+\("launchToOnStartup"\)\?\w+\(JSON\.parse\(\w+\("launchToOnStartup"\)\)\):\w+\(\{signalAction:\{signal:"SOFT_RELOAD_PAGE"\}\}\)\))',
         _reload, t, label="recarga al iniciar con espera")
t = once(r'(sectionListRenderer\.contents\.filter\((\w+)=>)!\2\.adSlotRenderer\)',
         lambda m: m.group(1) + '!%s.adSlotRenderer&&!Object.keys(%s).some(k=>/^ad[A-Z]|[Mm]asthead/.test(k)))' % (m.group(2), m.group(2)),
         t, label="filtro de anuncios del inicio")

# 2e-bis) Limpieza generica de anuncios en el feed: en cada respuesta JSON se quitan de los arreglos los elementos
#     que son anuncios (adSlotRenderer, masthead, "Patrocinado"/"Sponsored" en mosaicos). Solo con AdBlock activado.
ADCLEAN = r"""function __mk(it){var ks=Object.keys(it),i,k,v,k2;for(i=0;i<ks.length;i++){k=ks[i];if(/^ad[A-Z]|[Mm]asthead|promotedSparkles/.test(k))return!0;v=it[k];if(v&&typeof v==="object"&&!Array.isArray(v)){for(k2 in v){if(/^adSlot|^adLayout|^inFeedAd|^tvAdRenderer|[Mm]asthead/.test(k2))return!0}}}return!1}
function __ms(it){try{var s=JSON.stringify(it);return s.length<60000&&/"(Patrocinado|Sponsored|Publicidad|Anuncio)"|adSlotRenderer|inFeedAdLayout|tvAdRenderer|[Mm]astheadAd/.test(s)}catch(e){return!1}}
function __mz(o,d){if(!o||typeof o!=="object"||(d=d||0)>14)return;if(Array.isArray(o)){for(var i=o.length-1;i>=0;i--){var it=o[i];if(it&&typeof it==="object"){if(!Array.isArray(it)&&__mk(it)){o.splice(i,1);continue}__mz(it,d+1);if(!Array.isArray(it)&&__ms(it))o.splice(i,1)}}}else{for(var k in o){if(/[Mm]asthead|^adSlot/.test(k)){delete o[k]}else __mz(o[k],d+1)}}}
"""
def _cover_set():
    """Cortina SIN innerHTML (YouTube exige Trusted Types y lo bloquea): imagen animada por URL https + nombre."""
    img = sys.argv[5] if len(sys.argv) > 5 else None
    label = (brand + " " + __import__("os").environ.get("COVER_LABEL", "")).strip()
    if not img:
        return 'd.textContent="%s"' % label
    assert img.startswith("https://"), "la imagen de la cortina debe ser una URL https"
    return ('d.style.background="#000";var w=document.createElement("div");w.style.cssText="text-align:center";'
            'var bx=document.createElement("div");bx.style.cssText="position:relative;height:64vh;width:61.4vh;margin:0 auto";'
            'var im=document.createElement("img");im.alt="";im.style.cssText="position:absolute;left:0;top:0;height:100%%";im.src="%s";bx.appendChild(im);'
            'var tx=document.createElement("div");tx.style.cssText="margin-top:2vh;font:4vh sans-serif;color:#aaa";tx.textContent="%s";'
            'w.appendChild(bx);w.appendChild(tx);d.appendChild(w)' % (img, label))


# Cortina: tapa el inicio (que llega sin filtrar) hasta que llega el feed ya limpio tras la recarga; maximo 6 s.
COVER_JS = r"""(function(){try{function mk(){var d=document.createElement("div");d.id="__myv_cover";d.style.cssText="position:fixed;left:0;top:0;right:0;bottom:0;background:#0f0f0f;z-index:2147483646;display:flex;align-items:center;justify-content:center;color:#777;font:34px sans-serif";COVERSET;return d}
window.__myvD={rs:document.readyState,b:document.body?1:0,ap:0,t0:Date.now()};window.__myvCoverT=0;window.__myvCoverOff=function(){window.__myvCoverDone=1;var e=document.getElementById("__myv_cover");if(e)e.remove()};
var iv=setInterval(function(){try{if(window.__myvCoverDone){clearInterval(iv);return}var b=document.body;if(b&&!document.getElementById("__myv_cover")){b.appendChild(mk());window.__myvD.ap++;if(!window.__myvCoverT){window.__myvCoverT=Date.now();setTimeout(function(){window.__myvCoverOff()},9000)}}}catch(e){}},60)}catch(e){}})();"""
t = once(r'(var (\w+)=JSON\.parse;JSON\.parse=function\(\)\{var (\w+)=\2\.apply\(this,arguments\);)',
         lambda m: ADCLEAN.replace("\n", "") + COVER_JS.replace("COVERSET", _cover_set()).replace("BRAND", brand) + m.group(1) + (
             'try{if(Ma("enableAdBlock"))__mz(%s);var __mf=window.__myvCoverOff;if(__mf&&window.__myvReloaded&&%s&&%s.contents&&%s.contents.tvBrowseRenderer){window.__myvCoverOff=null;setTimeout(__mf,Math.max(700,3500-(Date.now()-(window.__myvCoverT||0))))}}catch(_e){}'
             % (m.group(3), m.group(3), m.group(3), m.group(3))),
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
