import streamlit as st
try:
    import google.generativeai as genai
except ModuleNotFoundError:
    st.error("Missing: google-generativeai. Add to requirements.txt.")
    st.stop()

from PIL import Image, ImageEnhance
import os, json, re
from datetime import datetime, timedelta
import random

st.set_page_config(
    page_title="KisanAI",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════
# LANGUAGES
# ══════════════════════════════════════════════════════════════
LANGUAGES = {
    "English": "en", "हिंदी (Hindi)": "hi", "ਪੰਜਾਬੀ (Punjabi)": "pa",
    "मराठी (Marathi)": "mr", "తెలుగు (Telugu)": "te", "தமிழ் (Tamil)": "ta",
    "ಕನ್ನಡ (Kannada)": "kn", "বাংলা (Bengali)": "bn", "ગુજરાતી (Gujarati)": "gu",
    "ଓଡ଼ିଆ (Odia)": "or", "മലയാളം (Malayalam)": "ml", "অসমীয়া (Assamese)": "as",
    "اردو (Urdu)": "ur",
}
LANG_INSTRUCTIONS = {
    "en": "Respond in clear, simple English. Speak like a helpful village agricultural expert.",
    "hi": "हिंदी में जवाब दें। सरल भाषा में, जैसे गाँव का कृषि विशेषज्ञ बोलता है।",
    "pa": "ਪੰਜਾਬੀ ਵਿੱਚ ਜਵਾਬ ਦਿਓ। ਸਰਲ ਭਾਸ਼ਾ ਵਿੱਚ।",
    "mr": "मराठीत उत्तर द्या.", "te": "తెలుగులో సమాధానం ఇవ్వండి.",
    "ta": "தமிழில் பதில் சொல்லுங்கள்.", "kn": "ಕನ್ನಡದಲ್ಲಿ ಉತ್ತರ ನೀಡಿ.",
    "bn": "বাংলায় উত্তর দিন।", "gu": "ગુજરાતીમાં જવાબ આપો.",
    "or": "ଓଡ଼ିଆରେ ଉତ୍ତର ଦିଅ।", "ml": "മലയാളത്തിൽ ഉത്തരം നൽകുക.",
    "as": "অসমীয়াত উত্তৰ দিয়ক।", "ur": "اردو میں جواب دیں۔",
}

# ══════════════════════════════════════════════════════════════
# DATABASES
# ══════════════════════════════════════════════════════════════
TREATMENT_COSTS = {
    "organic": {
        "Cow Urine Extract": {"cost": 80, "quantity": "2-3 liters/100 plants", "dilution": "1:5 with water"},
        "Neem Oil Spray": {"cost": 250, "quantity": "500ml/100 plants", "dilution": "3% solution"},
        "Bordeaux Mixture": {"cost": 250, "quantity": "300g/100 plants", "dilution": "1% solution"},
        "Copper Fungicide (Organic)": {"cost": 280, "quantity": "250g/100 plants", "dilution": "0.5% solution"},
        "Trichoderma": {"cost": 400, "quantity": "500g/100 plants", "dilution": "0.5% solution"},
        "Bacillus subtilis": {"cost": 350, "quantity": "100g/100 plants", "dilution": "0.1% solution"},
        "Azadirachtin": {"cost": 380, "quantity": "200ml/100 plants", "dilution": "0.3% solution"},
        "Seaweed Extract": {"cost": 260, "quantity": "250ml/100 plants", "dilution": "0.3% solution"},
        "Karanja Oil": {"cost": 220, "quantity": "400ml/100 plants", "dilution": "2.5% solution"},
        "Sulfur Dust": {"cost": 120, "quantity": "500g/100 plants", "dilution": "Direct dust"},
        "Potassium Bicarbonate": {"cost": 300, "quantity": "150g/100 plants", "dilution": "1% solution"},
        "Lime Sulfur": {"cost": 180, "quantity": "1 liter/100 plants", "dilution": "1:10 with water"},
    },
    "chemical": {
        "Carbendazim (Bavistin)": {"cost": 120, "quantity": "100g/100 plants", "dilution": "0.1% solution"},
        "Mancozeb (Indofil)": {"cost": 120, "quantity": "150g/100 plants", "dilution": "0.2% solution"},
        "Copper Oxychloride": {"cost": 150, "quantity": "200g/100 plants", "dilution": "0.25% solution"},
        "Tebuconazole (Folicur)": {"cost": 320, "quantity": "120ml/100 plants", "dilution": "0.05% solution"},
        "Propiconazole (Tilt)": {"cost": 190, "quantity": "100ml/100 plants", "dilution": "0.1% solution"},
        "Azoxystrobin (Amistar)": {"cost": 650, "quantity": "80ml/100 plants", "dilution": "0.02% solution"},
        "Imidacloprid (Confidor)": {"cost": 350, "quantity": "80ml/100 plants", "dilution": "0.008% solution"},
        "Metalaxyl + Mancozeb (Ridomil Gold)": {"cost": 190, "quantity": "100g/100 plants", "dilution": "0.25% solution"},
        "Chlorothalonil": {"cost": 220, "quantity": "120g/100 plants", "dilution": "0.15% solution"},
        "Hexaconazole (Contaf Plus)": {"cost": 350, "quantity": "100ml/100 plants", "dilution": "0.04% solution"},
    },
}

CROP_ROTATION_DATA = {
    "Tomato": {"rotations": ["Beans", "Cabbage", "Cucumber"], "info": {"Tomato": "High-value solanaceae. Susceptible to blight & wilt. Needs 3+ year rotation.", "Beans": "Nitrogen-fixing legume. Breaks disease cycle.", "Cabbage": "Brassica family. Controls tomato diseases.", "Cucumber": "No common diseases with tomato. Completes rotation."}},
    "Rose": {"rotations": ["Marigold", "Chrysanthemum", "Herbs"], "info": {"Rose": "Susceptible to black spot, powdery mildew, rust.", "Marigold": "Natural pest repellent. Attracts beneficial insects.", "Chrysanthemum": "Different pest profile. Breaks rose pathogen cycle.", "Herbs": "Basil, rosemary improve soil health."}},
    "Grape": {"rotations": ["Legume Cover Crops", "Cereals", "Vegetables"], "info": {"Grape": "Perennial vine. Powdery mildew, phylloxera concerns.", "Legume Cover Crops": "Nitrogen replenishment.", "Cereals": "Wheat/maize. Nematode cycle break.", "Vegetables": "Re-establishes soil microbiology."}},
    "Cucumber": {"rotations": ["Maize", "Okra", "Legumes"], "info": {"Cucumber": "Cucurbitaceae. 2-3 year rotation.", "Maize": "Different root system.", "Okra": "No overlapping pests.", "Legumes": "Nitrogen restoration."}},
    "Corn": {"rotations": ["Soybean", "Pulses", "Oilseeds"], "info": {"Corn": "Heavy nitrogen feeder. 3+ year rotation critical.", "Soybean": "Nitrogen-fixing.", "Pulses": "High market value.", "Oilseeds": "Income diversification."}},
    "Potato": {"rotations": ["Peas", "Mustard", "Cereals"], "info": {"Potato": "Solanaceae. Late blight, nematodes. 4-year rotation.", "Peas": "Nitrogen-fixing.", "Mustard": "Biofumigation. Natural nematode control.", "Cereals": "Completes disease-break cycle."}},
    "Wheat": {"rotations": ["Soybean", "Pulses", "Mustard"], "info": {"Wheat": "Cereal crop. Rust and smut susceptible.", "Soybean": "Nitrogen fixer.", "Pulses": "Breaks wheat pathogen cycle.", "Mustard": "Biofumigation benefits."}},
    "Rice": {"rotations": ["Pulses", "Vegetables", "Wheat"], "info": {"Rice": "Water-intensive cereal.", "Pulses": "Nitrogen fixation. Soil improvement.", "Vegetables": "Income diversification.", "Wheat": "Dry-season crop."}},
}

REGIONS = ["North India", "South India", "East India", "West India", "Central India", "Northeast India"]
SOIL_TYPES = ["Black Soil (Regur)", "Red Soil", "Laterite Soil", "Alluvial Soil", "Sandy Soil", "Clay Soil", "Loamy Soil"]

PLANT_COMMON_DISEASES = {
    "Tomato": "Early blight, Late blight, Septoria leaf spot, Fusarium wilt, Bacterial wilt, Spider mites, Powdery mildew",
    "Rose": "Black spot, Powdery mildew, Rose rosette virus, Rust, Botrytis",
    "Apple": "Apple scab, Fire blight, Powdery mildew, Cedar apple rust",
    "Lettuce": "Lettuce mosaic virus, Downy mildew, Bottom rot, Tip burn",
    "Grape": "Powdery mildew, Downy mildew, Black rot, Grape phylloxera",
    "Pepper": "Anthracnose, Bacterial wilt, Phytophthora blight, Cercospora leaf spot",
    "Cucumber": "Powdery mildew, Downy mildew, Angular leaf spot, Anthracnose",
    "Strawberry": "Leaf scorch, Powdery mildew, Red stele root rot",
    "Corn": "Leaf blotch, Rust, Stewart's wilt, Fusarium ear rot",
    "Potato": "Late blight, Early blight, Verticillium wilt, Potato scab",
    "Wheat": "Rust, Powdery mildew, Loose smut, Karnal bunt, Foot rot",
    "Rice": "Blast, Brown spot, Sheath blight, Bacterial leaf blight",
    "Cotton": "Boll rot, Leaf curl virus, Bacterial blight, Fusarium wilt",
    "Sugarcane": "Red rot, Smut, Ratoon stunting, Grassy shoot",
    "Onion": "Purple blotch, Downy mildew, Stemphylium blight, Basal rot",
    "Mango": "Anthracnose, Powdery mildew, Bacterial canker, Stem end rot",
    "Banana": "Panama wilt, Sigatoka, Bunchy top virus, Anthracnose",
    "Chilli": "Anthracnose, Bacterial wilt, Leaf curl virus, Powdery mildew",
    "Brinjal": "Little leaf disease, Bacterial wilt, Fruit borer, Phomopsis blight",
}

# ══════════════════════════════════════════════════════════════
# CSS — Matches Uizard dark sidebar + content layout
# ══════════════════════════════════════════════════════════════
st.html("""
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
:root {
  --bg:     #111714;
  --bg2:    #161d17;
  --bg3:    #1c2520;
  --card:   #1a211b;
  --card2:  #1f2820;
  --border: rgba(74,222,128,0.12);
  --b2:     rgba(74,222,128,0.22);
  --green:  #4ade80;
  --green2: #22c55e;
  --green3: #16a34a;
  --gdim:   rgba(74,222,128,0.1);
  --gold:   #fbbf24;
  --red:    #f87171;
  --blue:   #60a5fa;
  --purple: #a78bfa;
  --text:   #d4e8d6;
  --t2:     #6b8f70;
  --t3:     #374a39;
  --r:      10px;
  --rlg:    14px;
}

*, *::before, *::after { box-sizing: border-box; }

html, body, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="block-container"],
.main { background: var(--bg) !important; font-family: 'Inter', sans-serif !important; color: var(--text) !important; }

#MainMenu, footer, header,
[data-testid="stDecoration"],
[data-testid="collapsedControl"],
.stDeployButton { display: none !important; }

[data-testid="block-container"] { max-width: 100% !important; padding: 0 28px 60px !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background: var(--bg2) !important;
  border-right: 1px solid var(--border) !important;
  min-width: 220px !important; max-width: 220px !important;
}
[data-testid="stSidebar"] * { color: var(--t2) !important; font-family: 'Inter', sans-serif !important; }
[data-testid="stSidebar"] .stRadio label { font-size: 0.85rem !important; }
[data-testid="stSidebarNav"] { display: none !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(74,222,128,0.25); border-radius: 4px; }

/* ── Top bar inside content ── */
.topbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 0 16px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 20px;
}
.page-title {
  font-family: 'Outfit', sans-serif;
  font-size: 1.35rem; font-weight: 700; color: var(--text);
  display: flex; align-items: center; gap: 10px;
}
.page-title-icon {
  width: 28px; height: 28px; background: var(--gdim);
  border: 1px solid var(--b2); border-radius: 8px;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 0.9rem;
}

/* ── Summary cards (dashboard) ── */
.sum-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 12px; margin-bottom: 20px; }
.sum-card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: var(--rlg); padding: 18px 16px;
  transition: border-color 0.18s;
}
.sum-card:hover { border-color: var(--b2); }
.sum-icon {
  width: 36px; height: 36px; border-radius: 9px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1rem; margin-bottom: 12px;
}
.sum-label { font-size: 0.72rem; color: var(--t2); letter-spacing: 0.06em; margin-bottom: 4px; }
.sum-val { font-family: 'Outfit', sans-serif; font-size: 1.5rem; font-weight: 700; color: var(--text); }
.sum-sub { font-size: 0.72rem; color: var(--t3); margin-top: 4px; }

/* ── Section header ── */
.sec-hd {
  font-family: 'Outfit', sans-serif;
  font-size: 1rem; font-weight: 600; color: var(--text);
  margin: 20px 0 12px; display: flex; align-items: center; justify-content: space-between;
}
.sec-hd-sub { font-size: 0.78rem; color: var(--t2); font-weight: 400; }

/* ── Table ── */
.diag-table { width: 100%; border-collapse: collapse; }
.diag-table th {
  font-size: 0.7rem; color: var(--t2); text-transform: uppercase;
  letter-spacing: 0.1em; padding: 10px 14px; text-align: left;
  border-bottom: 1px solid var(--border); font-weight: 600;
}
.diag-table td {
  padding: 11px 14px; font-size: 0.84rem; color: var(--text);
  border-bottom: 1px solid rgba(74,222,128,0.06);
  vertical-align: middle;
}
.diag-table tr:hover td { background: var(--gdim); }
.crop-dot {
  display: inline-flex; align-items: center; gap: 8px;
}
.dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.dot-g { background: var(--green2); }
.dot-y { background: var(--gold); }
.dot-r { background: var(--red); }
.conf-chip {
  display: inline-block; font-size: 0.75rem; font-weight: 600;
  padding: 2px 10px; border-radius: 99px;
}
.conf-hi { background: rgba(34,197,94,0.12); color: #4ade80; }
.conf-mid { background: rgba(251,191,36,0.12); color: #fbbf24; }
.conf-lo { background: rgba(248,113,113,0.12); color: #f87171; }
.action-btn {
  background: transparent; border: 1px solid var(--border);
  color: var(--t2); font-size: 0.72rem; padding: 4px 10px;
  border-radius: 6px; cursor: pointer;
}

/* ── Disease result card ── */
.diag-hero {
  position: relative; overflow: hidden;
  background: linear-gradient(135deg, #0d2214 0%, #122b18 60%, #0f2010 100%);
  border: 1px solid rgba(74,222,128,0.3); border-radius: var(--rlg);
  padding: 24px; margin-bottom: 16px;
}
.diag-hero::after {
  content: ''; position: absolute; top: -40px; right: -40px;
  width: 180px; height: 180px; border-radius: 50%;
  background: radial-gradient(circle, rgba(74,222,128,0.15) 0%, transparent 70%);
}
.diag-title {
  font-family: 'Outfit', sans-serif;
  font-size: 1.7rem; font-weight: 800; color: #fff;
  margin-bottom: 8px; position: relative; z-index: 1;
}
.diag-conf-row { display: flex; align-items: center; gap: 10px; margin-top: 12px; position: relative; z-index: 1; }
.conf-bar-bg { flex: 1; background: rgba(255,255,255,0.07); border-radius: 99px; height: 5px; }
.conf-bar-fill { height: 100%; border-radius: 99px; }

/* ── Badges ── */
.badge-row { display: flex; gap: 7px; flex-wrap: wrap; margin: 10px 0; position: relative; z-index: 1; }
.badge {
  display: inline-flex; align-items: center;
  padding: 3px 10px; border-radius: 99px;
  font-size: 0.68rem; font-weight: 600; letter-spacing: 0.05em;
}
.b-green  { background: rgba(74,222,128,0.12); color: #4ade80; border: 1px solid rgba(74,222,128,0.2); }
.b-amber  { background: rgba(251,191,36,0.12);  color: #fbbf24; border: 1px solid rgba(251,191,36,0.2); }
.b-red    { background: rgba(248,113,113,0.12); color: #f87171; border: 1px solid rgba(248,113,113,0.2); }
.b-blue   { background: rgba(96,165,250,0.12);  color: #60a5fa; border: 1px solid rgba(96,165,250,0.2); }
.b-purple { background: rgba(167,139,250,0.12); color: #a78bfa; border: 1px solid rgba(167,139,250,0.2); }
.b-gray   { background: rgba(255,255,255,0.06); color: var(--t2); border: 1px solid var(--border); }

/* ── Stat cards in row ── */
.stat-row { display: grid; grid-template-columns: repeat(4,1fr); gap: 10px; margin: 14px 0; }
.stat-c {
  background: var(--card); border: 1px solid var(--border);
  border-top: 2px solid var(--green3); border-radius: var(--r);
  padding: 14px 12px; text-align: center;
}
.stat-v { font-family: 'Outfit', sans-serif; font-size: 1.4rem; font-weight: 700; color: var(--green); }
.stat-l { font-size: 0.62rem; color: var(--t2); text-transform: uppercase; letter-spacing: 0.1em; margin-top: 3px; }

/* ── Treatment row ── */
.treat-r {
  display: flex; align-items: center; justify-content: space-between;
  background: var(--card2); border: 1px solid var(--border);
  border-radius: var(--r); padding: 10px 14px; margin: 5px 0; gap: 10px;
}
.treat-r:hover { border-color: var(--b2); }
.treat-n { font-size: 0.88rem; font-weight: 600; color: var(--text); }
.treat-d { font-size: 0.72rem; color: var(--t2); margin-top: 2px; }
.treat-p {
  font-size: 0.76rem; font-weight: 700; color: var(--green);
  background: rgba(74,222,128,0.09); border: 1px solid rgba(74,222,128,0.18);
  border-radius: 99px; padding: 3px 10px; white-space: nowrap;
}

/* ── Action items ── */
.act-item {
  display: flex; gap: 10px; align-items: flex-start;
  background: rgba(74,222,128,0.04); border: 1px solid rgba(74,222,128,0.1);
  border-radius: var(--r); padding: 9px 12px; margin: 5px 0;
  font-size: 0.84rem; color: var(--text); line-height: 1.5;
}
.act-n {
  flex-shrink: 0; width: 20px; height: 20px; border-radius: 6px;
  background: var(--green3); color: #fff;
  font-size: 0.65rem; font-weight: 800;
  display: flex; align-items: center; justify-content: center;
}

/* ── Verdict ── */
.verdict {
  background: rgba(74,222,128,0.06); border: 1px solid rgba(74,222,128,0.2);
  border-left: 3px solid var(--green3); border-radius: var(--r);
  padding: 10px 14px; font-size: 0.84rem; color: var(--green);
  margin: 10px 0;
}

/* ── Info card ── */
.info-c {
  background: var(--card); border: 1px solid var(--border);
  border-radius: var(--rlg); padding: 16px 18px; margin: 8px 0;
}
.info-title {
  font-family: 'Outfit', sans-serif;
  font-size: 0.78rem; font-weight: 600; color: var(--green2);
  text-transform: uppercase; letter-spacing: 0.1em;
  margin-bottom: 10px; display: flex; align-items: center; gap: 6px;
}
.info-title::after { content: ''; flex: 1; height: 1px; background: var(--border); }

/* ── Chat ── */
.chat-wrap { display: flex; flex-direction: column; gap: 10px; }
.msg-bot, .msg-usr { display: flex; align-items: flex-start; gap: 9px; }
.msg-usr { flex-direction: row-reverse; }
.av { width: 30px; height: 30px; border-radius: 8px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; font-size: 0.85rem; font-weight: 700; }
.av-b { background: var(--green3); color: #fff; }
.av-u { background: var(--bg3); border: 1px solid var(--b2); color: var(--text); }
.bub { max-width: 78%; padding: 10px 14px; border-radius: var(--r); font-size: 0.86rem; line-height: 1.6; }
.bub-b { background: var(--card); border: 1px solid var(--border); color: var(--text); border-top-left-radius: 3px; }
.bub-u { background: rgba(74,222,128,0.1); border: 1px solid rgba(74,222,128,0.2); color: var(--text); border-top-right-radius: 3px; }

/* ── Rotation card ── */
.rot-c {
  background: var(--card); border: 1px solid var(--border);
  border-radius: var(--rlg); padding: 18px 16px; text-align: center;
  transition: all 0.2s;
}
.rot-c:hover { border-color: var(--b2); }
.rot-yr { font-size: 0.62rem; font-weight: 700; color: var(--gold); text-transform: uppercase; letter-spacing: 0.18em; margin-bottom: 8px; }
.rot-crop { font-family: 'Outfit', sans-serif; font-size: 1.1rem; font-weight: 700; color: var(--text); margin: 6px 0; }
.rot-desc { font-size: 0.78rem; color: var(--t2); line-height: 1.55; margin-top: 6px; }

/* ── Streamlit overrides ── */
.stButton > button {
  background: var(--green3) !important; color: #fff !important;
  border: none !important; border-radius: var(--r) !important;
  font-weight: 600 !important; font-size: 0.86rem !important;
  padding: 9px 22px !important; font-family: 'Inter', sans-serif !important;
  transition: all 0.18s ease !important;
}
.stButton > button:hover { background: #15803d !important; transform: translateY(-1px) !important; }
.stDownloadButton > button {
  background: transparent !important; color: var(--green) !important;
  border: 1px solid rgba(74,222,128,0.3) !important; border-radius: var(--r) !important;
}
input, textarea, [data-baseweb="input"] input {
  background: var(--card) !important; border: 1px solid var(--border) !important;
  color: var(--text) !important; border-radius: var(--r) !important;
  font-family: 'Inter', sans-serif !important;
}
input:focus, textarea:focus { border-color: var(--green2) !important; }
.stSelectbox > div > div, [data-baseweb="select"] {
  background: var(--card) !important; border: 1px solid var(--border) !important;
  color: var(--text) !important; border-radius: var(--r) !important;
}
[data-baseweb="popover"] { background: #1a211b !important; border: 1px solid var(--b2) !important; }
[data-baseweb="option"]:hover { background: var(--gdim) !important; }
[data-testid="stFileUploader"] { background: var(--card) !important; border: 1.5px dashed var(--b2) !important; border-radius: var(--rlg) !important; }
[data-testid="stExpander"] { background: var(--card) !important; border: 1px solid var(--border) !important; border-radius: var(--r) !important; }
.streamlit-expanderHeader { color: var(--t2) !important; font-size: 0.88rem !important; }
[data-testid="metric-container"] { background: var(--card) !important; border: 1px solid var(--border) !important; border-radius: var(--r) !important; }
[data-testid="stTabs"] [data-baseweb="tab-list"] { background: var(--card) !important; border: 1px solid var(--border) !important; border-radius: var(--r) !important; padding: 3px !important; }
[data-testid="stTabs"] [data-baseweb="tab"] { background: transparent !important; color: var(--t2) !important; border-radius: 8px !important; font-size: 0.84rem !important; }
[data-testid="stTabs"] [aria-selected="true"] { background: var(--green3) !important; color: #fff !important; }
[data-testid="stTabs"] [data-baseweb="tab-border"] { display: none !important; }
.stAlert { border-radius: var(--r) !important; background: var(--card) !important; border: 1px solid var(--border) !important; }
[data-testid="stRadio"] label { color: var(--t2) !important; font-size: 0.85rem !important; }
[data-testid="stCheckbox"] label { color: var(--t2) !important; font-size: 0.85rem !important; }
p, label, div, span { color: var(--text); font-family: 'Inter', sans-serif; }
h1,h2,h3,h4 { font-family: 'Outfit', sans-serif !important; color: var(--text) !important; }
</style>
""")

# ══════════════════════════════════════════════════════════════
# GEMINI CONFIG
# ══════════════════════════════════════════════════════════════
_api_key = os.environ.get("GEMINI_API_KEY", "").strip()
if not _api_key:
    st.error("⚠️ GEMINI_API_KEY not set. Go to Manage App → Secrets.")
    st.stop()
try:
    genai.configure(api_key=_api_key)
except Exception as e:
    st.error(f"Gemini config error: {e}")
    st.stop()

# ══════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════
_defaults = {
    "page": "dashboard", "lang": "English", "lang_code": "en",
    "last_diagnosis": None, "chat_messages": [],
    "crop_rotation_result": None, "cost_roi_result": None,
    "scan_history": [],
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Seed some demo history if empty
if not st.session_state.scan_history:
    demo = [
        {"crop": "Tomato", "disease": "Late Blight", "conf": 92, "lang": "Hindi", "date": "28/03/2026 09:20", "severity": "severe", "shared": "Private"},
        {"crop": "Wheat", "disease": "Loose Smut", "conf": 85, "lang": "Punjabi", "date": "28/03/2026 06:10", "severity": "moderate", "shared": "Extension team"},
        {"crop": "Rice", "disease": "Brown Spot", "conf": 78, "lang": "Bengali", "date": "27/03/2026 03:55", "severity": "mild", "shared": "Field team"},
        {"crop": "Potato", "disease": "Early Blight", "conf": 88, "lang": "English", "date": "26/03/2026 11:30", "severity": "moderate", "shared": "Private"},
        {"crop": "Chilli", "disease": "Anthracnose", "conf": 71, "lang": "Telugu", "date": "25/03/2026 08:15", "severity": "mild", "shared": "Private"},
    ]
    st.session_state.scan_history = demo

lang_code = st.session_state.lang_code
lang_instruction = LANG_INSTRUCTIONS.get(lang_code, LANG_INSTRUCTIONS["en"])

# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════
def enhance_image(img):
    img = ImageEnhance.Contrast(img).enhance(1.4)
    img = ImageEnhance.Brightness(img).enhance(1.1)
    img = ImageEnhance.Sharpness(img).enhance(1.4)
    return img

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

def normalize_name(raw):
    if not isinstance(raw, str): return ""
    n = raw.strip()
    if " - " in n: n = n.split(" - ", 1)[0].strip()
    if ":" in n: n = n.split(":", 1)[0].strip()
    return n

def get_treatment_info(ttype, tname):
    costs = TREATMENT_COSTS.get(ttype, {})
    tl = tname.lower()
    for k, v in costs.items():
        if k.lower() == tl: return dict(v, _m=True)
        if k.lower() in tl or tl in k.lower(): return dict(v, _m=True)
    return {"cost": 300 if ttype == "organic" else 250, "quantity": "As per package", "dilution": "Follow label", "_m": False}

def calc_loss_pct(severity, infected, total):
    bands = {"healthy": (0,2), "mild": (5,15), "moderate": (20,40), "severe": (50,70)}
    lo, hi = bands.get((severity or "moderate").lower(), (20,40))
    ratio = max(0.0, min(infected / max(total,1), 1.0))
    return int(round(min((lo+hi)/2 * ratio, 80.0)))

def sev_cls(sev):
    s = (sev or "").lower()
    if "health" in s: return "b-green"
    if "mild" in s: return "b-blue"
    if "severe" in s: return "b-red"
    return "b-amber"

def type_cls(dtype):
    d = (dtype or "").lower()
    if "fungal" in d: return "b-purple"
    if "bacterial" in d: return "b-blue"
    if "viral" in d: return "b-red"
    if "pest" in d: return "b-amber"
    return "b-green"

def conf_chip_cls(c):
    if c >= 80: return "conf-hi"
    if c >= 60: return "conf-mid"
    return "conf-lo"

def conf_color(c):
    if c >= 80: return "#4ade80"
    if c >= 60: return "#fbbf24"
    return "#f87171"

# ══════════════════════════════════════════════════════════════
# PDF GENERATION
# ══════════════════════════════════════════════════════════════
def generate_pdf_report(d, lc="en"):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import io, os, urllib.request

    FREESANS_R  = "/usr/share/fonts/truetype/freefont/FreeSans.ttf"
    FREESANS_B  = "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
    FREESERIF_R = "/usr/share/fonts/truetype/freefont/FreeSerif.ttf"
    FREESERIF_B = "/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf"
    USE_SERIF   = lc in ("ur", "bn", "ta", "ml", "as")

    fn = "Helvetica"; bf = "Helvetica-Bold"
    try:
        if USE_SERIF and os.path.exists(FREESERIF_R):
            if "FreeSerif" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("FreeSerif", FREESERIF_R))
                pdfmetrics.registerFont(TTFont("FreeSerif-Bold", FREESERIF_B if os.path.exists(FREESERIF_B) else FREESERIF_R))
            fn, bf = "FreeSerif", "FreeSerif-Bold"
        elif os.path.exists(FREESANS_R):
            if "FreeSans" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("FreeSans", FREESANS_R))
                pdfmetrics.registerFont(TTFont("FreeSans-Bold", FREESANS_B))
            fn, bf = "FreeSans", "FreeSans-Bold"
    except: pass

    if fn == "Helvetica":
        try:
            cr = "/tmp/NotoSans-Regular.ttf"; cb = "/tmp/NotoSans-Bold.ttf"
            for url, path in [
                ("https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSans/NotoSans-Regular.ttf", cr),
                ("https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSans/NotoSans-Bold.ttf", cb),
            ]:
                if not os.path.exists(path): urllib.request.urlretrieve(url, path)
            if "NotoSans" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("NotoSans", cr))
                pdfmetrics.registerFont(TTFont("NotoSans-Bold", cb))
            fn, bf = "NotoSans", "NotoSans-Bold"
        except: pass

    result = d.get("result", {}); plant = d.get("plant_type","Unknown")
    disease = result.get("disease_name","Unknown"); severity = result.get("severity","unknown").title()
    conf = result.get("confidence",0); region = d.get("region",""); soil = d.get("soil","")
    infected = d.get("infected_count",0); total = d.get("total_plants",100)
    loss_pct = calc_loss_pct(d.get("severity", severity.lower()), infected, total)

    LABELS = {
        "en": dict(title="KisanAI — Plant Disease Report", plant="Plant", disease="Disease", severity="Severity",
                   confidence="Confidence", region="Region", soil="Soil", infected="Infected", total="Total",
                   loss="Yield Loss", actions="Immediate Actions", organic="Organic Treatments",
                   chemical="Chemical Treatments", prevention="Prevention", notes="Notes",
                   treatment="Treatment", qty="Quantity", price="Price (Rs.)", generated="Generated by KisanAI"),
        "hi": dict(title="किसान AI — पौधे की बीमारी रिपोर्ट", plant="पौधा", disease="बीमारी", severity="गंभीरता",
                   confidence="विश्वास", region="क्षेत्र", soil="मिट्टी", infected="संक्रमित", total="कुल",
                   loss="उपज हानि", actions="तुरंत करें", organic="जैविक उपचार", chemical="रासायनिक उपचार",
                   prevention="रोकथाम", notes="नोट्स", treatment="उपचार", qty="मात्रा", price="कीमत (Rs.)", generated="किसान AI द्वारा"),
        "pa": dict(title="ਕਿਸਾਨ AI — ਪੌਦੇ ਦੀ ਬਿਮਾਰੀ ਰਿਪੋਰਟ", plant="ਪੌਦਾ", disease="ਬਿਮਾਰੀ", severity="ਗੰਭੀਰਤਾ",
                   confidence="ਭਰੋਸਾ", region="ਖੇਤਰ", soil="ਮਿੱਟੀ", infected="ਸੰਕਰਮਿਤ", total="ਕੁੱਲ",
                   loss="ਝਾੜ ਨੁਕਸਾਨ", actions="ਤੁਰੰਤ ਕਰੋ", organic="ਜੈਵਿਕ ਇਲਾਜ", chemical="ਰਸਾਇਣਕ ਇਲਾਜ",
                   prevention="ਰੋਕਥਾਮ", notes="ਨੋਟਸ", treatment="ਇਲਾਜ", qty="ਮਾਤਰਾ", price="ਕੀਮਤ (Rs.)", generated="ਕਿਸਾਨ AI"),
        "ur": dict(title="کسان AI — پودے کی بیماری رپورٹ", plant="پودا", disease="بیماری", severity="شدت",
                   confidence="اعتماد", region="علاقہ", soil="مٹی", infected="متاثرہ", total="کل",
                   loss="پیداوار نقصان", actions="فوری اقدامات", organic="نامیاتی علاج", chemical="کیمیائی علاج",
                   prevention="روک تھام", notes="نوٹس", treatment="علاج", qty="مقدار", price="قیمت (Rs.)", generated="کسان AI"),
    }
    L = LABELS.get(lc, LABELS["en"])
    GREEN = colors.HexColor("#1a7a32"); LT_GREEN = colors.HexColor("#e8f5e2")
    BLUE  = colors.HexColor("#1a5896"); LT_BLUE  = colors.HexColor("#e8f0f8")
    DARK  = colors.HexColor("#1a1a1a"); GRAY     = colors.HexColor("#666666")

    def P(text, size=9, bold=False, color=DARK, align="LEFT", sa=3):
        s = ParagraphStyle("p", fontName=bf if bold else fn, fontSize=size, textColor=color,
                           leading=size*1.5, spaceAfter=sa,
                           alignment={"LEFT":0,"CENTER":1,"RIGHT":2}.get(align,0), wordWrap="CJK")
        return Paragraph(str(text), s)

    def sec(t):
        return [Spacer(1, 0.2*cm), P(t, 11, bold=True, color=GREEN, sa=2),
                HRFlowable(width="100%", thickness=1, color=LT_GREEN, spaceAfter=4)]

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=1.8*cm, rightMargin=1.8*cm, topMargin=1.8*cm, bottomMargin=1.8*cm)
    W = A4[0] - 3.6*cm
    story = []
    story.append(P(L["title"], 17, bold=True, color=GREEN, align="CENTER", sa=3))
    story.append(P(datetime.now().strftime("%d %B %Y  |  %I:%M %p"), 8, color=GRAY, align="CENTER", sa=6))
    story.append(HRFlowable(width="100%", thickness=1.5, color=GREEN, spaceAfter=8))

    c1,c2,c3,c4 = W*.18, W*.32, W*.18, W*.32
    def row(k1,v1,k2="",v2=""):
        return [P(k1,bold=True,color=GREEN), P(str(v1)), P(k2,bold=True,color=GREEN) if k2 else P(""), P(str(v2)) if v2 else P("")]
    summary = [row(L["plant"],plant,L["region"],region), row(L["disease"],disease,L["soil"],soil),
               row(L["severity"],severity,L["confidence"],f"{conf}%"), row(L["infected"],f"{infected}/{total}",L["loss"],f"{loss_pct}%")]
    t = Table(summary, colWidths=[c1,c2,c3,c4])
    t.setStyle(TableStyle([("ROWBACKGROUNDS",(0,0),(-1,-1),[LT_GREEN,colors.white]),
                            ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#cccccc")),
                            ("VALIGN",(0,0),(-1,-1),"TOP"),("TOPPADDING",(0,0),(-1,-1),5),
                            ("BOTTOMPADDING",(0,0),(-1,-1),5),("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5)]))
    story.append(t)

    def ttbl(items, ttype, hc, lc_):
        rows = [[P(L["treatment"],bold=True,color=colors.white,size=9), P(L["qty"],bold=True,color=colors.white,size=9), P(L["price"],bold=True,color=colors.white,size=9)]]
        for item in items:
            if not isinstance(item,str): continue
            n = normalize_name(item); info = get_treatment_info(ttype, n)
            rows.append([P(n,9), P(info["quantity"],9), P(f"Rs.{info['cost']}",9)])
        if len(rows)==1: return
        tbl = Table(rows, colWidths=[W*.40, W*.38, W*.22])
        tbl.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),hc),
                                  ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,lc_]),
                                  ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#cccccc")),
                                  ("VALIGN",(0,0),(-1,-1),"TOP"),("TOPPADDING",(0,0),(-1,-1),5),
                                  ("BOTTOMPADDING",(0,0),(-1,-1),5),("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5)]))
        story.append(tbl)

    if result.get("immediate_action"):
        story += sec(f"⚡ {L['actions']}")
        for i,a in enumerate(result["immediate_action"],1): story.append(P(f"{i}.  {a}",9,sa=4))
    if result.get("organic_treatments"):
        story += sec(f"🌿 {L['organic']}"); ttbl(result["organic_treatments"],"organic",GREEN,LT_GREEN)
    if result.get("chemical_treatments"):
        story += sec(f"⚗️ {L['chemical']}"); ttbl(result["chemical_treatments"],"chemical",BLUE,LT_BLUE)
    if result.get("prevention_long_term"):
        story += sec(f"🛡️ {L['prevention']}")
        for p in result["prevention_long_term"][:5]: story.append(P(f"•  {p}",9,sa=4))
    if result.get("plant_specific_notes"):
        story += sec(f"📌 {L['notes']}"); story.append(P(result["plant_specific_notes"],9,color=DARK))
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=LT_GREEN))
    story.append(P(f"{L['generated']}  ·  {datetime.now().strftime('%d/%m/%Y')}", 7, color=GRAY, align="CENTER", sa=0))
    doc.build(story)
    buf.seek(0)
    return buf.read()

