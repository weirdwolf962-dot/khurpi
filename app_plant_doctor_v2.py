import streamlit as st
try:
    import google.generativeai as genai
except ModuleNotFoundError:
    st.error("Missing dependency: google-generativeai — add it to requirements.txt and redeploy.")
    st.stop()

from PIL import Image, ImageEnhance
import os, json, re
from datetime import datetime

st.set_page_config(
    page_title="🌿 Kisan AI",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────
# INDIAN LANGUAGES
# ─────────────────────────────────────────────────────────────
LANGUAGES = {
    "English": "en",
    "हिंदी (Hindi)": "hi",
    "ਪੰਜਾਬੀ (Punjabi)": "pa",
    "मराठी (Marathi)": "mr",
    "తెలుగు (Telugu)": "te",
    "தமிழ் (Tamil)": "ta",
    "ಕನ್ನಡ (Kannada)": "kn",
    "বাংলা (Bengali)": "bn",
    "ગુજરાતી (Gujarati)": "gu",
    "ଓଡ଼ିଆ (Odia)": "or",
    "മലയാളം (Malayalam)": "ml",
    "অসমীয়া (Assamese)": "as",
    "اردو (Urdu)": "ur",
}

LANG_INSTRUCTIONS = {
    "en": "Respond in clear, simple English. Avoid technical jargon. Speak like a helpful village doctor.",
    "hi": "हिंदी में जवाब दें। सरल और आसान भाषा में। जैसे एक मददगार गाँव का डॉक्टर बोलता है।",
    "pa": "ਪੰਜਾਬੀ ਵਿੱਚ ਜਵਾਬ ਦਿਓ। ਸਰਲ ਅਤੇ ਆਸਾਨ ਭਾਸ਼ਾ ਵਿੱਚ।",
    "mr": "मराठीत उत्तर द्या. सोप्या भाषेत.",
    "te": "తెలుగులో సమాధానం ఇవ్వండి. సులభమైన భాషలో.",
    "ta": "தமிழில் பதில் சொல்லுங்கள். எளிய மொழியில்.",
    "kn": "ಕನ್ನಡದಲ್ಲಿ ಉತ್ತರ ನೀಡಿ. ಸರಳ ಭಾಷೆಯಲ್ಲಿ.",
    "bn": "বাংলায় উত্তর দিন। সহজ ভাষায়।",
    "gu": "ગુજરાતીમાં જવાબ આપો. સરળ ભાષામાં.",
    "or": "ଓଡ଼ିଆରେ ଉତ୍ତର ଦିଅ। ସରଳ ଭାଷାରେ।",
    "ml": "മലയാളത്തിൽ ഉത്തരം നൽകുക. ലളിതമായ ഭാഷയിൽ.",
    "as": "অসমীয়াত উত্তৰ দিয়ক। সহজ ভাষাত।",
    "ur": "اردو میں جواب دیں۔ سادہ زبان میں۔",
}

# ─────────────────────────────────────────────────────────────
# DATABASES (unchanged from original)
# ─────────────────────────────────────────────────────────────
TREATMENT_COSTS = {
    "organic": {
        "Cow Urine Extract": {"cost": 80, "quantity": "2-3 liters per 100 plants", "dilution": "1:5 with water"},
        "Sulfur Dust": {"cost": 120, "quantity": "500g per 100 plants", "dilution": "Direct dust - 5-10g per plant"},
        "Sulfur Powder": {"cost": 150, "quantity": "200g per 100 plants", "dilution": "3% suspension - 20ml per plant"},
        "Lime Sulfur": {"cost": 180, "quantity": "1 liter per 100 plants", "dilution": "1:10 with water"},
        "Neem Oil Spray": {"cost": 250, "quantity": "500ml per 100 plants", "dilution": "3% solution - 5ml per liter"},
        "Bordeaux Mixture": {"cost": 250, "quantity": "300g per 100 plants", "dilution": "1% solution - 10g per liter"},
        "Karanja Oil": {"cost": 220, "quantity": "400ml per 100 plants", "dilution": "2.5% solution - 2.5ml per liter"},
        "Copper Fungicide (Organic)": {"cost": 280, "quantity": "250g per 100 plants", "dilution": "0.5% solution - 5g per liter"},
        "Potassium Bicarbonate": {"cost": 300, "quantity": "150g per 100 plants", "dilution": "1% solution - 10g per liter"},
        "Bacillus subtilis": {"cost": 350, "quantity": "100g per 100 plants", "dilution": "0.1% solution - 1g per liter"},
        "Azadirachtin": {"cost": 380, "quantity": "200ml per 100 plants", "dilution": "0.3% solution - 3ml per liter"},
        "Trichoderma": {"cost": 400, "quantity": "500g per 100 plants", "dilution": "0.5% solution - 5g per liter"},
        "Spinosad": {"cost": 2000, "quantity": "100ml per 100 plants", "dilution": "0.02% solution - 0.2ml per liter"},
        "Seaweed Extract": {"cost": 260, "quantity": "250ml per 100 plants", "dilution": "0.3% solution - 3ml per liter"},
    },
    "chemical": {
        "Carbendazim (Bavistin)": {"cost": 120, "quantity": "100g per 100 plants", "dilution": "0.1% solution - 1g per liter"},
        "Mancozeb (Indofil)": {"cost": 120, "quantity": "150g per 100 plants", "dilution": "0.2% solution - 2g per liter"},
        "Copper Oxychloride": {"cost": 150, "quantity": "200g per 100 plants", "dilution": "0.25% solution - 2.5g per liter"},
        "Profenofos (Meothrin)": {"cost": 200, "quantity": "100ml per 100 plants", "dilution": "0.05% solution - 0.5ml per liter"},
        "Chlorothalonil": {"cost": 220, "quantity": "120g per 100 plants", "dilution": "0.15% solution - 1.5g per liter"},
        "Deltamethrin (Decis)": {"cost": 220, "quantity": "50ml per 100 plants", "dilution": "0.005% solution - 0.05ml per liter"},
        "Imidacloprid (Confidor)": {"cost": 350, "quantity": "80ml per 100 plants", "dilution": "0.008% solution - 0.08ml per liter"},
        "Tebuconazole (Folicur)": {"cost": 320, "quantity": "120ml per 100 plants", "dilution": "0.05% solution - 0.5ml per liter"},
        "Thiamethoxam (Actara)": {"cost": 290, "quantity": "100g per 100 plants", "dilution": "0.04% solution - 0.4g per liter"},
        "Azoxystrobin (Amistar)": {"cost": 650, "quantity": "80ml per 100 plants", "dilution": "0.02% solution - 0.2ml per liter"},
        "Hexaconazole (Contaf Plus)": {"cost": 350, "quantity": "100ml per 100 plants", "dilution": "0.04% solution - 0.4ml per liter"},
        "Metalaxyl + Mancozeb (Ridomil Gold)": {"cost": 190, "quantity": "100g per 100 plants", "dilution": "0.25% solution - 2.5g per liter"},
        "Propiconazole (Tilt)": {"cost": 190, "quantity": "100ml per 100 plants", "dilution": "0.1% solution - 1ml per liter"},
    },
}

CROP_ROTATION_DATA = {
    "Tomato": {"rotations": ["Beans", "Cabbage", "Cucumber"], "info": {"Tomato": "High-value solanaceae crop. Susceptible to early/late blight, fusarium wilt. Needs 3+ year rotation.", "Beans": "Nitrogen-fixing legume. Improves soil. Breaks disease cycle.", "Cabbage": "Brassica family. Helps control tomato diseases.", "Cucumber": "No common diseases with tomato. Completes rotation cycle."}},
    "Rose": {"rotations": ["Marigold", "Chrysanthemum", "Herbs"], "info": {"Rose": "Ornamental crop. Susceptible to black spot, powdery mildew.", "Marigold": "Natural pest repellent. Attracts beneficial insects.", "Chrysanthemum": "Different pest profile. Breaks rose pathogen cycle.", "Herbs": "Basil, rosemary improve soil health. Confuse rose pests."}},
    "Apple": {"rotations": ["Legume Cover Crops", "Grasses", "Berries"], "info": {"Apple": "Perennial crop. Susceptible to apple scab, fire blight.", "Legume Cover Crops": "Nitrogen fixation. Breaks pathogen cycle.", "Grasses": "Erosion control. Beneficial insect habitat.", "Berries": "Different root depth. Continues income during off-year."}},
    "Lettuce": {"rotations": ["Spinach", "Broccoli", "Cauliflower"], "info": {"Lettuce": "Cool-season leafy crop. Quick 60-70 day cycle.", "Spinach": "Resistant to lettuce diseases. Tolerates cold.", "Broccoli": "Different pest profile. Breaks disease cycle.", "Cauliflower": "Completes 3-crop rotation cycle."}},
    "Grape": {"rotations": ["Legume Cover Crops", "Cereals", "Vegetables"], "info": {"Grape": "Perennial vine. Powdery mildew, phylloxera concerns.", "Legume Cover Crops": "Nitrogen replenishment. Disease elimination.", "Cereals": "Wheat/maize. Nematode cycle break.", "Vegetables": "Re-establishes soil microbiology."}},
    "Pepper": {"rotations": ["Onion", "Garlic", "Spinach"], "info": {"Pepper": "Solanaceae crop. Anthracnose, bacterial wilt issues.", "Onion": "Allium family. Breaks solanaceae cycle.", "Garlic": "Natural pest deterrent. Soil antimicrobial.", "Spinach": "No common pepper diseases. Spring/fall compatible."}},
    "Cucumber": {"rotations": ["Maize", "Okra", "Legumes"], "info": {"Cucumber": "Cucurbitaceae family. 2-3 year rotation suggested.", "Maize": "Different root system. Strong market demand.", "Okra": "No overlapping pests. Heat-tolerant.", "Legumes": "Nitrogen restoration. Disease-free break."}},
    "Strawberry": {"rotations": ["Garlic", "Onion", "Leafy Greens"], "info": {"Strawberry": "Low-growing perennial. 3-year bed rotation needed.", "Garlic": "Antimicrobial soil activity. Excellent succession crop.", "Onion": "Deters strawberry pests.", "Leafy Greens": "Quick cycle. Utilizes residual nutrients."}},
    "Corn": {"rotations": ["Soybean", "Pulses", "Oilseeds"], "info": {"Corn": "Heavy nitrogen feeder. 3+ year rotation critical.", "Soybean": "Nitrogen-fixing. Reduces fertilizer needs 40-50%.", "Pulses": "Chickpea/lentil. High market value.", "Oilseeds": "Sunflower/safflower. Income diversification."}},
    "Potato": {"rotations": ["Peas", "Mustard", "Cereals"], "info": {"Potato": "Solanaceae crop. Late blight, nematodes. 4-year rotation.", "Peas": "Nitrogen-fixing. Breaks potato pathogen cycle.", "Mustard": "Biofumigation. Natural nematode control.", "Cereals": "Wheat/barley. Completes disease-break cycle."}},
}

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
    "Wheat": "Rust, Powdery mildew, Loose smut, Karnal bunt, Foot rot",
    "Rice": "Blast, Brown spot, Sheath blight, Bacterial leaf blight, False smut",
    "Cotton": "Boll rot, Leaf curl virus, Bacterial blight, Fusarium wilt, Verticillium wilt",
    "Sugarcane": "Red rot, Smut, Ratoon stunting, Grassy shoot, Pineapple disease",
    "Onion": "Purple blotch, Downy mildew, Stemphylium blight, Basal rot, Thrips",
    "Garlic": "White rot, Downy mildew, Stemphylium blight, Rust, Purple blotch",
    "Mango": "Anthracnose, Powdery mildew, Mango malformation, Bacterial canker, Stem end rot",
    "Banana": "Panama wilt, Sigatoka, Bunchy top virus, Anthracnose, Weevil borer",
    "Chilli": "Anthracnose, Bacterial wilt, Leaf curl virus, Powdery mildew, Thrips",
    "Brinjal": "Little leaf disease, Bacterial wilt, Fruit borer, Phomopsis blight, Cercospora",
}

