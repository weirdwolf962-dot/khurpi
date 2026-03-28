import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
import json
from datetime import datetime
import re

st.set_page_config(
    page_title="🌿 AI Plant Doctor - Smart Edition",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============ TREATMENT COSTS & QUANTITIES DATABASE ============
# ============ TREATMENT COSTS & QUANTITIES DATABASE ============

TREATMENT_COSTS = {
    "organic": {
        "Cow Urine Extract": {
            "cost": 80,   # locally prepared / very low-cost input
            "quantity": "2-3 liters per 100 plants",
            "dilution": "1:5 with water",
        },
        "Sulfur Dust": {
            "cost": 120,
            "quantity": "500g per 100 plants",
            "dilution": "Direct dust - 5-10g per plant",
        },
        "Sulfur Powder": {
            "cost": 150,
            "quantity": "200g per 100 plants",
            "dilution": "3% suspension - 20ml per plant",
        },
        "Lime Sulfur": {
            "cost": 180,
            "quantity": "1 liter per 100 plants",
            "dilution": "1:10 with water",
        },
        "Neem Oil Spray": {
            # ~₹340–550 per liter retail; 500 ml ≈ ₹170–275
            "cost": 250,
            "quantity": "500ml per 100 plants",
            "dilution": "3% solution - 5ml per liter",
        },
        "Bordeaux Mixture": {
            "cost": 250,
            "quantity": "300g per 100 plants",
            "dilution": "1% solution - 10g per liter",
        },
        "Karanja Oil": {
            "cost": 220,
            "quantity": "400ml per 100 plants",
            "dilution": "2.5% solution - 2.5ml per liter",
        },
        "Copper Fungicide (Organic)": {
            "cost": 280,
            "quantity": "250g per 100 plants",
            "dilution": "0.5% solution - 5g per liter",
        },
        "Potassium Bicarbonate": {
            "cost": 300,
            "quantity": "150g per 100 plants",
            "dilution": "1% solution - 10g per liter",
        },
        "Bacillus subtilis": {
            "cost": 350,
            "quantity": "100g per 100 plants",
            "dilution": "0.1% solution - 1g per liter",
        },
        "Azadirachtin": {
            "cost": 380,
            "quantity": "200ml per 100 plants",
            "dilution": "0.3% solution - 3ml per liter",
        },
        "Trichoderma": {
            "cost": 400,
            "quantity": "500g per 100 plants",
            "dilution": "0.5% solution - 5g per liter",
        },
        # Spinosad is a bio‑insecticide; market price for 100 ml is ~₹1,900–2,000
        "Spinosad": {
            "cost": 2000,
            "quantity": "100ml per 100 plants",
            "dilution": "0.02% solution - 0.2ml per liter",
        },
        # Added: seaweed extract as a common organic biostimulant
        "Seaweed Extract": {
            # 500 ml pack ≈ ₹500–530; assuming ~250 ml per 100 plants
            "cost": 260,
            "quantity": "250ml per 100 plants",
            "dilution": "0.3% solution - 3ml per liter",
        },
    },
    "chemical": {
        # Bavistin / Carbendazim 50% WP: 100 g ≈ ₹90–140
        "Carbendazim (Bavistin)": {
            "cost": 120,
            "quantity": "100g per 100 plants",
            "dilution": "0.1% solution - 1g per liter",
        },
        # Indofil M-45 (Mancozeb 75% WP): 100 g ≈ ₹75; 500 g ≈ ₹279
        "Mancozeb (Indofil)": {
            "cost": 120,
            "quantity": "150g per 100 plants",
            "dilution": "0.2% solution - 2g per liter",
        },
        "Copper Oxychloride": {
            "cost": 150,
            "quantity": "200g per 100 plants",
            "dilution": "0.25% solution - 2.5g per liter",
        },
        "Profenofos (Meothrin)": {
            "cost": 200,
            "quantity": "100ml per 100 plants",
            "dilution": "0.05% solution - 0.5ml per liter",
        },
        "Chlorothalonil": {
            "cost": 220,
            "quantity": "120g per 100 plants",
            "dilution": "0.15% solution - 1.5g per liter",
        },
        "Deltamethrin (Decis)": {
            "cost": 220,
            "quantity": "50ml per 100 plants",
            "dilution": "0.005% solution - 0.05ml per liter",
        },
        # Confidor (Imidacloprid 17.8% SL): 100 ml ≈ ₹300–380
        "Imidacloprid (Confidor)": {
            "cost": 350,
            "quantity": "80ml per 100 plants",
            "dilution": "0.008% solution - 0.08ml per liter",
        },
        "Fluconazole (Contaf)": {
            "cost": 350,
            "quantity": "150ml per 100 plants",
            "dilution": "0.06% solution - 0.6ml per liter",
        },
        "Tebuconazole (Folicur)": {
            "cost": 320,
            "quantity": "120ml per 100 plants",
            "dilution": "0.05% solution - 0.5ml per liter",
        },
        "Thiamethoxam (Actara)": {
            "cost": 290,
            "quantity": "100g per 100 plants",
            "dilution": "0.04% solution - 0.4g per liter",
        },
        # Amistar / Amistar Top: 100 ml ≈ ₹560–700
        "Azoxystrobin (Amistar)": {
            "cost": 650,
            "quantity": "80ml per 100 plants",
            "dilution": "0.02% solution - 0.2ml per liter",
        },
        "Hexaconazole (Contaf Plus)": {
            "cost": 350,
            "quantity": "100ml per 100 plants",
            "dilution": "0.04% solution - 0.4ml per liter",
        },
        "Phosphorous Acid": {
            "cost": 250,
            "quantity": "200ml per 100 plants",
            "dilution": "0.3% solution - 3ml per liter",
        },
        # Added: Ridomil Gold (Metalaxyl + Mancozeb)
        "Metalaxyl + Mancozeb (Ridomil Gold)": {
            # 100 g pack ≈ ₹180–190
            "cost": 190,
            "quantity": "100g per 100 plants",
            "dilution": "0.25% solution - 2.5g per liter",
        },
        # Added: Tilt (Propiconazole 25% EC)
        "Propiconazole (Tilt)": {
            # 100 ml ≈ ₹190; 250 ml ≈ ₹390
            "cost": 190,
            "quantity": "100ml per 100 plants",
            "dilution": "0.1% solution - 1ml per liter",
        },
    },
}

# ============ CROP ROTATION DATABASE ============
CROP_ROTATION_DATA = {
    "Tomato": {
        "rotations": ["Beans", "Cabbage", "Cucumber"],
        "info": {
            "Tomato": "High-value solanaceae crop. Susceptible to early/late blight, fusarium wilt, and bacterial diseases. Benefits from crop rotation of 3+ years.",
            "Beans": "Nitrogen-fixing legume. Improves soil nitrogen content. Breaks disease cycle for tomato. Compatible with tomato crop rotation.",
            "Cabbage": "Brassica family. Helps control tomato diseases. Requires different nutrient profile. Good rotation choice.",
            "Cucumber": "Cucurbitaceae family. No common diseases with tomato. Light feeder after beans. Completes rotation cycle.",
        },
    },
    "Rose": {
        "rotations": ["Marigold", "Chrysanthemum", "Herbs"],
        "info": {
            "Rose": "Ornamental crop. Susceptible to black spot, powdery mildew, rose rosette virus. Needs disease break.",
            "Marigold": "Natural pest repellent. Flowers attract beneficial insects. Cleanses soil. Excellent companion.",
            "Chrysanthemum": "Different pest/disease profile. Breaks rose pathogen cycle. Similar care requirements.",
            "Herbs": "Basil, rosemary improve soil health. Aromatics confuse rose pests. Reduces chemical inputs.",
        },
    },
    "Apple": {
        "rotations": ["Legume Cover Crops", "Grasses", "Berries"],
        "info": {
            "Apple": "Long-term perennial crop. Susceptible to apple scab, fire blight, rust. Needs 4-5 year rotation minimum.",
            "Legume Cover Crops": "Nitrogen fixation. Soil improvement. Breaks pathogen cycle. Reduces input costs.",
            "Grasses": "Erosion control. Soil structure improvement. Natural pest predator habitat. Beneficial insects.",
            "Berries": "Different root depth. Utilize different nutrients. Continues income during apple off-year.",
        },
    },
    "Lettuce": {
        "rotations": ["Spinach", "Broccoli", "Cauliflower"],
        "info": {
            "Lettuce": "Cool-season leafy crop. Susceptible to downy mildew, tip burn, mosaic virus. Quick 60-70 day cycle.",
            "Spinach": "Similar family (Amaranthaceae). Resistant to lettuce diseases. Tolerates cold. Soil enrichment.",
            "Broccoli": "Brassica family. Different pest profile. Breaks disease cycle. Heavy feeder needs composting.",
            "Cauliflower": "Brassica family. Follows spinach. Light-sensitive. Completes 3-crop cycle for lettuce disease control.",
        },
    },
    "Grape": {
        "rotations": ["Legume Cover Crops", "Cereals", "Vegetables"],
        "info": {
            "Grape": "Perennial vine crop. Powdery mildew, downy mildew, phylloxera major concerns. 5+ year rotation needed.",
            "Legume Cover Crops": "Nitrogen replenishment. Soil structure restoration. Disease vector elimination.",
            "Cereals": "Wheat/maize. Different nutrient uptake. Soil consolidation. Nematode cycle break.",
            "Vegetables": "Diverse crops reduce soil depletion. Polyculture benefits. Re-establishes soil microbiology.",
        },
    },
    "Pepper": {
        "rotations": ["Onion", "Garlic", "Spinach"],
        "info": {
            "Pepper": "Solanaceae crop. Anthracnose, bacterial wilt, phytophthora major issues. 3-year rotation essential.",
            "Onion": "Allium family. Different disease profile. Fungicide applications reduced. Breaks solanaceae cycle.",
            "Garlic": "Allium family. Natural pest deterrent. Soil antimicrobial properties. Autumn/winter crop.",
            "Spinach": "Cool-season crop. No common pepper diseases. Nitrogen-fixing partners. Spring/fall compatible.",
        },
    },
    "Cucumber": {
        "rotations": ["Maize", "Okra", "Legumes"],
        "info": {
            "Cucumber": "Cucurbitaceae family. Powdery mildew, downy mildew, beetle damage. 2-3 year rotation suggested.",
            "Maize": "Tall crop provides shade break. Different root system. Utilizes soil nitrogen. Strong market demand.",
            "Okra": "Malvaceae family. No overlapping pests. Nitrogen-fixing tendency. Heat-tolerant summer crop.",
            "Legumes": "Nitrogen restoration. Disease-free break for cucumber. Pea/bean varieties available for season.",
        },
    },
    "Strawberry": {
        "rotations": ["Garlic", "Onion", "Leafy Greens"],
        "info": {
            "Strawberry": "Low-growing perennial. Leaf scorch, powdery mildew, red stele root rot issues. 3-year bed rotation.",
            "Garlic": "Deep-rooted. Antimicrobial soil activity. Plant autumn, harvest spring. Excellent succession crop.",
            "Onion": "Bulb crop. Disease-free break. Allergenic properties deter strawberry pests. Rotation crop.",
            "Leafy Greens": "Spinach/lettuce. Quick cycle. Utilizes residual nutrients. Spring/fall timing options.",
        },
    },
    "Corn": {
        "rotations": ["Soybean", "Pulses", "Oilseeds"],
        "info": {
            "Corn": "Heavy nitrogen feeder. Leaf blotch, rust, corn borer, fumonisin concerns. 3+ year rotation critical.",
            "Soybean": "Nitrogen-fixing legume. Reduces fertilizer needs 40-50%. Breaks corn pest cycle naturally.",
            "Pulses": "Chickpea/lentil. Additional nitrogen fixation. High market value. Diverse pest profile than corn.",
            "Oilseeds": "Sunflower/safflower. Soil structure improvement. Different nutrient uptake. Income diversification.",
        },
    },
    "Potato": {
        "rotations": ["Peas", "Mustard", "Cereals"],
        "info": {
            "Potato": "Solanaceae crop. Late blight, early blight, nematodes persistent issue. 4-year rotation required.",
            "Peas": "Nitrogen-fixing legume. Cold-season crop. Breaks potato pathogen cycle. Soil health restoration.",
            "Mustard": "Oil crop. Biofumigation properties. Natural nematode control. Green manure if plowed.",
            "Cereals": "Wheat/barley. Different root depth. Soil consolidation. Completes disease-break rotation cycle.",
        },
    },
}

REGIONS = ["North India", "South India", "East India", "West India", "Central India"]
SOIL_TYPES = ["Black Soil", "Red Soil", "Laterite Soil", "Alluvial Soil", "Clay Soil"]
MARKET_FOCUS = ["Stable essentials", "High-value cash crops", "Low input / low risk"]

# ============ GLOBAL STYLES ============
st.markdown(
    """
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
    /* ── Base ── */
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
        --bg:        #0c1008;
        --surface:   #141a0f;
        --surface2:  #1c2416;
        --border:    rgba(134, 188, 66, 0.18);
        --accent:    #86bc42;
        --accent2:   #b5e05a;
        --muted:     #6b7c5a;
        --text:      #dde8cc;
        --text-dim:  #8fa07a;
        --danger:    #e05a5a;
        --warn:      #d4a12a;
        --info:      #5a9fd4;
        --radius:    12px;
        --radius-sm: 7px;
    }

    html, body, .stApp, [data-testid="stAppViewContainer"] {
        background: var(--bg) !important;
        color: var(--text) !important;
        font-family: 'DM Sans', sans-serif !important;
    }

    p, span, div, label { color: var(--text); font-size: 1rem; }
    h1, h2, h3, h4, h5 { font-family: 'DM Serif Display', serif !important; color: var(--text) !important; }
    h2, h3, h4 { font-size: 1.25rem !important; color: var(--text) !important; }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg); }
    ::-webkit-scrollbar-thumb { background: var(--accent); border-radius: 4px; }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: var(--surface) !important;
        border-right: 1px solid var(--border) !important;
    }
    [data-testid="stSidebar"] * { color: var(--text) !important; }

    /* ── Inputs ── */
    input, textarea, select,
    [data-baseweb="input"] input,
    [data-baseweb="textarea"] textarea {
        background: var(--surface2) !important;
        border: 1px solid var(--border) !important;
        color: var(--text) !important;
        border-radius: var(--radius-sm) !important;
        font-family: 'DM Sans', sans-serif !important;
    }
    [data-testid="stNumberInput"] input { background: var(--surface2) !important; color: var(--text) !important; }
    [data-testid="stTextInput"] input { background: var(--surface2) !important; color: var(--text) !important; }
    [data-testid="stSelectbox"] { background: var(--surface2) !important; }
    .stSelectbox > div > div { background: var(--surface2) !important; border: 1px solid var(--border) !important; color: var(--text) !important; border-radius: var(--radius-sm) !important; }
    [data-testid="stExpander"] { background: var(--surface2) !important; border: 1px solid var(--border) !important; border-radius: var(--radius) !important; }
    .streamlit-expanderHeader { color: var(--text) !important; font-family: 'DM Sans', sans-serif !important; }

    /* ── Metric ── */
    [data-testid="metric-container"] {
        background: var(--surface2) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        padding: 14px !important;
    }
    [data-testid="stMetricValue"] { color: var(--accent2) !important; font-family: 'DM Serif Display', serif !important; }
    [data-testid="stMetricLabel"] { color: var(--muted) !important; }

    /* ── Buttons ── */
    .stButton > button {
        background: var(--accent) !important;
        color: #0c1008 !important;
        border: none !important;
        padding: 10px 28px !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        border-radius: var(--radius-sm) !important;
        letter-spacing: 0.02em !important;
        transition: background 0.2s, transform 0.15s !important;
        font-family: 'DM Sans', sans-serif !important;
    }
    .stButton > button:hover { background: var(--accent2) !important; transform: translateY(-1px) !important; }

    /* ── Radio ── */
    [data-testid="stRadio"] label { color: var(--text) !important; }
    [data-testid="stRadio"] [data-testid="stMarkdownContainer"] p { color: var(--text-dim) !important; font-size: 0.9rem !important; }

    /* ── Form submit ── */
    [data-testid="stFormSubmitButton"] button {
        background: var(--accent) !important;
        color: #0c1008 !important;
        border: none !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 600 !important;
        font-family: 'DM Sans', sans-serif !important;
    }

    /* ─────────────────────────────────────
       CUSTOM COMPONENTS
    ───────────────────────────────────── */

    /* Header */
    .pd-header {
        display: flex;
        align-items: center;
        gap: 18px;
        padding: 32px 28px;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        margin-bottom: 28px;
    }
    .pd-header-icon { font-size: 3rem; line-height: 1; }
    .pd-header-title {
        font-family: 'DM Serif Display', serif;
        font-size: 2.2rem;
        color: var(--accent2);
        line-height: 1.1;
    }
    .pd-header-sub { font-size: 0.9rem; color: var(--muted); margin-top: 4px; letter-spacing: 0.08em; text-transform: uppercase; }

    /* Feature chips */
    .pd-chips { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 28px; }
    .pd-chip {
        background: var(--surface2);
        border: 1px solid var(--border);
        border-radius: 99px;
        padding: 6px 16px;
        font-size: 0.82rem;
        color: var(--accent);
        font-weight: 500;
        letter-spacing: 0.04em;
    }

    /* Page header (sub-pages) */
    .pd-page-header {
        padding: 22px 24px;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        margin-bottom: 22px;
    }
    .pd-page-title { font-family: 'DM Serif Display', serif; font-size: 1.8rem; color: var(--accent2); }
    .pd-page-sub { font-size: 0.85rem; color: var(--muted); margin-top: 3px; text-transform: uppercase; letter-spacing: 0.07em; }

    /* Card / panel */
    .pd-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 20px;
        margin: 12px 0;
    }
    .pd-card-title {
        font-family: 'DM Serif Display', serif;
        font-size: 1rem;
        color: var(--accent);
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Upload zone */
    .pd-upload {
        background: var(--surface);
        border: 1px dashed var(--accent);
        border-radius: var(--radius);
        padding: 24px;
        margin: 12px 0;
    }

    /* Disease header */
    .pd-disease-header {
        background: var(--surface2);
        border: 1px solid var(--border);
        border-left: 4px solid var(--accent);
        border-radius: var(--radius);
        padding: 22px 24px;
        margin-bottom: 20px;
    }
    .pd-disease-name { font-family: 'DM Serif Display', serif; font-size: 2rem; color: var(--text); margin-bottom: 10px; }
    .pd-disease-meta { display: flex; gap: 10px; flex-wrap: wrap; }

    /* Badges */
    .pd-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 99px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    .sev-healthy  { background: #1b3d1a; color: #6dcc6a; border: 1px solid #6dcc6a40; }
    .sev-mild     { background: #1a2e3d; color: #5ab4e0; border: 1px solid #5ab4e040; }
    .sev-moderate { background: #3d2e0a; color: #d4a12a; border: 1px solid #d4a12a40; }
    .sev-severe   { background: #3d1212; color: #e05a5a; border: 1px solid #e05a5a40; }
    .type-fungal   { background: #2a1a3d; color: #b57aec; border: 1px solid #b57aec40; }
    .type-bacterial{ background: #0d2e40; color: #5ab4e0; border: 1px solid #5ab4e040; }
    .type-viral    { background: #3d1212; color: #e05a5a; border: 1px solid #e05a5a40; }
    .type-pest     { background: #3d2800; color: #e0a040; border: 1px solid #e0a04040; }
    .type-nutrient { background: #1a3d1a; color: #6dcc6a; border: 1px solid #6dcc6a40; }
    .type-healthy  { background: #1a3d1a; color: #6dcc6a; border: 1px solid #6dcc6a40; }

    /* Info section */
    .pd-section {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 18px 20px;
        margin: 10px 0;
    }
    .pd-section-title {
        font-family: 'DM Serif Display', serif;
        font-size: 1rem;
        color: var(--accent);
        margin-bottom: 10px;
        display: flex; align-items: center; gap: 7px;
    }

    /* Treatment item */
    .pd-treatment {
        background: var(--surface2);
        border: 1px solid var(--border);
        border-radius: var(--radius-sm);
        padding: 14px 16px;
        margin: 8px 0;
    }
    .pd-t-name  { font-weight: 600; color: var(--text); font-size: 0.95rem; margin-bottom: 4px; }
    .pd-t-qty   { color: #6dcc6a; font-size: 0.85rem; margin: 2px 0; }
    .pd-t-dil   { color: var(--warn); font-size: 0.82rem; margin: 2px 0; }
    .pd-t-cost  { color: var(--accent); font-size: 0.85rem; font-weight: 600; margin-top: 5px; }

    /* Cost info inline */
    .pd-cost-info {
        background: var(--surface2);
        border: 1px solid var(--border);
        border-radius: var(--radius-sm);
        padding: 10px 14px;
        margin: 10px 0;
        font-size: 0.9rem;
        color: var(--text-dim);
    }

    /* Stat box */
    .pd-stat {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 18px;
        margin: 8px 0;
        text-align: center;
    }
    .pd-stat-val { font-family: 'DM Serif Display', serif; font-size: 1.8rem; color: var(--accent2); margin: 6px 0; }
    .pd-stat-label { font-size: 0.8rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.07em; }

    /* Alert boxes */
    .pd-warn    { background: #3d2e0a; border: 1px solid var(--warn); border-radius: var(--radius-sm); padding: 14px 16px; color: #e8c97a; font-size: 0.95rem; margin: 8px 0; }
    .pd-success { background: #1b3d1a; border: 1px solid #6dcc6a; border-radius: var(--radius-sm); padding: 14px 16px; color: #8ee88b; font-size: 0.95rem; margin: 8px 0; }
    .pd-info    { background: #0d2030; border: 1px solid var(--info); border-radius: var(--radius-sm); padding: 14px 16px; color: #8ecce8; font-size: 0.95rem; margin: 8px 0; }
    .pd-error   { background: #3d1212; border: 1px solid var(--danger); border-radius: var(--radius-sm); padding: 14px 16px; color: #f0a0a0; font-size: 0.95rem; margin: 8px 0; }

    /* Chat */
    .pd-chat-wrap { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; margin: 14px 0; max-height: 480px; overflow-y: auto; }
    .pd-chat-user { background: var(--surface2); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 10px 14px; margin: 6px 0; font-size: 0.92rem; }
    .pd-chat-bot  { background: #1a2416; border: 1px solid rgba(134,188,66,0.25); border-radius: var(--radius-sm); padding: 10px 14px; margin: 6px 0; font-size: 0.92rem; }
    .pd-chat-label { font-size: 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 3px; }
    .pd-kisan-response { background: var(--surface); border: 1px solid var(--accent); border-radius: var(--radius); padding: 20px; margin: 16px 0; font-size: 1rem; line-height: 1.75; color: var(--text); }

    /* Rotation card */
    .pd-rotation {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 20px;
        margin: 10px 0;
        text-align: center;
    }
    .pd-rotation-year { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--muted); margin-bottom: 8px; }
    .pd-rotation-crop { font-family: 'DM Serif Display', serif; font-size: 1.35rem; color: var(--accent2); margin: 6px 0; }
    .pd-rotation-desc { font-size: 0.84rem; color: var(--text-dim); line-height: 1.55; margin-top: 8px; }

    /* Debug */
    .pd-debug { background: var(--bg); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 14px; font-family: monospace; font-size: 0.88rem; max-height: 350px; overflow-y: auto; color: var(--text-dim); white-space: pre-wrap; margin: 8px 0; }

    /* Tips card */
    .pd-tips { background: #1a2416; border: 1px solid rgba(134,188,66,0.3); border-radius: var(--radius); padding: 14px 18px; margin: 10px 0; }
    .pd-tips-title { font-weight: 600; color: var(--accent); margin-bottom: 6px; font-size: 0.9rem; }

    /* Result container */
    .pd-result { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 24px; margin: 14px 0; }
</style>
""",
    unsafe_allow_html=True,
)

# ============ GEMINI CONFIG ============
try:
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
except Exception:
    st.error("GEMINI_API_KEY not found in environment variables!")
    st.stop()

EXPERT_PROMPT_TEMPLATE = """You are an elite plant pathologist with 40 years of specialized experience diagnosing diseases in {plant_type}.
You are an expert specifically in {plant_type} diseases and health issues.

SPECIALIZED ANALYSIS FOR: {plant_type}
Common diseases in {plant_type}: {common_diseases}

Your task is to provide the MOST ACCURATE diagnosis specifically for {plant_type}.

CRITICAL RULES:
1. RESPOND ONLY WITH VALID JSON - NO markdown, NO explanations
2. Use your specialized knowledge of {plant_type}
3. Consider {plant_type}-specific diseases and conditions
4. Cross-reference against known {plant_type} pathologies
5. Be extremely confident ONLY if symptoms match {plant_type} disease profiles
6. Discount diseases that don't typically affect {plant_type}

RESPOND WITH EXACTLY THIS JSON:
{{
  "plant_species": "{plant_type}",
  "disease_name": "Specific disease name or Unable to diagnose",
  "disease_type": "fungal/bacterial/viral/pest/nutrient/environmental/healthy",
  "severity": "healthy/mild/moderate/severe",
  "confidence": 85,
  "confidence_reason": "Detailed explanation specific to {plant_type}",
  "image_quality": "Excellent/Good/Fair/Poor - explanation",
  "symptoms": ["Specific symptom seen in {plant_type}", "Secondary symptom", "Tertiary symptom if present"],
  "differential_diagnosis": ["Disease A (common in {plant_type}): Why it might be this", "Disease B (common in {plant_type}): Why it might be this", "Disease C: Why this is unlikely for {plant_type}"],
  "probable_causes": ["Primary cause relevant to {plant_type}", "Secondary cause", "Environmental factor"],
  "immediate_action": ["Action 1: Specific to {plant_type}", "Action 2: Specific to {plant_type}", "Action 3: Specific to {plant_type}"],
  "organic_treatments": ["Treatment 1: Product and application for {plant_type}", "Treatment 2: Alternative for {plant_type}"],
    "chemical_treatments": [
    "Chemical 1: Safe for {plant_type} with dilution",
    "Chemical 2: Alternative safe for {plant_type}"
  ],
  
   "prevention_long_term": ["Prevention strategy 1 for {plant_type}", "Prevention strategy 2 for {plant_type}", "Resistant varieties: If available for {plant_type}"],
  "plant_specific_notes": "Important notes specific to {plant_type} care and disease management",
  "similar_conditions": "Other {plant_type} conditions that look similar"
}}"""

PLANT_COMMON_DISEASES = {
    "Tomato": "Early blight, Late blight, Septoria leaf spot, Fusarium wilt, Bacterial wilt, Spider mites, Powdery mildew",
    "Rose": "Black spot, Powdery mildew, Rose rosette virus, Rose slugs, Rust, Botrytis",
    "Apple": "Apple scab, Fire blight, Powdery mildew, Cedar apple rust, Sooty blotch, Apple maggot",
    "Lettuce": "Lettuce mosaic virus, Downy mildew, Septoria leaf spot, Bottom rot, Tip burn",
    "Grape": "Powdery mildew, Downy mildew, Black rot, Phomopsis cane and leaf spot, Grape phylloxera",
    "Pepper": "Anthracnose, Bacterial wilt, Phytophthora blight, Cercospora leaf spot, Pepper weevil",
    "Cucumber": "Powdery mildew, Downy mildew, Angular leaf spot, Anthracnose, Cucumber beetles",
    "Strawberry": "Leaf scorch, Powdery mildew, Red stele root rot, Angular leaf spot, Slugs",
    "Corn": "Leaf blotch, Rust, Stewart's wilt, Fusarium ear rot, Corn borer",
    "Potato": "Late blight, Early blight, Verticillium wilt, Potato scab, Rhizoctonia",
}

# ============ HELPER FUNCTIONS ============


def get_type_badge_class(disease_type):
    type_lower = disease_type.lower() if disease_type else "healthy"
    if "fungal" in type_lower:
        return "pd-badge type-fungal"
    elif "bacterial" in type_lower:
        return "pd-badge type-bacterial"
    elif "viral" in type_lower:
        return "pd-badge type-viral"
    elif "pest" in type_lower:
        return "pd-badge type-pest"
    elif "nutrient" in type_lower:
        return "pd-badge type-nutrient"
    else:
        return "pd-badge type-healthy"


def get_severity_badge_class(severity):
    severity_lower = severity.lower() if severity else "moderate"
    if "healthy" in severity_lower or "none" in severity_lower:
        return "pd-badge sev-healthy"
    elif "mild" in severity_lower:
        return "pd-badge sev-mild"
    elif "moderate" in severity_lower:
        return "pd-badge sev-moderate"
    elif "severe" in severity_lower:
        return "pd-badge sev-severe"
    return "pd-badge sev-moderate"


def get_treatment_cost(treatment_type, treatment_name):
    costs = TREATMENT_COSTS.get(treatment_type, {})
    treatment_name_lower = treatment_name.lower()
    for key, value in costs.items():
        if key.lower() == treatment_name_lower:
            return value["cost"] if isinstance(value, dict) else value
    for key, value in costs.items():
        if key.lower() in treatment_name_lower or treatment_name_lower in key.lower():
            return value["cost"] if isinstance(value, dict) else value
    return 300 if treatment_type == "organic" else 250


def get_treatment_info(treatment_type, treatment_name):
    costs = TREATMENT_COSTS.get(treatment_type, {})
    for key, value in costs.items():
        if key.lower() == treatment_name.lower():
            if isinstance(value, dict):
                return value
            return {
                "cost": value,
                "quantity": "As per package",
                "dilution": "Follow label instructions",
            }
    for key, value in costs.items():
        if key.lower() in treatment_name.lower() or treatment_name.lower() in key.lower():
            if isinstance(value, dict):
                return value
            return {
                "cost": value,
                "quantity": "As per package",
                "dilution": "Follow label instructions",
            }
    return {
        "cost": 300 if treatment_type == "organic" else 250,
        "quantity": "As per package",
        "dilution": "Follow label instructions",
    }


def normalize_treatment_name(raw_name: str) -> str:
    if not isinstance(raw_name, str):
        return ""
    name = raw_name.strip()
    if " - " in name:
        name = name.split(" - ", 1)[0].strip()
    if ":" in name:
        name = name.split(":", 1)[0].strip()
    return name


def render_treatment_selection_ui(
    plant_type: str,
    disease_name: str,
    organic_treatments,
    chemical_treatments,
    default_infected_count: int,
):
    st.markdown(
        """<div class="pd-section"><div class="pd-section-title">Setup Cost Calculator & ROI</div></div>""",
        unsafe_allow_html=True,
    )

    default_n = max(int(default_infected_count or 1), 1)
    infected_plants = st.number_input(
        "Number of infected plants you want to treat (for cost & ROI)",
        min_value=1,
        step=1,
        value=default_n,
        key="cost_calc_infected_plants",
    )

    organic_names = [
        normalize_treatment_name(t)
        for t in (organic_treatments or [])
        if isinstance(t, str)
    ]
    chemical_names = [
        normalize_treatment_name(t)
        for t in (chemical_treatments or [])
        if isinstance(t, str)
    ]

    st.markdown(
        "<br><div class='info-section'><div class='info-title'>Select Treatment for Cost Calculation</div></div>",
        unsafe_allow_html=True,
    )

    treatment_type_choice = st.radio(
        "Which treatment will you actually use?",
        ["Organic", "Chemical"],
        horizontal=True,
        key="cost_calc_treatment_type",
    )
    selected_type_key = "organic" if treatment_type_choice == "Organic" else "chemical"

    if selected_type_key == "organic":
        if not organic_names:
            st.warning(
                "No organic treatments were suggested. "
                "You can still enter custom costs on the Cost Calculator page."
            )
            st.session_state.treatment_selection = None
            return
        selected_name = st.selectbox(
            "Select organic treatment (from AI suggestions)",
            organic_names,
            key="cost_calc_selected_organic_treatment",
        )
    else:
        if not chemical_names:
            st.warning(
                "No chemical treatments were suggested. "
                "You can still enter custom costs on the Cost Calculator page."
            )
            st.session_state.treatment_selection = None
            return
        selected_name = st.selectbox(
            "Select chemical treatment (from AI suggestions)",
            chemical_names,
            key="cost_calc_selected_chemical_treatment",
        )

    info = get_treatment_info(selected_type_key, selected_name)
    unit_cost = info.get("cost", 0)
    quantity = info.get("quantity", "As per package")

    base_plants = 100
    if infected_plants <= base_plants:
        total_cost = int(round(unit_cost))
    else:
        total_cost = int(round(unit_cost * infected_plants / base_plants))

    st.session_state.treatment_selection = {
        "plant_type": plant_type,
        "disease_name": disease_name,
        "treatment_type": selected_type_key,  # 'organic' or 'chemical'
        "treatment_name": selected_name,
        "infected_plants": infected_plants,
        "unit_cost": unit_cost,
        "base_plants": base_plants,
        "total_cost": total_cost,
        "quantity": quantity,
    }

    st.markdown(
        f"""
        <div class="pd-cost-info" style="margin-top: 10px;">
            Selected: <b>{selected_name}</b> ({treatment_type_choice})<br>
            Quantity guideline: {quantity}<br>
            Estimated total treatment cost for {infected_plants} plants: <b>Rs {total_cost}</b><br>
            <span style="font-size:0.9rem; color:#b0c4ff;">
                This is based on typical Indian retail prices and standard doses
                for about 100 plants.
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_diagnosis_and_treatments(result: dict, plant_type: str, infected_count: int):
    disease_name = result.get("disease_name", "Unknown")
    disease_type = result.get("disease_type", "unknown")
    severity = result.get("severity", "unknown")
    confidence = result.get("confidence", 0)

    severity_class = get_severity_badge_class(severity)
    type_class = get_type_badge_class(disease_type)

    st.markdown(
        f"""
        <div class="pd-disease-header">
            <div class="pd-disease-name">{disease_name}</div>
            <div class="pd-disease-meta">
                <span class="{severity_class}">{severity.title()}</span>
                <span class="{type_class}">{disease_type.title()}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Plant", plant_type)
    with col2:
        st.metric("Confidence", f"{confidence}%")
    with col3:
        st.metric("Severity", severity.title())

    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown(
            """<div class="pd-section"><div class="pd-section-title">Symptoms</div>""",
            unsafe_allow_html=True,
        )
        for symptom in result.get("symptoms", []):
            st.write(f"• {symptom}")
        st.markdown("</div>", unsafe_allow_html=True)

        if result.get("differential_diagnosis"):
            st.markdown(
                """<div class="pd-section"><div class="pd-section-title">Other Possibilities</div>""",
                unsafe_allow_html=True,
            )
            for diag in result.get("differential_diagnosis", []):
                st.write(f"• {diag}")
            st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        st.markdown(
            """<div class="pd-section"><div class="pd-section-title">Causes</div>""",
            unsafe_allow_html=True,
        )
        for cause in result.get("probable_causes", []):
            st.write(f"• {cause}")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            """<div class="pd-section"><div class="pd-section-title">Actions</div>""",
            unsafe_allow_html=True,
        )
        for i, action in enumerate(result.get("immediate_action", []), 1):
            st.write(f"**{i}.** {action}")
        st.markdown("</div>", unsafe_allow_html=True)

    col_t1, col_t2 = st.columns(2)
    organic_total_block = 0
    chemical_total_block = 0

    with col_t1:
        st.markdown(
            """<div class="pd-section"><div class="pd-section-title">Organic Treatments</div>""",
            unsafe_allow_html=True,
        )
        organic_treatments = result.get("organic_treatments", [])
        for treatment in organic_treatments:
            if not isinstance(treatment, str):
                continue
            t_name = normalize_treatment_name(treatment)
            info = get_treatment_info("organic", t_name)
            cost = info.get("cost", 300)
            quantity = info.get("quantity", "As per package")
            dilution = info.get("dilution", "Follow label instructions")
            organic_total_block += cost
            st.markdown(
                f"""
                <div class="pd-treatment">
                    <div class="pd-t-name">💊 {t_name}</div>
                    <div class="pd-t-qty">Quantity: {quantity}</div>
                    <div class="pd-t-dil">Dilution: {dilution}</div>
                    <div class="pd-cost-info" style="margin-top: 8px; border-left: 5px solid #81c784;">
                        Cost: Rs {cost}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with col_t2:
        st.markdown(
            """<div class="pd-section"><div class="pd-section-title">Chemical Treatments</div>""",
            unsafe_allow_html=True,
        )
        chemical_treatments = result.get("chemical_treatments", [])
        for treatment in chemical_treatments:
            if not isinstance(treatment, str):
                continue
            t_name = normalize_treatment_name(treatment)
            info = get_treatment_info("chemical", t_name)
            cost = info.get("cost", 250)
            quantity = info.get("quantity", "As per package")
            dilution = info.get("dilution", "Follow label instructions")
            chemical_total_block += cost
            st.markdown(
                f"""
                <div class="pd-treatment">
                    <div class="pd-t-name">⚗️ {t_name}</div>
                    <div class="pd-t-qty">Quantity: {quantity}</div>
                    <div class="pd-t-dil">Dilution: {dilution}</div>
                    <div class="pd-cost-info" style="margin-top: 8px; border-left: 5px solid #64b5f6;">
                        Cost: Rs {cost}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """<div class="pd-section"><div class="pd-section-title">Prevention</div>""",
        unsafe_allow_html=True,
    )
    for tip in result.get("prevention_long_term", []):
        st.write(f"• {tip}")
    st.markdown("</div>", unsafe_allow_html=True)

    if result.get("plant_specific_notes"):
        st.markdown(
            f"""
            <div class="pd-section">
                <div class="pd-section-title">{plant_type} Care Notes</div>
                {result.get("plant_specific_notes")}
            </div>
            """,
            unsafe_allow_html=True,
        )

    if result.get("similar_conditions"):
        st.markdown(
            f"""
            <div class="pd-section">
                <div class="pd-section-title">Similar Conditions in {plant_type}</div>
                {result.get("similar_conditions")}
            </div>
            """,
            unsafe_allow_html=True,
        )

    render_treatment_selection_ui(
        plant_type=plant_type,
        disease_name=disease_name,
        organic_treatments=organic_treatments,
        chemical_treatments=chemical_treatments,
        default_infected_count=infected_count,
    )

    return organic_total_block, chemical_total_block


def calculate_loss_percentage(disease_severity, infected_count, total_plants=100):
    """
    Estimate yield loss (%) based on:
    1) Severity band (healthy/mild/moderate/severe) -> typical loss range
    2) Fraction of plants that are infected

    Method:
    - Map severity to a loss band (literature-style ranges)
    - Take the midpoint of that band as base_loss
    - Scale by infected_ratio = infected_count / total_plants
    - Clamp to [0, 80] to avoid unrealistic extremes
    """
    severity_bands = {
        "healthy": (0, 2),      # 0–2% loss
        "mild": (5, 15),        # 5–15% loss
        "moderate": (20, 40),   # 20–40% loss
        "severe": (50, 70),     # 50–70% loss
    }

    sev = (disease_severity or "moderate").lower()
    low, high = severity_bands.get(sev, severity_bands["moderate"])
    base_loss = (low + high) / 2.0  # midpoint of the band

    if total_plants <= 0:
        infected_ratio = 1.0
    else:
        infected_ratio = max(0.0, min(infected_count / total_plants, 1.0))

    loss_percent = base_loss * infected_ratio

    # Clamp to a reasonable range
    loss_percent = max(0.0, min(loss_percent, 80.0))

    return int(round(loss_percent))


def resize_image(image, max_width=600, max_height=500):
    image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    return image


def enhance_image_for_analysis(image):
    from PIL import ImageEnhance

    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.5)
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(1.1)
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(1.5)
    return image