# ══════════════════════════════════════════════════════════════
# AI HELPERS
# ══════════════════════════════════════════════════════════════
DIAG_PROMPT = """You are an expert plant pathologist. Analyse the uploaded leaf image for {plant_type}.
Known diseases: {common_diseases}. Region: {region}. Soil: {soil}.
{lang_instruction}
CRITICAL: Respond ONLY with valid JSON, no markdown.
{{"disease_name":"","disease_type":"fungal/bacterial/viral/pest/nutrient/healthy","severity":"healthy/mild/moderate/severe",
"confidence":85,"symptoms":["s1","s2","s3"],"differential_diagnosis":["a","b"],
"probable_causes":["c1","c2"],"immediate_action":["a1","a2","a3"],
"organic_treatments":["Neem Oil Spray","Bordeaux Mixture"],
"chemical_treatments":["Mancozeb (Indofil)","Carbendazim (Bavistin)"],
"prevention_long_term":["p1","p2","p3"],
"plant_specific_notes":"notes","similar_conditions":"similar","should_treat":true,"treat_reason":"reason"}}"""

def get_kisan_response(question, diag_ctx=None):
    model = genai.GenerativeModel("gemini-2.5-flash")
    ctx = ""
    if diag_ctx:
        ctx = f"Context: Plant={diag_ctx.get('plant_type')}, Disease={diag_ctx.get('disease_name')}, Severity={diag_ctx.get('severity')}\n\n"
    prompt = (f"{lang_instruction}\nYou are KisanAI — expert agricultural advisor for Indian farmers. "
              f"Use ₹ for currency. Be concise and practical.\n{ctx}Question: {question}")
    return model.generate_content(prompt).text.strip()