REGIONS = ["North India", "South India", "East India", "West India", "Central India", "Northeast India"]
SOIL_TYPES = ["Black Soil (Regur)", "Red Soil", "Laterite Soil", "Alluvial Soil", "Sandy Soil", "Clay Soil", "Loamy Soil"]

# ─────────────────────────────────────────────────────────────
# GLOBAL CSS — Glassmorphism Dark Theme
# ─────────────────────────────────────────────────────────────
st.html("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Poppins:wght@600;700&display=swap" rel="stylesheet">
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
    --bg1: #0a0f0a;
    --bg2: #0d1810;
    --glass: rgba(255,255,255,0.04);
    --glass-border: rgba(134,188,66,0.15);
    --glass-hover: rgba(255,255,255,0.07);
    --accent: #7dc742;
    --accent2: #a8e063;
    --accent-glow: rgba(125,199,66,0.25);
    --red: #e05a5a;
    --yellow: #d4a12a;
    --blue: #5a9fd4;
    --text: #e8f0dc;
    --text-dim: #8fa07a;
    --text-muted: #4e6040;
    --radius: 16px;
    --radius-sm: 10px;
    --radius-lg: 24px;
}

html, body, .stApp, [data-testid="stAppViewContainer"],
[data-testid="stMain"], .main, .block-container {
    background: transparent !important;
    font-family: 'Inter', sans-serif !important;
    color: var(--text) !important;
}

/* Full page gradient background */
[data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed;
    inset: 0;
    background:
        radial-gradient(ellipse 80% 60% at 20% 10%, rgba(40,80,20,0.45) 0%, transparent 60%),
        radial-gradient(ellipse 60% 50% at 80% 80%, rgba(20,60,10,0.3) 0%, transparent 60%),
        linear-gradient(135deg, #060d06 0%, #0a140a 40%, #081008 100%);
    z-index: -1;
    pointer-events: none;
}

/* Floating orbs */
[data-testid="stAppViewContainer"]::after {
    content: '';
    position: fixed;
    width: 500px; height: 500px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(125,199,66,0.06) 0%, transparent 70%);
    top: -100px; right: -100px;
    pointer-events: none;
    z-index: -1;
}

.block-container { max-width: 1000px !important; padding: 0 24px 80px !important; }

/* Hide default streamlit elements */
#MainMenu, footer, header, [data-testid="stDecoration"],
[data-testid="stSidebarNav"], .stDeployButton { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--accent); border-radius: 4px; opacity: 0.5; }

/* ── Glass card ── */
.glass {
    background: var(--glass);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius);
    padding: 20px 24px;
    margin: 10px 0;
}
.glass-sm {
    background: var(--glass);
    backdrop-filter: blur(12px);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-sm);
    padding: 14px 18px;
}

