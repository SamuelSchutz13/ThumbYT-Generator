"""Gera uma thumbnail: palavra grande amarela com ponto final no topo.
Uso: python thumb.py imagem.png "PALAVRA." saida.png [esquerda|centro|direita]
"""
import os
import sys
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

W, H = 1920, 1080
YELLOW = (240, 178, 10)
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = next((p for p in (
    os.path.join(HERE, "InterDisplay-Black.otf"),
    "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf",
    r"C:\Windows\Fonts\impact.ttf",
) if os.path.exists(p)), None)


@lru_cache(maxsize=4)  # a base só depende da imagem; o app re-renderiza a cada tecla
def base(src):
    img = Image.open(src).convert("RGB")
    # recorte 16:9 centralizado
    r = img.width / img.height
    if r > W / H:
        nw = int(img.height * W / H); x = (img.width - nw) // 2
        img = img.crop((x, 0, x + nw, img.height))
    else:
        nh = int(img.width * H / W); y = (img.height - nh) // 2
        img = img.crop((0, y, img.width, y + nh))
    img = img.resize((W, H), Image.LANCZOS)
    img = ImageEnhance.Color(img).enhance(1.15)
    img = ImageEnhance.Contrast(img).enhance(1.08)
    grad = Image.new("L", (1, H))
    for y in range(H):
        grad.putpixel((0, y), int(110 * max(0, 1 - y / (H * 0.45))))
    dark = Image.new("RGB", (W, H), (0, 0, 0))
    return Image.composite(dark, img, grad.resize((W, H))).convert("RGBA")


def render(src, word, align="esquerda", scale=1.0):
    assert FONT, "Fonte não encontrada: coloque InterDisplay-Black.otf ao lado do thumb.py"
    # Fonte: maior tamanho que cabe na largura e em 30% da altura
    margin = 40
    for size in range(400, 8, -4):
        f = ImageFont.truetype(FONT, size)
        b = f.getbbox(word)
        if b[2] - b[0] <= W - 2 * margin and b[3] - b[1] <= H * 0.30:
            break
    if scale != 1.0:  # acima de 1 o texto pode passar da borda: é escolha do usuário
        size = max(8, round(size * scale))
        f = ImageFont.truetype(FONT, size)
        b = f.getbbox(word)
    tw = b[2] - b[0]
    x = {"esquerda": margin, "centro": (W - tw) // 2, "direita": W - margin - tw}[align] - b[0]
    y = 20 - b[1]

    # sombra difusa
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((x + 6, y + 10), word, font=f, fill=(0, 0, 0, 150))
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    out = base(src).copy()  # copy: alpha_composite altera no lugar e a base fica em cache
    out.alpha_composite(sh)
    txt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(txt).text((x, y), word, font=f, fill=YELLOW + (245,))
    out.alpha_composite(txt)
    return out.convert("RGB"), size


if __name__ == "__main__":
    src, word, out = sys.argv[1], sys.argv[2], sys.argv[3]
    img, size = render(src, word, sys.argv[4] if len(sys.argv) > 4 else "esquerda")
    img.save(out, quality=95)
    print("ok", out, size)
