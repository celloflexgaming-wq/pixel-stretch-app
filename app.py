import streamlit as st
import numpy as np
import cv2
from PIL import Image
import io
import tempfile
import os
import random

st.set_page_config(page_title="Anton Repponen Auto-Stretch", layout="wide")

st.title("Anton Repponen: 100% Full Stretch")
st.write("Upload media. De hele afbeelding wordt nu 100% bedekt met het time stretch effect, zonder reststukjes.")

# Geheugen voor de AUTO modus
if 'auto_mode' not in st.session_state:
    st.session_state.auto_mode = False
if 'auto_blocks' not in st.session_state:
    st.session_state.auto_blocks = 100
if 'auto_seed' not in st.session_state:
    st.session_state.auto_seed = 42

uploaded_file = st.file_uploader("Upload een foto of video...", type=["jpg", "jpeg", "png", "mp4", "mov"])

# --- VERNIEUWDE FUNCTIE VOOR 100% DEKKING ---
def apply_repponen_stretch(img_array, num_blocks, seed):
    np.random.seed(seed)
    h, w = img_array.shape[:2]
    
    # We beginnen met een leeg canvas (optioneel) of een kopie
    stretch_array = img_array.copy()
    
    actual_blocks = min(num_blocks, h)
    
    if actual_blocks > 1:
        y_splits = np.sort(np.random.choice(range(1, h), actual_blocks - 1, replace=False))
        y_points = [0] + y_splits.tolist() + [h]
    else:
        y_points = [0, h]
        
    for i in range(len(y_points) - 1):
        y_start = y_points[i]
        y_end = y_points[i+1]
        
        # Kies de bron-pixel op de X-as voor deze hele baan
        x_start = np.random.randint(0, w)
        
        # Pak exact deze pixel-kolom uit de ORIGINELE foto
        lijn_pixels = img_array[y_start:y_end, x_start:x_start+1]
        
        # OPLOSSING: Overschrijf de VOLLEDIGE breedte van de baan (alle X-coördinaten)
        # Er blijven nu geen originele stukjes meer over.
        stretch_array[y_start:y_end, :] = lijn_pixels
            
    return stretch_array

if uploaded_file is not None:
    is_video = uploaded_file.type.startswith('video')
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.write("### 🎛️ Handmatige Controle")
        manual_blocks = st.slider("Aantal banen (resolutie)", 10, 500, 100)
        manual_seed = st.slider("Patroon Wisselaar (Seed)", 1, 1000, 42)
        if st.button("Pas Handmatig Toe"):
            st.session_state.auto_mode = False
            
    with col2:
        st.write("### 🤖 Algoritme")
        st.info("Genereert direct willekeurige waarden voor totale deconstructie.")
        if st.button("✨ AUTO STRETCH ALLES", use_container_width=True):
            st.session_state.auto_mode = True
            st.session_state.auto_blocks = random.randint(40, 450)
            st.session_state.auto_seed = random.randint(1, 9999)
            
    active_blocks = st.session_state.auto_blocks if st.session_state.auto_mode else manual_blocks
    active_seed = st.session_state.auto_seed if st.session_state.auto_mode else manual_seed
    
    st.divider()
    
    if not is_video:
        # --- FOTO VERWERKING ---
        image = Image.open(uploaded_file).convert('RGB')
        img_array = np.array(image)
        
        result_array = apply_repponen_stretch(img_array, active_blocks, active_seed)
        result_image = Image.fromarray(result_array)
        
        st.image(result_image, caption=f"Huidig Resultaat (Banen: {active_blocks} | Seed: {active_seed})", use_container_width=True)
        
        buf = io.BytesIO()
        result_image.save(buf, format="PNG")
        st.download_button("⬇️ Download High-Res Foto", buf.getvalue(), "auto_stretch_100.png", "image/png")
        
    else:
        # --- VIDEO VERWERKING ---
        st.write(f"**Video Rendering Actief** (Banen: {active_blocks} | Seed: {active_seed})")
        
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
        status_text = st.empty()
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            bewerkt_frame = apply_repponen_stretch(frame, active_blocks, active_seed)
            out.write(bewerkt_frame)
            
            huidig_frame += 1
            if huidig_frame % 5 == 0 or huidig_frame == totaal_frames:
                progress_bar.progress(min(huidig_frame / totaal_frames, 1.0))
                status_text.text(f"Frame {huidig_frame} van {totaal_frames} verwerkt...")
                
        cap.release()
        out.release()
        progress_bar.empty()
        status_text.empty()
        st.success("✅ Video succesvol gerenderd!")
        
        with open(out_file.name, 'rb') as v:
            st.download_button("⬇️ Download Bewerkte Video", v.read(), "auto_stretch_100_video.mp4", "video/mp4")
            
        os.unlink(tfile.name)
        os.unlink(out_file.name)