/* ── TOP HEADER ── */
.top-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px 0 16px;
    border-bottom: 1px solid var(--glass-border);
    margin-bottom: 20px;
}
.logo-wrap { display: flex; align-items: center; gap: 12px; }
.logo-icon {
    width: 44px; height: 44px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.4rem;
    box-shadow: 0 4px 20px var(--accent-glow);
}
.logo-title { font-family: 'Poppins', sans-serif; font-size: 1.4rem; font-weight: 700; color: var(--text); line-height: 1.1; }
.logo-sub { font-size: 0.72rem; color: var(--text-dim); letter-spacing: 0.1em; text-transform: uppercase; }

/* ── CHAT AREA ── */
.chat-area {
    display: flex;
    flex-direction: column;
    gap: 12px;
    min-height: 200px;
    padding: 8px 0;
}

.msg-bot, .msg-user {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    animation: fadeUp 0.3s ease;
}
.msg-user { flex-direction: row-reverse; }

@keyframes fadeUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}

.avatar {
    width: 34px; height: 34px; border-radius: 10px; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; font-weight: 600;
}
.avatar-bot {
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    box-shadow: 0 2px 12px var(--accent-glow);
    color: #0a0f0a;
}
.avatar-user {
    background: rgba(255,255,255,0.1);
    color: var(--text);
    border: 1px solid var(--glass-border);
}

.bubble {
    max-width: 82%;
    padding: 12px 16px;
    border-radius: var(--radius);
    font-size: 0.93rem;
    line-height: 1.65;
}
.bubble-bot {
    background: rgba(255,255,255,0.05);
    border: 1px solid var(--glass-border);
    color: var(--text);
    border-top-left-radius: 4px;
}
.bubble-user {
    background: linear-gradient(135deg, rgba(125,199,66,0.18), rgba(125,199,66,0.1));
    border: 1px solid rgba(125,199,66,0.25);
    color: var(--text);
    border-top-right-radius: 4px;
    text-align: right;
}

/* ── DIAGNOSIS RESULT CARD ── */
.diag-card {
    background: rgba(255,255,255,0.04);
    backdrop-filter: blur(20px);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-lg);
    padding: 24px;
    margin: 8px 0;
}
.diag-title {
    font-family: 'Poppins', sans-serif;
    font-size: 1.35rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 4px;
}
.diag-meta { display: flex; gap: 8px; flex-wrap: wrap; margin: 10px 0 16px; }

.badge {
    display: inline-flex; align-items: center; gap: 4px;
    font-size: 0.75rem; font-weight: 600;
    padding: 4px 12px; border-radius: 99px;
    letter-spacing: 0.04em;
}
.badge-healthy  { background: rgba(109,204,106,0.15); color: #6dcc6a; border: 1px solid rgba(109,204,106,0.3); }
.badge-mild     { background: rgba(90,180,224,0.15);  color: #5ab4e0; border: 1px solid rgba(90,180,224,0.3); }
.badge-moderate { background: rgba(212,161,42,0.15);  color: #d4a12a; border: 1px solid rgba(212,161,42,0.3); }
.badge-severe   { background: rgba(224,90,90,0.15);   color: #e05a5a; border: 1px solid rgba(224,90,90,0.3); }
.badge-green    { background: rgba(125,199,66,0.12);  color: var(--accent2); border: 1px solid rgba(125,199,66,0.2); }
.badge-blue     { background: rgba(90,159,212,0.12);  color: #5a9fd4; border: 1px solid rgba(90,159,212,0.2); }

/* Confidence bar */
.conf-wrap { margin: 12px 0; }
.conf-label { font-size: 0.75rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 6px; }
.conf-bar-bg { background: rgba(255,255,255,0.08); border-radius: 99px; height: 8px; overflow: hidden; }
.conf-bar-fill { height: 100%; border-radius: 99px; transition: width 1s ease; }

/* Section heading inside card */
.sec-head {
    font-size: 0.72rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.1em;
    color: var(--text-dim); margin: 16px 0 8px;
    display: flex; align-items: center; gap: 6px;
}
.sec-head::after {
    content: ''; flex: 1; height: 1px;
    background: var(--glass-border);
}

/* Action item */
.action-item {
    display: flex; align-items: flex-start; gap: 10px;
    padding: 10px 14px;
    background: rgba(125,199,66,0.06);
    border: 1px solid rgba(125,199,66,0.12);
    border-radius: var(--radius-sm);
    margin: 5px 0;
    font-size: 0.88rem;
    color: var(--text);
    line-height: 1.5;
}
.action-num {
    flex-shrink: 0;
    width: 22px; height: 22px; border-radius: 6px;
    background: var(--accent); color: #0a0f0a;
    font-size: 0.72rem; font-weight: 700;
    display: flex; align-items: center; justify-content: center;
    margin-top: 1px;
}

/* Treatment pill */
.treat-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 14px;
    background: rgba(255,255,255,0.04);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-sm);
    margin: 5px 0;
    flex-wrap: wrap; gap: 6px;
}
.treat-name { font-size: 0.9rem; font-weight: 500; color: var(--text); }
.treat-detail { font-size: 0.78rem; color: var(--text-dim); margin-top: 2px; }
.treat-cost {
    font-size: 0.82rem; font-weight: 600;
    color: var(--accent2);
    background: rgba(125,199,66,0.1);
    padding: 3px 10px; border-radius: 99px;
    border: 1px solid rgba(125,199,66,0.2);
    white-space: nowrap;
}
.treat-fallback { font-size: 0.72rem; color: var(--yellow); margin-top: 2px; }

/* ROI box */
.roi-box {
    display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
    margin: 12px 0;
}
.roi-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-sm);
    padding: 14px 16px;
    text-align: center;
}
.roi-val { font-family: 'Poppins', sans-serif; font-size: 1.6rem; font-weight: 700; margin: 4px 0; }
.roi-label { font-size: 0.72rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.07em; }

/* Rotation card */
.rot-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 10px 0; }
.rot-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-sm);
    padding: 14px; text-align: center;
}
.rot-year { font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--text-muted); margin-bottom: 6px; }
.rot-crop { font-size: 1rem; font-weight: 600; color: var(--accent2); margin: 4px 0; }
.rot-desc { font-size: 0.78rem; color: var(--text-dim); line-height: 1.5; margin-top: 6px; }

/* ── INPUT BAR ── */
.input-bar-wrap {
    position: sticky;
    bottom: 0;
    background: linear-gradient(to top, rgba(6,13,6,0.98) 70%, transparent);
    padding: 14px 0 8px;
    z-index: 100;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, var(--accent), #5fa830) !important;
    color: #0a0f0a !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 10px 22px !important;
    font-family: 'Inter', sans-serif !important;
    box-shadow: 0 4px 16px var(--accent-glow) !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.02em !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 24px var(--accent-glow) !important;
}

/* ── Inputs ── */
input, textarea,
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid var(--glass-border) !important;
    color: var(--text) !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'Inter', sans-serif !important;
}
input:focus, textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px var(--accent-glow) !important;
}
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input { background: rgba(255,255,255,0.05) !important; color: var(--text) !important; }

/* Selectbox */
.stSelectbox > div > div {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid var(--glass-border) !important;
    color: var(--text) !important;
    border-radius: var(--radius-sm) !important;
}
[data-baseweb="select"] { background: rgba(255,255,255,0.05) !important; }
[data-baseweb="popover"] { background: #0d180f !important; border: 1px solid var(--glass-border) !important; }

/* File uploader */
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1.5px dashed var(--glass-border) !important;
    border-radius: var(--radius) !important;
}
[data-testid="stFileUploader"]:hover { border-color: var(--accent) !important; }
[data-testid="stFileUploader"] * { color: var(--text-dim) !important; }