def get_rotation_plan(plant_type, region, soil_type):
    if plant_type in CROP_ROTATION_DATA: return CROP_ROTATION_DATA[plant_type]
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = f"""Agricultural expert. For {plant_type} in {region} ({soil_type}), give crop rotation.
Respond ONLY with valid JSON:
{{"rotations":["Crop1","Crop2","Crop3"],"info":{{"{plant_type}":"Info","Crop1":"Why","Crop2":"Why","Crop3":"Why"}}}}"""
    try:
        r = extract_json(model.generate_content(prompt).text)
        if r and "rotations" in r: return r
    except: pass
    return {"rotations":["Legumes","Cereals","Oilseeds"],
            "info":{plant_type:"Primary crop.","Legumes":"Nitrogen-fixing.","Cereals":"Different profile.","Oilseeds":"Diversification."}}

# ══════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.html("""
    <div style="padding:18px 4px 16px;border-bottom:1px solid rgba(74,222,128,0.12);margin-bottom:16px;">
      <div style="display:flex;align-items:center;gap:9px;">
        <div style="width:30px;height:30px;border-radius:8px;background:linear-gradient(135deg,#16a34a,#4ade80);
                    display:flex;align-items:center;justify-content:center;font-size:0.9rem;">🌿</div>
        <div>
          <div style="font-family:'Outfit',sans-serif;font-size:1rem;font-weight:700;color:#d4e8d6;">KisanAI</div>
          <div style="font-size:0.65rem;color:#4ade80;letter-spacing:0.08em;text-transform:uppercase;">Plant Doctor</div>
        </div>
      </div>
    </div>""")

    st.html('<div style="font-size:0.62rem;color:#374a39;text-transform:uppercase;letter-spacing:0.12em;padding:0 4px;margin-bottom:6px;">Diagnose</div>')

    pages = {
        "🏠  Home": "dashboard",
        "📷  Upload & Diagnose": "diagnose",
        "📋  Diagnosis Results": "results",
        "🌱  Field Log & Treatment": "fieldlog",
        "🌐  Languages & Support": "languages",
    }
    for label, pid in pages.items():
        is_active = st.session_state.page == pid
        bg = "rgba(74,222,128,0.1)" if is_active else "transparent"
        color = "#4ade80" if is_active else "#6b8f70"
        st.html(f"""<div onclick="" style="background:{bg};border-radius:8px;padding:8px 10px;margin:2px 0;
                    font-size:0.84rem;color:{color};cursor:pointer;border:{'1px solid rgba(74,222,128,0.18)' if is_active else 'none'};">
                    {label}</div>""")
        if st.button(label, key=f"nav_{pid}", use_container_width=True,
                     help=f"Go to {label}"):
            st.session_state.page = pid
            st.rerun()

    st.html('<div style="height:16px;"></div>')
    st.html('<div style="font-size:0.62rem;color:#374a39;text-transform:uppercase;letter-spacing:0.12em;padding:0 4px;margin-bottom:6px;">Shared advice</div>')
    st.html('<div style="font-size:0.82rem;color:#4b6b50;padding:6px 10px;">👥 Extension team</div>')
    st.html('<div style="font-size:0.82rem;color:#4b6b50;padding:6px 10px;">📚 Training</div>')

    st.html('<div style="flex:1;"></div>')
    st.html('<div style="height:20px;"></div>')

    # Language selector in sidebar
    st.html('<div style="font-size:0.62rem;color:#374a39;text-transform:uppercase;letter-spacing:0.12em;padding:0 4px;margin-bottom:6px;">Language</div>')
    chosen_lang = st.selectbox("🌐 Language", list(LANGUAGES.keys()),
                                index=list(LANGUAGES.keys()).index(st.session_state.lang),
                                label_visibility="collapsed", key="lang_sel_sb")
    if chosen_lang != st.session_state.lang:
        st.session_state.lang = chosen_lang
        st.session_state.lang_code = LANGUAGES[chosen_lang]
        st.rerun()

    st.html('<div style="margin-top:12px;padding:8px 4px;border-top:1px solid rgba(74,222,128,0.1);">'
            '<div style="font-size:0.7rem;color:#374a39;">● Model status <span style="float:right">Last updated</span></div>'
            '</div>')

# ══════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════
if st.session_state.page == "dashboard":

    st.html("""<div class="topbar">
      <div class="page-title"><span class="page-title-icon">⊞</span> Dashboard</div>
    </div>""")

    diag = st.session_state.last_diagnosis

    # Summary cards
    total_scans = len(st.session_state.scan_history)
    last_conf = diag.get("confidence", 0) if diag else 0
    last_disease = diag.get("disease_name", "—")[:14] if diag else "—"
    last_plant = diag.get("plant_type", "—") if diag else "—"

    c1,c2,c3,c4 = st.columns(4)
    cards = [
        (c1, "📷", "rgba(74,222,128,0.1)", "Total Scans", str(total_scans), "All time"),
        (c2, "🦠", "rgba(251,191,36,0.1)", "Last Disease", last_disease, f"Conf {last_conf}%"),
        (c3, "🌱", "rgba(96,165,250,0.1)", "Last Crop", last_plant, "Most recent"),
        (c4, "📊", "rgba(167,139,250,0.1)", "Avg Confidence",
         f"{int(sum(h['conf'] for h in st.session_state.scan_history)/max(len(st.session_state.scan_history),1))}%",
         "Last 5 scans"),
    ]
    for col, icon, bg, lbl, val, sub in cards:
        with col:
            col.html(f"""<div class="sum-card">
              <div class="sum-icon" style="background:{bg};">{icon}</div>
              <div class="sum-label">{lbl}</div>
              <div class="sum-val">{val}</div>
              <div class="sum-sub">{sub}</div>
            </div>""")

    # Quick actions row
    st.html('<div class="sec-hd">KisanAI — Quick Actions</div>')
    qa1, qa2, qa3, qa4 = st.columns(4)

    with qa1:
        st.html("""<div class="info-c" style="cursor:pointer;">
          <div style="font-size:1.4rem;margin-bottom:8px;">📷</div>
          <div style="font-family:'Outfit',sans-serif;font-size:0.88rem;font-weight:600;color:#d4e8d6;margin-bottom:4px;">Upload leaf photo</div>
          <div style="font-size:0.75rem;color:#6b8f70;">Drag or capture a leaf for instant diagnosis</div>
        </div>""")
        if st.button("Upload leaf photo", key="qa_upload", use_container_width=True):
            st.session_state.page = "diagnose"; st.rerun()

    with qa2:
        st.html("""<div class="info-c">
          <div style="font-size:1.4rem;margin-bottom:8px;">⚡</div>
          <div style="font-family:'Outfit',sans-serif;font-size:0.88rem;font-weight:600;color:#d4e8d6;margin-bottom:4px;">Instant diagnosis</div>
          <div style="font-size:0.75rem;color:#6b8f70;">KisanAI uses Gemini for fast, explainable diagnosis</div>
        </div>""")
        if st.button("Start diagnosis", key="qa_diag", use_container_width=True):
            st.session_state.page = "diagnose"; st.rerun()

    with qa3:
        if diag:
            st.html(f"""<div class="info-c">
              <div style="font-size:1.4rem;margin-bottom:8px;">🌿</div>
              <div style="font-family:'Outfit',sans-serif;font-size:0.88rem;font-weight:600;color:#d4e8d6;margin-bottom:4px;">{diag.get('plant_type','—')}</div>
              <div style="font-size:0.75rem;color:#6b8f70;">{diag.get('disease_name','—')} · {diag.get('confidence',0)}% conf</div>
            </div>""")
        else:
            st.html("""<div class="info-c">
              <div style="font-size:1.4rem;margin-bottom:8px;">🌾</div>
              <div style="font-family:'Outfit',sans-serif;font-size:0.88rem;font-weight:600;color:#d4e8d6;margin-bottom:4px;">No scan yet</div>
              <div style="font-size:0.75rem;color:#6b8f70;">Upload a photo to get started</div>
            </div>""")

    with qa4:
        if diag:
            lc_d = diag.get("lang_code","en")
            PDF_L = {"en":"Download PDF","hi":"PDF डाउनलोड","pa":"PDF ਡਾਊਨਲੋਡ","ur":"PDF ڈاؤنلوڈ"}
            try:
                pdf_bytes = generate_pdf_report(diag, lc_d)
                fname = f"KisanAI_{diag.get('plant_type','crop')}.pdf"
                st.html("""<div class="info-c">
                  <div style="font-size:1.4rem;margin-bottom:8px;">📄</div>
                  <div style="font-family:'Outfit',sans-serif;font-size:0.88rem;font-weight:600;color:#d4e8d6;margin-bottom:4px;">Download report</div>
                  <div style="font-size:0.75rem;color:#6b8f70;">Printable PDF in your language</div>
                </div>""")
                st.download_button(label=PDF_L.get(lc_d,"📄 Download PDF"),
                                   data=pdf_bytes, file_name=fname, mime="application/pdf",
                                   key="dash_pdf", use_container_width=True)
            except: st.html("""<div class="info-c"><div style="font-size:0.8rem;color:#6b8f70;">PDF available after diagnosis</div></div>""")
        else:
            st.html("""<div class="info-c">
              <div style="font-size:1.4rem;margin-bottom:8px;">📄</div>
              <div style="font-family:'Outfit',sans-serif;font-size:0.88rem;font-weight:600;color:#d4e8d6;margin-bottom:4px;">Download PDF</div>
              <div style="font-size:0.75rem;color:#6b8f70;">Available after first diagnosis</div>
            </div>""")

    # Confidence trend chart
    st.html('<div class="sec-hd">Confidence Trend — Last 5 Scans <span class="sec-hd-sub">Based on recent diagnoses</span></div>')

    history = st.session_state.scan_history
    if history:
        import json as _json
        labels = [h["crop"] for h in history[-5:]]
        data   = [h["conf"]  for h in history[-5:]]

        chart_html = f"""
        <div style="background:var(--card,#1a211b);border:1px solid rgba(74,222,128,0.12);
                    border-radius:12px;padding:18px 20px;margin-bottom:4px;">
          <canvas id="confChart" style="width:100%;height:160px;display:block;"></canvas>
        </div>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
        <script>
        (function(){{
          var ctx = document.getElementById('confChart');
          if (!ctx) return;
          new Chart(ctx, {{
            type: 'line',
            data: {{
              labels: {_json.dumps(labels)},
              datasets: [{{
                label: 'Confidence %',
                data: {_json.dumps(data)},
                borderColor: '#22c55e',
                backgroundColor: 'rgba(34,197,94,0.08)',
                borderWidth: 2,
                pointBackgroundColor: '#4ade80',
                pointBorderColor: '#111714',
                pointRadius: 5,
                tension: 0.4,
                fill: true,
              }}]
            }},
            options: {{
              responsive: true,
              maintainAspectRatio: false,
              plugins: {{ legend: {{ display: false }} }},
              scales: {{
                x: {{ ticks: {{ color: '#6b8f70', font: {{ size: 11 }} }}, grid: {{ color: 'rgba(74,222,128,0.06)' }} }},
                y: {{ min: 0, max: 100, ticks: {{ color: '#6b8f70', font: {{ size: 11 }} }},
                       grid: {{ color: 'rgba(74,222,128,0.06)' }} }}
              }}
            }}
          }});
        }})();
        </script>"""
        st.html(chart_html)

    # Recent diagnoses table
    st.html('<div class="sec-hd">Recent diagnoses</div>')

    header_html = """<table class="diag-table">
    <thead><tr>
      <th>Crop</th><th>Disease</th><th>Confidence</th><th>Language</th><th>Date</th><th>Shared</th><th>Action</th>
    </tr></thead><tbody>"""
    rows_html = ""
    for h in st.session_state.scan_history:
        dot_cls = "dot-g" if h["conf"] >= 80 else "dot-y" if h["conf"] >= 60 else "dot-r"
        conf_cls = conf_chip_cls(h["conf"])
        rows_html += f"""<tr>
          <td><span class="crop-dot"><span class="dot {dot_cls}"></span>{h['crop']}</span></td>
          <td>{h['disease']}</td>
          <td><span class="conf-chip {conf_cls}">{h['conf']}%</span></td>
          <td>{h['lang']}</td>
          <td>{h['date']}</td>
          <td><span style="font-size:0.78rem;color:#6b8f70;">{h['shared']}</span></td>
          <td><button class="action-btn">↓</button></td>
        </tr>"""
    st.html(header_html + rows_html + "</tbody></table>")

# ══════════════════════════════════════════════════════════════
# PAGE: UPLOAD & DIAGNOSE
# ══════════════════════════════════════════════════════════════
elif st.session_state.page == "diagnose":

    st.html("""<div class="topbar">
      <div class="page-title"><span class="page-title-icon">📷</span> Upload &amp; Diagnose</div>
      <div style="font-size:0.8rem;color:#6b8f70;">Drag and drop images or upload from files</div>
    </div>""")

    left_col, right_col = st.columns([3, 2])

    with left_col:
        st.html('<div class="info-title">📸 Upload leaf photos</div>')
        uploaded = st.file_uploader("Drop leaf photos (up to 3 for best results)",
                                     type=["jpg","jpeg","png"], accept_multiple_files=True,
                                     label_visibility="collapsed", key="uploader")

        if uploaded:
            imgs = [Image.open(f) for f in uploaded[:3]]
            im_cols = st.columns(min(len(imgs), 3))
            for i, (col, img) in enumerate(zip(im_cols, imgs)):
                with col:
                    thumb = img.copy(); thumb.thumbnail((200,200), Image.Resampling.LANCZOS)
                    st.image(thumb, use_container_width=True)
                    st.html(f'<div style="font-size:0.7rem;color:#6b8f70;text-align:center;margin-top:2px;">'
                            f'{uploaded[i].name[:20]} · {img.width}×{img.height}</div>')

        # Tips
        st.html("""<div class="info-c" style="margin-top:14px;">
          <div class="info-title">💡 Quick Tips</div>
          <div style="font-size:0.78rem;color:#6b8f70;line-height:1.7;">
            1. Capture leaf margins and veins clearly.<br>
            2. Include a ruler or coin for scale if possible.<br>
            3. If uncertain, upload multiple images from different angles.
          </div>
        </div>""")

    with right_col:
        st.html('<div class="info-title">⚙️ Session Settings</div>')

        plant_opts = ["🤖 Auto-detect from image"] + sorted(list(PLANT_COMMON_DISEASES.keys())) + ["✏️ Type manually..."]
        sel_plant = st.selectbox("Crop Type", plant_opts, label_visibility="visible", key="plant_sel_d")
        if sel_plant == "✏️ Type manually...":
            cp = st.text_input("Enter plant name", placeholder="e.g. Papaya, Jackfruit...", key="custom_plant_d")
            chosen_plant = cp.strip() if cp and cp.strip() else None
        elif sel_plant == "🤖 Auto-detect from image":
            chosen_plant = "AUTO"
            st.html('<div style="font-size:0.75rem;color:#4ade80;padding:4px 0;">AI will detect crop from photo</div>')
        else:
            chosen_plant = sel_plant

        region_opts = ["🤖 Auto-detect"] + REGIONS
        sel_region = st.selectbox("Region", region_opts, label_visibility="visible", key="region_d")
        region = sel_region if sel_region != "🤖 Auto-detect" else "AUTO"

        soil_opts = ["🤖 Auto-detect"] + SOIL_TYPES + ["✏️ Type manually..."]
        sel_soil = st.selectbox("Soil Type", soil_opts, label_visibility="visible", key="soil_d")
        if sel_soil == "✏️ Type manually...":
            cs = st.text_input("Soil type", placeholder="e.g. Sandy loam...", key="custom_soil_d")
            soil = cs.strip() if cs and cs.strip() else "Unknown"
        elif sel_soil == "🤖 Auto-detect":
            soil = "AUTO"
        else:
            soil = sel_soil

        st.html('<div style="height:6px;"></div>')
        st.html('<div class="info-title">📋 Preferred Output Language</div>')
        lang_for_diag = st.selectbox("Output language", list(LANGUAGES.keys()),
                                      index=list(LANGUAGES.keys()).index(st.session_state.lang),
                                      label_visibility="collapsed", key="lang_diag")

        nc, tc = st.columns(2)
        with nc: infected_n = st.number_input("Infected plants", min_value=1, value=10, step=1, key="inf_n")
        with tc: total_n = st.number_input("Total plants", min_value=1, value=100, step=10, key="tot_n")

        st.html('<div style="height:8px;"></div>')
        can_diag = bool(uploaded and chosen_plant)
        if uploaded and not chosen_plant:
            st.html('<div style="font-size:0.8rem;color:#fbbf24;padding:6px 0;">Select a crop or choose Auto-detect</div>')

        if can_diag:
            if st.button("🔍  Diagnose Now", use_container_width=True, key="diag_btn"):
                with st.spinner("Analysing your plant with Gemini..."):
                    try:
                        imgs = [Image.open(f) for f in uploaded[:3]]
                        actual_plant = chosen_plant; actual_region = region; actual_soil = soil
                        lc_for_diag = LANGUAGES.get(lang_for_diag, "en")

                        if chosen_plant == "AUTO" or region == "AUTO" or soil == "AUTO":
                            dp = f"""Look at this plant image. Identify crop, region, soil.
