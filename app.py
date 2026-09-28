import streamlit as st
import numpy as np
import cv2
from PIL import Image
import io
import tempfile
import os

# Maakt de website lekker breed
st.set_page_config(page_title="Anton Repponen Effect", layout="wide")

st.title("Anton Repponen: Randomized Blocks")
st.write("Sleep een foto of video in het vlak. Gebruik de sliders om de blokken aan te passen!")

# Het drag & drop vlak
uploaded_file = st.file_uploader("", type=["jpg", "jpeg", "png", "mp4", "mov"])

if uploaded_file is not None:
    is_video = uploaded_file.type.startswith('video')
    
    # Twee nieuwe sliders voor het blokken-effect
    col1, col2 = st.columns(2)
    with col1:
        num_blocks = st.slider("Aantal horizontale blokken", 1, 150, 40)
    with col2:
        # De 'seed' zorgt ervoor dat we de willekeurigheid kunnen veranderen tot we het mooi vinden
        random_seed = st.slider("Wissel het patroon (Seed)", 1, 100, 42)
        
    def apply_block_stretch(img_array, num_blocks, seed):
        # We stellen de willekeurigheid in op een vast getal (seed). 
        # Hierdoor blijven de blokken in een video op precies dezelfde plek per frame!
        np.random.seed(seed)
        
        h, w = img_array.shape[:2]
        stretch_array = img_array.copy()
        
        for _ in range(num_blocks):
            # 1. Kies een willekeurige start-hoogte (Y-as)
            y_start = np.random.randint(0, h)
            
            # 2. Kies een willekeurige dikte voor het blok
            block_height = np.random.randint(10, max(20, h // 8))
            y_end = min(h, y_start + block_height)
            
            # 3. Kies waar de pixel-lijn begint (X-as). 
            # We houden hem in de linker 80% zodat er ruimte is om te stretchen.
            x_start = np.random.randint(0, int(w * 0.8))
            
            # Pak deze specifieke reeks pixels
            lijn_pixels = stretch_array[y_start:y_end, x_start:x_start+1]
            
            # Smeer deze uit naar de rechterkant van het beeld
            stretch_array[y_start:y_end, x_start:] = lijn_pixels
            
        return stretch_array

    if not is_video:
        # --- FOTO VERWERKING ---
        image = Image.open(uploaded_file).convert('RGB')
        img_array = np.array(image)
        
        # Voer ons nieuwe blokken-effect uit
        stretch_array = apply_block_stretch(img_array, num_blocks, random_seed)
        
        result_image = Image.fromarray(stretch_array)
        st.image(result_image, caption='Jouw Randomized Block Kunstwerk', use_container_width=True)
        
        buf = io.BytesIO()
        result_image.save(buf, format="PNG")
        st.download_button("Download Foto (High-Res)", buf.getvalue(), "repponen_blocks.png", "image/png")
        
    else:
        # --- VIDEO VERWERKING ---
        st.info("Video wordt frame-voor-frame verwerkt. Dit kan even duren...")
        
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
        
        huidig_frame = 0
        progress_bar = st.progress(0)
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Pas de blokken toe (dankzij de 'seed' gebeurt dit elk frame op exact dezelfde coördinaten)
            bewerkt_frame = apply_block_stretch(frame, num_blocks, random_seed)
            out.write(bewerkt_frame)
            
            huidig_frame += 1
            if huidig_frame % 5 == 0 or huidig_frame == totaal_frames:
                progress_bar.progress(min(huidig_frame / totaal_frames, 1.0))
                
        cap.release()
        out.release()
        progress_bar.empty()
        st.success("Video klaar!")
        
        with open(out_file.name, 'rb') as v:
            st.download_button("Download Bewerkte Video", v.read(), "repponen_video_blocks.mp4", "video/mp4")
            
        os.unlink(tfile.name)
        os.unlink(out_file.name)