/* Radio */
[data-testid="stRadio"] label { color: var(--text) !important; }

/* Number input */
[data-testid="stNumberInput"] { }

/* Tabs */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.04) !important;
    border-radius: var(--radius-sm) !important;
    border: 1px solid var(--glass-border) !important;
    gap: 2px !important;
    padding: 4px !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--text-dim) !important;
    border-radius: 8px !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: linear-gradient(135deg, var(--accent), #5fa830) !important;
    color: #0a0f0a !important;
    font-weight: 600 !important;
}
[data-testid="stTabs"] [data-baseweb="tab-border"] { display: none !important; }
[data-testid="stTabs"] [data-baseweb="tab-panel"] {
    background: transparent !important;
    padding: 16px 0 0 !important;
}

/* Expander */
[data-testid="stExpander"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: var(--radius-sm) !important;
}
.streamlit-expanderHeader { color: var(--text) !important; font-size: 0.9rem !important; }

/* Misc labels */
p, span, div, label { color: var(--text); font-size: 0.93rem; }
h1, h2, h3 { font-family: 'Poppins', sans-serif !important; color: var(--text) !important; }

/* Warning / info banners */
.stAlert { border-radius: var(--radius-sm) !important; background: rgba(255,255,255,0.04) !important; border: 1px solid var(--glass-border) !important; }

/* Sidebar (for language selector) */
[data-testid="stSidebar"] {
    background: rgba(10,15,10,0.95) !important;
    backdrop-filter: blur(20px) !important;
    border-right: 1px solid var(--glass-border) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }

/* Image */
.stImage img { border-radius: var(--radius-sm); border: 1px solid var(--glass-border); }

/* Spinner */
.stSpinner > div { border-color: var(--accent) transparent transparent transparent !important; }

/* Divider */
hr { border-color: var(--glass-border) !important; margin: 16px 0 !important; }
</style>
""")

# ─────────────────────────────────────────────────────────────
# GEMINI CONFIG
# ─────────────────────────────────────────────────────────────
_api_key = os.environ.get("GEMINI_API_KEY", "").strip()
if not _api_key:
    st.markdown("""
    <div class="glass" style="max-width:560px;margin:80px auto;border-color:rgba(224,90,90,0.3);">
        <div style="font-size:1.1rem;font-weight:600;color:#e05a5a;margin-bottom:10px;">⚠️ API Key Missing</div>
        <div style="color:var(--text-dim);line-height:1.7;font-size:0.9rem;">
            <b style="color:var(--text);">GEMINI_API_KEY</b> is not set.<br><br>
            Go to your Streamlit app → <i>Manage app</i> → <i>Secrets</i> and add:<br>
            <code style="background:rgba(0,0,0,0.4);padding:6px 12px;border-radius:6px;display:inline-block;margin-top:8px;color:var(--accent2);">GEMINI_API_KEY = "your-key-here"</code><br><br>
            Get a free key at <a href="https://aistudio.google.com/apikey" style="color:var(--accent);">aistudio.google.com/apikey</a>
        </div>
    </div>""", unsafe_allow_html=True)
    st.stop()

try:
    genai.configure(api_key=_api_key)
except Exception as e:
    st.error(f"Could not configure Gemini: {e}")
    st.stop()

# ─────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────
def enhance_image(image):
    e = ImageEnhance.Contrast(image); image = e.enhance(1.4)
    e = ImageEnhance.Brightness(image); image = e.enhance(1.1)
    e = ImageEnhance.Sharpness(image); image = e.enhance(1.4)
    return image

def resize_image(image, max_w=600, max_h=500):
    image.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    return image

def extract_json(text):
    if isinstance(text, list): text = "\n".join(str(x) for x in text)
    if not isinstance(text, str): text = str(text)
    try: return json.loads(text)
    except: pass
    cleaned = text
    for fence in ["```json", "```"]:
        if fence in cleaned:
            parts = cleaned.split(fence, 1)
            if len(parts) > 1:
                cleaned = parts[1]
                if "```" in cleaned: cleaned = cleaned.split("```", 1)[0]
            break
    try: return json.loads(cleaned.strip())
    except: pass
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try: return json.loads(m.group(0))
        except: pass
    return None

def get_treatment_info(ttype, tname):
    costs = TREATMENT_COSTS.get(ttype, {})
    for k, v in costs.items():
        if k.lower() == tname.lower():
            return dict(v, _matched=True) if isinstance(v, dict) else {"cost": v, "quantity": "As per package", "dilution": "Follow label", "_matched": True}
    for k, v in costs.items():
        if k.lower() in tname.lower() or tname.lower() in k.lower():
            return dict(v, _matched=True) if isinstance(v, dict) else {"cost": v, "quantity": "As per package", "dilution": "Follow label", "_matched": True}
    return {"cost": 300 if ttype == "organic" else 250, "quantity": "As per package", "dilution": "Follow label", "_matched": False}

def normalize_name(raw):
    if not isinstance(raw, str): return ""
    name = raw.strip()
    if " - " in name: name = name.split(" - ", 1)[0].strip()
    if ":" in name: name = name.split(":", 1)[0].strip()
    return name

def calc_loss_pct(severity, infected, total):
    bands = {"healthy": (0,2), "mild": (5,15), "moderate": (20,40), "severe": (50,70)}
    lo, hi = bands.get((severity or "moderate").lower(), (20,40))
    base = (lo + hi) / 2
    ratio = max(0.0, min(infected / max(total, 1), 1.0))
    return int(round(min(base * ratio, 80.0)))

def sev_badge(sev):
    s = (sev or "").lower()
    cls = "badge-healthy" if "health" in s else "badge-mild" if "mild" in s else "badge-severe" if "severe" in s else "badge-moderate"
    icon = "✅" if "health" in s else "🟡" if "mild" in s else "🔴" if "severe" in s else "🟠"
    return f'<span class="badge {cls}">{icon} {sev.title()}</span>'

def conf_color(c):
    if c >= 80: return "#7dc742"
    if c >= 60: return "#d4a12a"
    return "#e05a5a"

# ─────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────
for k, v in {
    "messages": [],
    "last_diagnosis": None,
    "lang": "English",
    "lang_code": "en",
    "awaiting_photo": False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

lang_code = st.session_state.lang_code
lang_instruction = LANG_INSTRUCTIONS.get(lang_code, LANG_INSTRUCTIONS["en"])

# ─────────────────────────────────────────────────────────────
# TOP HEADER
# ─────────────────────────────────────────────────────────────
col_logo, col_lang = st.columns([3, 1])
with col_logo:
    st.markdown("""
    <div class="top-header">
        <div class="logo-wrap">
            <div class="logo-icon">🌿</div>
            <div>
                <div class="logo-title">Kisan AI</div>
                <div class="logo-sub">Plant Doctor · Gemini 2.5</div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

with col_lang:
    st.markdown("<div style='padding-top:22px;'></div>", unsafe_allow_html=True)
    chosen_lang = st.selectbox(
        "🌐 Language",
        list(LANGUAGES.keys()),
        index=list(LANGUAGES.keys()).index(st.session_state.lang),
        label_visibility="collapsed",
        key="lang_selector"
    )
    if chosen_lang != st.session_state.lang:
        st.session_state.lang = chosen_lang
        st.session_state.lang_code = LANGUAGES[chosen_lang]
        st.rerun()