Respond ONLY with valid JSON: {{"detected_plant":"Wheat","detected_region":"North India","detected_soil":"Alluvial Soil","detection_confidence":80}}"""
                            dr = extract_json(genai.GenerativeModel("gemini-2.5-flash").generate_content([dp] + [enhance_image(i.copy()) for i in imgs]).text)
                            if dr:
                                if chosen_plant == "AUTO": actual_plant = dr.get("detected_plant","Unknown")
                                if region == "AUTO": actual_region = dr.get("detected_region","North India")
                                if soil == "AUTO": actual_soil = dr.get("detected_soil","Alluvial Soil")
                                st.success(f"🤖 Detected: {actual_plant} · {actual_region} · {actual_soil}")

                        common = PLANT_COMMON_DISEASES.get(actual_plant, "various plant diseases")
                        li = LANG_INSTRUCTIONS.get(lc_for_diag, LANG_INSTRUCTIONS["en"])
                        prompt = DIAG_PROMPT.format(plant_type=actual_plant, common_diseases=common,
                                                     region=actual_region, soil=actual_soil, lang_instruction=li)
                        enhanced = [enhance_image(i.copy()) for i in imgs]
                        result = extract_json(genai.GenerativeModel("gemini-2.5-flash").generate_content([prompt]+enhanced).text)

                        if result:
                            entry = {
                                "plant_type": actual_plant, "disease_name": result.get("disease_name","Unknown"),
                                "disease_type": result.get("disease_type","unknown"),
                                "severity": result.get("severity","unknown"),
                                "confidence": result.get("confidence",0),
                                "infected_count": int(infected_n), "total_plants": int(total_n),
                                "region": actual_region, "soil": actual_soil,
                                "result": result, "timestamp": datetime.now().isoformat(),
                                "lang_code": lc_for_diag,
                            }
                            st.session_state.last_diagnosis = entry
                            st.session_state.scan_history.insert(0, {
                                "crop": actual_plant, "disease": result.get("disease_name","Unknown"),
                                "conf": result.get("confidence",0), "lang": lang_for_diag,
                                "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                "severity": result.get("severity","unknown"), "shared": "Private",
                            })
                            st.session_state.page = "results"; st.rerun()
                        else:
                            st.error("Could not parse AI response. Try a clearer photo.")
                    except Exception as e:
                        st.error(f"Analysis failed: {e}")

        # Privacy note
        st.html("""<div style="font-size:0.72rem;color:#374a39;margin-top:12px;line-height:1.6;padding:10px;
                    background:rgba(255,255,255,0.02);border-radius:8px;border:1px solid rgba(74,222,128,0.06);">
          🔒 Privacy: Images processed locally where possible. Uploaded for model inference; deleted after 30 days.
        </div>""")

# ══════════════════════════════════════════════════════════════
# PAGE: DIAGNOSIS RESULTS
# ══════════════════════════════════════════════════════════════
elif st.session_state.page == "results":

    diag = st.session_state.last_diagnosis
    if not diag:
        st.html('<div style="padding:40px;text-align:center;color:#6b8f70;">No diagnosis yet. Upload a leaf photo first.</div>')
        if st.button("← Go to Upload", key="go_upload"):
            st.session_state.page = "diagnose"; st.rerun()
    else:
        result = diag.get("result", {})
        disease = result.get("disease_name","Unknown")
        severity = result.get("severity","unknown")
        conf = result.get("confidence",0)
        dtype = result.get("disease_type","").title()
        plant = diag.get("plant_type","")
        infected = diag.get("infected_count",0)
        total_p = diag.get("total_plants",100)
        loss_pct = calc_loss_pct(severity, infected, total_p)
        conf_c = conf_color(conf)

        # Top action bar
        act1, act2, act3, act4 = st.columns(4)
        with act1:
            lc_d = diag.get("lang_code","en")
            PDF_L = {"en":"📥 Download PDF","hi":"📥 PDF डाउनलोड","pa":"📥 PDF ਡਾਊਨਲੋਡ","ur":"📥 PDF ڈاؤنلوڈ"}
            try:
                pdf_bytes = generate_pdf_report(diag, lc_d)
                st.download_button(PDF_L.get(lc_d,"📥 Download PDF"),
                                   data=pdf_bytes,
                                   file_name=f"KisanAI_{plant}.pdf",
                                   mime="application/pdf", key="res_pdf",
                                   use_container_width=True)
            except Exception as e:
                st.error(f"PDF error: {e}")
        with act2:
            if st.button("💬 Ask KisanAI", key="goto_chat", use_container_width=True):
                st.session_state.page = "fieldlog"; st.rerun()
        with act3:
            if st.button("📷 New Scan", key="new_scan", use_container_width=True):
                st.session_state.page = "diagnose"; st.rerun()
        with act4:
            if st.button("🏠 Dashboard", key="goto_dash", use_container_width=True):
                st.session_state.page = "dashboard"; st.rerun()

        st.html("<div style='height:12px;'></div>")

        # Disease hero
        sev_b = sev_cls(severity); type_b = type_cls(dtype)
        sev_icon = "✅" if "health" in severity.lower() else "🟡" if "mild" in severity.lower() else "🔴" if "severe" in severity.lower() else "🟠"
        st.html(f"""
        <div class="diag-hero">
          <div class="diag-title">{disease}</div>
          <div class="badge-row">
            <span class="badge {sev_b}">{sev_icon} {severity.title()}</span>
            <span class="badge {type_b}">{dtype}</span>
            <span class="badge b-green">🌱 {plant}</span>
            <span class="badge b-blue">📍 {diag.get('region','')}</span>
            <span class="badge b-gray">🌱 {diag.get('soil','')}</span>
          </div>
          <div class="diag-conf-row">
            <span style="font-size:0.7rem;color:#6b8f70;text-transform:uppercase;letter-spacing:0.08em;">AI Confidence</span>
            <div class="conf-bar-bg"><div class="conf-bar-fill" style="width:{conf}%;background:{conf_c};"></div></div>
            <span style="font-size:0.82rem;font-weight:700;color:{conf_c};">{conf}%</span>
          </div>
        </div>""")

        # Stat row
        s1,s2,s3,s4 = st.columns(4)
        for col, lbl, val, clr in [
            (s1,"Infected Plants",str(infected),"#4ade80"),
            (s2,"Total Plants",str(total_p),"#d4e8d6"),
            (s3,"Yield Loss",f"{loss_pct}%","#f87171"),
            (s4,"Confidence",f"{conf}%",conf_c),
        ]:
            with col: col.html(f'<div class="stat-c"><div class="stat-v" style="color:{clr};">{val}</div><div class="stat-l">{lbl}</div></div>')

        st.html("<div style='height:10px;'></div>")

        # Two columns: actions + causes
        lc1, lc2 = st.columns(2)
        with lc1:
            st.html('<div class="info-title">⚡ Immediate Actions</div>')
            for i,a in enumerate(result.get("immediate_action",[]),1):
                st.html(f'<div class="act-item"><div class="act-n">{i}</div><div>{a}</div></div>')
            if result.get("symptoms"):
                st.html('<div class="info-title" style="margin-top:14px;">🔎 Symptoms Observed</div>')
                for s in result.get("symptoms",[]):
                    st.html(f'<div style="padding:3px 0;font-size:0.83rem;color:#6b8f70;">• {s}</div>')
        with lc2:
            st.html('<div class="info-title">📋 Probable Causes</div>')
            for c in result.get("probable_causes",[]):
                st.html(f'<div style="padding:3px 0;font-size:0.83rem;color:#6b8f70;">• {c}</div>')
            if result.get("differential_diagnosis"):
                st.html('<div class="info-title" style="margin-top:14px;">🔬 Other Possibilities</div>')
                for dd in result.get("differential_diagnosis",[]):
                    st.html(f'<div style="padding:3px 0;font-size:0.83rem;color:#6b8f70;">• {dd}</div>')

        st.html("<div style='height:8px;'></div>")

        # Treatments
        t1, t2 = st.columns(2)
        org_total = 0; chem_total = 0
        with t1:
            st.html('<div class="info-title">🌿 Organic Treatments</div>')
            for t in result.get("organic_treatments",[]):
                if not isinstance(t,str): continue
                n = normalize_name(t); info = get_treatment_info("organic",n)
                org_total += info["cost"]
                flag = "" if info.get("_m") else " ⚠️"
                st.html(f'''<div class="treat-r">
                  <div><div class="treat-n">🌿 {n}{flag}</div>
                  <div class="treat-d">{info["quantity"]} · {info["dilution"]}</div></div>
                  <div class="treat-p">₹{info["cost"]}</div></div>''')

        with t2:
            st.html('<div class="info-title">⚗️ Chemical Treatments</div>')
            for t in result.get("chemical_treatments",[]):
                if not isinstance(t,str): continue
                n = normalize_name(t); info = get_treatment_info("chemical",n)
                chem_total += info["cost"]
                flag = "" if info.get("_m") else " ⚠️"
                st.html(f'''<div class="treat-r">
                  <div><div class="treat-n">⚗️ {n}{flag}</div>
                  <div class="treat-d">{info["quantity"]} · {info["dilution"]}</div></div>
                  <div class="treat-p">₹{info["cost"]}</div></div>''')

        # ROI
        yield_val = 1000 * 40
        pot_loss = int(yield_val * loss_pct / 100)
        org_roi = int((pot_loss-org_total)/max(org_total,1)*100) if org_total else 0
        chem_roi = int((pot_loss-chem_total)/max(chem_total,1)*100) if chem_total else 0
        oc = "#4ade80" if org_roi>=chem_roi else "#6b8f70"; cc = "#60a5fa" if chem_roi>org_roi else "#6b8f70"

        st.html("<div style='height:8px;'></div>")
        st.html('<div class="info-title">💰 Cost & ROI (per 100 plants)</div>')
        r1,r2 = st.columns(2)
        r1.html(f'<div class="stat-c"><div class="stat-v" style="color:{oc};font-size:1.2rem;">₹{org_total}</div><div class="stat-l">Organic Cost · ROI {org_roi}%</div></div>')
        r2.html(f'<div class="stat-c"><div class="stat-v" style="color:{cc};font-size:1.2rem;">₹{chem_total}</div><div class="stat-l">Chemical Cost · ROI {chem_roi}%</div></div>')

        if result.get("prevention_long_term"):
            st.html("<div style='height:8px;'></div>")
            st.html('<div class="info-title">🛡️ Long-term Prevention</div>')
            for p in result.get("prevention_long_term",[]):
                st.html(f'<div class="act-item" style="background:rgba(96,165,250,0.04);border-color:rgba(96,165,250,0.1);">🛡️ {p}</div>')

        if result.get("plant_specific_notes"):
            st.html("<div style='height:8px;'></div>")
            st.html('<div class="info-title">📌 Plant Notes</div>')
            st.html(f'<div class="info-c"><div style="font-size:0.84rem;color:#6b8f70;line-height:1.65;">{result["plant_specific_notes"]}</div></div>')

        should_treat = result.get("should_treat", True)
        treat_reason = result.get("treat_reason","")
        v_style = "verdict" if should_treat else "verdict\" style=\"border-left-color:#fbbf24;color:#fbbf24"
        st.html(f'<div class="{v_style}">{"✅ Treat immediately" if should_treat else "💡 Monitor closely"}. {treat_reason}</div>')

# ══════════════════════════════════════════════════════════════
# PAGE: FIELD LOG & TREATMENT (chat + rotation + ROI)
# ══════════════════════════════════════════════════════════════
elif st.session_state.page == "fieldlog":

    st.html("""<div class="topbar">
      <div class="page-title"><span class="page-title-icon">🌱</span> Field Log &amp; Treatment Planner</div>
    </div>""")

    tab1, tab2, tab3 = st.tabs(["💬 KisanAI Chat", "🔄 Crop Rotation", "📊 Cost & ROI"])

    # ── Chat
    with tab1:
        diag = st.session_state.last_diagnosis
        if diag:
            st.html(f'''<div class="info-c" style="margin-bottom:12px;">
              <div class="info-title">Current Diagnosis Context</div>
              <div style="display:flex;gap:18px;flex-wrap:wrap;font-size:0.83rem;">
                <span>🌱 <b style="color:#d4e8d6;">{diag.get("plant_type")}</b></span>
                <span>🦠 {diag.get("disease_name")}</span>
                <span>⚠️ {diag.get("severity","").title()}</span>
                <span>📊 {diag.get("confidence",0)}%</span>
              </div></div>''')
        else:
            st.html('<div style="font-size:0.82rem;color:#fbbf24;padding:8px;margin-bottom:10px;">No diagnosis yet — answers will be general</div>')

        cc = st.columns([5,1])
        with cc[1]:
            if st.button("🗑️ Clear", key="clear_chat"):
                st.session_state.chat_messages = []; st.rerun()

        if not st.session_state.chat_messages:
            welcome = {
                "en": "🙏 Namaste! I'm KisanAI.\n\nAsk me about:\n• 📸 Disease treatment & prevention\n• 💰 Cost & ROI calculations\n• 🔄 Crop rotation advice\n• 🌾 Any farming question",
                "hi": "🙏 नमस्ते! मैं किसान AI हूं।\n\n• 💊 इलाज की सलाह\n• 💰 लागत और मुनाफा\n• 🔄 फसल चक्र\n\nकुछ भी पूछें!",
                "pa": "🙏 ਸਤ ਸ੍ਰੀ ਅਕਾਲ! ਕਿਸਾਨ AI ਹਾਂ।\n\n• 💊 ਇਲਾਜ ਦੀ ਸਲਾਹ\n• 💰 ਲਾਗਤ ਅਤੇ ਮੁਨਾਫਾ\n\nਕੁਝ ਵੀ ਪੁੱਛੋ!",
                "ur": "🙏 آداب! کسان AI ہوں۔\n\n• 💊 علاج کی سفارش\n• 💰 لاگت اور منافع\n\nکچھ بھی پوچھیں!",
            }
            msg = welcome.get(lang_code, welcome["en"])
            st.html(f"""<div class="chat-wrap">
              <div class="msg-bot"><div class="av av-b">🌿</div>
              <div class="bub bub-b" style="white-space:pre-line;">{msg}</div></div>
            </div>""")
        else:
            parts = ['<div class="chat-wrap">']
            for m in st.session_state.chat_messages[-30:]:
                if m["role"] == "user":
                    parts.append(f'<div class="msg-usr"><div class="av av-u">👤</div><div class="bub bub-u">{m["content"]}</div></div>')
                else:
                    parts.append(f'<div class="msg-bot"><div class="av av-b">🌿</div><div class="bub bub-b" style="white-space:pre-line;">{m["content"]}</div></div>')
            parts.append("</div>")
            st.html("".join(parts))

        st.html("<div style='height:8px;'></div>")
        ic, bc = st.columns([6,1])
        ph = {"en":"Ask about your crop, disease, treatment...","hi":"अपनी फसल के बारे में पूछें...","pa":"ਆਪਣੀ ਫਸਲ ਬਾਰੇ ਪੁੱਛੋ...","ur":"اپنی فصل کے بارے میں پوچھیں..."}
        with ic:
            user_text = st.text_input("msg", placeholder=ph.get(lang_code,"Ask anything..."),
                                       label_visibility="collapsed", key="chat_input")
        with bc:
            send = st.button("➤", key="send_btn", use_container_width=True)
        if send and user_text.strip():
            st.session_state.chat_messages.append({"role":"user","content":user_text.strip()})
            try:
                ans = get_kisan_response(user_text.strip(), st.session_state.last_diagnosis)
                st.session_state.chat_messages.append({"role":"bot","content":ans})
            except Exception as e:
                st.session_state.chat_messages.append({"role":"bot","content":f"Error: {e}"})
            st.rerun()

    # ── Crop Rotation
    with tab2:
        diag = st.session_state.last_diagnosis
        default_plant = diag["plant_type"] if diag and diag.get("plant_type") else None

        ri1, ri2 = st.columns(2)
        with ri1:
            st.html('<div class="info-title">🌱 Current Crop</div>')
            use_last = False
            if default_plant:
                use_last = st.checkbox(f"Use diagnosed: {default_plant}", value=True, key="use_last")
            if use_last and default_plant:
                plant_rot = default_plant
                st.html(f'<div style="font-size:0.8rem;color:#4ade80;padding:4px 0;">✓ Using {plant_rot}</div>')
            else:
                opts = sorted(list(PLANT_COMMON_DISEASES.keys())) + ["Other (type below)"]
                sel = st.selectbox("Select crop", opts, label_visibility="collapsed", key="rot_sel")
                if sel == "Other (type below)":
                    plant_rot = st.text_input("Crop name", placeholder="e.g. Banana, Mango...", label_visibility="collapsed", key="rot_custom")
                else:
                    plant_rot = sel
        with ri2:
            st.html('<div class="info-title">📍 Field Details</div>')
            region_rot = st.selectbox("Region", REGIONS, label_visibility="collapsed", key="rot_region")
            soil_rot = st.selectbox("Soil Type", SOIL_TYPES, label_visibility="collapsed", key="rot_soil")

        if st.button("📋 Generate Rotation Plan", use_container_width=True, key="gen_rot"):
            if plant_rot:
                with st.spinner(f"Generating rotation plan for {plant_rot}..."):
                    r = get_rotation_plan(plant_rot, region_rot, soil_rot)
                    st.session_state.crop_rotation_result = {"plant_type":plant_rot,"rotations":r.get("rotations",[]),"info":r.get("info",{}),"region":region_rot,"soil":soil_rot}
            else: st.warning("Please select or enter a plant name.")

        rr = st.session_state.crop_rotation_result
        if rr:
            st.html("<div style='height:8px;'></div>")
            st.html('<div class="info-title">📅 3-Year Rotation Strategy</div>')
            rots = rr["rotations"]; info_d = rr["info"]
            rc1,rc2,rc3 = st.columns(3)
            for col,yr,crop,desc in [
                (rc1,"📌 YEAR 1 · NOW",rr["plant_type"],info_d.get(rr["plant_type"],"Primary crop.")[:80]),
                (rc2,"🔄 YEAR 2 · NEXT",rots[0] if rots else "—",info_d.get(rots[0],"")[:80] if rots else ""),
                (rc3,"🌿 YEAR 3 · THIRD",rots[1] if len(rots)>1 else "—",info_d.get(rots[1],"")[:80] if len(rots)>1 else ""),
            ]:
                with col: col.html(f'<div class="rot-c"><div class="rot-yr">{yr}</div><div class="rot-crop">{crop}</div><div class="rot-desc">{desc}</div></div>')

    # ── Cost & ROI
    with tab3:
        diag = st.session_state.last_diagnosis
        if not diag:
            st.html('<div style="color:#fbbf24;font-size:0.85rem;">Run a diagnosis first to calculate ROI.</div>')
        else:
            plant_name = diag.get("plant_type","Unknown"); disease_name = diag.get("disease_name","Unknown")
            infected_count = diag.get("infected_count",50); total_plants = diag.get("total_plants",100)
            sev = diag.get("severity","moderate"); result = diag.get("result",{})

            dm1,dm2,dm3,dm4,dm5 = st.columns(5)
            for col,lbl,val in [(dm1,"Plant",plant_name),(dm2,"Disease",disease_name[:12]+"..."),(dm3,"Severity",sev.title()),(dm4,"Confidence",f'{diag.get("confidence",0)}%'),(dm5,"Infected",str(infected_count))]:
                with col: col.html(f'<div class="stat-c"><div class="stat-v" style="font-size:0.95rem;">{val}</div><div class="stat-l">{lbl}</div></div>')

            st.html("<div style='height:10px;'></div>")
            t_choice = st.radio("Treatment type", ["Organic","Chemical"], horizontal=True, key="roi_type")
            sel_type = "organic" if t_choice=="Organic" else "chemical"
            treat_list = result.get(f"{'organic' if sel_type=='organic' else 'chemical'}_treatments",[])
            treat_names = [normalize_name(t) for t in treat_list if isinstance(t,str)]
            total_treat = 300
            if treat_names:
                sel_t = st.selectbox("Select treatment", treat_names, key="roi_treat")
                ti = get_treatment_info(sel_type, sel_t)
                total_treat = int(ti["cost"] * max(infected_count,1) / 100)
                st.html(f'<div style="font-size:0.78rem;color:#4ade80;padding:4px 0;">Estimated ₹{total_treat} for {infected_count} plants · {ti["quantity"]}</div>')

            ci1,ci2,ci3,ci4 = st.columns(4)
            with ci1: org_c_in = st.number_input("Organic cost (₹)", value=total_treat if sel_type=="organic" else 0, min_value=0, step=100, key="roi_org")
            with ci2: chem_c_in = st.number_input("Chemical cost (₹)", value=total_treat if sel_type=="chemical" else 0, min_value=0, step=100, key="roi_chem")
            with ci3: yield_kg = st.number_input("Yield (kg)", value=1000, min_value=100, step=100, key="roi_yield")
            with ci4: mkt = st.number_input("Price (₹/kg)", value=40, min_value=1, step=5, key="roi_mkt")

            if st.button("📊 Calculate ROI", use_container_width=True, key="calc_roi"):
                al = calc_loss_pct(sev, infected_count, total_plants)
                tr = int(yield_kg * mkt); pl = int(tr * al / 100)
                oroi = int((pl-org_c_in)/max(org_c_in,1)*100) if org_c_in>0 else 0
                croi = int((pl-chem_c_in)/max(chem_c_in,1)*100) if chem_c_in>0 else 0
                st.session_state.cost_roi_result = {"total":tr,"loss":pl,"loss_pct":al,"org_cost":org_c_in,"chem_cost":chem_c_in,"org_roi":oroi,"chem_roi":croi}

            roi = st.session_state.cost_roi_result
            if roi:
                rm1,rm2,rm3 = st.columns(3)
                rm1.html(f'<div class="stat-c"><div class="stat-v">₹{roi["total"]:,}</div><div class="stat-l">Total Yield Value</div></div>')
                rm2.html(f'<div class="stat-c"><div class="stat-v" style="color:#f87171;">₹{roi["loss"]:,}</div><div class="stat-l">Loss if Untreated ({roi["loss_pct"]}%)</div></div>')
                rm3.html(f'<div class="stat-c"><div class="stat-v">{infected_count}/{total_plants}</div><div class="stat-l">Infected / Total</div></div>')
                rr1,rr2 = st.columns(2)
                oc = "#4ade80" if roi["org_roi"]>=roi["chem_roi"] else "#6b8f70"
                xc = "#60a5fa" if roi["chem_roi"]>roi["org_roi"] else "#6b8f70"
                rr1.html(f'<div class="stat-c"><div class="stat-v" style="color:{oc};">{roi["org_roi"]}%</div><div class="stat-l">Organic ROI · Cost ₹{roi["org_cost"]:,}</div></div>')
                rr2.html(f'<div class="stat-c"><div class="stat-v" style="color:{xc};">{roi["chem_roi"]}%</div><div class="stat-l">Chemical ROI · Cost ₹{roi["chem_cost"]:,}</div></div>')
                best = "Organic" if roi["org_roi"]>=roi["chem_roi"] else "Chemical"
                st.html(f'<div class="verdict">✅ {best} treatment provides better ROI. Estimated savings vs no treatment: ₹{roi["loss"]:,}</div>')

# ══════════════════════════════════════════════════════════════
# PAGE: LANGUAGES & SUPPORT
# ══════════════════════════════════════════════════════════════
elif st.session_state.page == "languages":

    st.html("""<div class="topbar">
      <div class="page-title"><span class="page-title-icon">🌐</span> Languages &amp; Support</div>
    </div>""")

    lc1, lc2 = st.columns([3,2])

    with lc1:
        st.html('<div class="info-title">🌐 Select Language</div>')
        st.html('<div style="font-size:0.8rem;color:#6b8f70;margin-bottom:12px;">Choose from English and 12 Indian languages. The app will show sample translations in the selected language.</div>')

        lang_grid = [
            ("English","en","Upload · Diagnose · Results"),
            ("हिंदी (Hindi)","hi","अपलोड · निदान · परिणाम"),
            ("ਪੰਜਾਬੀ (Punjabi)","pa","ਅਪਲੋਡ · ਨਿਦਾਨ · ਨਤੀਜੇ"),
            ("বাংলা (Bengali)","bn","আপলোড · নির্ণয় · ফলাফল"),
            ("తెలుగు (Telugu)","te","అప్‌లోడ్ · నిర్ণయం · ఫలితాలు"),
            ("தமிழ் (Tamil)","ta","பதிவேற்று · கண்டறி · முடிவுகள்"),
            ("ಕನ್ನಡ (Kannada)","kn","ಅಪ್‌ಲೋಡ್ · ರೋಗ ನಿರ್ಣಯ · ಫಲಿತಾಂಶ"),
            ("मराठी (Marathi)","mr","अपलोड · निदान · निकाल"),
            ("ગુજરાતી (Gujarati)","gu","અપલોડ · નિદાન · પરિણામ"),
            ("اردو (Urdu)","ur","اپلوڈ · تشخیص · نتائج"),
            ("മലയാളം (Malayalam)","ml","അപ്‌ലോഡ് · നിർണ്ണയം · ഫലങ്ങൾ"),
            ("ଓଡ଼ିଆ (Odia)","or","ଅପଲୋଡ · ନିଦାନ · ଫଳ"),
        ]

        lg1, lg2 = st.columns(2)
        for i, (name, code, sample) in enumerate(lang_grid):
            is_sel = st.session_state.lang_code == code
            bg = "rgba(74,222,128,0.08)" if is_sel else "var(--card,#1a211b)"
            border = "rgba(74,222,128,0.3)" if is_sel else "rgba(74,222,128,0.1)"
            col = lg1 if i % 2 == 0 else lg2
            col.html(f"""<div style="background:{bg};border:1px solid {border};border-radius:10px;
                         padding:12px 14px;margin:4px 0;cursor:pointer;">
              <div style="font-size:0.88rem;font-weight:600;color:#d4e8d6;">{name}</div>
              <div style="font-size:0.72rem;color:#6b8f70;margin-top:3px;">{sample}</div>
            </div>""")

        st.html("<div style='height:8px;'></div>")
        new_lang = st.selectbox("Switch app language", list(LANGUAGES.keys()),
                                 index=list(LANGUAGES.keys()).index(st.session_state.lang),
                                 label_visibility="visible", key="lang_switch")
        if st.button("✓ Apply Language", key="apply_lang", use_container_width=True):
            st.session_state.lang = new_lang
            st.session_state.lang_code = LANGUAGES[new_lang]
            st.success(f"Language changed to {new_lang}"); st.rerun()

        # Photo tips
        st.html("<div style='height:16px;'></div>")
        st.html('<div class="info-title">📷 Photo Troubleshooting Guide</div>')
        t1,t2,t3 = st.columns(3)
        for col,icon,label,desc in [
            (t1,"✅","Good: clear focus","Even lighting, close-up"),
            (t2,"❌","Avoid direct sunlight","Washed out details"),
            (t3,"❌","Avoid blurry hands","Use steady support"),
        ]:
            with col: col.html(f'<div class="rot-c"><div style="font-size:1.5rem;">{icon}</div><div class="rot-crop" style="font-size:0.82rem;">{label}</div><div class="rot-desc">{desc}</div></div>')

    with lc2:
        st.html('<div class="info-title">📊 Multilingual FAQs</div>')
        faqs = [
            ("What symptoms indicate a fungal infection?", "Circular spots, yellowing between veins, fuzzy growth on leaves."),
            ("How to safely apply recommended treatments?", "Wear gloves, follow dilution guide, spray early morning."),
            ("Local regulations for pesticide use?", "Check state-specific chemicals list; always read label first."),
        ]
        for q, a in faqs:
            with st.expander(q):
                st.html(f'<div style="font-size:0.83rem;color:#6b8f70;line-height:1.65;">{a}</div>')

        st.html("<div style='height:12px;'></div>")
        st.html('<div class="info-title">📞 Toll-free Helpline</div>')
        st.html("""<div class="info-c">
          <div style="font-family:'Outfit',sans-serif;font-size:1.1rem;font-weight:700;color:#4ade80;margin-bottom:4px;">1800-11-KISAN</div>
          <div style="font-size:0.78rem;color:#6b8f70;">Available Mon–Sat 8:00–18:00<br>Hindi, Punjabi, English, regional languages</div>
        </div>""")

        st.html("<div style='height:12px;'></div>")
        st.html('<div class="info-title">💬 WhatsApp Support</div>')
        st.html("""<div class="info-c">
          <div style="font-size:0.82rem;color:#6b8f70;margin-bottom:10px;">Quick templates to start a conversation in your language</div>
          <div style="background:rgba(74,222,128,0.06);border:1px solid rgba(74,222,128,0.12);border-radius:8px;padding:10px 12px;margin:6px 0;">
            <div style="font-size:0.78rem;font-weight:600;color:#d4e8d6;">Template: Report leaf spots</div>
            <div style="font-size:0.72rem;color:#6b8f70;margin-top:3px;">"My tomato leaves have brown circular spots with yellow edges..."</div>
          </div>
          <div style="background:rgba(74,222,128,0.06);border:1px solid rgba(74,222,128,0.12);border-radius:8px;padding:10px 12px;margin:6px 0;">
            <div style="font-size:0.78rem;font-weight:600;color:#d4e8d6;">Template: Request agronomist visit</div>
            <div style="font-size:0.72rem;color:#6b8f70;margin-top:3px;">"Please send an agronomist to inspect my wheat field..."</div>
          </div>
        </div>""")

        st.html("<div style='height:12px;'></div>")
        st.html('<div class="info-title">🤖 How Gemini Powers Diagnosis</div>')
        st.html("""<div class="info-c">
          <div style="font-size:0.8rem;color:#6b8f70;line-height:1.7;">
            <b style="color:#d4e8d6;">Input:</b> Leaf photo + crop type + growth stage (optional)<br>
            <b style="color:#d4e8d6;">Process:</b> Gemini vision model + language grounding<br>
            <b style="color:#d4e8d6;">Output:</b> Disease name, confidence score, treatment steps<br><br>
            Model trained on annotated agronomy datasets. Accuracy varies by crop and imaging conditions.
          </div>
        </div>""")

        st.html("<div style='height:12px;'></div>")
        st.html('<div class="info-title">📝 Feedback to Improve Model</div>')
        rating = st.radio("Rating", [1,2,3,4,5], horizontal=True, key="fb_rating")
        feedback = st.text_area("What was wrong? (optional)", placeholder="e.g. Symptom mislabeled as terminal when it's fungal", label_visibility="visible", key="fb_text")
        if st.button("Submit Feedback", key="submit_fb", use_container_width=True):
            st.success("Thank you! Your feedback helps improve KisanAI.")