def extract_json_robust(response_text):
    """
    Safely extract a JSON object from the model response.
    Returns a dict on success, or None on failure.
    """
    # Normalize to string
    if isinstance(response_text, list):
        response_text = "\n".join(str(x) for x in response_text)
    elif not isinstance(response_text, str):
        response_text = str(response_text)

    if not response_text or not response_text.strip():
        return None

    # 1) Try direct JSON
    try:
        return json.loads(response_text)
    except Exception:
        pass

    cleaned = response_text

    # 2) Strip ```json ... ``` or ``` ... ``` fences
    if "```json" in cleaned:
        parts = cleaned.split("```json", 1)
        if len(parts) > 1:
            cleaned = parts[1]
        if "```" in cleaned:
            cleaned = cleaned.split("```", 1)[0]
    elif "```" in cleaned:
        parts = cleaned.split("```", 1)
        if len(parts) > 1:
            cleaned = parts[1]
        if "```" in cleaned:
            cleaned = cleaned.split("```", 1)[0]

    cleaned = cleaned.strip()

    # 3) Fallback: first {...} block
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    match = re.search(r"\{[\s\S]*\}", response_text)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass

    return None

def validate_json_result(data):
    required_fields = [
        "disease_name",
        "disease_type",
        "severity",
        "confidence",
        "symptoms",
        "probable_causes",
    ]
    if not isinstance(data, dict):
        return False, "Response is not a dictionary"
    missing = [f for f in required_fields if f not in data]
    if missing:
        return False, f"Missing fields: {', '.join(missing)}"
    return True, "Valid"


