"""
Vendoring de toutes les ressources externes pour un usage 100% hors ligne.
A lancer une seule fois (ou pour rafraichir les ressources) :
    python vendor_assets.py

Telecharge et stocke localement dans assets/ :
  - le CSS de l'editeur Notesnook (mise en forme du contenu des syntheses)
  - les polices du site (Fraunces + Geist, Google Fonts) -> assets/fonts/ + assets/fonts.css
  - les polices KaTeX referencees par le CSS Notesnook (rendu des maths)
Et reecrit le CSS Notesnook pour pointer vers les copies locales (plus aucun
appel reseau a la lecture des pages).
"""
import os
import re
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

NOTESNOOK_CSS_URL = "https://app.notesnook.com/assets/editor-styles.css?d=1690887574068"
NOTESNOOK_BASE = "https://app.notesnook.com"

GOOGLE_CSS_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700"
    "&family=Geist:wght@400;500;600&display=swap"
)

ASSETS_DIR = "assets"
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
NOTESNOOK_OUT = os.path.join(ASSETS_DIR, "notesnook-editor.css")
FONTS_CSS_OUT = os.path.join(ASSETS_DIR, "fonts.css")


def fetch(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req) as r:
        data = r.read()
    return data if binary else data.decode("utf-8")


def vendor_notesnook():
    """Telecharge le CSS Notesnook, vendorise ses polices KaTeX, neutralise iconify."""
    css = fetch(NOTESNOOK_CSS_URL)

    # 1. Polices KaTeX : chemins absolus /assets/KaTeX_*.woff2 -> copies locales
    katex = sorted(set(re.findall(r"/assets/(KaTeX_[A-Za-z0-9_-]+\.woff2)", css)))
    print(f"Notesnook : {len(katex)} police(s) KaTeX a telecharger")
    for name in katex:
        data = fetch(f"{NOTESNOOK_BASE}/assets/{name}", binary=True)
        with open(os.path.join(FONTS_DIR, name), "wb") as f:
            f.write(data)
        print(f"  {name}  ({len(data)//1024} Ko)")
    # Rend les refs KaTeX relatives a assets/fonts.css (le .woff2 charge en 1er,
    # les fallback .woff/.ttf ne sont donc jamais requetes).
    css = css.replace("/assets/KaTeX_", "fonts/KaTeX_")

    # 2. Icone iconify (poignee de glisser de l'editeur, inutile en lecture)
    css = re.sub(r"url\(\s*https://api\.iconify\.design/[^)]*\)", "none", css)

    with open(NOTESNOOK_OUT, "w", encoding="utf-8") as f:
        f.write(css)
    print(f"OK -> {NOTESNOOK_OUT}")


def vendor_google_fonts():
    """Telecharge les polices du site et genere assets/fonts.css local."""
    css = fetch(GOOGLE_CSS_URL)
    urls = sorted(set(re.findall(r"url\((https://[^)]+\.woff2)\)", css)))
    print(f"\nSite : {len(urls)} police(s) Google a telecharger")

    mapping = {}
    for i, url in enumerate(urls):
        fam = "fraunces" if "fraunces" in url.lower() else (
            "geist" if "geist" in url.lower() else "font")
        name = f"{fam}-{i:02d}.woff2"
        data = fetch(url, binary=True)
        with open(os.path.join(FONTS_DIR, name), "wb") as f:
            f.write(data)
        mapping[url] = f"fonts/{name}"
        print(f"  {name}  ({len(data)//1024} Ko)")

    for remote, local in mapping.items():
        css = css.replace(remote, local)
    header = ("/* Polices vendorisees pour usage hors ligne. */\n"
              "/* Genere par vendor_assets.py — ne pas editer a la main. */\n")
    with open(FONTS_CSS_OUT, "w", encoding="utf-8") as f:
        f.write(header + css)
    print(f"OK -> {FONTS_CSS_OUT}")


def main():
    os.makedirs(FONTS_DIR, exist_ok=True)
    vendor_notesnook()
    vendor_google_fonts()
    print("\nTermine. Tout est local dans assets/.")


if __name__ == "__main__":
    main()