# ─────────────────────────────────────────────────────────────
# CHAT HISTORY DISPLAY
# ─────────────────────────────────────────────────────────────
def render_messages():
    if not st.session_state.messages:
        welcome = {
            "en": "🙏 Namaste! I'm your Kisan AI Plant Doctor, powered by Gemini 2.5.\n\nI can help you with:\n• 📸 **Diagnose** plant diseases from photos\n• 💊 **Treatment** recommendations (organic & chemical)\n• 💰 **Cost & ROI** for treatments\n• 🔄 **Crop rotation** planning\n• 🌾 Any farming question in your language\n\nTo get started, upload a leaf photo below or just ask me anything!",
            "hi": "🙏 नमस्ते! मैं आपका किसान AI प्लांट डॉक्टर हूं।\n\nमैं आपकी मदद कर सकता हूं:\n• 📸 फोटो से पौधे की बीमारी **पहचानना**\n• 💊 **इलाज** की सलाह (जैविक और रासायनिक)\n• 💰 **लागत और मुनाफे** का हिसाब\n• 🔄 **फसल चक्र** की योजना\n• 🌾 खेती से जुड़ा कोई भी सवाल\n\nशुरू करने के लिए नीचे पत्ती की फोटो डालें या कोई सवाल पूछें!",
            "pa": "🙏 ਸਤ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਤੁਹਾਡਾ ਕਿਸਾਨ AI ਪਲਾਂਟ ਡਾਕਟਰ ਹਾਂ।\n\nਮੈਂ ਤੁਹਾਡੀ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ:\n• 📸 ਫੋਟੋ ਤੋਂ ਪੌਦੇ ਦੀ ਬਿਮਾਰੀ **ਪਛਾਣਨਾ**\n• 💊 **ਇਲਾਜ** ਦੀ ਸਲਾਹ\n• 💰 **ਲਾਗਤ ਅਤੇ ਮੁਨਾਫਾ**\n• 🔄 **ਫਸਲ ਚੱਕਰ** ਯੋਜਨਾ\n\nਸ਼ੁਰੂ ਕਰਨ ਲਈ ਹੇਠਾਂ ਪੱਤੇ ਦੀ ਫੋਟੋ ਪਾਓ!",
        }
        msg = welcome.get(lang_code, welcome["en"])
        st.markdown(f"""
        <div class="msg-bot">
            <div class="avatar avatar-bot">🌿</div>
            <div class="bubble bubble-bot" style="white-space:pre-line;">{msg}</div>
        </div>""", unsafe_allow_html=True)
        return

    for m in st.session_state.messages:
        role = m["role"]
        content = m["content"]
        if role == "user":
            st.markdown(f"""
            <div class="msg-user">
                <div class="avatar avatar-user">👤</div>
                <div class="bubble bubble-user">{content}</div>
            </div>""", unsafe_allow_html=True)
        else:
            if m.get("type") == "diagnosis":
                render_diagnosis_card(m["data"])
            else:
                st.markdown(f"""
                <div class="msg-bot">
                    <div class="avatar avatar-bot">🌿</div>
                    <div class="bubble bubble-bot" style="white-space:pre-line;">{content}</div>
                </div>""", unsafe_allow_html=True)

