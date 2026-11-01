import os, tempfile
from PIL import Image
import thumb

src = os.path.join(tempfile.mkdtemp(), "src.png")
Image.new("RGB", (800, 1200), (40, 90, 160)).save(src)  # retrato: testa o recorte vertical
for align in ("esquerda", "centro", "direita"):
    img, size = thumb.render(src, "TESTE.", align)
    assert img.size == (thumb.W, thumb.H) and 8 < size <= 400
assert thumb.render(src, "TESTE.")[0] != thumb.render(src, "")[0]  # o texto foi desenhado
assert thumb.render(src, "")[0].getpixel((10, 1070)) != (0, 0, 0)  # base em cache não foi alterada
base_size = thumb.render(src, "TESTE.")[1]
assert thumb.render(src, "TESTE.", scale=0.5)[1] < base_size < thumb.render(src, "TESTE.", scale=1.5)[1]
print("ok")