def generate_crop_rotation_plan(plant_type, region, soil_type, market_focus):
    if plant_type in CROP_ROTATION_DATA:
        return CROP_ROTATION_DATA[plant_type]
    else:
        return get_manual_rotation_plan(plant_type)


def get_manual_rotation_plan(plant_name):
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
    except Exception:
        return None
    prompt = f"""You are an agricultural expert with deep knowledge of crop rotation and soil health. For the plant: {plant_name}
Provide ONLY a valid JSON response in this exact format (no markdown, no explanations, no code blocks):
{{"rotations": ["Crop1", "Crop2", "Crop3"], "info": {{"{plant_name}": "Detailed info about {plant_name}", "Crop1": "Why good after {plant_name}", "Crop2": "Why follows Crop1", "Crop3": "Why completes cycle"}}}}"""
    try:
        response = model.generate_content(prompt)
        result = extract_json_robust(response.text)
        if result and "rotations" in result and "info" in result:
            return result
    except Exception:
        pass
    return {
        "rotations": ["Legumes or Pulses", "Cereals (Wheat/Maize)", "Oilseeds or Vegetables"],
        "info": {
            plant_name: "Primary crop. Requires disease break and soil replenishment.",
            "Legumes or Pulses": "Nitrogen-fixing crops. Soil improvement and disease cycle break.",
            "Cereals (Wheat/Maize)": "Different nutrient profile. Continues income generation.",
            "Oilseeds or Vegetables": "Diverse crop selection. Completes rotation cycle.",
        },
    }