def generate_pdf_report(d, lc="en"):
    """Generate a clean PDF report in the selected language using reportlab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import io, os

    # Load Unicode font for Devanagari/Gurmukhi
    font_name = "Helvetica"
    bold_font = "Helvetica-Bold"
    # Try to use a unicode font if available (for Hindi/Punjabi)
    unicode_fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    ]
    for fp in unicode_fonts:
        if os.path.exists(fp):
            try:
                pdfmetrics.registerFont(TTFont("UniFont", fp))
                font_name = "UniFont"
                bold_font = "UniFont"
                break
            except: pass

    result = d.get("result", {})
    plant = d.get("plant_type", "Unknown")
    disease = result.get("disease_name", "Unknown")
    severity = result.get("severity", "unknown").title()
    conf = result.get("confidence", 0)
    region = d.get("region", "")
    soil = d.get("soil", "")
    infected = d.get("infected_count", 0)
    total = d.get("total_plants", 100)
    loss_pct = calc_loss_pct(d.get("severity", severity.lower()), infected, total)

    # Labels per language
    labels = {
        "en": {
            "title": "Kisan AI — Plant Disease Report",
            "plant": "Plant", "disease": "Disease", "severity": "Severity",
            "confidence": "Confidence", "region": "Region", "soil": "Soil Type",
            "infected": "Infected Plants", "total": "Total Plants", "loss": "Est. Yield Loss",
            "actions": "Immediate Actions", "organic": "Organic Treatments",
            "chemical": "Chemical Treatments", "prevention": "Long-term Prevention",
            "org_cost": "Organic Cost (per 100 plants)", "chem_cost": "Chemical Cost (per 100 plants)",
            "notes": "Plant-Specific Notes", "generated": "Generated by Kisan AI",
            "treatment": "Treatment", "qty": "Quantity", "price": "Price (₹)",
        },
        "hi": {
            "title": "किसान AI — पौधे की बीमारी रिपोर्ट",
            "plant": "पौधा", "disease": "बीमारी", "severity": "गंभीरता",
            "confidence": "विश्वास", "region": "क्षेत्र", "soil": "मिट्टी का प्रकार",
            "infected": "संक्रमित पौधे", "total": "कुल पौधे", "loss": "अनुमानित उपज हानि",
            "actions": "तुरंत करें", "organic": "जैविक उपचार",
            "chemical": "रासायनिक उपचार", "prevention": "दीर्घकालिक रोकथाम",
            "org_cost": "जैविक लागत (100 पौधों के लिए)", "chem_cost": "रासायनिक लागत (100 पौधों के लिए)",
            "notes": "पौधे विशेष नोट्स", "generated": "किसान AI द्वारा तैयार",
            "treatment": "उपचार", "qty": "मात्रा", "price": "कीमत (₹)",
        },
        "pa": {
            "title": "ਕਿਸਾਨ AI — ਪੌਦੇ ਦੀ ਬਿਮਾਰੀ ਰਿਪੋਰਟ",
            "plant": "ਪੌਦਾ", "disease": "ਬਿਮਾਰੀ", "severity": "ਗੰਭੀਰਤਾ",
            "confidence": "ਭਰੋਸਾ", "region": "ਖੇਤਰ", "soil": "ਮਿੱਟੀ ਦੀ ਕਿਸਮ",
            "infected": "ਸੰਕਰਮਿਤ ਪੌਦੇ", "total": "ਕੁੱਲ ਪੌਦੇ", "loss": "ਅਨੁਮਾਨਿਤ ਝਾੜ ਨੁਕਸਾਨ",
            "actions": "ਤੁਰੰਤ ਕਰੋ", "organic": "ਜੈਵਿਕ ਇਲਾਜ",
            "chemical": "ਰਸਾਇਣਕ ਇਲਾਜ", "prevention": "ਲੰਬੇ ਸਮੇਂ ਦੀ ਰੋਕਥਾਮ",
            "org_cost": "ਜੈਵਿਕ ਲਾਗਤ (100 ਪੌਦਿਆਂ ਲਈ)", "chem_cost": "ਰਸਾਇਣਕ ਲਾਗਤ (100 ਪੌਦਿਆਂ ਲਈ)",
            "notes": "ਪੌਦੇ ਸੰਬੰਧੀ ਨੋਟਸ", "generated": "ਕਿਸਾਨ AI ਦੁਆਰਾ ਤਿਆਰ",
            "treatment": "ਇਲਾਜ", "qty": "ਮਾਤਰਾ", "price": "ਕੀਮਤ (₹)",
        },
    }
    L = labels.get(lc, labels["en"])

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    GREEN = colors.HexColor("#2d7a1f")
    LIGHT_GREEN = colors.HexColor("#e8f5e2")
    DARK = colors.HexColor("#1a2e1a")
    GRAY = colors.HexColor("#666666")
    RED = colors.HexColor("#c0392b")
    ORANGE = colors.HexColor("#e67e22")

    sev_color = {"healthy": GREEN, "mild": colors.HexColor("#2980b9"),
                 "moderate": ORANGE, "severe": RED}.get(severity.lower(), GRAY)

    def para(text, size=10, bold=False, color=DARK, space_before=0, space_after=4, align="LEFT"):
        align_map = {"LEFT": 0, "CENTER": 1, "RIGHT": 2}
        s = ParagraphStyle("custom", fontName=bold_font if bold else font_name,
                           fontSize=size, textColor=color,
                           spaceAfter=space_after, spaceBefore=space_before,
                           alignment=align_map.get(align, 0), leading=size*1.4)
        return Paragraph(str(text), s)

    def section_header(text):
        return [
            Spacer(1, 0.3*cm),
            para(text, size=11, bold=True, color=GREEN, space_before=4),
            HRFlowable(width="100%", thickness=1, color=LIGHT_GREEN, spaceAfter=4),
        ]

    story = []

    # Header
    story.append(para(L["title"], size=18, bold=True, color=GREEN, align="CENTER", space_after=4))
    story.append(para(f"🗓 {datetime.now().strftime('%d %B %Y, %I:%M %p')}", size=9, color=GRAY, align="CENTER", space_after=2))
    story.append(Spacer(1, 0.5*cm))

    # Summary table
    sev_display = f"{severity}"
    summary_data = [
        [L["plant"], plant, L["region"], region],
        [L["disease"], disease, L["soil"], soil],
        [L["severity"], sev_display, L["confidence"], f"{conf}%"],
        [L["infected"], str(infected), L["total"], str(total)],
        [L["loss"], f"{loss_pct}%", "", ""],
    ]
    summary_table = Table(summary_data, colWidths=[3.5*cm, 5.5*cm, 3.5*cm, 5.5*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.white),
        ('BACKGROUND', (0,0), (0,-1), LIGHT_GREEN),
        ('BACKGROUND', (2,0), (2,-1), LIGHT_GREEN),
        ('FONTNAME', (0,0), (0,-1), bold_font),
        ('FONTNAME', (2,0), (2,-1), bold_font),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TEXTCOLOR', (0,0), (0,-1), GREEN),
        ('TEXTCOLOR', (2,0), (2,-1), GREEN),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#dddddd")),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.white, colors.HexColor("#f9f9f9")]),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TEXTCOLOR', (1,1), (1,1), sev_color),
        ('FONTNAME', (1,1), (1,1), bold_font),
    ]))
    story.append(summary_table)

    # Immediate actions
    actions = result.get("immediate_action", [])
    if actions:
        story += section_header(f"⚡ {L['actions']}")
        for i, a in enumerate(actions, 1):
            story.append(para(f"{i}. {a}", size=10, space_after=3))

    # Organic treatments
    org_treats = result.get("organic_treatments", [])
    if org_treats:
        story += section_header(f"🌿 {L['organic']}")
        org_rows = [[L["treatment"], L["qty"], L["price"]]]
        for t in org_treats:
            if not isinstance(t, str): continue
            n = normalize_name(t)
            info = get_treatment_info("organic", n)
            org_rows.append([n, info["quantity"], f"Rs.{info['cost']}"])
        t = Table(org_rows, colWidths=[6*cm, 7*cm, 4*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), GREEN),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), bold_font),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#dddddd")),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_GREEN]),
            ('PADDING', (0,0), (-1,-1), 6),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(t)

    # Chemical treatments
    chem_treats = result.get("chemical_treatments", [])
    if chem_treats:
        story += section_header(f"⚗️ {L['chemical']}")
        chem_rows = [[L["treatment"], L["qty"], L["price"]]]
        for t in chem_treats:
            if not isinstance(t, str): continue
            n = normalize_name(t)
            info = get_treatment_info("chemical", n)
            chem_rows.append([n, info["quantity"], f"Rs.{info['cost']}"])
        t2 = Table(chem_rows, colWidths=[6*cm, 7*cm, 4*cm])
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2980b9")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), bold_font),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#dddddd")),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#e8f0f8")]),
            ('PADDING', (0,0), (-1,-1), 6),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(t2)

    # Prevention
    prevention = result.get("prevention_long_term", [])
    if prevention:
        story += section_header(f"🛡️ {L['prevention']}")
        for p in prevention[:4]:
            story.append(para(f"• {p}", size=10, space_after=3))

    # Notes
    notes = result.get("plant_specific_notes", "")
    if notes:
        story += section_header(f"📌 {L['notes']}")
        story.append(para(notes, size=10, color=DARK))

    # Footer
    story.append(Spacer(1, 0.8*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=LIGHT_GREEN))
    story.append(para(f"{L['generated']} · kisanai.streamlit.app · {datetime.now().strftime('%d/%m/%Y')}", size=8, color=GRAY, align="CENTER", space_before=4))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def render_diagnosis_card(d):
    result = d.get("result", {})
    disease = result.get("disease_name", "Unknown")
    severity = result.get("severity", "unknown")
    conf = result.get("confidence", 0)
    dtype = result.get("disease_type", "").title()
    plant = d.get("plant_type", "")
    infected = d.get("infected_count", 0)
    total = d.get("total_plants", 100)
    loss_pct = calc_loss_pct(severity, infected, total)

    conf_c = conf_color(conf)
    sev_html = sev_badge(severity)

    actions = result.get("immediate_action", [])
    org_treats = result.get("organic_treatments", [])
    chem_treats = result.get("chemical_treatments", [])
    prevention = result.get("prevention_long_term", [])

    # Organic cost estimate
    org_total = 0
    org_rows = []
    for t in org_treats:
        if not isinstance(t, str): continue
        n = normalize_name(t)
        info = get_treatment_info("organic", n)
        org_total += info["cost"]
        matched = info.get("_matched", True)
        fallback = '' if matched else '<div class="treat-fallback">⚠️ Estimated price</div>'
        org_rows.append(f'<div class="treat-row"><div><div class="treat-name">🌿 {n}</div><div class="treat-detail">{info["quantity"]} · {info["dilution"]}</div>{fallback}</div><div class="treat-cost">₹{info["cost"]}</div></div>')

    chem_total = 0
    chem_rows = []
    for t in chem_treats:
        if not isinstance(t, str): continue
        n = normalize_name(t)
        info = get_treatment_info("chemical", n)
        chem_total += info["cost"]
        matched = info.get("_matched", True)
        fallback = '' if matched else '<div class="treat-fallback">⚠️ Estimated price</div>'
        chem_rows.append(f'<div class="treat-row"><div><div class="treat-name">⚗️ {n}</div><div class="treat-detail">{info["quantity"]} · {info["dilution"]}</div>{fallback}</div><div class="treat-cost">₹{info["cost"]}</div></div>')

    # ROI calculation
    yield_val = 1000 * 40  # default 1000kg @ ₹40/kg
    potential_loss = int(yield_val * loss_pct / 100)
    org_roi = int((potential_loss - org_total) / max(org_total, 1) * 100) if org_total else 0
    chem_roi = int((potential_loss - chem_total) / max(chem_total, 1) * 100) if chem_total else 0

    roi_org_color = "#7dc742" if org_roi >= chem_roi else "var(--text-dim)"
    roi_chem_color = "#5a9fd4" if chem_roi > org_roi else "var(--text-dim)"

    action_html = "".join([f'<div class="action-item"><div class="action-num">{i+1}</div><div>{a}</div></div>' for i, a in enumerate(actions)])
    org_treat_html = "".join(org_rows)
    chem_treat_html = "".join(chem_rows)
    prev_html = "".join([f'<div class="action-item" style="background:rgba(90,159,212,0.06);border-color:rgba(90,159,212,0.15);">🛡️ {p}</div>' for p in prevention[:3]])

    # Rotation
    rot_html = ""
    if plant in CROP_ROTATION_DATA:
        rd = CROP_ROTATION_DATA[plant]
        rots = rd.get("rotations", [])
        info_d = rd.get("info", {})
        rot_items = [(f"Year 1 · Now", plant, info_d.get(plant,"")[:80])]
        for i, r in enumerate(rots[:2]):
            rot_items.append((f"Year {i+2} · Next", r, info_d.get(r,"")[:80]))
        rot_cards = "".join([f'<div class="rot-card"><div class="rot-year">{y}</div><div class="rot-crop">{c}</div><div class="rot-desc">{d_}</div></div>' for y,c,d_ in rot_items])
        rot_html = f'<div class="sec-head">🔄 Crop Rotation Plan</div><div class="rot-grid">{rot_cards}</div>'

    notes = result.get("plant_specific_notes", "")
    notes_html = f'<div class="sec-head">📌 Notes</div><div class="bubble bubble-bot" style="max-width:100%;margin:0;">{notes}</div>' if notes else ""

    st.markdown(f"""
    <div class="msg-bot" style="align-items:flex-start;">
      <div class="avatar avatar-bot">🌿</div>
      <div style="flex:1;min-width:0;">
        <div class="diag-card">

          <div class="diag-title">{disease}</div>
          <div class="diag-meta">
            {sev_html}
            <span class="badge badge-green">{dtype}</span>
            <span class="badge badge-blue">🌱 {plant}</span>
          </div>

          <div class="conf-wrap">
            <div class="conf-label">Diagnosis Confidence</div>
            <div class="conf-bar-bg">
              <div class="conf-bar-fill" style="width:{conf}%;background:{conf_c};"></div>
            </div>
            <div style="font-size:0.78rem;color:{conf_c};margin-top:4px;font-weight:600;">{conf}%</div>
          </div>

          <div class="sec-head">⚡ Do This First</div>
          {action_html}

          <div class="sec-head">🌿 Organic Treatment</div>
          {org_treat_html if org_treat_html else '<div style="color:var(--text-dim);font-size:0.85rem;">No organic treatments listed.</div>'}

          <div class="sec-head">⚗️ Chemical Treatment</div>
          {chem_treat_html if chem_treat_html else '<div style="color:var(--text-dim);font-size:0.85rem;">No chemical treatments listed.</div>'}

          <div class="sec-head">💰 Cost & ROI (per 100 plants)</div>
          <div class="roi-box">
            <div class="roi-card">
              <div class="roi-label">Organic Cost</div>
              <div class="roi-val" style="color:{roi_org_color};">₹{org_total}</div>
              <div style="font-size:0.75rem;color:var(--text-dim);">ROI: {org_roi}%</div>
            </div>
            <div class="roi-card">
              <div class="roi-label">Chemical Cost</div>
              <div class="roi-val" style="color:{roi_chem_color};">₹{chem_total}</div>
              <div style="font-size:0.75rem;color:var(--text-dim);">ROI: {chem_roi}%</div>
            </div>
          </div>
          <div style="font-size:0.78rem;color:var(--text-dim);margin-top:2px;">Based on {infected} infected / {total} total plants · {loss_pct}% estimated yield loss</div>

          {prev_html and f'<div class="sec-head">🛡️ Prevention</div>{prev_html}' or ''}
          {rot_html}
          {notes_html}

        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    # PDF Download button
    lc = d.get("lang_code", "en")
    pdf_label = {"en": "📄 Download PDF Report", "hi": "📄 PDF रिपोर्ट डाउनलोड करें", "pa": "📄 PDF ਰਿਪੋਰਟ ਡਾਊਨਲੋਡ ਕਰੋ"}.get(lc, "📄 Download PDF Report")
    if st.button(pdf_label, key=f"pdf_btn_{d.get('timestamp','0').replace(':','_')}", use_container_width=False):
        with st.spinner("Generating PDF..." if lc == "en" else "PDF बन रहा है..." if lc == "hi" else "PDF ਬਣ ਰਿਹਾ ਹੈ..."):
            pdf_bytes = generate_pdf_report(d, lc)
            fname = f"KisanAI_{plant}_{disease.replace(' ','_')[:20]}.pdf"
            st.download_button(
                label="⬇️ Click to Save PDF" if lc == "en" else "⬇️ PDF सेव करें" if lc == "hi" else "⬇️ PDF ਸੇਵ ਕਰੋ",
                data=pdf_bytes,
                file_name=fname,
                mime="application/pdf",
                key=f"pdf_dl_{d.get('timestamp','0').replace(':','_')}",
            )


