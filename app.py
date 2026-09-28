import streamlit as st
import numpy as np
from PIL import Image
import io
import random
from streamlit_drawable_canvas import st_canvas

st.set_page_config(page_title="Repponen Selective Stretch", layout="wide")

st.title("Anton Repponen: Selectieve Canvas Stretch")
st.write("1. Upload een foto.\n2. Gebruik je muis om kaders (sleep blokjes) te tekenen over de gebieden die je wilt stretchen.\n3. De voorgrond blijft onaangetast!")

# --- HET EFFECT (Nu toepasbaar op een specifiek kader) ---
def apply_stretch_to_box(img_array, x_start, y_start, width, height, complexity, seed):
    np.random.seed(seed)
    random.seed(seed)
    
    # Bepaal de grenzen van het kader
    x_end = x_start + width
    y_end = y_start + height
    
    # We knippen alleen het stukje uit dat we willen bewerken
    box_array = img_array[y_start:y_end, x_start:x_end].copy()
    h, w = box_array.shape[:2]
    
    # Verdeel dit specifieke kader in rijen (bijv. 10 tot 40 rijen afhankelijk van de hoogte)
    num_rows = max(5, int(h / 15)) 
    
    if num_rows > 1:
        y_splits = np.sort(np.random.choice(range(1, h), num_rows - 1, replace=False))
        y_points = [0] + y_splits.tolist() + [h]
    else:
        y_points = [0, h]
        
    for i in range(len(y_points) - 1):
        ry_start = y_points[i]
        ry_end = y_points[i+1]
        
        # Verdeel de rij in segmenten
        num_segments = np.random.randint(1, max(2, complexity + 1))
        
        if num_segments > 1:
             x_splits = np.sort(np.random.choice(range(1, w), num_segments - 1, replace=False))
             x_points = [0] + x_splits.tolist() + [w]
        else:
             x_points = [0, w]
             
        for j in range(len(x_points) - 1):
            rx_start = x_points[j]
            rx_end = x_points[j+1]
            
            # Stretch dit specifieke segment
            pixel_x = np.random.randint(rx_start, rx_end) if rx_start != rx_end else rx_start
            lijn_pixels = box_array[ry_start:ry_end, pixel_x:pixel_x+1]
            box_array[ry_start:ry_end, rx_start:rx_end] = lijn_pixels

    # Plak het bewerkte kader terug in de originele foto
    img_array[y_start:y_end, x_start:x_end] = box_array
    return img_array

uploaded_file = st.file_uploader("Upload een statische FOTO...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    raw_image = Image.open(uploaded_file).convert('RGB')
    
    # We schalen de foto naar een vaste breedte zodat het teken-canvas goed werkt
    CANVAS_WIDTH = 1000
    ratio = CANVAS_WIDTH / raw_image.width
    CANVAS_HEIGHT = int(raw_image.height * ratio)
    resized_image = raw_image.resize((CANVAS_WIDTH, CANVAS_HEIGHT), Image.Resampling.LANCZOS)
    
    col1, col2 = st.columns([2, 1])
    
    with col2:
        st.write("### 🎛️ Instellingen per blokje")
        complexity = st.slider("Complexiteit (Segmenten)", 1, 20, 6)
        seed = st.slider("Variatie (Seed)", 1, 500, 42)
        st.info("Teken één of meerdere blauwe rechthoeken op de foto hiernaast. Druk daarna op Render.")
        render_btn = st.button("🚀 Render Kunstwerk", use_container_width=True)

    with col1:
        st.write("### 🖱️ Teken je kaders")
        # Het interactieve tekenveld
        canvas_result = st_canvas(
            fill_color="rgba(0, 150, 255, 0.3)",  # Transparant blauw
            stroke_width=2,
            stroke_color="#0096FF",
            background_image=resized_image,
            update_streamlit=True,
            height=CANVAS_HEIGHT,
            width=CANVAS_WIDTH,
            drawing_mode="rect",
            key="canvas",
        )

    st.divider()

    if render_btn:
        if canvas_result.json_data is not None and len(canvas_result.json_data["objects"]) > 0:
            st.write("### 🖼️ Jouw Resultaat")
            
            # Maak een werk-kopie van de getoonde foto
            img_array = np.array(resized_image)
            
            # Loop door elk getekend rechthoekje heen
            for obj in canvas_result.json_data["objects"]:
                if obj["type"] == "rect":
                    # Haal de coördinaten op uit het canvas
                    x = int(obj["left"])
                    y = int(obj["top"])
                    w = int(obj["width"])
                    h = int(obj["height"])
                    
                    # Pas het effect toe op precies deze coördinaten
                    img_array = apply_stretch_to_box(img_array, x, y, w, h, complexity, seed)
            
            result_image = Image.fromarray(img_array)
            st.image(result_image, use_container_width=True)
            
            buf = io.BytesIO()
            result_image.save(buf, format="PNG")
            st.download_button("⬇️ Download Kunstwerk", buf.getvalue(), "selective_stretch.png", "image/png")
        else:
            st.warning("Teken eerst een vierkantje over de foto voordat je op Render klikt!")
