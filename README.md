# mvs

Script de interfaz para **MyouVTube** (`yt-ui.js`). Es una **versión derivada de
[TizenTube](https://github.com/reisxd/TizenTube)** de Reis Can (reisxd), publicada bajo
**GPL-3.0-only** (ver `LICENSE`). Todo el mérito del código original es de su autor.

## Qué cambia respecto al original
- Textos visibles: "TizenTube" / "TizenTube Cobalt" pasan a "MyouVTube".
- Se quitan las secciones de apoyo y de redes sociales (enlaces del autor y QR) y el crédito bajo el título de ajustes.
- Se desactiva el actualizador integrado: sin menú, sin chequeo al arrancar y sin consulta a la API de GitHub.
- El resto (bloqueo de anuncios, SponsorBlock, DeArrow, velocidad, etc.) no se toca.
- Los identificadores internos (`window.h5vcc.tizentube`, usados por la app nativa) se conservan a propósito.

## Origen y reproducción
- Base: `dist/userScript.js` de `@foxreis/tizentube` (npm), descargado el 2026-11-03.
  sha256 del original: `3282713ee329c0cfb3c68eee0057dd413418244601ce815f282db22bbdb0fefe`
- sha256 de `yt-ui.js`: `0d9229465710db0ed1d430f998f8cafed88dd6b20c8051645d70bc09378c69b2`
- Se genera con `scripts/patch_userscript.py` (corresponding source: código de TizenTube + ese script):
  ```
  python3 -I scripts/patch_userscript.py userScript.js yt-ui.js MyouVTube
  ```
  El script falla si el original cambia de forma que algún parche no encuentre su lugar,
  en vez de generar un archivo a medias.

## Uso
La app lo carga desde jsDelivr:
`https://cdn.jsdelivr.net/gh/salgadomartin107-art/mvs@main/yt-ui.js`

Este repo no recibe automáticamente las correcciones del autor original; para actualizar hay que
repetir el proceso con un `userScript.js` nuevo.
