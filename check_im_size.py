import os
from PIL import Image

for f in ["0_Im1.png", "1_Im2.png", "2_Xi2.png", "3_Xi3.png"]:
    p = os.path.join(r"C:\Users\VSUN\.gemini\antigravity\scratch\einvoice_app\extracted_imgs", f)
    im = Image.open(p)
    print(f"{f}: size={im.size}, mode={im.mode}")