# ─────────────────────────────────────────────────────────────
# RENDER CHAT
# ─────────────────────────────────────────────────────────────
render_messages()

st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# INPUT AREA
# ─────────────────────────────────────────────────────────────
st.markdown('<div class="input-bar-wrap">', unsafe_allow_html=True)

with st.expander("📸 Upload leaf photo for diagnosis", expanded=False):
    plant_col, region_col = st.columns(2)
    with plant_col:
        plant_options = ["🤖 Auto-detect from image"] + sorted(list(PLANT_COMMON_DISEASES.keys())) + ["✏️ Type manually..."]
        sel_plant = st.selectbox("Your plant", plant_options, label_visibility="collapsed", key="plant_sel")
        if sel_plant == "✏️ Type manually...":
            custom_plant = st.text_input("Plant name", placeholder="e.g. Papaya, Jackfruit, Sorghum...", label_visibility="collapsed", key="custom_plant")
            chosen_plant = custom_plant.strip() if custom_plant and custom_plant.strip() else None
        elif sel_plant == "🤖 Auto-detect from image":
            chosen_plant = "AUTO"
        else:
            chosen_plant = sel_plant

    with region_col:
        region_options = ["🤖 Auto-detect from image"] + REGIONS
        sel_region = st.selectbox("Region", region_options, label_visibility="collapsed", key="region_sel")
        region = sel_region if sel_region != "🤖 Auto-detect from image" else "AUTO"

        soil_options = ["🤖 Auto-detect from image"] + SOIL_TYPES + ["✏️ Type manually..."]
        sel_soil = st.selectbox("Soil type", soil_options, label_visibility="collapsed", key="soil_sel")
        if sel_soil == "✏️ Type manually...":
            custom_soil = st.text_input("Soil type", placeholder="e.g. Sandy loam, Peat soil...", label_visibility="collapsed", key="custom_soil")
            soil = custom_soil.strip() if custom_soil and custom_soil.strip() else "Unknown"
        elif sel_soil == "🤖 Auto-detect from image":
            soil = "AUTO"
        else:
            soil = sel_soil

    n_col, t_col = st.columns(2)
    with n_col:
        infected_n = st.number_input("Sick plants", min_value=1, value=10, step=1, key="infected_n")
    with t_col:
        total_n = st.number_input("Total plants", min_value=1, value=100, step=10, key="total_n")

    uploaded = st.file_uploader("Drop leaf photo here", type=["jpg","jpeg","png"], accept_multiple_files=True, label_visibility="collapsed", key="uploader")

    if uploaded:
        imgs = [Image.open(f) for f in uploaded[:3]]
        # Show small thumbnails side by side
        thumb_cols = st.columns(min(len(imgs) * 2, 6))
        for i, img in enumerate(imgs):
            with thumb_cols[i * 2]:
                thumb = img.copy()
                thumb.thumbnail((120, 120), Image.Resampling.LANCZOS)
                st.image(thumb, use_container_width=False, width=100)
            with thumb_cols[i * 2 + 1]:
                st.markdown(f"<div style='font-size:0.75rem;color:var(--text-dim);padding-top:8px;'>📷 Photo {i+1}<br>{img.width}×{img.height}</div>", unsafe_allow_html=True)

    can_diagnose = uploaded and (chosen_plant is not None)
    if uploaded and chosen_plant is None:
        st.warning("Please select or type your plant name, or choose Auto-detect.")

    if can_diagnose and st.button("🔍 Diagnose Now", use_container_width=True, key="diag_btn"):
        with st.spinner("Analysing your plant..."):
            try:
                need_autodetect = chosen_plant == "AUTO" or region == "AUTO" or soil == "AUTO"
                actual_plant = chosen_plant
                actual_region = region
                actual_soil = soil

                if need_autodetect:
                    detect_prompt = f"""{lang_instruction}
Look at this plant image carefully and identify:
1. The exact crop/plant species visible
2. The region of India this appears to be from (based on visual cues like soil color, environment, foliage)
3. The soil type visible

CRITICAL: Respond ONLY with valid JSON, no markdown, no explanation.

{{
  "detected_plant": "Exact plant name e.g. Wheat, Tomato, Rice",
  "detected_region": "One of: North India, South India, East India, West India, Central India, Northeast India, or best guess",
  "detected_soil": "Soil type e.g. Alluvial Soil, Black Soil, or best guess",
  "detection_confidence": 80
}}"""
                    detect_model = genai.GenerativeModel("gemini-2.5-flash")
                    detect_imgs = [enhance_image(img.copy()) for img in imgs]
                    detect_resp = detect_model.generate_content([detect_prompt] + detect_imgs)
                    detect_result = extract_json(detect_resp.text)
                    if detect_result:
                        if chosen_plant == "AUTO":
                            actual_plant = detect_result.get("detected_plant", "Unknown Plant")
                        if region == "AUTO":
                            actual_region = detect_result.get("detected_region", "North India")
                        if soil == "AUTO":
                            actual_soil = detect_result.get("detected_soil", "Alluvial Soil")
                        st.info(f"🤖 Auto-detected: **{actual_plant}** · {actual_region} · {actual_soil}")

                common = PLANT_COMMON_DISEASES.get(actual_plant, "various plant diseases")
                prompt = f"""{lang_instruction}

You are an expert plant pathologist specialising in {actual_plant} diseases.
Common diseases for this plant: {common}
Region: {actual_region}, Soil: {actual_soil}

CRITICAL: Respond ONLY with valid JSON, no markdown.

{{
  "disease_name": "Specific disease name or Healthy",
  "disease_type": "fungal/bacterial/viral/pest/nutrient/healthy",
  "severity": "healthy/mild/moderate/severe",
  "confidence": 85,
  "symptoms": ["symptom 1","symptom 2","symptom 3"],
  "probable_causes": ["cause 1","cause 2"],
  "immediate_action": ["step 1","step 2","step 3"],
  "organic_treatments": ["Neem Oil Spray","Bordeaux Mixture"],
  "chemical_treatments": ["Mancozeb (Indofil)","Carbendazim (Bavistin)"],
  "prevention_long_term": ["prevention 1","prevention 2","prevention 3"],
  "plant_specific_notes": "Key notes for this specific plant",
  "should_treat": true,
  "treat_reason": "One sentence plain-language reason"
}}"""
                model = genai.GenerativeModel("gemini-2.5-flash")
                enhanced = [enhance_image(img.copy()) for img in imgs]
                response = model.generate_content([prompt] + enhanced)
                result = extract_json(response.text)

                if result:
                    diag_data = {
                        "plant_type": actual_plant,
                        "disease_name": result.get("disease_name", "Unknown"),
                        "severity": result.get("severity", "unknown"),
                        "confidence": result.get("confidence", 0),
                        "infected_count": int(infected_n),
                        "total_plants": int(total_n),
                        "region": actual_region,
                        "soil": actual_soil,
                        "result": result,
                        "timestamp": datetime.now().isoformat(),
                        "lang_code": lang_code,
                    }
                    st.session_state.last_diagnosis = diag_data
                    st.session_state.messages.append({
                        "role": "user",
                        "content": f"📸 Uploaded {len(imgs)} photo(s) of {actual_plant} from {actual_region}"
                    })
                    should_treat = result.get("should_treat", True)
                    treat_reason = result.get("treat_reason", "")
                    verdict = f"{'✅ Yes, treat immediately' if should_treat else '👍 No treatment needed right now'}. {treat_reason}"
                    st.session_state.messages.append({
                        "role": "bot",
                        "type": "diagnosis",
                        "data": diag_data,
                        "content": verdict,
                    })
                    st.rerun()
                else:
                    st.error("Could not read AI response. Try a clearer photo.")
            except Exception as e:
                st.error(f"Analysis failed: {e}")

