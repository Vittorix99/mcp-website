import cv2
import numpy as np
from PIL import Image
import os
def invert_png(input_path, output_path):
    # Carica l'immagine con OpenCV
    image = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)

    if image is None:
        raise Exception("Errore: impossibile caricare l'immagine. Controlla il percorso del file.")

    # Controlla se l'immagine ha un canale alpha (trasparenza)
    if image.shape[-1] == 4:  # PNG con trasparenza
        bgr = image[:, :, :3]  # Estrai i canali RGB
        alpha = image[:, :, 3]  # Estrai il canale alpha
        
        # Inverti solo i colori RGB
        inverted_bgr = cv2.bitwise_not(bgr)

        # Ricrea l'immagine con il canale alpha originale
        inverted_image = np.dstack((inverted_bgr, alpha))
    else:  # PNG senza trasparenza
        inverted_image = cv2.bitwise_not(image)

    # Converti l'immagine in formato PIL per salvarla come PNG
    inverted_pil = Image.fromarray(cv2.cvtColor(inverted_image, cv2.COLOR_BGRA2RGBA))

    # Salva l'immagine invertita
    inverted_pil.save(output_path, format="PNG")
    print(f"✅ Immagine invertita salvata in: {output_path}")

# Esempio di utilizzo:
input_png = "logonew.png"  # Sostituisci con il percorso del tuo PNG
output_png = "output_inverted.png"


print("Directory corrente:", os.getcwd())   

invert_png(input_png, output_png)