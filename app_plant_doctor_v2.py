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
    page_icon="assets/leaf.svg",
    layout="wide",
    initial_sidebar_ebar="expanded",
)

# ══════════════════════════════════════════════════════════════
# LANGUAGES
# ══════════════════════════════════════════════════════════════
LANGUAGES = {
    "English": "en", "Hindi": "hi", "Punjabi": "pa",
    "Marathi": "mr", "Telugu": "te", "Tamil": "ta",
    "Kannada": "kn", "Bengali": "bn", "Gujarati": "gu",
    "Odia": "or", "Malayalam": "ml", "Assamese": "as",
    "Urdu": "ur",
}
LANG_INSTRUCTIONS = {
    "en": "Respond in clear, simple English. Speak like a helpful village agricultural expert.",
    "hi": "Hindi mein jawab dein. Saral bhasha mein, jaise gaon ka krishi visheshagya bolta hai.",
    "pa": "Punjabi vich jawab deo. Saral bhasha vich.",
    "mr": "Marathi madhye uttar dya.", "te": "Telugu lo samadhaanam ivvandi.",
    "ta": "Tamil il padhil sollunga.", "kn": "Kannadada li uttara nidi.",
    "bn": "Banglay utthar din.", "gu": "Gujarati ma jawab apo.",
    "or": "Odia re uttara dia.", "ml": "Malayalam il utharam nalku.",
    "as": "Axomiya t utthar dia.", "ur": "Urdu mein jawab den.",
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
# CSS — Uizard-style dark dashboard (no emojis in UI chrome)
# ══════════════════════════════════════════════════════════════
st.html("""
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {
  --bg:       #1c1c1e;
  --bg2:      #242426;
  --bg3:      #2a2a2c;
  --card:     #2c2c2e;
  --card2:    #323234;
  --border:   rgba(255,255,255,0.07);
  --border2:  rgba(255,255,255,0.12);
  --green:    #4cd964;
  --green2:   #30d158;
  --green3:   #248a3d;
  --gdim:     rgba(76,217,100,0.08);
  --gold:     #ffd60a;
  --red:      #ff453a;
  --blue:     #0a84ff;
  --purple:   #bf5af2;
  --text:     #f2f2f7;
  --t2:       #8e8e93;
  --t3:       #48484a;
  --r:        10px;
  --rlg:      14px;
  --sidebar:  220px;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="block-container"],
.main {
  background: var(--bg) !important;
  font-family: 'DM Sans', sans-serif !important;
  color: var(--text) !important;
}

#MainMenu, footer, header,
[data-testid="stDecoration"],
[data-testid="collapsedControl"],
.stDeployButton { display: none !important; }

[data-testid="block-container"] {
  max-width: 100% !important;
  padding: 0 32px 60px !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background: var(--bg2) !important;
  border-right: 1px solid var(--border) !important;
  min-width: var(--sidebar) !important;
  max-width: var(--sidebar) !important;
}
[data-testid="stSidebar"] * {
  color: var(--t2) !important;
  font-family: 'DM Sans', sans-serif !important;
}
[data-testid="stSidebarNav"] { display: none !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }

/* ── Page header bar ── */
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 0 18px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 24px;
}
.page-title {
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--text);
  display: flex;
  align-items: center;
  gap: 10px;
  letter-spacing: -0.02em;
}
.topbar-search {
  flex: 1;
  max-width: 300px;
  margin: 0 24px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.topbar-search-input {
  background: transparent;
  border: none;
  color: var(--t2);
  font-size: 0.84rem;
  font-family: 'DM Sans', sans-serif;
  outline: none;
  width: 100%;
}
.topbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}
.topbar-icon-btn {
  width: 34px;
  height: 34px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--t2);
  font-size: 0.85rem;
}
.topbar-avatar {
  width: 34px;
  height: 34px;
  background: linear-gradient(135deg, #248a3d, #4cd964);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 700;
  color: #fff;
  cursor: pointer;
}

/* ── Result cards (Diagnosis Results row) ── */
.result-cards-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 24px;
}
.result-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--rlg);
  padding: 18px;
  cursor: pointer;
  transition: border-color 0.15s, transform 0.15s;
  position: relative;
  overflow: hidden;
}
.result-card:hover {
  border-color: var(--border2);
  transform: translateY(-1px);
}
.result-card-thumb {
  width: 100%;
  height: 90px;
  border-radius: 8px;
  background: var(--bg3);
  margin-bottom: 12px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}
.result-card-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 8px;
}
.result-card-thumb-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg3);
}
.result-card-icon {
  width: 36px;
  height: 36px;
  border-radius: 9px;
  background: var(--gdim);
  border: 1px solid rgba(76,217,100,0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
}
.result-card-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 3px;
}
.result-card-sub {
  font-size: 0.74rem;
  color: var(--t2);
  margin-bottom: 8px;
}
.result-card-meta {
  font-size: 0.72rem;
  color: var(--t3);
  font-family: 'DM Mono', monospace;
}

/* ── Quick action cards ── */
.qa-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--rlg);
  padding: 18px;
  cursor: pointer;
  transition: border-color 0.15s;
}
.qa-card:hover { border-color: var(--border2); }
.qa-card-thumb {
  width: 100%;
  height: 120px;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 12px;
  background: var(--bg3);
  position: relative;
}
.qa-card-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.qa-card-title {
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 4px;
}
.qa-card-desc {
  font-size: 0.73rem;
  color: var(--t2);
  line-height: 1.55;
}

/* ── Section header ── */
.sec-hd {
  font-size: 0.98rem;
  font-weight: 600;
  color: var(--text);
  margin: 22px 0 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  letter-spacing: -0.01em;
}
.sec-hd-badge {
  font-size: 0.7rem;
  color: var(--t2);
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 99px;
  padding: 2px 10px;
  font-weight: 400;
}

/* ── Data table ── */
.diag-table { width: 100%; border-collapse: collapse; }
.diag-table th {
  font-size: 0.68rem;
  color: var(--t2);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  padding: 10px 16px;
  text-align: left;
  border-bottom: 1px solid var(--border);
  font-weight: 500;
}
.diag-table td {
  padding: 12px 16px;
  font-size: 0.84rem;
  color: var(--text);
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
}
.diag-table tr:last-child td { border-bottom: none; }
.diag-table tr:hover td { background: rgba(255,255,255,0.02); }
.cell-with-icon {
  display: flex;
  align-items: center;
  gap: 10px;
}
.cell-icon {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: var(--bg3);
  border: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dot-green { background: var(--green2); }
.dot-gold  { background: var(--gold); }
.dot-red   { background: var(--red); }
.conf-pill {
  display: inline-block;
  font-size: 0.74rem;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 99px;
  font-family: 'DM Mono', monospace;
}
.pill-green  { background: rgba(48,209,88,0.1);  color: #30d158; }
.pill-gold   { background: rgba(255,214,10,0.1);  color: #ffd60a; }
.pill-red    { background: rgba(255,69,58,0.1);   color: #ff453a; }
.share-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 0.73rem;
  color: var(--t2);
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: 99px;
  padding: 2px 9px;
}
.tbl-action-btn {
  width: 28px;
  height: 28px;
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--t2);
  font-size: 0.75rem;
  text-decoration: none;
}

/* ── Summary stat cards ── */
.sum-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 22px; }
.sum-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--rlg);
  padding: 18px 16px;
}
.sum-label { font-size: 0.7rem; color: var(--t2); letter-spacing: 0.05em; margin-bottom: 6px; text-transform: uppercase; }
.sum-val { font-size: 1.6rem; font-weight: 700; color: var(--text); letter-spacing: -0.02em; line-height: 1; }
.sum-sub { font-size: 0.72rem; color: var(--t3); margin-top: 5px; }

/* ── Disease hero ── */
.diag-hero {
  background: var(--card2);
  border: 1px solid var(--border2);
  border-radius: var(--rlg);
  padding: 24px;
  margin-bottom: 18px;
  position: relative;
  overflow: hidden;
}
.diag-hero::before {
  content: '';
  position: absolute;
  top: 0; right: 0;
  width: 200px; height: 200px;
  background: radial-gradient(circle at 80% 20%, rgba(76,217,100,0.1) 0%, transparent 60%);
  pointer-events: none;
}
.diag-title {
  font-size: 1.8rem;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.03em;
  margin-bottom: 8px;
}
.conf-bar-bg { flex: 1; background: rgba(255,255,255,0.06); border-radius: 99px; height: 4px; }
.conf-bar-fill { height: 100%; border-radius: 99px; }
.diag-conf-row { display: flex; align-items: center; gap: 12px; margin-top: 14px; }

/* ── Badges ── */
.badge-row { display: flex; gap: 6px; flex-wrap: wrap; margin: 10px 0; }
.badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 99px;
  font-size: 0.68rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.b-green  { background: rgba(76,217,100,0.1);  color: #4cd964; border: 1px solid rgba(76,217,100,0.2); }
.b-amber  { background: rgba(255,214,10,0.1);   color: #ffd60a; border: 1px solid rgba(255,214,10,0.2); }
.b-red    { background: rgba(255,69,58,0.1);    color: #ff453a; border: 1px solid rgba(255,69,58,0.2); }
.b-blue   { background: rgba(10,132,255,0.1);   color: #0a84ff; border: 1px solid rgba(10,132,255,0.2); }
.b-purple { background: rgba(191,90,242,0.1);   color: #bf5af2; border: 1px solid rgba(191,90,242,0.2); }
.b-gray   { background: rgba(255,255,255,0.05); color: var(--t2); border: 1px solid var(--border); }

/* ── Stat mini cards ── */
.stat-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 14px 0; }
.stat-c {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 14px 12px;
  text-align: center;
}
.stat-v { font-size: 1.4rem; font-weight: 700; color: var(--text); letter-spacing: -0.02em; font-family: 'DM Mono', monospace; }
.stat-l { font-size: 0.62rem; color: var(--t2); text-transform: uppercase; letter-spacing: 0.08em; margin-top: 4px; }

/* ── Treatment rows ── */
.treat-r {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 10px 14px;
  margin: 5px 0;
  gap: 10px;
  transition: border-color 0.15s;
}
.treat-r:hover { border-color: var(--border2); }
.treat-n { font-size: 0.88rem; font-weight: 600; color: var(--text); }
.treat-d { font-size: 0.72rem; color: var(--t2); margin-top: 2px; }
.treat-p {
  font-size: 0.76rem;
  font-weight: 700;
  color: var(--green);
  background: rgba(76,217,100,0.08);
  border: 1px solid rgba(76,217,100,0.15);
  border-radius: 99px;
  padding: 3px 10px;
  white-space: nowrap;
  font-family: 'DM Mono', monospace;
}

/* ── Action items ── */
.act-item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  background: rgba(255,255,255,0.02);
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 9px 12px;
  margin: 5px 0;
  font-size: 0.84rem;
  color: var(--text);
  line-height: 1.55;
}
.act-n {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  border-radius: 6px;
  background: var(--green3);
  color: #fff;
  font-size: 0.65rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ── Verdict ── */
.verdict {
  background: rgba(76,217,100,0.05);
  border: 1px solid rgba(76,217,100,0.18);
  border-left: 3px solid var(--green3);
  border-radius: var(--r);
  padding: 10px 14px;
  font-size: 0.84rem;
  color: var(--green);
  margin: 10px 0;
}

/* ── Info card ── */
.info-c {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--rlg);
  padding: 16px 18px;
  margin: 8px 0;
}
.info-title {
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--t2);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.info-title::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border);
}

/* ── Chat ── */
.chat-wrap { display: flex; flex-direction: column; gap: 10px; }
.msg-bot, .msg-usr { display: flex; align-items: flex-start; gap: 9px; }
.msg-usr { flex-direction: row-reverse; }
.av { width: 28px; height: 28px; border-radius: 7px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: 700; }
.av-b { background: var(--green3); color: #fff; }
.av-u { background: var(--bg3); border: 1px solid var(--border2); color: var(--text); }
.bub { max-width: 78%; padding: 10px 14px; border-radius: var(--r); font-size: 0.86rem; line-height: 1.6; }
.bub-b { background: var(--card); border: 1px solid var(--border); color: var(--text); border-top-left-radius: 3px; }
.bub-u { background: rgba(76,217,100,0.08); border: 1px solid rgba(76,217,100,0.18); color: var(--text); border-top-right-radius: 3px; }

/* ── Rotation ── */
.rot-c {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--rlg);
  padding: 18px 16px;
  text-align: center;
  transition: border-color 0.15s;
}
.rot-c:hover { border-color: var(--border2); }
.rot-yr { font-size: 0.6rem; font-weight: 700; color: var(--gold); text-transform: uppercase; letter-spacing: 0.18em; margin-bottom: 8px; }
.rot-crop { font-size: 1.1rem; font-weight: 700; color: var(--text); margin: 6px 0; letter-spacing: -0.01em; }
.rot-desc { font-size: 0.76rem; color: var(--t2); line-height: 1.55; margin-top: 6px; }

/* ── Streamlit overrides ── */
.stButton > button {
  background: var(--green3) !important;
  color: #fff !important;
  border: none !important;
  border-radius: var(--r) !important;
  font-weight: 600 !important;
  font-size: 0.84rem !important;
  padding: 9px 20px !important;
  font-family: 'DM Sans', sans-serif !important;
  transition: all 0.15s ease !important;
  letter-spacing: 0.01em !important;
}
.stButton > button:hover {
  background: #1a6e30 !important;
  transform: translateY(-1px) !important;
}
.stDownloadButton > button {
  background: transparent !important;
  color: var(--green) !important;
  border: 1px solid rgba(76,217,100,0.25) !important;
  border-radius: var(--r) !important;
}
input, textarea, [data-baseweb="input"] input {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  color: var(--text) !important;
  border-radius: var(--r) !important;
  font-family: 'DM Sans', sans-serif !important;
  font-size: 0.85rem !important;
}
input:focus, textarea:focus { border-color: var(--green3) !important; box-shadow: 0 0 0 2px rgba(76,217,100,0.1) !important; }
.stSelectbox > div > div, [data-baseweb="select"] {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  color: var(--text) !important;
  border-radius: var(--r) !important;
}
[data-baseweb="popover"] { background: var(--card2) !important; border: 1px solid var(--border2) !important; }
[data-baseweb="option"]:hover { background: rgba(255,255,255,0.04) !important; }
[data-testid="stFileUploader"] {
  background: var(--card) !important;
  border: 1.5px dashed var(--border2) !important;
  border-radius: var(--rlg) !important;
}
[data-testid="stExpander"] {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r) !important;
}
.streamlit-expanderHeader { color: var(--t2) !important; font-size: 0.86rem !important; }
[data-testid="stTabs"] [data-baseweb="tab-list"] {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r) !important;
  padding: 3px !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
  background: transparent !important;
  color: var(--t2) !important;
  border-radius: 7px !important;
  font-size: 0.83rem !important;
  font-weight: 500 !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
  background: var(--green3) !important;
  color: #fff !important;
}
[data-testid="stTabs"] [data-baseweb="tab-border"] { display: none !important; }
.stAlert {
  border-radius: var(--r) !important;
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
}
[data-testid="stRadio"] label { color: var(--t2) !important; font-size: 0.84rem !important; }
[data-testid="stCheckbox"] label { color: var(--t2) !important; font-size: 0.84rem !important; }
p, label, div, span { color: var(--text); font-family: 'DM Sans', sans-serif; }
h1,h2,h3,h4 { font-family: 'DM Sans', sans-serif !important; color: var(--text) !important; letter-spacing: -0.02em !important; }

/* Sidebar nav button style override */
[data-testid="stSidebar"] .stButton > button {
  background: transparent !important;
  color: var(--t2) !important;
  border: none !important;
  text-align: left !important;
  justify-content: flex-start !important;
  padding: 7px 10px !important;
  font-size: 0.83rem !important;
  border-radius: 7px !important;
  transition: background 0.12s !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background: rgba(255,255,255,0.05) !important;
  transform: none !important;
}
</style>
""")

# ══════════════════════════════════════════════════════════════
# SVG ICONS
# ══════════════════════════════════════════════════════════════
ICONS = {
    "leaf": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/></svg>""",
    "camera": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>""",
    "grid": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>""",
    "history": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="12 8 12 12 14 14"/><path d="M3.05 11a9 9 0 1 1 .5 4m-.5-4V7m0 4h4"/></svg>""",
    "star": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>""",
    "archive": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="21 8 21 21 3 21 3 8"/><rect x="1" y="3" width="22" height="5"/><line x1="10" y1="12" x2="14" y2="12"/></svg>""",
    "users": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>""",
    "book": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>""",
    "globe": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>""",
    "search": """<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>""",
    "bell": """<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>""",
    "settings": """<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>""",
    "help": """<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>""",
    "download": """<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>""",
    "share": """<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>""",
    "chevron-right": """<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>""",
    "plant": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 22V12"/><path d="M12 12C12 12 9 9 9 6a3 3 0 0 1 6 0c0 3-3 6-3 6z"/><path d="M12 12c0 0-3-2-6-1a3 3 0 0 0 3 5c2 0 3-4 3-4z"/><path d="M12 12c0 0 3-2 6-1a3 3 0 0 1-3 5c-2 0-3-4-3-4z"/></svg>""",
    "bug": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="8" y="6" width="8" height="14" rx="4"/><path d="M19 7l-3 2"/><path d="M5 7l3 2"/><path d="M19 12h-2"/><path d="M7 12H5"/><path d="M19 17l-3-2"/><path d="M5 17l3-2"/><path d="M9 4l1.5-2"/><path d="M15 4l-1.5-2"/></svg>""",
    "calculator": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="2" width="16" height="20" rx="2"/><line x1="8" y1="6" x2="16" y2="6"/><line x1="8" y1="10" x2="8" y2="10"/><line x1="12" y1="10" x2="12" y2="10"/><line x1="16" y1="10" x2="16" y2="10"/><line x1="8" y1="14" x2="8" y2="14"/><line x1="12" y1="14" x2="12" y2="14"/><line x1="16" y1="14" x2="16" y2="14"/><line x1="8" y1="18" x2="16" y2="18"/></svg>""",
    "file-text": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>""",
    "edit": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>""",
    "refresh": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>""",
    "lock": """<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>""",
    "users-sm": """<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>""",
    "rotate": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M21 2v6h-6"/><path d="M3 12a9 9 0 0 1 15-6.7L21 8"/><path d="M3 22v-6h6"/><path d="M21 12a9 9 0 0 1-15 6.7L3 16"/></svg>""",
    "chart": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/><line x1="2" y1="20" x2="22" y2="20"/></svg>""",
    "message": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>""",
    "shield": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>""",
    "microscope": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 18h8"/><path d="M3 22h18"/><path d="M14 22a7 7 0 1 0 0-14h-1"/><path d="M9 14h2"/><path d="M9 12a2 2 0 0 1-2-2V6h6v4a2 2 0 0 1-2 2z"/><path d="M12 6V3a1 1 0 0 0-1-1H9a1 1 0 0 0-1 1v3"/></svg>""",
}

def icon(name, color="currentColor", size=16):
    svg = ICONS.get(name, "")
    return svg.replace('stroke="currentColor"', f'stroke="{color}"').replace('width="16" height="16"', f'width="{size}" height="{size}"').replace('width="18" height="18"', f'width="{size}" height="{size}"').replace('width="20" height="20"', f'width="{size}" height="{size}"').replace('width="14" height="14"', f'width="{size}" height="{size}"').replace('width="15" height="15"', f'width="{size}" height="{size}"').replace('width="11" height="11"', f'width="{size}" height="{size}"').replace('width="13" height="13"', f'width="{size}" height="{size}"')

# ══════════════════════════════════════════════════════════════
# GEMINI CONFIG
# ══════════════════════════════════════════════════════════════
_api_key = os.environ.get("GEMINI_API_KEY", "").strip()
if not _api_key:
    st.error("GEMINI_API_KEY not set. Go to Manage App > Secrets.")
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
    "scan_history": [], "uploaded_images": [],
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

if not st.session_state.scan_history:
    st.session_state.scan_history = [
        {"crop": "Tomato", "disease": "Late Blight", "conf": 92, "lang": "Hindi", "date": "28/03/2026 09:20", "severity": "severe", "shared": "Private"},
        {"crop": "Wheat", "disease": "Loose Smut", "conf": 85, "lang": "Punjabi", "date": "28/03/2026 06:10", "severity": "moderate", "shared": "Extension team"},
        {"crop": "Rice", "disease": "Brown Spot", "conf": 78, "lang": "Bengali", "date": "27/03/2026 03:55", "severity": "mild", "shared": "Field team"},
        {"crop": "Potato", "disease": "Early Blight", "conf": 88, "lang": "English", "date": "26/03/2026 11:30", "severity": "moderate", "shared": "Private"},
        {"crop": "Chilli", "disease": "Anthracnose", "conf": 71, "lang": "Telugu", "date": "25/03/2026 08:15", "severity": "mild", "shared": "Private"},
    ]

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
    if c >= 80: return "pill-green"
    if c >= 60: return "pill-gold"
    return "pill-red"

def conf_color(c):
    if c >= 80: return "#30d158"
    if c >= 60: return "#ffd60a"
    return "#ff453a"

def dot_cls(c):
    if c >= 80: return "dot-green"
    if c >= 60: return "dot-gold"
    return "dot-red"

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
    fn = "Helvetica"; bf = "Helvetica-Bold"
    try:
        if os.path.exists(FREESANS_R):
            if "FreeSans" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("FreeSans", FREESANS_R))
                pdfmetrics.registerFont(TTFont("FreeSans-Bold", FREESANS_B))
            fn, bf = "FreeSans", "FreeSans-Bold"
    except: pass

    result = d.get("result", {}); plant = d.get("plant_type","Unknown")
    disease = result.get("disease_name","Unknown"); severity = result.get("severity","unknown").title()
    conf = result.get("confidence",0); region = d.get("region",""); soil = d.get("soil","")
    infected = d.get("infected_count",0); total = d.get("total_plants",100)
    loss_pct = calc_loss_pct(d.get("severity", severity.lower()), infected, total)

    GREEN = colors.HexColor("#248a3d"); LT_GREEN = colors.HexColor("#e6f5ea")
    DARK = colors.HexColor("#1a1a1a"); GRAY = colors.HexColor("#6e6e73")

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
    story.append(P("KisanAI — Plant Disease Report", 17, bold=True, color=GREEN, align="CENTER", sa=3))
    story.append(P(datetime.now().strftime("%d %B %Y  |  %I:%M %p"), 8, color=GRAY, align="CENTER", sa=6))
    story.append(HRFlowable(width="100%", thickness=1.5, color=GREEN, spaceAfter=8))

    c1,c2,c3,c4 = W*.18, W*.32, W*.18, W*.32
    def row(k1,v1,k2="",v2=""):
        return [P(k1,bold=True,color=GREEN), P(str(v1)), P(k2,bold=True,color=GREEN) if k2 else P(""), P(str(v2)) if v2 else P("")]
    summary = [row("Plant",plant,"Region",region), row("Disease",disease,"Soil",soil),
               row("Severity",severity,"Confidence",f"{conf}%"), row("Infected",f"{infected}/{total}","Yield Loss",f"{loss_pct}%")]
    t = Table(summary, colWidths=[c1,c2,c3,c4])
    t.setStyle(TableStyle([("ROWBACKGROUNDS",(0,0),(-1,-1),[LT_GREEN,colors.white]),
                            ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#cccccc")),
                            ("VALIGN",(0,0),(-1,-1),"TOP"),("TOPPADDING",(0,0),(-1,-1),5),
                            ("BOTTOMPADDING",(0,0),(-1,-1),5),("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5)]))
    story.append(t)

    def ttbl(items, ttype, hc, lc_):
        rows = [[P("Treatment",bold=True,color=colors.white,size=9), P("Quantity",bold=True,color=colors.white,size=9), P("Price (Rs.)",bold=True,color=colors.white,size=9)]]
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
        story += sec("Immediate Actions")
        for i,a in enumerate(result["immediate_action"],1): story.append(P(f"{i}.  {a}",9,sa=4))
    if result.get("organic_treatments"):
        story += sec("Organic Treatments"); ttbl(result["organic_treatments"],"organic",GREEN,LT_GREEN)
    if result.get("chemical_treatments"):
        story += sec("Chemical Treatments"); ttbl(result["chemical_treatments"],"chemical",colors.HexColor("#1a5896"),colors.HexColor("#e8f0f8"))
    if result.get("prevention_long_term"):
        story += sec("Prevention")
        for p in result["prevention_long_term"][:5]: story.append(P(f"  {p}",9,sa=4))
    if result.get("plant_specific_notes"):
        story += sec("Notes"); story.append(P(result["plant_specific_notes"],9,color=DARK))
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=LT_GREEN))
    story.append(P(f"Generated by KisanAI  {datetime.now().strftime('%d/%m/%Y')}", 7, color=GRAY, align="CENTER", sa=0))
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
              f"Use Rs. for currency. Be concise and practical.\n{ctx}Question: {question}")
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
    st.html(f"""
    <div style="padding:20px 12px 16px;border-bottom:1px solid rgba(255,255,255,0.07);margin-bottom:14px;">
      <div style="display:flex;align-items:center;gap:9px;">
        <div style="width:32px;height:32px;border-radius:9px;
                    background:linear-gradient(135deg,#248a3d,#4cd964);
                    display:flex;align-items:center;justify-content:center;color:#fff;">
          {icon("leaf", "#fff", 16)}
        </div>
        <div>
          <div style="font-family:'DM Sans',sans-serif;font-size:1rem;font-weight:700;color:#f2f2f7;letter-spacing:-0.01em;">KisanAI</div>
          <div style="font-size:0.62rem;color:#30d158;letter-spacing:0.1em;text-transform:uppercase;font-weight:500;">Plant Doctor</div>
        </div>
      </div>
    </div>""")

    st.html('<div style="font-size:0.62rem;color:#48484a;text-transform:uppercase;letter-spacing:0.12em;padding:0 12px;margin-bottom:6px;font-weight:600;">Diagnose</div>')

    pages = [
        ("Home", "dashboard", "grid"),
        ("Upload photo", "diagnose", "camera"),
        ("History", "results", "history"),
        ("Saved scans", "fieldlog", "star"),
        ("Archived", "languages", "archive"),
    ]

    for label, pid, ic in pages:
        is_active = st.session_state.page == pid
        bg = "rgba(255,255,255,0.06)" if is_active else "transparent"
        color = "#f2f2f7" if is_active else "#8e8e93"
        st.html(f"""<div style="background:{bg};border-radius:8px;padding:8px 12px;margin:1px 6px;
                    font-size:0.83rem;color:{color};display:flex;align-items:center;gap:9px;font-weight:{'500' if is_active else '400'};">
                    <span style="color:{color};opacity:0.8;">{icon(ic, color, 15)}</span>{label}
                    {'<span style="margin-left:auto;font-size:0.65rem;background:rgba(255,255,255,0.08);border-radius:99px;padding:1px 7px;color:#8e8e93;">2</span>' if label == 'History' else ''}
                </div>""")
        if st.button(label, key=f"nav_{pid}", use_container_width=True):
            st.session_state.page = pid
            st.rerun()

    st.html('<div style="height:18px;"></div>')
    st.html('<div style="font-size:0.62rem;color:#48484a;text-transform:uppercase;letter-spacing:0.12em;padding:0 12px;margin-bottom:6px;font-weight:600;">Shared advice</div>')
    st.html(f"""<div style="padding:7px 12px;margin:1px 6px;font-size:0.83rem;color:#8e8e93;display:flex;align-items:center;gap:9px;">
        {icon("users","#8e8e93",14)} Extension team</div>""")
    st.html(f"""<div style="padding:7px 12px;margin:1px 6px;font-size:0.83rem;color:#8e8e93;display:flex;align-items:center;gap:9px;">
        {icon("book","#8e8e93",14)} Training</div>""")

    st.html('<div style="height:20px;"></div>')
    st.html('<div style="font-size:0.62rem;color:#48484a;text-transform:uppercase;letter-spacing:0.12em;padding:0 12px;margin-bottom:8px;font-weight:600;">Language</div>')
    chosen_lang = st.selectbox("Language", list(LANGUAGES.keys()),
                                index=list(LANGUAGES.keys()).index(st.session_state.lang),
                                label_visibility="collapsed", key="lang_sel_sb")
    if chosen_lang != st.session_state.lang:
        st.session_state.lang = chosen_lang
        st.session_state.lang_code = LANGUAGES[chosen_lang]
        st.rerun()

    st.html("""<div style="margin-top:16px;padding:10px 12px;border-top:1px solid rgba(255,255,255,0.07);">
      <div style="display:flex;align-items:center;justify-content:space-between;">
        <div style="display:flex;align-items:center;gap:6px;">
          <div style="width:6px;height:6px;border-radius:50%;background:#30d158;"></div>
          <span style="font-size:0.7rem;color:#8e8e93;">Model active</span>
        </div>
        <span style="font-size:0.7rem;color:#48484a;">v2.5-flash</span>
      </div>
    </div>""")

    st.html("""<div style="padding:8px 12px 16px;">
      <div style="background:linear-gradient(135deg,#248a3d,#1a6e30);border-radius:10px;padding:12px;text-align:center;cursor:pointer;">
        <div style="font-size:0.78rem;font-weight:700;color:#fff;letter-spacing:0.02em;">Scan</div>
      </div>
    </div>""")

# ══════════════════════════════════════════════════════════════
# TOPBAR COMPONENT
# ══════════════════════════════════════════════════════════════
def render_topbar(title, icon_name="grid"):
    st.html(f"""<div class="topbar">
      <div class="page-title">
        <span style="color:#8e8e93;">{icon(icon_name, "#8e8e93", 18)}</span>
        {title}
      </div>
      <div class="topbar-search">
        <span style="color:#8e8e93;flex-shrink:0;">{icon("search","#8e8e93",14)}</span>
        <input class="topbar-search-input" placeholder="Search crops or disease" disabled>
      </div>
      <div class="topbar-actions">
        <div class="topbar-icon-btn">{icon("help","#8e8e93",14)}</div>
        <div class="topbar-icon-btn">{icon("bell","#8e8e93",14)}</div>
        <div class="topbar-icon-btn">{icon("settings","#8e8e93",14)}</div>
        <div class="topbar-avatar">YA</div>
      </div>
    </div>""")

# ══════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════
if st.session_state.page == "dashboard":

    render_topbar("Dashboard", "grid")

    diag = st.session_state.last_diagnosis
    total_scans = len(st.session_state.scan_history)
    last_conf = diag.get("confidence", 0) if diag else 0
    last_disease = diag.get("disease_name", "—") if diag else "—"
    last_plant = diag.get("plant_type", "—") if diag else "—"
    avg_conf = int(sum(h["conf"] for h in st.session_state.scan_history) / max(len(st.session_state.scan_history),1))

    # Diagnosis results section (like the top card row in Uizard)
    st.html('<div class="sec-hd">Diagnosis results</div>')

    rc1, rc2, rc3, rc4 = st.columns(4)
    result_cards = [
        (rc1, "camera", "Preview", "1 photo", f"Detected: {last_disease[:18] if diag else 'No scan yet'}", None),
        (rc2, "edit", "Treatment plan", "Chemical & cultural", f"Est. cost: Rs. 1,200", None),
        (rc3, "calculator", "ROI calculator", "Interactive", "Projected profit: Rs. 9,500", None),
        (rc4, "file-text", "Guides", "Printable PDFs", "Local vendors list", None),
    ]
    for col, ic, title, sub, meta, _ in result_cards:
        with col:
            col.html(f"""<div class="result-card">
              <div class="result-card-thumb result-card-thumb-placeholder">
                <div style="color:#48484a;">{icon(ic, "#48484a", 28)}</div>
              </div>
              <div class="result-card-title">{title}</div>
              <div class="result-card-sub">{sub}</div>
              <div class="result-card-meta">{meta}</div>
            </div>""")

    # Quick actions — with leaf image thumbnails like Uizard
    st.html('<div class="sec-hd">KisanAI — Quick Actions</div>')

    qa1, qa2, qa3, qa4 = st.columns(4)

    with qa1:
        qa1.html(f"""<div class="qa-card">
          <div class="qa-card-thumb" style="background:linear-gradient(135deg,#1a2e1c,#2a4a2e);display:flex;align-items:center;justify-content:center;">
            <div style="text-align:center;">
              <div style="color:rgba(76,217,100,0.6);margin-bottom:8px;">{icon("camera","rgba(76,217,100,0.6)",32)}</div>
              <div style="font-size:0.7rem;color:rgba(255,255,255,0.3);font-weight:500;">Drag or capture a leaf</div>
            </div>
          </div>
          <div class="qa-card-title">Upload leaf photo</div>
          <div class="qa-card-desc">Upload a clear leaf photo for instant AI-powered diagnosis with confidence score.</div>
        </div>""")
        if st.button("Upload leaf photo", key="qa_upload", use_container_width=True):
            st.session_state.page = "diagnose"; st.rerun()

    with qa2:
        qa2.html(f"""<div class="qa-card">
          <div class="qa-card-thumb" style="background:linear-gradient(135deg,#1a1e2e,#2a3048);display:flex;align-items:center;justify-content:center;">
            <div style="text-align:center;">
              <div style="color:rgba(10,132,255,0.6);margin-bottom:8px;">{icon("bug","rgba(10,132,255,0.6)",32)}</div>
              <div style="font-size:0.7rem;color:rgba(255,255,255,0.3);font-weight:500;">Instant diagnosis</div>
            </div>
          </div>
          <div class="qa-card-title">Instant diagnosis</div>
          <div class="qa-card-desc">KisanAI uses Gemini vision models for fast, explainable plant disease diagnosis.</div>
        </div>""")
        if st.button("Download report.pdf", key="qa_diag", use_container_width=True):
            st.session_state.page = "diagnose"; st.rerun()

    with qa3:
        thumb_bg = "background:linear-gradient(135deg,#1a2a1a,#2a3e2a);"
        if diag:
            thumb_content = f"""<div style="text-align:center;">
              <div style="color:rgba(76,217,100,0.7);margin-bottom:6px;">{icon("leaf","rgba(76,217,100,0.7)",28)}</div>
              <div style="font-size:0.72rem;color:rgba(255,255,255,0.5);font-weight:500;">{diag.get('plant_type','—')}</div>
              <div style="font-size:0.64rem;color:rgba(255,255,255,0.25);margin-top:2px;">{diag.get('confidence',0)}% confidence</div>
            </div>"""
        else:
            thumb_content = f"""<div style="color:rgba(255,255,255,0.2);">{icon("leaf","rgba(255,255,255,0.2)",28)}</div>"""
        qa3.html(f"""<div class="qa-card">
          <div class="qa-card-thumb" style="{thumb_bg}display:flex;align-items:center;justify-content:center;">
            {thumb_content}
          </div>
          <div class="qa-card-title">{'leaf_sample.jpg' if diag else 'No scan yet'}</div>
          <div class="qa-card-desc">{'Last diagnosed: ' + diag.get('disease_name','—') if diag else 'Upload a leaf photo to get started.'}</div>
        </div>""")

    with qa4:
        qa4.html(f"""<div class="qa-card">
          <div class="qa-card-thumb" style="background:linear-gradient(135deg,#2a1a1e,#3a2428);display:flex;align-items:center;justify-content:center;">
            <div style="text-align:center;">
              <div style="color:rgba(255,69,58,0.5);margin-bottom:6px;">{icon("camera","rgba(255,69,58,0.5)",28)}</div>
              <div style="font-size:0.7rem;color:rgba(255,255,255,0.3);">Tomato crop</div>
              <div style="font-size:0.62rem;color:rgba(255,255,255,0.15);margin-top:2px;">Late blight · 92%</div>
            </div>
          </div>
          <div class="qa-card-title">Use webcam capture</div>
          <div class="qa-card-desc">Instant diagnosis from device camera. Shows disease, confidence, annotated image.</div>
        </div>""")
        st.button("Use webcam capture", key="qa_webcam", use_container_width=True)

    # Confidence trend
    import json as _json
    history = st.session_state.scan_history
    if history:
        labels = [h["crop"] for h in history[-5:]]
        data   = [h["conf"]  for h in history[-5:]]
        chart_html = f"""
        <div style="background:var(--card,#2c2c2e);border:1px solid rgba(255,255,255,0.07);
                    border-radius:12px;padding:18px 20px;margin-bottom:4px;">
          <div style="font-size:0.7rem;color:#8e8e93;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:14px;font-weight:600;">Confidence Trend</div>
          <canvas id="confChart" style="width:100%;height:120px;display:block;"></canvas>
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
                borderColor: '#30d158',
                backgroundColor: 'rgba(48,209,88,0.06)',
                borderWidth: 1.5,
                pointBackgroundColor: '#30d158',
                pointBorderColor: '#2c2c2e',
                pointBorderWidth: 2,
                pointRadius: 4,
                tension: 0.4,
                fill: true,
              }}]
            }},
            options: {{
              responsive: true,
              maintainAspectRatio: false,
              plugins: {{ legend: {{ display: false }} }},
              scales: {{
                x: {{ ticks: {{ color: '#8e8e93', font: {{ size: 10, family: 'DM Sans' }} }}, grid: {{ color: 'rgba(255,255,255,0.04)' }}, border: {{ display: false }} }},
                y: {{ min: 0, max: 100, ticks: {{ color: '#8e8e93', font: {{ size: 10, family: 'DM Sans' }} }},
                       grid: {{ color: 'rgba(255,255,255,0.04)' }}, border: {{ display: false }} }}
              }}
            }}
          }});
        }})();
        </script>"""
        st.html(chart_html)

    # Recent diagnoses table
    st.html(f"""<div class="sec-hd">Recent diagnoses
      <span style="font-size:0.7rem;color:#8e8e93;font-weight:400;display:flex;align-items:center;gap:4px;">
        {icon("chevron-right","#8e8e93",12)} View all
      </span>
    </div>""")

    header_html = """<div style="background:var(--card,#2c2c2e);border:1px solid rgba(255,255,255,0.07);border-radius:12px;overflow:hidden;">
    <table class="diag-table" style="margin:0;">
    <thead><tr>
      <th style="padding-left:20px;">Crop</th>
      <th>Disease</th>
      <th>Confidence</th>
      <th>Language</th>
      <th>Date</th>
      <th>Shared</th>
      <th>Action</th>
    </tr></thead><tbody>"""
    rows_html = ""
    for h in st.session_state.scan_history:
        dc = dot_cls(h["conf"])
        cc = conf_chip_cls(h["conf"])
        share_icon = icon("lock","#8e8e93",11) if h["shared"] == "Private" else icon("users-sm","#8e8e93",11)
        action_icon = icon("download","#8e8e93",13) if h["shared"] == "Private" else icon("share","#8e8e93",13)
        rows_html += f"""<tr>
          <td style="padding-left:20px;">
            <div class="cell-with-icon">
              <div class="status-dot {dc}"></div>
              <div class="cell-icon">{icon("leaf","#8e8e93",12)}</div>
              {h['crop']}
            </div>
          </td>
          <td>{h['disease']}</td>
          <td><span class="conf-pill {cc}">{h['conf']}%</span></td>
          <td style="color:var(--t2,#8e8e93);">{h['lang']}</td>
          <td style="color:var(--t2,#8e8e93);font-size:0.78rem;">{h['date']}</td>
          <td><span class="share-pill">{share_icon} {h['shared']}</span></td>
          <td><div class="tbl-action-btn">{action_icon}</div></td>
        </tr>"""
    st.html(header_html + rows_html + "</tbody></table></div>")

# ══════════════════════════════════════════════════════════════
# PAGE: UPLOAD & DIAGNOSE
# ══════════════════════════════════════════════════════════════
elif st.session_state.page == "diagnose":

    render_topbar("Upload & Diagnose", "camera")

    left_col, right_col = st.columns([3, 2])

    with left_col:
        st.html('<div class="info-title">Upload leaf photos</div>')
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
                    col.html(f'<div style="font-size:0.68rem;color:#8e8e93;text-align:center;margin-top:4px;">'
                            f'{uploaded[i].name[:20]}</div>')

        st.html(f"""<div class="info-c" style="margin-top:14px;">
          <div class="info-title">Photo Tips</div>
          <div style="font-size:0.78rem;color:#8e8e93;line-height:1.8;">
            {icon("chevron-right","#30d158",12)} Capture leaf margins and veins clearly<br>
            {icon("chevron-right","#30d158",12)} Include a reference for scale when possible<br>
            {icon("chevron-right","#30d158",12)} Upload multiple angles for uncertain cases
          </div>
        </div>""")

    with right_col:
        st.html('<div class="info-title">Session Settings</div>')

        plant_opts = ["Auto-detect from image"] + sorted(list(PLANT_COMMON_DISEASES.keys())) + ["Type manually..."]
        sel_plant = st.selectbox("Crop Type", plant_opts, label_visibility="visible", key="plant_sel_d")
        if sel_plant == "Type manually...":
            cp = st.text_input("Enter plant name", placeholder="e.g. Papaya, Jackfruit...", key="custom_plant_d")
            chosen_plant = cp.strip() if cp and cp.strip() else None
        elif sel_plant == "Auto-detect from image":
            chosen_plant = "AUTO"
            st.html('<div style="font-size:0.74rem;color:#30d158;padding:4px 0;">AI will detect crop from photo</div>')
        else:
            chosen_plant = sel_plant

        region_opts = ["Auto-detect"] + REGIONS
        sel_region = st.selectbox("Region", region_opts, label_visibility="visible", key="region_d")
        region = sel_region if sel_region != "Auto-detect" else "AUTO"

        soil_opts = ["Auto-detect"] + SOIL_TYPES + ["Type manually..."]
        sel_soil = st.selectbox("Soil Type", soil_opts, label_visibility="visible", key="soil_d")
        if sel_soil == "Type manually...":
            cs = st.text_input("Soil type", placeholder="e.g. Sandy loam...", key="custom_soil_d")
            soil = cs.strip() if cs and cs.strip() else "Unknown"
        elif sel_soil == "Auto-detect":
            soil = "AUTO"
        else:
            soil = sel_soil

        st.html('<div style="height:6px;"></div>')
        lang_for_diag = st.selectbox("Output language", list(LANGUAGES.keys()),
                                      index=list(LANGUAGES.keys()).index(st.session_state.lang),
                                      label_visibility="visible", key="lang_diag")

        nc, tc = st.columns(2)
        with nc: infected_n = st.number_input("Infected plants", min_value=1, value=10, step=1, key="inf_n")
        with tc: total_n = st.number_input("Total plants", min_value=1, value=100, step=10, key="tot_n")

        st.html('<div style="height:10px;"></div>')
        can_diag = bool(uploaded and chosen_plant)
        if uploaded and not chosen_plant:
            st.html('<div style="font-size:0.78rem;color:#ffd60a;padding:6px 0;">Select a crop or choose Auto-detect</div>')

        if can_diag:
            if st.button("Diagnose Now", use_container_width=True, key="diag_btn"):
                with st.spinner("Analysing with Gemini Vision..."):
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
                                st.success(f"Detected: {actual_plant}  {actual_region}  {actual_soil}")

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

        st.html(f"""<div style="font-size:0.7rem;color:#48484a;margin-top:12px;line-height:1.65;padding:10px 12px;
                    background:rgba(255,255,255,0.02);border-radius:8px;border:1px solid rgba(255,255,255,0.06);
                    display:flex;align-items:flex-start;gap:8px;">
          <span style="flex-shrink:0;margin-top:1px;">{icon("lock","#48484a",12)}</span>
          Images processed for model inference and deleted after 30 days.
        </div>""")

# ══════════════════════════════════════════════════════════════
# PAGE: DIAGNOSIS RESULTS
# ══════════════════════════════════════════════════════════════
elif st.session_state.page == "results":

    render_topbar("Diagnosis Results", "microscope")

    diag = st.session_state.last_diagnosis
    if not diag:
        st.html('<div style="padding:60px;text-align:center;color:#8e8e93;">No diagnosis yet. Upload a leaf photo first.</div>')
        if st.button("Go to Upload", key="go_upload"):
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

        act1, act2, act3, act4 = st.columns(4)
        with act1:
            lc_d = diag.get("lang_code","en")
            try:
                pdf_bytes = generate_pdf_report(diag, lc_d)
                st.download_button("Download PDF Report",
                                   data=pdf_bytes,
                                   file_name=f"KisanAI_{plant}.pdf",
                                   mime="application/pdf", key="res_pdf",
                                   use_container_width=True)
            except Exception as e:
                st.error(f"PDF error: {e}")
        with act2:
            if st.button("Ask KisanAI", key="goto_chat", use_container_width=True):
                st.session_state.page = "fieldlog"; st.rerun()
        with act3:
            if st.button("New Scan", key="new_scan", use_container_width=True):
                st.session_state.page = "diagnose"; st.rerun()
        with act4:
            if st.button("Dashboard", key="goto_dash", use_container_width=True):
                st.session_state.page = "dashboard"; st.rerun()

        st.html("<div style='height:14px;'></div>")

        sev_b = sev_cls(severity); type_b = type_cls(dtype)
        sev_label = "Severe" if "severe" in severity.lower() else "Moderate" if "moderate" in severity.lower() else "Mild" if "mild" in severity.lower() else "Healthy"

        st.html(f"""
        <div class="diag-hero">
          <div class="diag-title">{disease}</div>
          <div class="badge-row">
            <span class="badge {sev_b}">{sev_label}</span>
            <span class="badge {type_b}">{dtype}</span>
            <span class="badge b-green">{plant}</span>
            <span class="badge b-blue">{diag.get('region','')}</span>
            <span class="badge b-gray">{diag.get('soil','')}</span>
          </div>
          <div class="diag-conf-row">
            <span style="font-size:0.68rem;color:#8e8e93;text-transform:uppercase;letter-spacing:0.08em;font-weight:500;">AI Confidence</span>
            <div class="conf-bar-bg"><div class="conf-bar-fill" style="width:{conf}%;background:{conf_c};"></div></div>
            <span style="font-size:0.84rem;font-weight:700;color:{conf_c};font-family:'DM Mono',monospace;">{conf}%</span>
          </div>
        </div>""")

        s1,s2,s3,s4 = st.columns(4)
        for col, lbl, val, clr in [
            (s1,"Infected Plants",str(infected),"#30d158"),
            (s2,"Total Plants",str(total_p),"#f2f2f7"),
            (s3,"Yield Loss",f"{loss_pct}%","#ff453a"),
            (s4,"Confidence",f"{conf}%",conf_c),
        ]:
            with col: col.html(f'<div class="stat-c"><div class="stat-v" style="color:{clr};">{val}</div><div class="stat-l">{lbl}</div></div>')

        st.html("<div style='height:12px;'></div>")

        lc1, lc2 = st.columns(2)
        with lc1:
            st.html('<div class="info-title">Immediate Actions</div>')
            for i,a in enumerate(result.get("immediate_action",[]),1):
                st.html(f'<div class="act-item"><div class="act-n">{i}</div><div>{a}</div></div>')
            if result.get("symptoms"):
                st.html('<div class="info-title" style="margin-top:14px;">Symptoms Observed</div>')
                for s in result.get("symptoms",[]):
                    st.html(f'<div style="padding:3px 0;font-size:0.83rem;color:#8e8e93;">  {s}</div>')
        with lc2:
            st.html('<div class="info-title">Probable Causes</div>')
            for c in result.get("probable_causes",[]):
                st.html(f'<div style="padding:3px 0;font-size:0.83rem;color:#8e8e93;">  {c}</div>')
            if result.get("differential_diagnosis"):
                st.html('<div class="info-title" style="margin-top:14px;">Other Possibilities</div>')
                for dd in result.get("differential_diagnosis",[]):
                    st.html(f'<div style="padding:3px 0;font-size:0.83rem;color:#8e8e93;">  {dd}</div>')

        st.html("<div style='height:10px;'></div>")

        t1, t2 = st.columns(2)
        org_total = 0; chem_total = 0
        with t1:
            st.html('<div class="info-title">Organic Treatments</div>')
            for t in result.get("organic_treatments",[]):
                if not isinstance(t,str): continue
                n = normalize_name(t); info = get_treatment_info("organic",n)
                org_total += info["cost"]
                st.html(f'''<div class="treat-r">
                  <div><div class="treat-n">{n}</div>
                  <div class="treat-d">{info["quantity"]}  ·  {info["dilution"]}</div></div>
                  <div class="treat-p">Rs. {info["cost"]}</div></div>''')

        with t2:
            st.html('<div class="info-title">Chemical Treatments</div>')
            for t in result.get("chemical_treatments",[]):
                if not isinstance(t,str): continue
                n = normalize_name(t); info = get_treatment_info("chemical",n)
                chem_total += info["cost"]
                st.html(f'''<div class="treat-r">
                  <div><div class="treat-n">{n}</div>
                  <div class="treat-d">{info["quantity"]}  ·  {info["dilution"]}</div></div>
                  <div class="treat-p">Rs. {info["cost"]}</div></div>''')

        yield_val = 1000 * 40
        pot_loss = int(yield_val * loss_pct / 100)
        org_roi = int((pot_loss-org_total)/max(org_total,1)*100) if org_total else 0
        chem_roi = int((pot_loss-chem_total)/max(chem_total,1)*100) if chem_total else 0
        oc = "#30d158" if org_roi>=chem_roi else "#8e8e93"; cc_c = "#0a84ff" if chem_roi>org_roi else "#8e8e93"

        st.html("<div style='height:10px;'></div>")
        st.html('<div class="info-title">Cost & ROI — per 100 plants</div>')
        r1,r2 = st.columns(2)
        r1.html(f'<div class="stat-c"><div class="stat-v" style="color:{oc};font-size:1.15rem;">Rs. {org_total}</div><div class="stat-l">Organic Cost  ·  ROI {org_roi}%</div></div>')
        r2.html(f'<div class="stat-c"><div class="stat-v" style="color:{cc_c};font-size:1.15rem;">Rs. {chem_total}</div><div class="stat-l">Chemical Cost  ·  ROI {chem_roi}%</div></div>')

        if result.get("prevention_long_term"):
            st.html("<div style='height:10px;'></div>")
            st.html('<div class="info-title">Long-term Prevention</div>')
            for p in result.get("prevention_long_term",[]):
                st.html(f'<div class="act-item" style="background:rgba(10,132,255,0.03);border-color:rgba(10,132,255,0.1);">'
                        f'<div style="color:#0a84ff;flex-shrink:0;">{icon("shield","#0a84ff",14)}</div>{p}</div>')

        if result.get("plant_specific_notes"):
            st.html("<div style='height:10px;'></div>")
            st.html('<div class="info-title">Plant Notes</div>')
            st.html(f'<div class="info-c"><div style="font-size:0.84rem;color:#8e8e93;line-height:1.65;">{result["plant_specific_notes"]}</div></div>')

        should_treat = result.get("should_treat", True)
        treat_reason = result.get("treat_reason","")
        if should_treat:
            st.html(f'<div class="verdict">Treat immediately. {treat_reason}</div>')
        else:
            st.html(f'<div class="verdict" style="border-left-color:#ffd60a;color:#ffd60a;">Monitor closely. {treat_reason}</div>')

# ══════════════════════════════════════════════════════════════
# PAGE: FIELD LOG & TREATMENT
# ══════════════════════════════════════════════════════════════
elif st.session_state.page == "fieldlog":

    render_topbar("Field Log & Treatment Planner", "star")

    tab1, tab2, tab3 = st.tabs(["KisanAI Chat", "Crop Rotation", "Cost & ROI"])

    with tab1:
        diag = st.session_state.last_diagnosis
        if diag:
            st.html(f'''<div class="info-c" style="margin-bottom:14px;">
              <div class="info-title">Diagnosis Context</div>
              <div style="display:flex;gap:24px;flex-wrap:wrap;font-size:0.83rem;">
                <span style="color:#f2f2f7;font-weight:600;">{diag.get("plant_type")}</span>
                <span style="color:#8e8e93;">{diag.get("disease_name")}</span>
                <span style="color:#8e8e93;">{diag.get("severity","").title()}</span>
                <span style="color:#8e8e93;font-family:'DM Mono',monospace;">{diag.get("confidence",0)}% confidence</span>
              </div></div>''')
        else:
            st.html('<div style="font-size:0.82rem;color:#ffd60a;padding:8px 12px;margin-bottom:10px;background:rgba(255,214,10,0.05);border:1px solid rgba(255,214,10,0.15);border-radius:8px;">No diagnosis yet — answers will be general</div>')

        cc = st.columns([5,1])
        with cc[1]:
            if st.button("Clear", key="clear_chat"):
                st.session_state.chat_messages = []; st.rerun()

        if not st.session_state.chat_messages:
            st.html(f"""<div class="chat-wrap">
              <div class="msg-bot">
                <div class="av av-b">{icon("leaf","#fff",12)}</div>
                <div class="bub bub-b">Hello! I'm KisanAI. Ask me about disease treatment, prevention, crop rotation, cost calculations, or any farming question.</div>
              </div>
            </div>""")
        else:
            parts = ['<div class="chat-wrap">']
            for m in st.session_state.chat_messages[-30:]:
                if m["role"] == "user":
                    parts.append(f'<div class="msg-usr"><div class="av av-u">U</div><div class="bub bub-u">{m["content"]}</div></div>')
                else:
                    parts.append(f'<div class="msg-bot"><div class="av av-b">K</div><div class="bub bub-b" style="white-space:pre-line;">{m["content"]}</div></div>')
            parts.append("</div>")
            st.html("".join(parts))

        st.html("<div style='height:8px;'></div>")
        ic2, bc = st.columns([6,1])
        with ic2:
            user_text = st.text_input("msg", placeholder="Ask about your crop, disease, treatment...",
                                       label_visibility="collapsed", key="chat_input")
        with bc:
            send = st.button("Send", key="send_btn", use_container_width=True)
        if send and user_text.strip():
            st.session_state.chat_messages.append({"role":"user","content":user_text.strip()})
            try:
                ans = get_kisan_response(user_text.strip(), st.session_state.last_diagnosis)
                st.session_state.chat_messages.append({"role":"bot","content":ans})
            except Exception as e:
                st.session_state.chat_messages.append({"role":"bot","content":f"Error: {e}"})
            st.rerun()

    with tab2:
        diag = st.session_state.last_diagnosis
        default_plant = diag["plant_type"] if diag and diag.get("plant_type") else None

        ri1, ri2 = st.columns(2)
        with ri1:
            st.html('<div class="info-title">Current Crop</div>')
            use_last = False
            if default_plant:
                use_last = st.checkbox(f"Use diagnosed: {default_plant}", value=True, key="use_last")
            if use_last and default_plant:
                plant_rot = default_plant
                st.html(f'<div style="font-size:0.78rem;color:#30d158;padding:4px 0;">Using {plant_rot}</div>')
            else:
                opts = sorted(list(PLANT_COMMON_DISEASES.keys())) + ["Other (type below)"]
                sel = st.selectbox("Select crop", opts, label_visibility="collapsed", key="rot_sel")
                if sel == "Other (type below)":
                    plant_rot = st.text_input("Crop name", placeholder="e.g. Banana, Mango...", label_visibility="collapsed", key="rot_custom")
                else:
                    plant_rot = sel
        with ri2:
            st.html('<div class="info-title">Field Details</div>')
            region_rot = st.selectbox("Region", REGIONS, label_visibility="collapsed", key="rot_region")
            soil_rot = st.selectbox("Soil Type", SOIL_TYPES, label_visibility="collapsed", key="rot_soil")

        if st.button("Generate Rotation Plan", use_container_width=True, key="gen_rot"):
            if plant_rot:
                with st.spinner(f"Generating rotation plan for {plant_rot}..."):
                    r = get_rotation_plan(plant_rot, region_rot, soil_rot)
                    st.session_state.crop_rotation_result = {"plant_type":plant_rot,"rotations":r.get("rotations",[]),"info":r.get("info",{}),"region":region_rot,"soil":soil_rot}
            else: st.warning("Please select or enter a plant name.")

        rr = st.session_state.crop_rotation_result
        if rr:
            st.html("<div style='height:10px;'></div>")
            st.html('<div class="info-title">3-Year Rotation Strategy</div>')
            rots = rr["rotations"]; info_d = rr["info"]
            rc1,rc2,rc3 = st.columns(3)
            for col,yr,crop,desc in [
                (rc1,"Year 1 — Now",rr["plant_type"],info_d.get(rr["plant_type"],"Primary crop.")[:80]),
                (rc2,"Year 2 — Next",rots[0] if rots else "—",info_d.get(rots[0],"")[:80] if rots else ""),
                (rc3,"Year 3 — Third",rots[1] if len(rots)>1 else "—",info_d.get(rots[1],"")[:80] if len(rots)>1 else ""),
            ]:
                with col: col.html(f'<div class="rot-c"><div class="rot-yr">{yr}</div><div class="rot-crop">{crop}</div><div class="rot-desc">{desc}</div></div>')

    with tab3:
        diag = st.session_state.last_diagnosis
        if not diag:
            st.html('<div style="color:#ffd60a;font-size:0.85rem;padding:12px;background:rgba(255,214,10,0.05);border:1px solid rgba(255,214,10,0.15);border-radius:8px;">Run a diagnosis first to calculate ROI.</div>')
        else:
            plant_name = diag.get("plant_type","Unknown"); disease_name = diag.get("disease_name","Unknown")
            infected_count = diag.get("infected_count",50); total_plants = diag.get("total_plants",100)
            sev = diag.get("severity","moderate"); result = diag.get("result",{})

            dm1,dm2,dm3,dm4,dm5 = st.columns(5)
            for col,lbl,val in [(dm1,"Plant",plant_name),(dm2,"Disease",disease_name[:12]+"..." if len(disease_name)>12 else disease_name),(dm3,"Severity",sev.title()),(dm4,"Confidence",f'{diag.get("confidence",0)}%'),(dm5,"Infected",str(infected_count))]:
                with col: col.html(f'<div class="stat-c"><div class="stat-v" style="font-size:0.9rem;">{val}</div><div class="stat-l">{lbl}</div></div>')

            st.html("<div style='height:12px;'></div>")
            t_choice = st.radio("Treatment type", ["Organic","Chemical"], horizontal=True, key="roi_type")
            sel_type = "organic" if t_choice=="Organic" else "chemical"
            treat_list = result.get(f"{'organic' if sel_type=='organic' else 'chemical'}_treatments",[])
            treat_names = [normalize_name(t) for t in treat_list if isinstance(t,str)]
            total_treat = 300
            if treat_names:
                sel_t = st.selectbox("Select treatment", treat_names, key="roi_treat")
                ti = get_treatment_info(sel_type, sel_t)
                total_treat = int(ti["cost"] * max(infected_count,1) / 100)
                st.html(f'<div style="font-size:0.76rem;color:#30d158;padding:4px 0;">Estimated Rs. {total_treat} for {infected_count} plants  ·  {ti["quantity"]}</div>')

            ci1,ci2,ci3,ci4 = st.columns(4)
            with ci1: org_c_in = st.number_input("Organic cost (Rs.)", value=total_treat if sel_type=="organic" else 0, min_value=0, step=100, key="roi_org")
            with ci2: chem_c_in = st.number_input("Chemical cost (Rs.)", value=total_treat if sel_type=="chemical" else 0, min_value=0, step=100, key="roi_chem")
            with ci3: yield_kg = st.number_input("Yield (kg)", value=1000, min_value=100, step=100, key="roi_yield")
            with ci4: mkt = st.number_input("Price (Rs./kg)", value=40, min_value=1, step=5, key="roi_mkt")

            if st.button("Calculate ROI", use_container_width=True, key="calc_roi"):
                al = calc_loss_pct(sev, infected_count, total_plants)
                tr = int(yield_kg * mkt); pl = int(tr * al / 100)
                oroi = int((pl-org_c_in)/max(org_c_in,1)*100) if org_c_in>0 else 0
                croi = int((pl-chem_c_in)/max(chem_c_in,1)*100) if chem_c_in>0 else 0
                st.session_state.cost_roi_result = {"total":tr,"loss":pl,"loss_pct":al,"org_cost":org_c_in,"chem_cost":chem_c_in,"org_roi":oroi,"chem_roi":croi}

            roi = st.session_state.cost_roi_result
            if roi:
                rm1,rm2,rm3 = st.columns(3)
                rm1.html(f'<div class="stat-c"><div class="stat-v" style="font-family:\'DM Mono\',monospace;">Rs. {roi["total"]:,}</div><div class="stat-l">Total Yield Value</div></div>')
                rm2.html(f'<div class="stat-c"><div class="stat-v" style="color:#ff453a;font-family:\'DM Mono\',monospace;">Rs. {roi["loss"]:,}</div><div class="stat-l">Loss if Untreated ({roi["loss_pct"]}%)</div></div>')
                rm3.html(f'<div class="stat-c"><div class="stat-v" style="font-family:\'DM Mono\',monospace;">{infected_count}/{total_plants}</div><div class="stat-l">Infected / Total</div></div>')
                rr1,rr2 = st.columns(2)
                oc = "#30d158" if roi["org_roi"]>=roi["chem_roi"] else "#8e8e93"
                xc = "#0a84ff" if roi["chem_roi"]>roi["org_roi"] else "#8e8e93"
                rr1.html(f'<div class="stat-c"><div class="stat-v" style="color:{oc};font-family:\'DM Mono\',monospace;">{roi["org_roi"]}%</div><div class="stat-l">Organic ROI  ·  Cost Rs. {roi["org_cost"]:,}</div></div>')
                rr2.html(f'<div class="stat-c"><div class="stat-v" style="color:{xc};font-family:\'DM Mono\',monospace;">{roi["chem_roi"]}%</div><div class="stat-l">Chemical ROI  ·  Cost Rs. {roi["chem_cost"]:,}</div></div>')
                best = "Organic" if roi["org_roi"]>=roi["chem_roi"] else "Chemical"
                st.html(f'<div class="verdict">{best} treatment provides better ROI. Estimated savings vs no treatment: Rs. {roi["loss"]:,}</div>')

# ══════════════════════════════════════════════════════════════
# PAGE: LANGUAGES & SUPPORT
# ══════════════════════════════════════════════════════════════
elif st.session_state.page == "languages":

    render_topbar("Languages & Support", "globe")

    lc1, lc2 = st.columns([3,2])

    with lc1:
        st.html('<div class="info-title">Select Language</div>')
        st.html('<div style="font-size:0.8rem;color:#8e8e93;margin-bottom:14px;">Choose from English and 12 Indian languages.</div>')

        lang_grid = [
            ("English","en","Upload · Diagnose · Results"),
            ("Hindi","hi","Upload · Nidan · Parinaam"),
            ("Punjabi","pa","Upload · Nidan · Natije"),
            ("Bengali","bn","Upload · Nirnay · Phalaphal"),
            ("Telugu","te","Upload · Nirnayanam · Phalit"),
            ("Tamil","ta","Upload · Kandari · Mudivu"),
            ("Kannada","kn","Upload · Nirdharana · Phalitaansha"),
            ("Marathi","mr","Upload · Nidan · Nikal"),
            ("Gujarati","gu","Upload · Nidan · Parinaam"),
            ("Urdu","ur","Upload · Tashkhees · Nataij"),
            ("Malayalam","ml","Upload · Nirnayam · Phalankal"),
            ("Odia","or","Upload · Nidana · Phala"),
        ]

        lg1, lg2 = st.columns(2)
        for i, (name, code, sample) in enumerate(lang_grid):
            is_sel = st.session_state.lang_code == code
            bg = "rgba(76,217,100,0.06)" if is_sel else "var(--card,#2c2c2e)"
            border = "rgba(76,217,100,0.2)" if is_sel else "rgba(255,255,255,0.07)"
            col = lg1 if i % 2 == 0 else lg2
            col.html(f"""<div style="background:{bg};border:1px solid {border};border-radius:10px;
                         padding:11px 14px;margin:4px 0;">
              <div style="font-size:0.86rem;font-weight:600;color:#f2f2f7;">{name}</div>
              <div style="font-size:0.7rem;color:#8e8e93;margin-top:2px;">{sample}</div>
            </div>""")

        st.html("<div style='height:10px;'></div>")
        new_lang = st.selectbox("Switch app language", list(LANGUAGES.keys()),
                                 index=list(LANGUAGES.keys()).index(st.session_state.lang),
                                 label_visibility="visible", key="lang_switch")
        if st.button("Apply Language", key="apply_lang", use_container_width=True):
            st.session_state.lang = new_lang
            st.session_state.lang_code = LANGUAGES[new_lang]
            st.success(f"Language changed to {new_lang}"); st.rerun()

        st.html("<div style='height:18px;'></div>")
        st.html('<div class="info-title">Photo Troubleshooting</div>')
        t1,t2,t3 = st.columns(3)
        for col,ok,label,desc in [
            (t1,True,"Clear focus","Even lighting, close-up"),
            (t2,False,"Avoid direct sun","Washed-out details"),
            (t3,False,"Avoid blur","Use steady surface"),
        ]:
            clr = "#30d158" if ok else "#ff453a"
            with col: col.html(f'<div class="rot-c"><div style="font-size:0.7rem;font-weight:700;color:{clr};text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px;">{"Pass" if ok else "Fail"}</div><div class="rot-crop" style="font-size:0.82rem;">{label}</div><div class="rot-desc">{desc}</div></div>')

    with lc2:
        st.html('<div class="info-title">Multilingual FAQs</div>')
        faqs = [
            ("What symptoms indicate a fungal infection?", "Circular spots, yellowing between veins, fuzzy or powdery growth on leaf surfaces."),
            ("How to safely apply recommended treatments?", "Wear gloves, follow dilution guide precisely, spray in early morning to reduce evaporation."),
            ("Local regulations for pesticide use?", "Check state-specific approved chemicals list. Always read the product label before application."),
        ]
        for q, a in faqs:
            with st.expander(q):
                st.html(f'<div style="font-size:0.83rem;color:#8e8e93;line-height:1.65;">{a}</div>')

        st.html("<div style='height:14px;'></div>")
        st.html('<div class="info-title">Toll-free Helpline</div>')
        st.html("""<div class="info-c">
          <div style="font-size:1.15rem;font-weight:700;color:#30d158;margin-bottom:4px;font-family:'DM Mono',monospace;">1800-11-KISAN</div>
          <div style="font-size:0.76rem;color:#8e8e93;line-height:1.6;">Available Mon–Sat 8:00–18:00<br>Hindi, Punjabi, English, regional languages</div>
        </div>""")

        st.html("<div style='height:14px;'></div>")
        st.html('<div class="info-title">WhatsApp Support</div>')
        st.html("""<div class="info-c">
          <div style="font-size:0.8rem;color:#8e8e93;margin-bottom:12px;">Quick templates to start a conversation in your language</div>
          <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.07);border-radius:8px;padding:10px 12px;margin:6px 0;">
            <div style="font-size:0.76rem;font-weight:600;color:#f2f2f7;">Report leaf spots</div>
            <div style="font-size:0.7rem;color:#8e8e93;margin-top:3px;">My tomato leaves have brown circular spots with yellow edges...</div>
          </div>
          <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.07);border-radius:8px;padding:10px 12px;margin:6px 0;">
            <div style="font-size:0.76rem;font-weight:600;color:#f2f2f7;">Request agronomist visit</div>
            <div style="font-size:0.7rem;color:#8e8e93;margin-top:3px;">Please send an agronomist to inspect my wheat field...</div>
          </div>
        </div>""")

        st.html("<div style='height:14px;'></div>")
        st.html('<div class="info-title">How Gemini Powers Diagnosis</div>')
        st.html("""<div class="info-c">
          <div style="font-size:0.78rem;color:#8e8e93;line-height:1.75;">
            <span style="color:#f2f2f7;font-weight:600;">Input</span>  Leaf photo + crop type + growth stage<br>
            <span style="color:#f2f2f7;font-weight:600;">Process</span>  Gemini vision model + language grounding<br>
            <span style="color:#f2f2f7;font-weight:600;">Output</span>  Disease name, confidence score, treatment steps
          </div>
        </div>""")

        st.html("<div style='height:14px;'></div>")
        st.html('<div class="info-title">Feedback</div>')
        rating = st.radio("Rating", [1,2,3,4,5], horizontal=True, key="fb_rating")
        feedback = st.text_area("What was wrong? (optional)", placeholder="e.g. Symptom mislabeled...", label_visibility="visible", key="fb_text")
        if st.button("Submit Feedback", key="submit_fb", use_container_width=True):
            st.success("Thank you. Your feedback helps improve KisanAI.")
