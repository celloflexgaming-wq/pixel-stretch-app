import streamlit as st
import numpy as np
import cv2
from PIL import Image
import io
import tempfile
import os
import random

st.set_page_config(page_title="Anton Repponen Block-Stretch", layout="wide")

st.title("Anton Repponen: Randomized Block Stretch")
st.write("Upload media. De afbeelding wordt opgedeeld in rijen en willekeurige segmenten, waarna specifieke blokken worden gestretcht voor dat typische verspringende effect.")

# Geheugen voor de AUTO modus
if 'auto_mode' not in st.session_state:
    st.session_state.auto_mode = False
if 'auto_rows' not in st.session_state:
    st.session_state.auto_rows = 50
if 'auto_complexity' not in st.session_state:
    st.session_state.auto_complexity = 5
if 'auto_stretch_chance' not in st.session_state:
    st.session_state.auto_stretch_chance = 70
if 'auto_seed' not in st.session_state:
    st.session_state.auto_seed = 42

uploaded_file = st.file_uploader("Upload een foto of video...", type=["jpg", "jpeg", "png", "mp4", "mov"])

# --- HET GEAVANCEERDE BLOKKEN ALGORITME ---
def apply_complex_block_stretch(img_array, num_rows, complexity, stretch_chance, seed):
    np.random.seed(seed)
    random.seed(seed) # Zorg dat ook pythons random module vastligt voor video's
    h, w = img_array.shape[:2]
    
    # We werken op een kopie zodat we delen intact kunnen laten
    result_array = img_array.copy()
    
    actual_rows = min(num_rows, h)
    
    # Bepaal de horizontale uitsnedes (rijen)
    if actual_rows > 1:
        y_splits = np.sort(np.random.choice(range(1, h), actual_rows - 1, replace=False))
        y_points = [0] + y_splits.tolist() + [h]
    else:
        y_points = [0, h]
        
    for i in range(len(y_points) - 1):
        y_start = y_points[i]
        y_end = y_points[i+1]
        
        # Voor elke rij, bepaal hoeveel kolommen (segmenten) deze rij krijgt.
        # 'complexity' bepaalt het maximale aantal segmenten per rij.
        num_segments = np.random.randint(1, max(2, complexity + 1))
        
        if num_segments > 1:
             x_splits = np.sort(np.random.choice(range(1, w), num_segments - 1, replace=False))
             x_points = [0] + x_splits.tolist() + [w]
        else:
             x_points = [0, w]
             
        # Loop door elk segment binnen deze rij
        for j in range(len(x_points) - 1):
            x_start = x_points[j]
            x_end = x_points[j+1]
            
            # Bepaal of we dit specifieke blokje gaan stretchen of intact laten
            if random.randint(1, 100) <= stretch_chance:
                # We gaan stretchen!
                # Kies willekeurig een pixelkolom BINNEN dit segment om uit te smeren
                pixel_x = np.random.randint(x_start, x_end)
                lijn_pixels = img_array[y_start:y_end, pixel_x:pixel_x+1]
                
                # Overschrijf dit segment met de gekozen pixel
                result_array[y_start:y_end, x_start:x_end] = lijn_pixels
            
            # Als de kans niet valt, doen we niets en blijft het originele stukje foto (of videoframe) staan.

    return result_array

if uploaded_file is not None:
    is_video = uploaded_file.type.startswith('video')
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.write("### 🎛️ Handmatige Controle")
        manual_rows = st.slider("Aantal Rijen (Hoogte)", 10, 200, 50, help="Hoeveel horizontale stroken er gemaakt worden.")
        manual_complexity = st.slider("Complexiteit (Blokjes per rij)", 1, 20, 5, help="Hoe meer, hoe vaker een rij verspringt.")
        manual_stretch_chance = st.slider("Kans op Stretch (%)", 0, 100, 70, help="100% is alles gestretcht, 0% is de originele foto.")
        manual_seed = st.slider("Patroon Wisselaar (Seed)", 1, 1000, 42)
        
        if st.button("Pas Handmatig Toe"):
            st.session_state.auto_mode = False
            
    with col2:
        st.write("### 🤖 AUTO Modus")
        st.info("Genereert een compleet willekeurig blokkenpatroon.")
        if st.button("✨ AUTO GENERATE BLOCKS", use_container_width=True):
            st.session_state.auto_mode = True
            st.session_state.auto_rows = random.randint(30, 150)
            st.session_state.auto_complexity = random.randint(3, 12)
            # We houden de kans redelijk hoog (tussen 60 en 95) voor een goed effect
            st.session_state.auto_stretch_chance = random.randint(60, 95) 
            st.session_state.auto_seed = random.randint(1, 9999)
            
    active_rows = st.session_state.auto_rows if st.session_state.auto_mode else manual_rows
    active_complexity = st.session_state.auto_complexity if st.session_state.auto_mode else manual_complexity
    active_chance = st.session_state.auto_stretch_chance if st.session_state.auto_mode else manual_stretch_chance
    active_seed = st.session_state.auto_seed if st.session_state.auto_mode else manual_seed
    
    st.divider()
    
    if not is_video:
        # --- FOTO VERWERKING ---
        image = Image.open(uploaded_file).convert('RGB')
        img_array = np.array(image)
        
        result_array = apply_complex_block_stretch(img_array, active_rows, active_complexity, active_chance, active_seed)
        result_image = Image.fromarray(result_array)
        
        st.image(result_image, caption=f"Resultaat (Rijen: {active_rows} | Complexiteit: {active_complexity} | Stretch: {active_chance}%)", use_container_width=True)
        
        buf = io.BytesIO()
        result_image.save(buf, format="PNG")
        st.download_button("⬇️ Download High-Res Foto", buf.getvalue(), "repponen_blocks.png", "image/png")
        
    else:
        # --- VIDEO VERWERKING ---
        st.write(f"**Video Rendering Actief** (Rijen: {active_rows} | Complexiteit: {active_complexity} | Stretch: {active_chance}%)")
        
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
                
            bewerkt_frame = apply_complex_block_stretch(frame, active_rows, active_complexity, active_chance, active_seed)
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
            st.download_button("⬇️ Download Bewerkte Video", v.read(), "repponen_video_blocks.mp4", "video/mp4")
            
        os.unlink(tfile.name)
        os.unlink(out_file.name)