# Chat input
chat_input_col, send_col = st.columns([5, 1])
with chat_input_col:
    user_text = st.text_input(
        "message",
        placeholder="Ask about your crop, disease, treatment, cost..." if lang_code == "en"
            else "अपनी फसल के बारे में पूछें..." if lang_code == "hi"
            else "ਆਪਣੀ ਫਸਲ ਬਾਰੇ ਪੁੱਛੋ..." if lang_code == "pa"
            else "Ask anything...",
        label_visibility="collapsed",
        key="chat_input"
    )
with send_col:
    send = st.button("Send ➤", use_container_width=True, key="send_btn")

st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# CHAT RESPONSE
# ─────────────────────────────────────────────────────────────
if send and user_text.strip():
    question = user_text.strip()
    st.session_state.messages.append({"role": "user", "content": question})

    diag = st.session_state.last_diagnosis
    context = ""
    if diag:
        context = f"""
Current diagnosis context:
- Plant: {diag.get('plant_type')}
- Disease: {diag.get('disease_name')}
- Severity: {diag.get('severity')}
- Region: {diag.get('region','Unknown')}
- Confidence: {diag.get('confidence')}%
"""

    system = f"""{lang_instruction}

You are Kisan AI — a friendly, expert agricultural advisor for Indian farmers.
Speak simply. Avoid complex jargon. Give practical, actionable advice.
Use short paragraphs. Use ₹ for currency.
{context}
Farmer's question: {question}

If they ask about crop rotation, cost, ROI, or treatment — answer in their language clearly.
If they ask something unrelated to farming, politely redirect to farming topics."""

    with st.spinner("..."):
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(system)
            answer = response.text.strip()
            st.session_state.messages.append({"role": "bot", "content": answer})
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
