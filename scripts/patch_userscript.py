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

# 2e) Recarga del inicio (SOFT_RELOAD_PAGE): se conserva, pero con 3 s de espera. Ejecutada de inmediato
#     (como en el original) deja el feed vacio en esta app; esperando a que el inicio cargue, funciona.
t = once(r'(\w+)\("reloadHomeOnStartup"\)&&(\(\w+\("launchToOnStartup"\)\?\w+\(JSON\.parse\(\w+\("launchToOnStartup"\)\)\):\w+\(\{signalAction:\{signal:"SOFT_RELOAD_PAGE"\}\}\)\))',
         lambda m: '%s("reloadHomeOnStartup")&&setTimeout(()=>{%s},3e3)' % (m.group(1), m.group(2)),
         t, label="recarga al iniciar con espera")

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