def get_farmer_bot_response(user_question, diagnosis_context=None):
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
    except Exception:
        return "Model not available. Please try again later."
    context_text = ""
    if diagnosis_context:
        context_text = (
            "Current Diagnosis:\n"
            f"- Plant: {diagnosis_context.get('plant_type', 'Unknown')}\n"
            f"- Disease: {diagnosis_context.get('disease_name', 'Unknown')}\n"
            f"- Severity: {diagnosis_context.get('severity', 'Unknown')}\n"
            f"- Confidence: {diagnosis_context.get('confidence', 'Unknown')}%\n"
        )
    prompt = (
        "You are an expert agricultural advisor for farmers with deep expertise in crop management, "
        "disease control, and sustainable farming practices.\n\n"
        f"{context_text}\n"
        f"Farmer question: {user_question}\n\n"
        "IMPORTANT: Provide a comprehensive, detailed response (5-8 sentences) that includes: "
        "1. Direct answer to the question 2. Practical, cost-effective solutions suitable for farming conditions "
        "3. Seasonal timing and weather considerations if applicable 4. Resource availability and sourcing information "
        "5. Long-term sustainability and soil health recommendations\n\n"
        "Use clear, professional English. Focus on actionable, readily available solutions with proven effectiveness."
    )
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return "Server error. Please try again."


