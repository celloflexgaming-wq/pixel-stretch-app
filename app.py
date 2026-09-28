import streamlit as st
import numpy as np
import cv2
from PIL import Image
import io
import tempfile
import os

# Maakt de website lekker breed
st.set_page_config(page_title="Anton Repponen Effect", layout="wide")

st.title("Anton Repponen: Full Time Stretch")
st.write("Sleep een foto of video in het vlak. De hele afbeelding wordt in uitgesmeerde banen verdeeld!")

# Het drag & drop vlak
uploaded_file = st.file_uploader("", type=["jpg", "jpeg", "png", "mp4", "mov"])

if uploaded_file is not None:
    is_video = uploaded_file.type.startswith('video')
    
    # Sliders voor het blokken-effect
    col1, col2 = st.columns(2)
    with col1:
        num_blocks = st.slider("Aantal horizontale banen (resolutie)", 10, 300, 80)
    with col2:
        random_seed = st.slider("Wissel het patroon (Seed)", 1, 200, 42)
        
    def apply_full_block_stretch(img_array, num_blocks, seed):
        np.random.seed(seed)
        h, w = img_array.shape[:2]
        stretch_array = img_array.copy()
        
        # Zorg dat we niet meer banen vragen dan er pixels in de hoogte zijn
        actual_blocks = min(num_blocks, h)
        
        # We verdelen de totale hoogte in 'actual_blocks' aaneengesloten stroken
        if actual_blocks > 1:
            y_splits = np.sort(np.random.choice(range(1, h), actual_blocks - 1, replace=False))
            y_points = [0] + y_splits.tolist() + [h]
        else:
            y_points = [0, h]
            
        # Loop door elke strook van boven naar beneden
        for i in range(len(y_points) - 1):
            y_start = y_points[i]
            y_end = y_points[i+1]
            
            # Kies een willekeurig startpunt op de X-as voor deze strook
            x_start = np.random.randint(0, w)
            
            # Kies willekeurig of we naar links of naar rechts uitsmeren
            direction = np.random.choice(["left", "right"])
            
            # Pak de pixelkolom
            lijn_pixels = stretch_array[y_start:y_end, x_start:x_start+1]
            
            # Pas de stretch toe
            if direction == "right":
                stretch_array[y_start:y_end, x_start:] = lijn_pixels
            else:
                stretch_array[y_start:y_end, :x_start] = lijn_pixels
                
        return stretch_array

    if not is_video:
        # --- FOTO VERWERKING ---
        image = Image.open(uploaded_file).convert('RGB')
        img_array = np.array(image)
        
        # Voer ons nieuwe, volledige dekkende effect uit
        stretch_array = apply_full_block_stretch(img_array, num_blocks, random_seed)
        
        result_image = Image.fromarray(stretch_array)
        st.image(result_image, caption='Jouw Full Time Stretch Kunstwerk', use_container_width=True)
        
        buf = io.BytesIO()
        result_image.save(buf, format="PNG")
        st.download_button("Download Foto (High-Res)", buf.getvalue(), "repponen_full_stretch.png", "image/png")
        
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
            
            # Pas het effect toe op het huidige frame
            bewerkt_frame = apply_full_block_stretch(frame, num_blocks, random_seed)
            out.write(bewerkt_frame)
            
            huidig_frame += 1
            if huidig_frame % 5 == 0 or huidig_frame == totaal_frames:
                progress_bar.progress(min(huidig_frame / totaal_frames, 1.0))
                
        cap.release()
        out.release()
        progress_bar.empty()
        st.success("Video klaar!")
        
        with open(out_file.name, 'rb') as v:
            st.download_button("Download Bewerkte Video", v.read(), "repponen_video_full_stretch.mp4", "video/mp4")
            
        os.unlink(tfile.name)
        os.unlink(out_file.name)
