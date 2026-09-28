import streamlit as st
import numpy as np
import cv2
from PIL import Image
import io
import tempfile
import os

# Maakt de website lekker breed
st.set_page_config(page_title="Anton Repponen Effect", layout="wide")

st.title("Anton Repponen: Pixel Stretch")
st.write("Sleep een foto of video in het vlak hieronder. Het effect wordt direct berekend!")

# 1. Het drag & drop vlak voor zowel foto's als video's
uploaded_file = st.file_uploader("", type=["jpg", "jpeg", "png", "mp4", "mov"])

if uploaded_file is not None:
    # We kijken of de gebruiker een video of een foto heeft geüpload
    is_video = uploaded_file.type.startswith('video')
    
    # 2. De slider die direct reageert (automatisch verwerken!)
    st.write("### Bepaal het startpunt van de stretch")
    stretch_percentage = st.slider("Startpunt (in % van de breedte)", 0, 100, 50)
    
    if not is_video:
        # --- FOTO VERWERKING ---
        image = Image.open(uploaded_file)
        img_array = np.array(image)
        hoogte, breedte, kanalen = img_array.shape
        
        # Bereken exact de pixel waar we moeten stretchen o.b.v. het percentage
        start_x = int((stretch_percentage / 100) * (breedte - 1))
        
        # Voer de pixel stretch uit
        stretch_array = img_array.copy()
        lijn_pixels = stretch_array[:, start_x:start_x+1]
        stretch_array[:, start_x:] = lijn_pixels
        
        # Toon het resultaat in hoge resolutie
        result_image = Image.fromarray(stretch_array)
        st.image(result_image, caption='Jouw Kunstwerk', use_column_width=True)
        
        # Knop om het in originele kwaliteit te downloaden
        buf = io.BytesIO()
        result_image.save(buf, format="PNG")
        st.download_button("Download Foto (High-Res)", buf.getvalue(), "repponen_stretch.png", "image/png")
        
    else:
        # --- VIDEO VERWERKING ---
        st.info("Video wordt frame-voor-frame verwerkt op de originele kwaliteit. Dit kan even duren...")
        
        # Tijdelijke opslag voor de verwerking
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        tfile.write(uploaded_file.read())
        
        cap = cv2.VideoCapture(tfile.name)
        breedte = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        hoogte = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        totaal_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        out_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(out_file.name, fourcc, fps, (breedte, hoogte))
        
        start_x = int((stretch_percentage / 100) * (breedte - 1))
        huidig_frame = 0
        progress_bar = st.progress(0)
        
        # Verwerk elk beeldje uit de video
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            lijn_pixels = frame[:, start_x:start_x+1]
            frame[:, start_x:] = lijn_pixels
            out.write(frame)
            
            huidig_frame += 1
            # Update de laadbalk soepel
            if huidig_frame % 5 == 0 or huidig_frame == totaal_frames:
                progress_bar.progress(min(huidig_frame / totaal_frames, 1.0))
                
        cap.release()
        out.release()
        progress_bar.empty()
        st.success("Video klaar!")
        
        # Geef het gerenderde bestand terug aan de gebruiker
        with open(out_file.name, 'rb') as v:
            st.download_button("Download Bewerkte Video", v.read(), "repponen_video.mp4", "video/mp4")
            
        # Ruim tijdelijke bestanden op
        os.unlink(tfile.name)
        os.unlink(out_file.name)