# ============ MAIN UI HEADER ============
st.markdown(
    """
<div class="pd-header">
    <div class="pd-header-icon">🌿</div>
    <div>
        <div class="pd-header-title">AI Plant Doctor</div>
        <div class="pd-header-sub">Gemini-powered plant disease diagnosis &middot; Smart Edition</div>
    </div>
</div>
<div class="pd-chips">
    <span class="pd-chip">🌱 Plant-Specific Analysis</span>
    <span class="pd-chip">🔬 Gemini 2.5 Vision</span>
    <span class="pd-chip">💊 Organic &amp; Chemical Treatments</span>
    <span class="pd-chip">📊 Cost &amp; ROI Calculator</span>
    <span class="pd-chip">🤖 KisanAI Chatbot</span>
    <span class="pd-chip">🔄 Crop Rotation Planner</span>
</div>
""",
    unsafe_allow_html=True,
)

# ============ SIDEBAR ============
with st.sidebar:
    st.markdown("""
    <div style="padding: 4px 0 20px;">
        <div style="font-family:'DM Serif Display',serif; font-size:1.3rem; color:var(--accent2);">🌿 Plant Doctor</div>
        <div style="font-size:0.72rem; color:var(--muted); text-transform:uppercase; letter-spacing:0.08em; margin-top:2px;">Smart Edition · Gemini 2.5</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigate",
        ["AI Plant Doctor", "KisanAI Assistant", "Crop Rotation Advisor", "Cost Calculator & ROI"],
        label_visibility="collapsed",
    )

    st.markdown("""<div style="margin-top:24px; margin-bottom:8px; font-size:0.72rem; text-transform:uppercase; letter-spacing:0.08em; color:var(--muted);">Supported Plants</div>""", unsafe_allow_html=True)
    plants_html = "".join([
        f'<div style="font-size:0.85rem; color:var(--text-dim); padding:3px 0; border-bottom:1px solid var(--border);">{p}</div>'
        for p in sorted(PLANT_COMMON_DISEASES.keys())
    ])
    st.markdown(f'<div style="max-height:280px;overflow-y:auto;">{plants_html}</div>', unsafe_allow_html=True)

    diag_state = st.session_state.get("last_diagnosis")
    if diag_state:
        st.markdown("""<div style="margin-top:24px; margin-bottom:8px; font-size:0.72rem; text-transform:uppercase; letter-spacing:0.08em; color:var(--muted);">Last Diagnosis</div>""", unsafe_allow_html=True)
        sev = diag_state.get("severity","?").title()
        sev_color = {"Healthy":"#6dcc6a","Mild":"#5ab4e0","Moderate":"#d4a12a","Severe":"#e05a5a"}.get(sev, "#8fa07a")
        st.markdown(f"""
        <div style="background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:12px;">
            <div style="font-size:0.82rem;color:var(--accent);font-weight:600;">{diag_state.get('plant_type','?')}</div>
            <div style="font-size:0.78rem;color:var(--text-dim);margin-top:2px;">{diag_state.get('disease_name','?')[:28]}</div>
            <div style="margin-top:8px;display:flex;gap:6px;align-items:center;">
                <span style="font-size:0.72rem;background:{sev_color}22;color:{sev_color};border:1px solid {sev_color}44;border-radius:99px;padding:2px 8px;">{sev}</span>
                <span style="font-size:0.72rem;color:var(--muted);">{diag_state.get('confidence',0)}% conf.</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ============ SESSION STATE DEFAULTS ============
if "last_diagnosis" not in st.session_state:
    st.session_state.last_diagnosis = None
if "treatment_selection" not in st.session_state:
    st.session_state.treatment_selection = None
if "farmer_bot_messages" not in st.session_state:
    st.session_state.farmer_bot_messages = []
if "crop_rotation_result" not in st.session_state:
    st.session_state.crop_rotation_result = None
if "cost_roi_result" not in st.session_state:
    st.session_state.cost_roi_result = None
if "kisan_response" not in st.session_state:
    st.session_state.kisan_response = None
if "model_choice" not in st.session_state:
    st.session_state.model_choice = "Gemini 2.5 Flash"
if "debug_mode" not in st.session_state:
    st.session_state.debug_mode = False
if "show_tips" not in st.session_state:
    st.session_state.show_tips = True
if "confidence_min" not in st.session_state:
    st.session_state.confidence_min = 65

# ============ MAIN PAGES ============

# --- AI Plant Doctor ---
if page == 'AI Plant Doctor':
    st.markdown("""
    <div class='pd-page-header'>
        <div class='pd-page-title'>AI Plant Doctor</div>
        <div class='pd-page-sub'>Upload a leaf photo &middot; get instant Gemini diagnosis</div>
    </div>
    """, unsafe_allow_html=True)

    col_plant, col_upload = st.columns([1, 2], gap='medium')
    with col_plant:
        st.markdown('<div class="pd-card"><div class="pd-card-title">Select Plant</div>', unsafe_allow_html=True)
        plant_options = ['Select a plant...'] + sorted(list(PLANT_COMMON_DISEASES.keys())) + ['Other (Manual Entry)']
        selected_plant = st.selectbox('Plant', plant_options, label_visibility='collapsed')
        if selected_plant == 'Other (Manual Entry)':
            custom_plant = st.text_input('Plant name', placeholder='e.g., Banana, Orange', label_visibility='collapsed')
            plant_type = custom_plant if custom_plant else 'Unknown Plant'
        else:
            plant_type = selected_plant if selected_plant != 'Select a plant...' else None
        if plant_type and plant_type in PLANT_COMMON_DISEASES:
            st.markdown(f'<div style="margin-top:10px;padding:10px 12px;background:var(--surface2);border:1px solid var(--border);border-radius:7px;"><div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:0.07em;color:var(--muted);margin-bottom:5px;">Common in {plant_type}</div><div style="font-size:0.82rem;color:var(--text-dim);line-height:1.55;">{PLANT_COMMON_DISEASES[plant_type]}</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_upload:
        st.markdown('<div class="pd-card"><div class="pd-card-title">Upload Leaf Images</div><div style="font-size:0.82rem;color:var(--muted);margin-bottom:10px;">Upload up to 3 clear photos for best results.</div>', unsafe_allow_html=True)
        uploaded_files = st.file_uploader('Images', type=['jpg','jpeg','png'], accept_multiple_files=True, label_visibility='collapsed')
        st.markdown('</div>', unsafe_allow_html=True)

    images = None
    analyze_btn = False
    if uploaded_files and len(uploaded_files) > 0 and plant_type and plant_type != 'Select a plant...':
        if len(uploaded_files) > 3:
            st.warning('Maximum 3 images — only the first 3 will be analyzed.')
            uploaded_files = uploaded_files[:3]
        images = [Image.open(f) for f in uploaded_files]
        st.markdown('<div class="pd-card" style="margin-top:8px;">', unsafe_allow_html=True)
        img_cols = st.columns(len(images))
        for idx_i, (col, image) in enumerate(zip(img_cols, images)):
            with col:
                st.caption(f'Image {idx_i + 1}')
                st.image(resize_image(image.copy()), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        _, col_btn, _ = st.columns([1, 2, 1])
        with col_btn:
            analyze_btn = st.button(f'Analyse {plant_type}', use_container_width=True, type='primary')

    if analyze_btn and images is not None and plant_type:
        progress_placeholder = st.empty()
        with st.spinner(f'Analysing {plant_type}...'):
            try:
                progress_placeholder.info(f'Processing {plant_type} leaf image(s)...')
                model_id = 'gemini-2.5-pro' if 'Pro' in st.session_state.model_choice else 'gemini-2.5-flash'
                model = genai.GenerativeModel(model_id)
                if st.session_state.debug_mode:
                    st.info(f'Model: {model_id}')
                common_diseases = PLANT_COMMON_DISEASES.get(plant_type, 'various plant diseases')
                prompt = EXPERT_PROMPT_TEMPLATE.format(plant_type=plant_type, common_diseases=common_diseases)
                enhanced_images = [enhance_image_for_analysis(img.copy()) for img in images]
                response = model.generate_content([prompt] + enhanced_images)
                raw_response = response.text
                if st.session_state.debug_mode:
                    with st.expander('Raw API Response'):
                        st.code(raw_response[:3000], language='json')
                result = extract_json_robust(raw_response)
                progress_placeholder.empty()
                if result is None:
                    st.error('Could not parse AI response. Try again or use a clearer image.')
                if result:
                    confidence = result.get('confidence', 0)
                    if confidence < st.session_state.confidence_min:
                        st.warning(f'Low confidence ({confidence}%) — result may be unreliable.')
                    st.session_state.last_diagnosis = {
                        'plant_type': plant_type,
                        'disease_name': result.get('disease_name', 'Unknown'),
                        'disease_type': result.get('disease_type', 'unknown'),
                        'severity': result.get('severity', 'unknown'),
                        'confidence': confidence,
                        'organic_cost': 0,
                        'chemical_cost': 0,
                        'infected_count': 50,
                        'timestamp': datetime.now().isoformat(),
                        'result': result,
                    }
            except Exception as e:
                st.error(f'Analysis failed: {str(e)}')
                progress_placeholder.empty()

    diag = st.session_state.last_diagnosis
    if diag:
        ts = diag.get('timestamp', '')[:10]
        st.markdown(f'<div class="pd-info" style="margin:16px 0 4px;">Showing last diagnosis{" · " + ts if ts else ""}. Navigate freely — results are preserved.</div>', unsafe_allow_html=True)
        organic_total_cost, chemical_total_cost = render_diagnosis_and_treatments(
            result=diag.get('result', {}),
            plant_type=diag.get('plant_type', 'Unknown'),
            infected_count=diag.get('infected_count', 50),
        )
        diag['organic_cost'] = organic_total_cost
        diag['chemical_cost'] = chemical_total_cost
        st.session_state.last_diagnosis = diag

# --- KisanAI Assistant ---
elif page == 'KisanAI Assistant':
    st.markdown('<div class="pd-page-header"><div class="pd-page-title">KisanAI Assistant</div><div class="pd-page-sub">Your personal agricultural advisor</div></div>', unsafe_allow_html=True)
    diag = st.session_state.last_diagnosis
    if diag:
        sev = diag.get('severity', '?').title()
        sev_color = {'Healthy':'#6dcc6a','Mild':'#5ab4e0','Moderate':'#d4a12a','Severe':'#e05a5a'}.get(sev, '#8fa07a')
        st.markdown(f'<div class="pd-card" style="margin-bottom:12px;"><div class="pd-card-title">Active diagnosis context</div><div style="display:flex;gap:18px;flex-wrap:wrap;align-items:center;"><div><div style="font-size:0.72rem;color:var(--muted);text-transform:uppercase;">Plant</div><div style="font-size:0.95rem;font-weight:500;">{diag.get("plant_type","?")}</div></div><div><div style="font-size:0.72rem;color:var(--muted);text-transform:uppercase;">Disease</div><div style="font-size:0.95rem;font-weight:500;">{diag.get("disease_name","?")}</div></div><div><div style="font-size:0.72rem;color:var(--muted);text-transform:uppercase;">Severity</div><span style="font-size:0.82rem;background:{sev_color}22;color:{sev_color};border:1px solid {sev_color}44;border-radius:99px;padding:2px 10px;">{sev}</span></div><div><div style="font-size:0.72rem;color:var(--muted);text-transform:uppercase;">Confidence</div><div style="color:var(--accent);font-weight:500;">{diag.get("confidence",0)}%</div></div></div></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="pd-warn" style="margin-bottom:14px;">No recent diagnosis found. Run AI Plant Doctor first for context-aware responses. You can still ask general farming questions below.</div>', unsafe_allow_html=True)

    _, col_clr, col_ref = st.columns([3, 1, 1])
    with col_clr:
        if st.button('Clear chat', use_container_width=True):
            st.session_state.farmer_bot_messages = []
            st.session_state.kisan_response = None
            st.rerun()
    with col_ref:
        if st.button('Refresh', use_container_width=True):
            st.rerun()

    st.markdown('<div class="pd-chat-wrap">', unsafe_allow_html=True)
    if len(st.session_state.farmer_bot_messages) == 0:
        st.markdown('<div class="pd-chat-bot" style="text-align:center;padding:20px;"><div style="font-size:1rem;margin-bottom:4px;">Welcome to KisanAI</div><div style="font-size:0.85rem;color:var(--muted);">Ask anything about crops, diseases, treatments, or farming practices.</div></div>', unsafe_allow_html=True)
    else:
        for msg in st.session_state.farmer_bot_messages[-20:]:
            if msg['role'] == 'farmer':
                st.markdown(f'<div class="pd-chat-user"><div class="pd-chat-label">You</div>{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="pd-chat-bot"><div class="pd-chat-label">KisanAI</div>{msg["content"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    with st.form('farmer_bot_form', clear_on_submit=True):
        user_question = st.text_area('Question', height=90, placeholder='Ask about treatments, prevention, costs, or any farming topic...', label_visibility='collapsed')
        submitted = st.form_submit_button('Send', use_container_width=True)
    if submitted and user_question.strip():
        st.session_state.farmer_bot_messages.append({'role': 'farmer', 'content': user_question.strip()})
        answer = get_farmer_bot_response(user_question.strip(), diagnosis_context=diag)
        st.session_state.farmer_bot_messages.append({'role': 'assistant', 'content': answer})
        st.session_state.kisan_response = answer
        st.rerun()

# --- Crop Rotation Advisor ---
elif page == 'Crop Rotation Advisor':
    st.markdown('<div class="pd-page-header"><div class="pd-page-title">Crop Rotation Advisor</div><div class="pd-page-sub">Sustainable 3-year rotation planning</div></div>', unsafe_allow_html=True)
    diag = st.session_state.last_diagnosis
    default_plant = diag['plant_type'] if diag and diag.get('plant_type') else None
    col_i1, col_i2 = st.columns(2, gap='medium')
    with col_i1:
        st.markdown('<div class="pd-card"><div class="pd-card-title">Crop Selection</div>', unsafe_allow_html=True)
        use_last = False
        if default_plant:
            use_last = st.checkbox(f'Use diagnosed plant: {default_plant}', value=True)
        if use_last and default_plant:
            plant_type = default_plant
            st.markdown(f'<div style="font-size:0.85rem;color:var(--accent);margin-top:4px;">Using: {plant_type}</div>', unsafe_allow_html=True)
        else:
            selected_option = st.selectbox('Select plant', sorted(list(PLANT_COMMON_DISEASES.keys())) + ['Other (manual entry)'], label_visibility='collapsed')
            if selected_option == 'Other (manual entry)':
                plant_type = st.text_input('Plant name', placeholder='e.g., Banana, Mango, Ginger', label_visibility='collapsed')
            else:
                plant_type = selected_option
        st.markdown('</div>', unsafe_allow_html=True)
    with col_i2:
        st.markdown('<div class="pd-card"><div class="pd-card-title">Region &amp; Soil</div>', unsafe_allow_html=True)
        region = st.selectbox('Region', REGIONS)
        soil_type = st.selectbox('Soil type', SOIL_TYPES)
        market_focus = st.selectbox('Market focus', MARKET_FOCUS)
        st.markdown('</div>', unsafe_allow_html=True)
    _, col_gen, _ = st.columns([1, 2, 1])
    with col_gen:
        gen_btn = st.button('Generate Rotation Plan', use_container_width=True, type='primary')
    if gen_btn:
        if plant_type:
            with st.spinner(f'Generating rotation plan for {plant_type}...'):
                rots_data = generate_crop_rotation_plan(plant_type, region, soil_type, market_focus)
                st.session_state.crop_rotation_result = {'plant_type': plant_type, 'rotations': rots_data.get('rotations', []), 'info': rots_data.get('info', {}), 'region': region, 'soil_type': soil_type}
        else:
            st.warning('Please select or enter a plant type first.')
    if st.session_state.crop_rotation_result:
        res = st.session_state.crop_rotation_result
        rots = res['rotations']
        info = res['info']
        st.markdown('<div style="margin:20px 0 8px;font-size:0.72rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);">3-Year Rotation Strategy</div>', unsafe_allow_html=True)
        col_y1, col_y2, col_y3 = st.columns(3, gap='medium')
        years = [('Year 1 · Current', res['plant_type'], info.get(res['plant_type'], 'Primary crop.')), ('Year 2 · Rotation', rots[0] if rots else '—', info.get(rots[0], 'Rotation crop.') if rots else ''), ('Year 3 · Alternative', rots[1] if len(rots)>1 else '—', info.get(rots[1], 'Alternative crop.') if len(rots)>1 else '')]
        for col, (label, crop, desc) in zip([col_y1, col_y2, col_y3], years):
            with col:
                st.markdown(f'<div class="pd-rotation"><div class="pd-rotation-year">{label}</div><div class="pd-rotation-crop">{crop}</div><div class="pd-rotation-desc">{desc}</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="pd-card" style="margin-top:16px;"><div class="pd-card-title">Benefits of Rotation</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:4px;"><div style="font-size:0.85rem;color:var(--text-dim);">60–80% reduction in pathogen buildup</div><div style="font-size:0.85rem;color:var(--text-dim);">Improved soil health &amp; structure</div><div style="font-size:0.85rem;color:var(--text-dim);">Lower chemical input costs</div><div style="font-size:0.85rem;color:var(--text-dim);">Enhanced soil biodiversity</div></div></div>', unsafe_allow_html=True)

# --- Cost Calculator & ROI ---
else:
    st.markdown('<div class="pd-page-header"><div class="pd-page-title">Cost &amp; ROI Analysis</div><div class="pd-page-sub">Investment analysis for treatment options</div></div>', unsafe_allow_html=True)
    diag = st.session_state.last_diagnosis
    if not diag:
        st.markdown('<div class="pd-warn">No diagnosis found. Run AI Plant Doctor first to get disease and treatment data, then come back here.</div>', unsafe_allow_html=True)
    else:
        plant_name = diag.get('plant_type', 'Unknown')
        disease_name = diag.get('disease_name', 'Unknown')
        selection = st.session_state.treatment_selection
        infected_count = selection['infected_plants'] if selection and isinstance(selection.get('infected_plants'), int) else diag.get('infected_count', 50)
        sev = diag.get('severity', '?').title()
        sev_color = {'Healthy':'#6dcc6a','Mild':'#5ab4e0','Moderate':'#d4a12a','Severe':'#e05a5a'}.get(sev, '#8fa07a')
        st.markdown(f'<div class="pd-card" style="margin-bottom:20px;"><div class="pd-card-title">Diagnosis Summary</div><div style="display:flex;gap:24px;flex-wrap:wrap;margin-top:4px;"><div><div style="font-size:0.72rem;color:var(--muted);text-transform:uppercase;">Plant</div><div style="font-size:1rem;font-weight:500;margin-top:2px;">{plant_name}</div></div><div><div style="font-size:0.72rem;color:var(--muted);text-transform:uppercase;">Disease</div><div style="font-size:1rem;font-weight:500;margin-top:2px;">{disease_name}</div></div><div><div style="font-size:0.72rem;color:var(--muted);text-transform:uppercase;">Severity</div><span style="font-size:0.82rem;background:{sev_color}22;color:{sev_color};border:1px solid {sev_color}44;border-radius:99px;padding:2px 10px;">{sev}</span></div><div><div style="font-size:0.72rem;color:var(--muted);text-transform:uppercase;">Confidence</div><div style="font-size:1rem;color:var(--accent);font-weight:500;margin-top:2px;">{diag.get("confidence",0)}%</div></div><div><div style="font-size:0.72rem;color:var(--muted);text-transform:uppercase;">Infected plants</div><div style="font-size:1rem;font-weight:500;margin-top:2px;">{infected_count}</div></div></div></div>', unsafe_allow_html=True)
        st.markdown('<div class="pd-card"><div class="pd-card-title">Treatment &amp; Yield Inputs</div>', unsafe_allow_html=True)
        if selection and isinstance(selection.get('total_cost'), int):
            use_cost = selection.get('buying_total_cost', selection['total_cost']) if selection.get('is_buying') else selection['total_cost']
            organic_default = use_cost if selection['treatment_type'] == 'organic' else 0
            chemical_default = 0 if selection['treatment_type'] == 'organic' else use_cost
        else:
            organic_default = int(diag.get('organic_cost', 300) * infected_count)
            chemical_default = int(diag.get('chemical_cost', 200) * infected_count)
        col_ii1, col_ii2, col_ii3, col_ii4 = st.columns(4)
        with col_ii1:
            organic_cost_total = st.number_input('Organic cost (Rs)', value=organic_default, min_value=0, step=100)
        with col_ii2:
            chemical_cost_total = st.number_input('Chemical cost (Rs)', value=chemical_default, min_value=0, step=100)
        with col_ii3:
            yield_kg = st.number_input('Yield (kg)', value=1000, min_value=100, step=100)
        with col_ii4:
            market_price = st.number_input('Price/kg (Rs)', value=40, min_value=1, step=5)
        st.markdown('</div>', unsafe_allow_html=True)
        auto_loss_pct = calculate_loss_percentage(diag.get('severity', 'moderate'), infected_count, total_plants=100)
        total_revenue = int(yield_kg * market_price)
        potential_loss = int(total_revenue * (auto_loss_pct / 100))
        st.markdown('<div style="margin:16px 0 8px;font-size:0.72rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);">Loss Estimate (auto-calculated)</div>', unsafe_allow_html=True)
        col_l1, col_l2, col_l3 = st.columns(3, gap='medium')
        with col_l1:
            st.markdown(f'<div class="pd-stat"><div class="pd-stat-label">Loss %</div><div class="pd-stat-val" style="color:#e05a5a;">{auto_loss_pct}%</div></div>', unsafe_allow_html=True)
        with col_l2:
            st.markdown(f'<div class="pd-stat"><div class="pd-stat-label">Total Yield Value</div><div class="pd-stat-val">Rs {total_revenue:,}</div></div>', unsafe_allow_html=True)
        with col_l3:
            st.markdown(f'<div class="pd-stat"><div class="pd-stat-label">Potential Loss</div><div class="pd-stat-val" style="color:#e05a5a;">Rs {potential_loss:,}</div></div>', unsafe_allow_html=True)
        _, col_calc, _ = st.columns([1, 2, 1])
        with col_calc:
            calc_btn = st.button('Calculate ROI', use_container_width=True, type='primary')
        if calc_btn:
            org_benefit = potential_loss - organic_cost_total
            chem_benefit = potential_loss - chemical_cost_total
            analysis = {
                'total_value': total_revenue, 'loss_prevented': potential_loss, 'loss_percentage': auto_loss_pct,
                'org_roi': int(org_benefit / organic_cost_total * 100) if organic_cost_total > 0 else 0,
                'chem_roi': int(chem_benefit / chemical_cost_total * 100) if chemical_cost_total > 0 else 0,
                'organic_net': org_benefit, 'chemical_net': chem_benefit,
                'total_organic_cost': organic_cost_total, 'total_chemical_cost': chemical_cost_total, 'infected_count': infected_count,
            }
            st.session_state.cost_roi_result = {'plant_name': plant_name, 'disease_name': disease_name, 'analysis': analysis}
        if st.session_state.cost_roi_result:
            ana = st.session_state.cost_roi_result['analysis']
            st.markdown('<div style="margin:20px 0 8px;font-size:0.72rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);">ROI Results</div>', unsafe_allow_html=True)
            col_r1, col_r2 = st.columns(2, gap='medium')
            org_color = '#6dcc6a' if ana['org_roi'] >= ana['chem_roi'] else 'var(--text-dim)'
            chem_color = '#5ab4e0' if ana['chem_roi'] >= ana['org_roi'] else 'var(--text-dim)'
            with col_r1:
                st.markdown(f'<div class="pd-card"><div class="pd-card-title">Organic Treatment</div><div style="font-size:2.2rem;font-family:DM Serif Display,serif;color:{org_color};margin:8px 0;">{ana["org_roi"]}% ROI</div><div style="display:flex;gap:16px;"><div><div style="font-size:0.72rem;color:var(--muted);">Cost</div><div>Rs {ana["total_organic_cost"]:,}</div></div><div><div style="font-size:0.72rem;color:var(--muted);">Net benefit</div><div style="color:{org_color};">Rs {ana["organic_net"]:,}</div></div></div></div>', unsafe_allow_html=True)
            with col_r2:
                st.markdown(f'<div class="pd-card"><div class="pd-card-title">Chemical Treatment</div><div style="font-size:2.2rem;font-family:DM Serif Display,serif;color:{chem_color};margin:8px 0;">{ana["chem_roi"]}% ROI</div><div style="display:flex;gap:16px;"><div><div style="font-size:0.72rem;color:var(--muted);">Cost</div><div>Rs {ana["total_chemical_cost"]:,}</div></div><div><div style="font-size:0.72rem;color:var(--muted);">Net benefit</div><div style="color:{chem_color};">Rs {ana["chemical_net"]:,}</div></div></div></div>', unsafe_allow_html=True)
            if ana['org_roi'] > ana['chem_roi']:
                verdict = f'Organic gives better ROI ({ana["org_roi"]}% vs {ana["chem_roi"]}%). Recommended for sustainable farming.'
            elif ana['chem_roi'] > ana['org_roi']:
                verdict = f'Chemical gives higher immediate ROI ({ana["chem_roi"]}% vs {ana["org_roi"]}%). Consider organic for long-term soil health.'
            else:
                verdict = 'Both treatments have equal ROI. Choose based on your sustainability goals.'
            st.markdown(f'<div class="pd-success" style="margin-top:12px;">{verdict}</div>', unsafe_allow_html=True)
