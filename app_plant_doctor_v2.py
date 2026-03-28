import streamlit as st
try:
    import google.generativeai as genai
except ModuleNotFoundError:
    st.error("Missing: google-generativeai. Add to requirements.txt.")
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
    "mr": "मराठीत उत्तर द्या. सोप्या भाषेत.", "te": "తెలుగులో సమాధానం ఇవ్వండి.",
    "ta": "தமிழில் பதில் சொல்லுங்கள்.", "kn": "ಕನ್ನಡದಲ್ಲಿ ಉತ್ತರ ನೀಡಿ.",
    "bn": "বাংলায় উত্তর দিন।", "gu": "ગુજરાતીમાં જવાબ આપો.",
    "or": "ଓଡ଼ିଆରେ ଉତ୍ତର ଦିଅ।", "ml": "മലയാളത്തിൽ ഉത്തരം നൽകുക.",
    "as": "অসমীয়াত উত্তৰ দিয়ক।", "ur": "اردو میں جواب دیں۔ سادہ زبان میں۔",
}

# ══════════════════════════════════════════════════════════════
# DATABASES
# ══════════════════════════════════════════════════════════════
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
        "Deltamethrin (Decis)": {"cost": 220, "quantity": "50ml per 100 plants", "dilution": "0.005% solution"},
        "Imidacloprid (Confidor)": {"cost": 350, "quantity": "80ml per 100 plants", "dilution": "0.008% solution"},
        "Tebuconazole (Folicur)": {"cost": 320, "quantity": "120ml per 100 plants", "dilution": "0.05% solution"},
        "Thiamethoxam (Actara)": {"cost": 290, "quantity": "100g per 100 plants", "dilution": "0.04% solution"},
        "Azoxystrobin (Amistar)": {"cost": 650, "quantity": "80ml per 100 plants", "dilution": "0.02% solution"},
        "Hexaconazole (Contaf Plus)": {"cost": 350, "quantity": "100ml per 100 plants", "dilution": "0.04% solution"},
        "Metalaxyl + Mancozeb (Ridomil Gold)": {"cost": 190, "quantity": "100g per 100 plants", "dilution": "0.25% solution"},
        "Propiconazole (Tilt)": {"cost": 190, "quantity": "100ml per 100 plants", "dilution": "0.1% solution"},
    },
}

CROP_ROTATION_DATA = {
    "Tomato": {"rotations": ["Beans", "Cabbage", "Cucumber"], "info": {"Tomato": "High-value solanaceae. Susceptible to blight & wilt. Needs 3+ year rotation.", "Beans": "Nitrogen-fixing legume. Breaks disease cycle.", "Cabbage": "Brassica family. Controls tomato diseases.", "Cucumber": "No common diseases with tomato. Completes rotation."}},
    "Rose": {"rotations": ["Marigold", "Chrysanthemum", "Herbs"], "info": {"Rose": "Susceptible to black spot, powdery mildew, rust.", "Marigold": "Natural pest repellent. Attracts beneficial insects.", "Chrysanthemum": "Different pest profile. Breaks rose pathogen cycle.", "Herbs": "Basil, rosemary improve soil health."}},
    "Apple": {"rotations": ["Legume Cover Crops", "Grasses", "Berries"], "info": {"Apple": "Perennial. Susceptible to scab, fire blight. 4-5 year rotation.", "Legume Cover Crops": "Nitrogen fixation. Breaks pathogen cycle.", "Grasses": "Erosion control. Beneficial insect habitat.", "Berries": "Different root depth. Income during off-year."}},
    "Lettuce": {"rotations": ["Spinach", "Broccoli", "Cauliflower"], "info": {"Lettuce": "Cool-season leafy crop. Quick 60-70 day cycle.", "Spinach": "Resistant to lettuce diseases. Tolerates cold.", "Broccoli": "Different pest profile. Breaks disease cycle.", "Cauliflower": "Completes 3-crop rotation cycle."}},
    "Grape": {"rotations": ["Legume Cover Crops", "Cereals", "Vegetables"], "info": {"Grape": "Perennial vine. Powdery mildew, phylloxera concerns.", "Legume Cover Crops": "Nitrogen replenishment. Disease elimination.", "Cereals": "Wheat/maize. Nematode cycle break.", "Vegetables": "Re-establishes soil microbiology."}},
    "Pepper": {"rotations": ["Onion", "Garlic", "Spinach"], "info": {"Pepper": "Solanaceae. Anthracnose, bacterial wilt issues.", "Onion": "Allium family. Breaks solanaceae cycle.", "Garlic": "Natural pest deterrent. Soil antimicrobial.", "Spinach": "No common pepper diseases. Spring/fall compatible."}},
    "Cucumber": {"rotations": ["Maize", "Okra", "Legumes"], "info": {"Cucumber": "Cucurbitaceae. 2-3 year rotation suggested.", "Maize": "Different root system. Strong market demand.", "Okra": "No overlapping pests. Heat-tolerant.", "Legumes": "Nitrogen restoration. Disease-free break."}},
    "Strawberry": {"rotations": ["Garlic", "Onion", "Leafy Greens"], "info": {"Strawberry": "Low-growing perennial. 3-year bed rotation needed.", "Garlic": "Antimicrobial soil activity. Excellent succession crop.", "Onion": "Deters strawberry pests.", "Leafy Greens": "Quick cycle. Utilizes residual nutrients."}},
    "Corn": {"rotations": ["Soybean", "Pulses", "Oilseeds"], "info": {"Corn": "Heavy nitrogen feeder. 3+ year rotation critical.", "Soybean": "Nitrogen-fixing. Reduces fertilizer needs 40-50%.", "Pulses": "Chickpea/lentil. High market value.", "Oilseeds": "Sunflower/safflower. Income diversification."}},
    "Potato": {"rotations": ["Peas", "Mustard", "Cereals"], "info": {"Potato": "Solanaceae. Late blight, nematodes. 4-year rotation.", "Peas": "Nitrogen-fixing. Breaks potato pathogen cycle.", "Mustard": "Biofumigation. Natural nematode control.", "Cereals": "Wheat/barley. Completes disease-break cycle."}},
}

REGIONS = ["North India", "South India", "East India", "West India", "Central India", "Northeast India"]
SOIL_TYPES = ["Black Soil (Regur)", "Red Soil", "Laterite Soil", "Alluvial Soil", "Sandy Soil", "Clay Soil", "Loamy Soil"]
MARKET_FOCUS = ["Stable essentials", "High-value cash crops", "Low input / low risk"]

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

# ══════════════════════════════════════════════════════════════
# PREMIUM CSS — Inspired by Image 1 but elevated
# ══════════════════════════════════════════════════════════════
st.html("""
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
:root {
  --bg:        #0c110d;
  --bg2:       #111a12;
  --bg3:       #172019;
  --card:      rgba(255,255,255,0.035);
  --border:    rgba(80,200,100,0.14);
  --border2:   rgba(80,200,100,0.28);
  --green:     #4ade80;
  --green2:    #22c55e;
  --green-dim: rgba(74,222,128,0.12);
  --gold:      #fbbf24;
  --red:       #f87171;
  --blue:      #60a5fa;
  --purple:    #c084fc;
  --text:      #e2ede3;
  --text2:     #7da882;
  --text3:     #3d5e42;
  --radius:    14px;
  --radius-lg: 20px;
  --radius-xl: 28px;
  --shadow:    0 8px 40px rgba(0,0,0,0.6);
}

*, *::before, *::after { box-sizing: border-box; }

html, body, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="block-container"],
.main { background: var(--bg) !important; font-family: 'DM Sans', sans-serif !important; color: var(--text) !important; }

#MainMenu, footer, header,
[data-testid="stDecoration"],
[data-testid="stSidebarNav"],
[data-testid="collapsedControl"],
.stDeployButton { display: none !important; }

[data-testid="block-container"] { max-width: 1080px !important; padding: 0 20px 80px !important; }

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(74,222,128,0.3); border-radius: 4px; }

/* ── TOP NAV ── */
.topnav {
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 0 14px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 0;
}
.nav-brand { display: flex; align-items: center; gap: 10px; }
.nav-logo {
  width: 38px; height: 38px; border-radius: 10px;
  background: linear-gradient(135deg, #16a34a, #4ade80);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.2rem; box-shadow: 0 4px 16px rgba(74,222,128,0.3);
}
.nav-title { font-family: 'Syne', sans-serif; font-size: 1.25rem; font-weight: 800; color: var(--text); }
.nav-sub { font-size: 0.72rem; color: var(--text2); letter-spacing: 0.08em; text-transform: uppercase; }

/* ── HERO HEADER ── */
.hero {
  position: relative; overflow: hidden;
  background: linear-gradient(160deg, #0d2214 0%, #0a160c 60%, var(--bg) 100%);
  border: 1px solid var(--border2);
  border-radius: var(--radius-xl);
  padding: 52px 36px 44px;
  margin: 20px 0 24px;
  text-align: center;
}
.hero::before {
  content: ''; position: absolute; inset: 0;
  background-image: radial-gradient(rgba(74,222,128,0.1) 1px, transparent 1px);
  background-size: 26px 26px; pointer-events: none;
}
.hero::after {
  content: ''; position: absolute;
  top: -60px; left: 50%; transform: translateX(-50%);
  width: 500px; height: 220px;
  background: radial-gradient(ellipse, rgba(74,222,128,0.18) 0%, transparent 70%);
  pointer-events: none;
}
.hero-badge {
  display: inline-flex; align-items: center; gap: 6px;
  background: rgba(74,222,128,0.1); border: 1px solid rgba(74,222,128,0.25);
  border-radius: 99px; padding: 5px 14px;
  font-size: 0.72rem; font-weight: 600; color: var(--green);
  letter-spacing: 0.1em; text-transform: uppercase;
  margin-bottom: 20px; position: relative; z-index: 1;
}
.hero-title {
  font-family: 'Syne', sans-serif;
  font-size: clamp(2.2rem, 5vw, 3.4rem);
  font-weight: 800; color: #fff;
  letter-spacing: -0.02em; line-height: 1.1;
  margin-bottom: 12px; position: relative; z-index: 1;
  text-shadow: 0 0 60px rgba(74,222,128,0.35);
}
.hero-title .hl { color: var(--green); }
.hero-sub {
  font-size: 1rem; color: var(--text2); font-weight: 400;
  max-width: 520px; margin: 0 auto; position: relative; z-index: 1;
  line-height: 1.65;
}

/* ── FEATURE PILLS ── */
.pills-row {
  display: flex; gap: 10px; flex-wrap: wrap;
  justify-content: center; margin: 24px 0;
}
.pill {
  display: inline-flex; align-items: center; gap: 7px;
  background: var(--card); border: 1px solid var(--border);
  border-radius: 99px; padding: 8px 18px;
  font-size: 0.82rem; font-weight: 600; color: var(--text2);
  cursor: default; transition: all 0.2s ease;
}
.pill:hover { background: var(--green-dim); border-color: var(--border2); color: var(--green); }
.pill-icon { font-size: 1rem; }

/* ── PAGE TABS ── */
.page-tabs {
  display: flex; gap: 4px;
  background: var(--card); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 4px;
  margin-bottom: 24px;
}
.page-tab {
  flex: 1; text-align: center; padding: 9px 12px;
  border-radius: 10px; font-size: 0.83rem; font-weight: 600;
  color: var(--text2); cursor: pointer;
  transition: all 0.18s ease;
}
.page-tab.active {
  background: linear-gradient(135deg, #16a34a, #15803d);
  color: #fff; box-shadow: 0 4px 14px rgba(22,163,74,0.35);
}

/* ── CARDS ── */
.card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: var(--radius-lg); padding: 22px 24px; margin: 12px 0;
  backdrop-filter: blur(10px);
}
.card-dashed {
  background: var(--card); border: 1.5px dashed var(--border2);
  border-radius: var(--radius-lg); padding: 22px 24px; margin: 12px 0;
  transition: border-color 0.2s ease;
}
.card-dashed:hover { border-color: var(--green); }

/* ── SECTION LABEL ── */
.sec-label {
  font-size: 0.68rem; font-weight: 700; letter-spacing: 0.14em;
  text-transform: uppercase; color: var(--green2);
  margin-bottom: 12px; display: flex; align-items: center; gap: 8px;
}
.sec-label::after { content: ''; flex: 1; height: 1px; background: var(--border); }

/* ── DISEASE CARD ── */
.disease-hero {
  position: relative; overflow: hidden;
  background: linear-gradient(135deg, #0d2214 0%, #122b18 100%);
  border: 1px solid rgba(74,222,128,0.35); border-radius: var(--radius-xl);
  padding: 28px 26px; margin-bottom: 20px;
}
.disease-hero::before {
  content: ''; position: absolute; top: -50px; right: -50px;
  width: 220px; height: 220px; border-radius: 50%;
  background: radial-gradient(circle, rgba(74,222,128,0.18) 0%, transparent 70%);
}
.disease-name {
  font-family: 'Syne', sans-serif;
  font-size: clamp(1.6rem, 3vw, 2.2rem); font-weight: 800;
  color: #fff; margin-bottom: 12px;
  text-shadow: 0 2px 12px rgba(0,0,0,0.4); position: relative; z-index: 1;
}
.badge-row { display: flex; gap: 8px; flex-wrap: wrap; position: relative; z-index: 1; }
.badge {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 4px 12px; border-radius: 99px;
  font-size: 0.72rem; font-weight: 700; letter-spacing: 0.06em;
  text-transform: uppercase;
}
.badge-healthy  { background: rgba(74,222,128,0.15); color: #4ade80; border: 1px solid rgba(74,222,128,0.3); }
.badge-mild     { background: rgba(96,165,250,0.15); color: #60a5fa; border: 1px solid rgba(96,165,250,0.3); }
.badge-moderate { background: rgba(251,191,36,0.15); color: #fbbf24; border: 1px solid rgba(251,191,36,0.3); }
.badge-severe   { background: rgba(248,113,113,0.15); color: #f87171; border: 1px solid rgba(248,113,113,0.3); }
.badge-green  { background: rgba(74,222,128,0.12); color: #4ade80; border: 1px solid rgba(74,222,128,0.2); }
.badge-blue   { background: rgba(96,165,250,0.12); color: #60a5fa; border: 1px solid rgba(96,165,250,0.2); }
.badge-purple { background: rgba(192,132,252,0.12); color: #c084fc; border: 1px solid rgba(192,132,252,0.2); }
.badge-amber  { background: rgba(251,191,36,0.12); color: #fbbf24; border: 1px solid rgba(251,191,36,0.2); }
.badge-red    { background: rgba(248,113,113,0.12); color: #f87171; border: 1px solid rgba(248,113,113,0.2); }

/* ── CONF BAR ── */
.conf-bar-bg { background: rgba(255,255,255,0.07); border-radius: 99px; height: 6px; overflow: hidden; margin: 8px 0 4px; }
.conf-bar { height: 100%; border-radius: 99px; }

/* ── TREATMENT ROW ── */
.treat-row {
  display: flex; align-items: flex-start; justify-content: space-between;
  background: rgba(255,255,255,0.03); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 12px 16px; margin: 6px 0; gap: 10px;
  transition: border-color 0.18s ease;
}
.treat-row:hover { border-color: var(--border2); }
.treat-name { font-size: 0.9rem; font-weight: 600; color: var(--text); }
.treat-detail { font-size: 0.75rem; color: var(--text2); margin-top: 3px; }
.treat-price {
  font-size: 0.8rem; font-weight: 700; color: var(--green);
  background: rgba(74,222,128,0.1); border: 1px solid rgba(74,222,128,0.2);
  border-radius: 99px; padding: 3px 10px; white-space: nowrap;
}

/* ── ACTION ITEM ── */
.action-item {
  display: flex; gap: 12px; align-items: flex-start;
  background: rgba(74,222,128,0.05); border: 1px solid rgba(74,222,128,0.12);
  border-radius: var(--radius); padding: 10px 14px; margin: 5px 0;
  font-size: 0.88rem; color: var(--text); line-height: 1.5;
}
.action-num {
  flex-shrink: 0; width: 22px; height: 22px; border-radius: 7px;
  background: var(--green2); color: #0c110d;
  font-size: 0.7rem; font-weight: 800;
  display: flex; align-items: center; justify-content: center; margin-top: 1px;
}

/* ── STAT CARD ── */
.stat-card {
  background: var(--card); border: 1px solid var(--border);
  border-top: 2px solid var(--green2);
  border-radius: var(--radius); padding: 18px 16px; text-align: center;
  transition: all 0.2s ease;
}
.stat-card:hover { border-top-color: var(--green); box-shadow: 0 6px 24px rgba(74,222,128,0.12); transform: translateY(-2px); }
.stat-val {
  font-family: 'Syne', sans-serif; font-size: 1.9rem; font-weight: 800;
  color: var(--green); margin: 6px 0; letter-spacing: -0.02em;
}
.stat-lbl { font-size: 0.65rem; color: var(--text3); font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em; }

/* ── ROTATION CARD ── */
.rot-card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: var(--radius-lg); padding: 20px 18px; text-align: center;
  transition: all 0.2s ease;
}
.rot-card:hover { border-color: var(--border2); transform: translateY(-2px); box-shadow: 0 8px 28px rgba(74,222,128,0.1); }
.rot-yr { font-size: 0.65rem; font-weight: 800; color: var(--gold); text-transform: uppercase; letter-spacing: 0.2em; margin-bottom: 8px; }
.rot-crop { font-family: 'Syne', sans-serif; font-size: 1.2rem; font-weight: 700; color: var(--text); margin: 6px 0; }
.rot-desc { font-size: 0.8rem; color: var(--text2); line-height: 1.55; margin-top: 8px; }

/* ── CHAT ── */
.chat-box { display: flex; flex-direction: column; gap: 10px; padding: 8px 0; }
.msg-bot, .msg-user { display: flex; align-items: flex-start; gap: 10px; animation: fadeUp 0.28s ease; }
.msg-user { flex-direction: row-reverse; }
@keyframes fadeUp { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
.av { width: 32px; height: 32px; border-radius: 9px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; font-size: 0.95rem; font-weight: 700; }
.av-bot { background: linear-gradient(135deg, var(--green2), #16a34a); color: #0c110d; box-shadow: 0 2px 10px rgba(74,222,128,0.3); }
.av-user { background: rgba(255,255,255,0.08); border: 1px solid var(--border2); color: var(--text); }
.bubble { max-width: 80%; padding: 11px 15px; border-radius: var(--radius); font-size: 0.9rem; line-height: 1.65; }
.bubble-bot { background: rgba(255,255,255,0.04); border: 1px solid var(--border); color: var(--text); border-top-left-radius: 4px; }
.bubble-user { background: linear-gradient(135deg, rgba(74,222,128,0.16), rgba(74,222,128,0.08)); border: 1px solid rgba(74,222,128,0.22); color: var(--text); border-top-right-radius: 4px; text-align: right; }

/* ── ALERT ── */
.alert-warn { background: rgba(251,191,36,0.07); border: 1px solid rgba(251,191,36,0.3); border-left: 3px solid var(--gold); border-radius: var(--radius); padding: 12px 16px; color: #fbbf24; font-size: 0.9rem; margin: 10px 0; }
.alert-ok   { background: rgba(74,222,128,0.06); border: 1px solid rgba(74,222,128,0.28); border-left: 3px solid var(--green2); border-radius: var(--radius); padding: 12px 16px; color: var(--green); font-size: 0.9rem; margin: 10px 0; }
.alert-err  { background: rgba(248,113,113,0.07); border: 1px solid rgba(248,113,113,0.3); border-left: 3px solid var(--red); border-radius: var(--radius); padding: 12px 16px; color: #f87171; font-size: 0.9rem; margin: 10px 0; }

/* ── BOTTOM INPUT BAR ── */
.input-wrap {
  position: sticky; bottom: 0;
  background: linear-gradient(to top, rgba(12,17,13,0.98) 70%, transparent);
  padding: 12px 0 6px; z-index: 100;
}

/* ── Streamlit overrides ── */
.stButton > button {
  background: linear-gradient(135deg, #16a34a, #15803d) !important;
  color: #e2ede3 !important; border: 1px solid rgba(74,222,128,0.4) !important;
  border-radius: var(--radius) !important; font-weight: 600 !important;
  font-size: 0.88rem !important; padding: 10px 22px !important;
  font-family: 'DM Sans', sans-serif !important;
  box-shadow: 0 4px 16px rgba(22,163,74,0.25) !important;
  transition: all 0.2s ease !important;
}
.stButton > button:hover { transform: translateY(-1px) !important; box-shadow: 0 6px 24px rgba(22,163,74,0.4) !important; }
.stDownloadButton > button {
  background: linear-gradient(135deg, #1e3a24, #142b19) !important;
  color: var(--green) !important; border: 1px solid rgba(74,222,128,0.35) !important;
  border-radius: var(--radius) !important; font-weight: 600 !important;
  font-size: 0.85rem !important;
}
input, textarea, [data-baseweb="input"] input {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid var(--border) !important; color: var(--text) !important;
  border-radius: var(--radius) !important; font-family: 'DM Sans', sans-serif !important;
}
input:focus, textarea:focus { border-color: var(--green2) !important; box-shadow: 0 0 0 2px rgba(74,222,128,0.15) !important; }
.stSelectbox > div > div, [data-baseweb="select"] {
  background: rgba(255,255,255,0.04) !important; border: 1px solid var(--border) !important;
  color: var(--text) !important; border-radius: var(--radius) !important;
}
[data-baseweb="popover"] { background: #111a12 !important; border: 1px solid var(--border2) !important; }
[data-baseweb="option"]:hover { background: var(--green-dim) !important; }
[data-testid="stNumberInput"] input { background: rgba(255,255,255,0.04) !important; color: var(--text) !important; }
[data-testid="stExpander"] { background: var(--card) !important; border: 1px solid var(--border) !important; border-radius: var(--radius) !important; }
.streamlit-expanderHeader { color: var(--text2) !important; }
[data-testid="stFileUploader"] { background: rgba(255,255,255,0.02) !important; border: 1.5px dashed var(--border2) !important; border-radius: var(--radius-lg) !important; }
[data-testid="stFileUploader"]:hover { border-color: var(--green2) !important; }
[data-testid="metric-container"] { background: var(--card) !important; border: 1px solid var(--border) !important; border-radius: var(--radius) !important; }
hr { border-color: var(--border) !important; }
p, label, span, div { font-family: 'DM Sans', sans-serif !important; }
h1, h2, h3, h4 { font-family: 'Syne', sans-serif !important; color: var(--text) !important; }
.stSpinner > div { border-color: var(--green2) transparent transparent transparent !important; }
[data-testid="stRadio"] label { color: var(--text) !important; }
[data-testid="stCheckbox"] label { color: var(--text) !important; }
[data-testid="stTabs"] [data-baseweb="tab-list"] { background: rgba(255,255,255,0.03) !important; border: 1px solid var(--border) !important; border-radius: var(--radius) !important; gap: 2px !important; padding: 3px !important; }
[data-testid="stTabs"] [data-baseweb="tab"] { background: transparent !important; color: var(--text2) !important; border-radius: 10px !important; font-size: 0.85rem !important; }
[data-testid="stTabs"] [aria-selected="true"] { background: linear-gradient(135deg, var(--green2), #15803d) !important; color: #fff !important; }
[data-testid="stTabs"] [data-baseweb="tab-border"] { display: none !important; }
.stAlert { border-radius: var(--radius) !important; background: rgba(255,255,255,0.04) !important; border: 1px solid var(--border) !important; }
</style>
""")

# ══════════════════════════════════════════════════════════════
# GEMINI CONFIG
# ══════════════════════════════════════════════════════════════
_api_key = os.environ.get("GEMINI_API_KEY", "").strip()
if not _api_key:
    st.html("""<div class="card" style="max-width:520px;margin:80px auto;border-color:rgba(248,113,113,0.3);">
        <div style="font-size:1.1rem;font-weight:700;color:#f87171;margin-bottom:10px;">⚠️ API Key Missing</div>
        <div style="color:var(--text2);font-size:0.9rem;line-height:1.7;">
          Set <b style="color:var(--text);">GEMINI_API_KEY</b> in Streamlit Secrets.<br><br>
          Go to Manage app → Secrets → add:<br>
          <code style="background:rgba(0,0,0,0.4);padding:4px 10px;border-radius:6px;color:#4ade80;display:inline-block;margin-top:6px;">GEMINI_API_KEY = "your-key-here"</code>
        </div></div>""")
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
    "page": "diagnosis", "lang": "English", "lang_code": "en",
    "last_diagnosis": None, "treatment_selection": None,
    "chat_messages": [], "crop_rotation_result": None,
    "cost_roi_result": None, "kisan_response": None,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

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

def resize_image(img, mw=600, mh=500):
    img.thumbnail((mw, mh), Image.Resampling.LANCZOS)
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
        if k.lower() == tl:
            return dict(v, _matched=True) if isinstance(v, dict) else {"cost": v, "quantity": "As per package", "dilution": "Follow label", "_matched": True}
    for k, v in costs.items():
        if k.lower() in tl or tl in k.lower():
            return dict(v, _matched=True) if isinstance(v, dict) else {"cost": v, "quantity": "As per package", "dilution": "Follow label", "_matched": True}
    return {"cost": 300 if ttype == "organic" else 250, "quantity": "As per package", "dilution": "Follow label", "_matched": False}

def calc_loss_pct(severity, infected, total):
    bands = {"healthy": (0, 2), "mild": (5, 15), "moderate": (20, 40), "severe": (50, 70)}
    lo, hi = bands.get((severity or "moderate").lower(), (20, 40))
    base = (lo + hi) / 2
    ratio = max(0.0, min(infected / max(total, 1), 1.0))
    return int(round(min(base * ratio, 80.0)))

def sev_badge_cls(sev):
    s = (sev or "").lower()
    if "health" in s: return "badge-healthy"
    if "mild" in s: return "badge-mild"
    if "severe" in s: return "badge-severe"
    return "badge-moderate"

def type_badge_cls(dtype):
    d = (dtype or "").lower()
    if "fungal" in d: return "badge-purple"
    if "bacterial" in d: return "badge-blue"
    if "viral" in d: return "badge-red"
    if "pest" in d: return "badge-amber"
    return "badge-green"

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

    font_name = "Helvetica"
    bold_font = "Helvetica-Bold"

    try:
        if USE_SERIF and os.path.exists(FREESERIF_R):
            if "FreeSerif" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("FreeSerif", FREESERIF_R))
                pdfmetrics.registerFont(TTFont("FreeSerif-Bold", FREESERIF_B if os.path.exists(FREESERIF_B) else FREESERIF_R))
            font_name, bold_font = "FreeSerif", "FreeSerif-Bold"
        elif os.path.exists(FREESANS_R):
            if "FreeSans" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("FreeSans", FREESANS_R))
                pdfmetrics.registerFont(TTFont("FreeSans-Bold", FREESANS_B))
            font_name, bold_font = "FreeSans", "FreeSans-Bold"
    except Exception: pass

    if font_name == "Helvetica":
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
            font_name, bold_font = "NotoSans", "NotoSans-Bold"
        except Exception: pass

    result  = d.get("result", {})
    plant   = d.get("plant_type", "Unknown")
    disease = result.get("disease_name", "Unknown")
    severity= result.get("severity", "unknown").title()
    conf    = result.get("confidence", 0)
    region  = d.get("region", "")
    soil    = d.get("soil", "")
    infected= d.get("infected_count", 0)
    total   = d.get("total_plants", 100)
    loss_pct= calc_loss_pct(d.get("severity", severity.lower()), infected, total)

    LABELS = {
        "en": dict(title="Kisan AI — Plant Disease Report", plant="Plant", disease="Disease", severity="Severity",
                   confidence="Confidence", region="Region", soil="Soil Type", infected="Infected", total="Total Plants",
                   loss="Est. Yield Loss", actions="Immediate Actions", organic="Organic Treatments",
                   chemical="Chemical Treatments", prevention="Long-term Prevention", notes="Plant-Specific Notes",
                   treatment="Treatment", qty="Quantity", price="Price (Rs.)", generated="Generated by Kisan AI"),
        "hi": dict(title="किसान AI — पौधे की बीमारी रिपोर्ट", plant="पौधा", disease="बीमारी", severity="गंभीरता",
                   confidence="विश्वास", region="क्षेत्र", soil="मिट्टी", infected="संक्रमित", total="कुल पौधे",
                   loss="उपज हानि", actions="तुरंत करें", organic="जैविक उपचार", chemical="रासायनिक उपचार",
                   prevention="दीर्घकालिक रोकथाम", notes="विशेष नोट्स",
                   treatment="उपचार", qty="मात्रा", price="कीमत (Rs.)", generated="किसान AI द्वारा"),
        "pa": dict(title="ਕਿਸਾਨ AI — ਪੌਦੇ ਦੀ ਬਿਮਾਰੀ ਰਿਪੋਰਟ", plant="ਪੌਦਾ", disease="ਬਿਮਾਰੀ", severity="ਗੰਭੀਰਤਾ",
                   confidence="ਭਰੋਸਾ", region="ਖੇਤਰ", soil="ਮਿੱਟੀ", infected="ਸੰਕਰਮਿਤ", total="ਕੁੱਲ ਪੌਦੇ",
                   loss="ਝਾੜ ਨੁਕਸਾਨ", actions="ਤੁਰੰਤ ਕਰੋ", organic="ਜੈਵਿਕ ਇਲਾਜ", chemical="ਰਸਾਇਣਕ ਇਲਾਜ",
                   prevention="ਲੰਬੇ ਸਮੇਂ ਦੀ ਰੋਕਥਾਮ", notes="ਵਿਸ਼ੇਸ਼ ਨੋਟਸ",
                   treatment="ਇਲਾਜ", qty="ਮਾਤਰਾ", price="ਕੀਮਤ (Rs.)", generated="ਕਿਸਾਨ AI ਦੁਆਰਾ"),
        "mr": dict(title="किसान AI — वनस्पती रोग अहवाल", plant="पीक", disease="रोग", severity="तीव्रता",
                   confidence="विश्वास", region="क्षेत्र", soil="माती", infected="संक्रमित", total="एकूण झाडे",
                   loss="उत्पादन नुकसान", actions="तातडीचे उपाय", organic="जैविक उपचार", chemical="रासायनिक उपचार",
                   prevention="दीर्घकालीन प्रतिबंध", notes="विशेष नोट्स",
                   treatment="उपचार", qty="प्रमाण", price="किंमत (Rs.)", generated="किसान AI द्वारे"),
        "ur": dict(title="کسان AI — پودے کی بیماری رپورٹ", plant="پودا", disease="بیماری", severity="شدت",
                   confidence="اعتماد", region="علاقہ", soil="مٹی", infected="متاثرہ", total="کل پودے",
                   loss="پیداوار نقصان", actions="فوری اقدامات", organic="نامیاتی علاج", chemical="کیمیائی علاج",
                   prevention="طویل مدتی روک تھام", notes="خصوصی نوٹس",
                   treatment="علاج", qty="مقدار", price="قیمت (Rs.)", generated="کسان AI"),
    }
    L = LABELS.get(lc, LABELS["en"])

    GREEN = colors.HexColor("#1a7a32"); LT_GREEN = colors.HexColor("#e8f5e2")
    BLUE  = colors.HexColor("#1a5896"); LT_BLUE  = colors.HexColor("#e8f0f8")
    DARK  = colors.HexColor("#1a1a1a"); GRAY     = colors.HexColor("#666666")

    def P(text, size=9, bold=False, color=DARK, align="LEFT", sa=3):
        s = ParagraphStyle("p", fontName=bold_font if bold else font_name,
                           fontSize=size, textColor=color, leading=size*1.5,
                           spaceAfter=sa, alignment={"LEFT":0,"CENTER":1,"RIGHT":2}.get(align,0), wordWrap="CJK")
        return Paragraph(str(text), s)

    def sec(t):
        return [Spacer(1, 0.25*cm), P(t, 11, bold=True, color=GREEN, sa=2),
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
        return [P(k1,bold=True,color=GREEN), P(str(v1)),
                P(k2,bold=True,color=GREEN) if k2 else P(""), P(str(v2)) if v2 else P("")]

    summary = [row(L["plant"],plant,L["region"],region), row(L["disease"],disease,L["soil"],soil),
               row(L["severity"],severity,L["confidence"],f"{conf}%"), row(L["infected"],f"{infected}/{total}",L["loss"],f"{loss_pct}%")]
    t = Table(summary, colWidths=[c1,c2,c3,c4])
    t.setStyle(TableStyle([("ROWBACKGROUNDS",(0,0),(-1,-1),[LT_GREEN,colors.white]),
                            ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#cccccc")),
                            ("VALIGN",(0,0),(-1,-1),"TOP"),("TOPPADDING",(0,0),(-1,-1),6),
                            ("BOTTOMPADDING",(0,0),(-1,-1),6),("LEFTPADDING",(0,0),(-1,-1),5),
                            ("RIGHTPADDING",(0,0),(-1,-1),5)]))
    story.append(t)

    def treat_tbl(items, ttype, hc, lc_):
        rows = [[P(L["treatment"],bold=True,color=colors.white,size=9),
                 P(L["qty"],bold=True,color=colors.white,size=9),
                 P(L["price"],bold=True,color=colors.white,size=9)]]
        for item in items:
            if not isinstance(item, str): continue
            n = normalize_name(item); info = get_treatment_info(ttype, n)
            rows.append([P(n,9), P(info["quantity"],9), P(f"Rs.{info['cost']}",9)])
        if len(rows) == 1: return
        tbl = Table(rows, colWidths=[W*.40, W*.38, W*.22])
        tbl.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),hc),
                                  ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,lc_]),
                                  ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#cccccc")),
                                  ("VALIGN",(0,0),(-1,-1),"TOP"),("TOPPADDING",(0,0),(-1,-1),6),
                                  ("BOTTOMPADDING",(0,0),(-1,-1),6),("LEFTPADDING",(0,0),(-1,-1),5),
                                  ("RIGHTPADDING",(0,0),(-1,-1),5)]))
        story.append(tbl)

    if result.get("immediate_action"):
        story += sec(f"⚡ {L['actions']}")
        for i,a in enumerate(result["immediate_action"],1): story.append(P(f"{i}.  {a}",9,sa=4))
    if result.get("organic_treatments"):
        story += sec(f"🌿 {L['organic']}"); treat_tbl(result["organic_treatments"],"organic",GREEN,LT_GREEN)
    if result.get("chemical_treatments"):
        story += sec(f"⚗️ {L['chemical']}"); treat_tbl(result["chemical_treatments"],"chemical",BLUE,LT_BLUE)
    if result.get("prevention_long_term"):
        story += sec(f"🛡️ {L['prevention']}")
        for p in result["prevention_long_term"][:5]: story.append(P(f"•  {p}",9,sa=4))
    if result.get("plant_specific_notes"):
        story += sec(f"📌 {L['notes']}"); story.append(P(result["plant_specific_notes"],9,color=DARK))

    story.append(Spacer(1, 0.6*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=LT_GREEN))
    story.append(P(f"{L['generated']}  ·  {datetime.now().strftime('%d/%m/%Y')}", 7, color=GRAY, align="CENTER", sa=0))
    doc.build(story)
    buf.seek(0)
    return buf.read()

# ══════════════════════════════════════════════════════════════
# AI HELPERS
# ══════════════════════════════════════════════════════════════
EXPERT_PROMPT = """You are an elite plant pathologist. Analyze the image of {plant_type}.
Common diseases: {common_diseases}
Region: {region}, Soil: {soil}
{lang_instruction}

CRITICAL: Respond ONLY with valid JSON, no markdown.
{{
  "disease_name": "Specific disease name or Healthy",
  "disease_type": "fungal/bacterial/viral/pest/nutrient/environmental/healthy",
  "severity": "healthy/mild/moderate/severe",
  "confidence": 85,
  "symptoms": ["symptom 1","symptom 2","symptom 3"],
  "differential_diagnosis": ["Possibility A: reason","Possibility B: reason"],
  "probable_causes": ["cause 1","cause 2"],
  "immediate_action": ["step 1","step 2","step 3"],
  "organic_treatments": ["Neem Oil Spray","Bordeaux Mixture"],
  "chemical_treatments": ["Mancozeb (Indofil)","Carbendazim (Bavistin)"],
  "prevention_long_term": ["prevention 1","prevention 2","prevention 3"],
  "plant_specific_notes": "Key notes for this plant",
  "similar_conditions": "Other conditions that look similar",
  "should_treat": true,
  "treat_reason": "One sentence reason"
}}"""

def get_kisan_response(question, diag_ctx=None):
    model = genai.GenerativeModel("gemini-2.5-flash")
    ctx = ""
    if diag_ctx:
        ctx = f"Diagnosis context: Plant={diag_ctx.get('plant_type')}, Disease={diag_ctx.get('disease_name')}, Severity={diag_ctx.get('severity')}, Confidence={diag_ctx.get('confidence')}%\n\n"
    prompt = (f"{lang_instruction}\n\nYou are Kisan AI — expert agricultural advisor for Indian farmers. "
              f"Speak simply, use ₹ for currency.\n{ctx}Farmer's question: {question}\n\n"
              f"If unrelated to farming, politely redirect. Give practical, actionable advice.")
    resp = model.generate_content(prompt)
    return resp.text.strip()

def generate_rotation_plan(plant_type, region, soil_type, market_focus):
    if plant_type in CROP_ROTATION_DATA:
        return CROP_ROTATION_DATA[plant_type]
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = f"""Agricultural expert. For {plant_type} in {region} ({soil_type}), market focus: {market_focus}.
Respond ONLY with valid JSON:
{{"rotations":["Crop1","Crop2","Crop3"],"info":{{"{plant_type}":"Info",
"Crop1":"Why after {plant_type}","Crop2":"Why follows Crop1","Crop3":"Why completes cycle"}}}}"""
    try:
        r = extract_json(model.generate_content(prompt).text)
        if r and "rotations" in r: return r
    except: pass
    return {"rotations":["Legumes","Cereals","Oilseeds"],
            "info":{plant_type:"Primary crop. Needs disease break.",
                    "Legumes":"Nitrogen-fixing. Improves soil.",
                    "Cereals":"Different nutrient profile.",
                    "Oilseeds":"Diversification crop."}}

# ══════════════════════════════════════════════════════════════
# TOP NAVIGATION
# ══════════════════════════════════════════════════════════════
nav_c1, nav_c2 = st.columns([3, 1])
with nav_c1:
    st.html("""
    <div class="topnav">
      <div class="nav-brand">
        <div class="nav-logo">🌿</div>
        <div>
          <div class="nav-title">Kisan AI</div>
          <div class="nav-sub">Plant Doctor · Powered by Gemini</div>
        </div>
      </div>
    </div>""")

with nav_c2:
    st.html("<div style='padding-top:14px;'></div>")
    chosen_lang = st.selectbox("🌐", list(LANGUAGES.keys()),
                                index=list(LANGUAGES.keys()).index(st.session_state.lang),
                                label_visibility="collapsed", key="lang_sel")
    if chosen_lang != st.session_state.lang:
        st.session_state.lang = chosen_lang
        st.session_state.lang_code = LANGUAGES[chosen_lang]
        st.rerun()

# ══════════════════════════════════════════════════════════════
# HERO HEADER (only on diagnosis page)
# ══════════════════════════════════════════════════════════════
if st.session_state.page == "diagnosis" and not st.session_state.last_diagnosis:
    st.html("""
    <div class="hero">
      <div class="hero-badge">✦ Built for Indian Farmers &nbsp;·&nbsp; Powered by Gemini 2.5 ✦</div>
      <div class="hero-title">🌿 AI Plant <span class="hl">Doctor</span></div>
      <div class="hero-sub">Upload a leaf photo · get an expert AI diagnosis · plan your treatment in your language</div>
    </div>
    <div class="pills-row">
      <div class="pill"><span class="pill-icon">🧬</span> Disease Diagnosis</div>
      <div class="pill"><span class="pill-icon">💊</span> Treatment Plans</div>
      <div class="pill"><span class="pill-icon">📊</span> Cost & ROI</div>
      <div class="pill"><span class="pill-icon">🔄</span> Crop Rotation</div>
      <div class="pill"><span class="pill-icon">🌐</span> 13 Languages</div>
    </div>""")

# ══════════════════════════════════════════════════════════════
# PAGE NAVIGATION TABS
# ══════════════════════════════════════════════════════════════
pg_cols = st.columns(4)
pages = [("diagnosis","🔬 Diagnose"), ("chat","🤖 KisanAI Chat"),
         ("rotation","🌱 Crop Rotation"), ("roi","📊 Cost & ROI")]
for i, (pid, plabel) in enumerate(pages):
    with pg_cols[i]:
        is_active = st.session_state.page == pid
        btn_style = "primary" if is_active else "secondary"
        if st.button(plabel, key=f"nav_{pid}", use_container_width=True, type=btn_style):
            st.session_state.page = pid
            st.rerun()

st.html("<div style='height:8px;'></div>")

# ══════════════════════════════════════════════════════════════
# PAGE: DISEASE DIAGNOSIS
# ══════════════════════════════════════════════════════════════
if st.session_state.page == "diagnosis":

    col_plant, col_upload = st.columns([1, 2])

    with col_plant:
        st.html('<div class="card-dashed">')
        st.html('<div class="sec-label">🌱 Select Plant</div>')
        plant_options = ["🤖 Auto-detect from image"] + sorted(list(PLANT_COMMON_DISEASES.keys())) + ["✏️ Type manually..."]
        sel_plant = st.selectbox("Plant", plant_options, label_visibility="collapsed", key="plant_sel")
        if sel_plant == "✏️ Type manually...":
            custom_plant = st.text_input("Plant name", placeholder="e.g. Papaya, Banana, Sorghum...", label_visibility="collapsed", key="custom_plant_inp")
            chosen_plant = custom_plant.strip() if custom_plant and custom_plant.strip() else None
        elif sel_plant == "🤖 Auto-detect from image":
            chosen_plant = "AUTO"
            st.html('<div class="alert-ok">📷 AI will identify the plant, region & soil from your photo</div>')
        else:
            chosen_plant = sel_plant
            if chosen_plant in PLANT_COMMON_DISEASES:
                st.html(f'<div class="alert-ok" style="font-size:0.8rem;">Common: {PLANT_COMMON_DISEASES[chosen_plant][:80]}...</div>')
        st.html("</div>")

    with col_upload:
        st.html('<div class="card-dashed">')
        st.html('<div class="sec-label">📸 Upload Leaf Photos</div>')

        region_s, soil_s = st.columns(2)
        with region_s:
            region_opts = ["🤖 Auto-detect"] + REGIONS
            sel_region = st.selectbox("Region", region_opts, label_visibility="collapsed", key="region_sel")
            region = sel_region if sel_region != "🤖 Auto-detect" else "AUTO"
        with soil_s:
            soil_opts = ["🤖 Auto-detect"] + SOIL_TYPES + ["✏️ Type manually..."]
            sel_soil = st.selectbox("Soil", soil_opts, label_visibility="collapsed", key="soil_sel")
            if sel_soil == "✏️ Type manually...":
                custom_soil = st.text_input("Soil type", placeholder="e.g. Sandy loam...", label_visibility="collapsed", key="custom_soil_inp")
                soil = custom_soil.strip() if custom_soil and custom_soil.strip() else "Unknown"
            elif sel_soil == "🤖 Auto-detect":
                soil = "AUTO"
            else:
                soil = sel_soil

        nc, tc = st.columns(2)
        with nc: infected_n = st.number_input("Infected plants", min_value=1, value=10, step=1, key="inf_n")
        with tc: total_n = st.number_input("Total plants", min_value=1, value=100, step=10, key="tot_n")

        uploaded = st.file_uploader("Drop leaf photos (up to 3)", type=["jpg","jpeg","png"],
                                     accept_multiple_files=True, label_visibility="collapsed", key="uploader")

        if uploaded:
            imgs = [Image.open(f) for f in uploaded[:3]]
            th_cols = st.columns(min(len(imgs)*3, 9))
            for i, img in enumerate(imgs):
                with th_cols[i*3]:
                    thumb = img.copy(); thumb.thumbnail((90,90), Image.Resampling.LANCZOS)
                    st.image(thumb, width=80)
                with th_cols[i*3+1]:
                    st.html(f"<div style='font-size:0.72rem;color:var(--text2);padding-top:6px;'>Photo {i+1}<br>{img.width}×{img.height}</div>")

        st.html("</div>")

    can_diag = bool(uploaded and chosen_plant)
    if uploaded and not chosen_plant:
        st.html('<div class="alert-warn">Select a plant or choose Auto-detect</div>')

    if can_diag:
        _, bcol, _ = st.columns([1,2,1])
        with bcol:
            if st.button(f"🔍 Diagnose Now", use_container_width=True, key="diag_btn"):
                with st.spinner("Analysing your plant..."):
                    try:
                        imgs = [Image.open(f) for f in uploaded[:3]]
                        need_auto = chosen_plant == "AUTO" or region == "AUTO" or soil == "AUTO"
                        actual_plant = chosen_plant; actual_region = region; actual_soil = soil

                        if need_auto:
                            dp = f"""{lang_instruction}
Look at this plant image. Identify:
1. Exact crop/plant species
2. Region of India (based on visual cues)
3. Soil type visible
CRITICAL: Respond ONLY with valid JSON:
{{"detected_plant":"Wheat","detected_region":"North India","detected_soil":"Alluvial Soil","detection_confidence":80}}"""
                            dr = extract_json(genai.GenerativeModel("gemini-2.5-flash").generate_content([dp] + [enhance_image(i.copy()) for i in imgs]).text)
                            if dr:
                                if chosen_plant == "AUTO": actual_plant = dr.get("detected_plant","Unknown Plant")
                                if region == "AUTO": actual_region = dr.get("detected_region","North India")
                                if soil == "AUTO": actual_soil = dr.get("detected_soil","Alluvial Soil")
                                st.html(f'<div class="alert-ok">🤖 Auto-detected: <b>{actual_plant}</b> · {actual_region} · {actual_soil}</div>')

                        common = PLANT_COMMON_DISEASES.get(actual_plant, "various plant diseases")
                        prompt = EXPERT_PROMPT.format(plant_type=actual_plant, common_diseases=common,
                                                       region=actual_region, soil=actual_soil,
                                                       lang_instruction=lang_instruction)
                        enhanced = [enhance_image(i.copy()) for i in imgs]
                        result = extract_json(genai.GenerativeModel("gemini-2.5-flash").generate_content([prompt] + enhanced).text)

                        if result:
                            st.session_state.last_diagnosis = {
                                "plant_type": actual_plant, "disease_name": result.get("disease_name","Unknown"),
                                "disease_type": result.get("disease_type","unknown"),
                                "severity": result.get("severity","unknown"),
                                "confidence": result.get("confidence",0),
                                "infected_count": int(infected_n), "total_plants": int(total_n),
                                "region": actual_region, "soil": actual_soil,
                                "result": result, "timestamp": datetime.now().isoformat(),
                                "lang_code": lang_code,
                            }
                            st.rerun()
                        else:
                            st.error("Could not parse AI response. Try a clearer photo.")
                    except Exception as e:
                        st.error(f"Analysis failed: {e}")

    # ── Show diagnosis result ──
    diag = st.session_state.last_diagnosis
    if diag:
        result = diag.get("result", {})
        disease = result.get("disease_name","Unknown")
        severity = result.get("severity","unknown")
        conf = result.get("confidence",0)
        dtype = result.get("disease_type","").title()
        plant = diag.get("plant_type","")
        infected = diag.get("infected_count",0)
        total_p = diag.get("total_plants",100)
        loss_pct = calc_loss_pct(severity, infected, total_p)
        conf_c = "#4ade80" if conf >= 80 else "#fbbf24" if conf >= 60 else "#f87171"

        # Disease hero
        sev_cls = sev_badge_cls(severity)
        type_cls = type_badge_cls(dtype)
        sev_icon = "✅" if "health" in severity.lower() else "🟡" if "mild" in severity.lower() else "🔴" if "severe" in severity.lower() else "🟠"

        st.html(f"""
        <div class="disease-hero">
          <div class="disease-name">{disease}</div>
          <div class="badge-row">
            <span class="badge {sev_cls}">{sev_icon} {severity.title()}</span>
            <span class="badge {type_cls}">{dtype}</span>
            <span class="badge badge-green">🌱 {plant}</span>
            <span class="badge badge-blue">📍 {diag.get('region','')}</span>
          </div>
          <div style="margin-top:16px;position:relative;z-index:1;">
            <div style="font-size:0.7rem;color:var(--text2);letter-spacing:0.08em;text-transform:uppercase;margin-bottom:4px;">Diagnosis Confidence</div>
            <div class="conf-bar-bg"><div class="conf-bar" style="width:{conf}%;background:{conf_c};"></div></div>
            <div style="font-size:0.78rem;color:{conf_c};font-weight:700;">{conf}%</div>
          </div>
        </div>""")

        # Metrics row
        mc1,mc2,mc3,mc4 = st.columns(4)
        for col, lbl, val, clr in [
            (mc1,"Infected Plants",str(infected),"var(--text)"),
            (mc2,"Total Plants",str(total_p),"var(--text)"),
            (mc3,"Yield Loss",f"{loss_pct}%","#f87171"),
            (mc4,"Confidence",f"{conf}%",conf_c)
        ]:
            with col: col.html(f'<div class="stat-card"><div class="stat-lbl">{lbl}</div><div class="stat-val" style="color:{clr};font-size:1.5rem;">{val}</div></div>')

        st.html("<div style='height:12px;'></div>")

        # Two-column detail
        lc1, lc2 = st.columns(2)
        with lc1:
            st.html('<div class="sec-label">⚡ Immediate Actions</div>')
            for i, a in enumerate(result.get("immediate_action",[]),1):
                st.html(f'<div class="action-item"><div class="action-num">{i}</div><div>{a}</div></div>')
            if result.get("symptoms"):
                st.html('<div class="sec-label" style="margin-top:16px;">🔎 Symptoms Observed</div>')
                for s in result.get("symptoms",[]):
                    st.html(f'<div style="padding:4px 0;font-size:0.87rem;color:var(--text2);">• {s}</div>')
            if result.get("differential_diagnosis"):
                st.html('<div class="sec-label" style="margin-top:16px;">🔬 Other Possibilities</div>')
                for dd in result.get("differential_diagnosis",[]):
                    st.html(f'<div style="padding:4px 0;font-size:0.84rem;color:var(--text2);">• {dd}</div>')

        with lc2:
            st.html('<div class="sec-label">📋 Probable Causes</div>')
            for c in result.get("probable_causes",[]):
                st.html(f'<div style="padding:4px 0;font-size:0.87rem;color:var(--text2);">• {c}</div>')
            if result.get("plant_specific_notes"):
                st.html('<div class="sec-label" style="margin-top:16px;">📌 Plant Notes</div>')
                st.html(f'<div class="card" style="font-size:0.87rem;color:var(--text2);line-height:1.65;">{result["plant_specific_notes"]}</div>')
            if result.get("similar_conditions"):
                st.html('<div class="sec-label" style="margin-top:16px;">🔗 Similar Conditions</div>')
                st.html(f'<div style="font-size:0.84rem;color:var(--text2);">{result["similar_conditions"]}</div>')

        # Treatments
        st.html("<div style='height:8px;'></div>")
        t1, t2 = st.columns(2)

        org_treats = result.get("organic_treatments",[])
        chem_treats = result.get("chemical_treatments",[])
        org_total = 0; chem_total = 0

        with t1:
            st.html('<div class="sec-label">🌿 Organic Treatments</div>')
            for t in org_treats:
                if not isinstance(t,str): continue
                n = normalize_name(t); info = get_treatment_info("organic",n)
                org_total += info["cost"]
                matched = "" if info.get("_matched") else '<span style="font-size:0.7rem;color:#fbbf24;"> ⚠️ est.</span>'
                st.html(f'''<div class="treat-row">
                  <div><div class="treat-name">🌿 {n}{matched}</div>
                  <div class="treat-detail">{info["quantity"]} · {info["dilution"]}</div></div>
                  <div class="treat-price">₹{info["cost"]}</div></div>''')

        with t2:
            st.html('<div class="sec-label">⚗️ Chemical Treatments</div>')
            for t in chem_treats:
                if not isinstance(t,str): continue
                n = normalize_name(t); info = get_treatment_info("chemical",n)
                chem_total += info["cost"]
                matched = "" if info.get("_matched") else '<span style="font-size:0.7rem;color:#fbbf24;"> ⚠️ est.</span>'
                st.html(f'''<div class="treat-row">
                  <div><div class="treat-name">⚗️ {n}{matched}</div>
                  <div class="treat-detail">{info["quantity"]} · {info["dilution"]}</div></div>
                  <div class="treat-price">₹{info["cost"]}</div></div>''')

        # ROI quick view
        yield_val = 1000 * 40
        potential_loss = int(yield_val * loss_pct / 100)
        org_roi = int((potential_loss - org_total) / max(org_total, 1) * 100) if org_total else 0
        chem_roi = int((potential_loss - chem_total) / max(chem_total, 1) * 100) if chem_total else 0
        org_c = "#4ade80" if org_roi >= chem_roi else "var(--text2)"
        chem_c = "#60a5fa" if chem_roi > org_roi else "var(--text2)"

        st.html("<div style='height:8px;'></div>")
        st.html('<div class="sec-label">💰 Cost & ROI (per 100 plants)</div>')
        r1,r2 = st.columns(2)
        with r1: r1.html(f'<div class="stat-card"><div class="stat-lbl">Organic Cost</div><div class="stat-val" style="color:{org_c};">₹{org_total}</div><div style="font-size:0.72rem;color:var(--text2);">ROI: {org_roi}%</div></div>')
        with r2: r2.html(f'<div class="stat-card"><div class="stat-lbl">Chemical Cost</div><div class="stat-val" style="color:{chem_c};">₹{chem_total}</div><div style="font-size:0.72rem;color:var(--text2);">ROI: {chem_roi}%</div></div>')
        st.html(f'<div style="font-size:0.75rem;color:var(--text3);margin-top:4px;">{infected} infected / {total_p} total · {loss_pct}% est. yield loss</div>')

        # Prevention
        if result.get("prevention_long_term"):
            st.html("<div style='height:8px;'></div>")
            st.html('<div class="sec-label">🛡️ Long-term Prevention</div>')
            for p in result.get("prevention_long_term",[]):
                st.html(f'<div class="action-item" style="background:rgba(96,165,250,0.05);border-color:rgba(96,165,250,0.12);">🛡️ {p}</div>')

        # Crop rotation inline preview
        if plant in CROP_ROTATION_DATA:
            st.html("<div style='height:8px;'></div>")
            st.html('<div class="sec-label">🔄 Crop Rotation Plan</div>')
            rd = CROP_ROTATION_DATA[plant]; rots = rd.get("rotations",[]); info_d = rd.get("info",{})
            rc1,rc2,rc3 = st.columns(3)
            for col, yr, crop, desc in [
                (rc1,"📌 Year 1 · Now", plant, info_d.get(plant,"")[:80]),
                (rc2, "🔄 Year 2 · Next", rots[0] if rots else "—", info_d.get(rots[0],"")[:80] if rots else ""),
                (rc3, "🌿 Year 3 · Last", rots[1] if len(rots)>1 else "—", info_d.get(rots[1],"")[:80] if len(rots)>1 else ""),
            ]:
                with col: col.html(f'<div class="rot-card"><div class="rot-yr">{yr}</div><div class="rot-crop">{crop}</div><div class="rot-desc">{desc}</div></div>')

        # Should treat verdict
        should_treat = result.get("should_treat", True)
        treat_reason = result.get("treat_reason","")
        verdict_style = "alert-ok" if should_treat else "alert-warn"
        verdict_icon = "✅" if should_treat else "💡"
        st.html(f'<div class="{verdict_style}">{verdict_icon} {"Treat immediately" if should_treat else "No treatment needed right now"}. {treat_reason}</div>')

        # PDF download
        PDF_LABELS = {
            "en":"📄 Download PDF Report","hi":"📄 PDF रिपोर्ट डाउनलोड करें","pa":"📄 PDF ਰਿਪੋਰਟ ਡਾਊਨਲੋਡ ਕਰੋ",
            "mr":"📄 PDF अहवाल डाउनलोड करा","te":"📄 PDF నివేదిక","ta":"📄 PDF அறிக்கை",
            "kn":"📄 PDF ವರದಿ","bn":"📄 PDF রিপোর্ট","gu":"📄 PDF રિપોર્ট",
            "ur":"📄 PDF رپورٹ ڈاؤنلوڈ کریں","or":"📄 PDF ରିପୋର୍ଟ","ml":"📄 PDF റിപ്പോർട്ട്","as":"📄 PDF প্ৰতিবেদন",
        }
        lc_d = diag.get("lang_code","en")
        try:
            pdf_bytes = generate_pdf_report(diag, lc_d)
            fname = f"KisanAI_{plant}_{disease.replace(' ','_')[:20]}.pdf"
            st.html("<div style='height:6px;'></div>")
            st.download_button(label=PDF_LABELS.get(lc_d,PDF_LABELS["en"]), data=pdf_bytes,
                                file_name=fname, mime="application/pdf",
                                key=f"pdf_{diag.get('timestamp','x').replace(':','_').replace('.','_')}")
        except Exception as e:
            st.error(f"PDF error: {e}")

# ══════════════════════════════════════════════════════════════
# PAGE: KISAN AI CHAT
# ══════════════════════════════════════════════════════════════
elif st.session_state.page == "chat":
    st.html("""
    <div style="padding:28px 0 16px;">
      <div style="font-family:'Syne',sans-serif;font-size:1.8rem;font-weight:800;color:var(--text);margin-bottom:6px;">🤖 KisanAI Assistant</div>
      <div style="color:var(--text2);font-size:0.9rem;">Ask anything about your crops, diseases, treatments or farming practices</div>
    </div>""")

    diag = st.session_state.last_diagnosis
    if diag:
        st.html(f'''<div class="card" style="border-left:3px solid var(--green2);margin-bottom:12px;">
          <div class="sec-label">Current Diagnosis Context</div>
          <div style="display:flex;gap:20px;flex-wrap:wrap;">
            <span>🌱 <b>{diag.get("plant_type")}</b></span>
            <span>🦠 {diag.get("disease_name")}</span>
            <span>⚠️ {diag.get("severity","").title()}</span>
            <span>📊 {diag.get("confidence",0)}% confidence</span>
          </div></div>''')
    else:
        st.html('<div class="alert-warn">No diagnosis yet. Run a diagnosis first for context-aware answers.</div>')

    cc1, cc2 = st.columns([5,1])
    with cc2:
        if st.button("🗑️ Clear", key="clear_chat", use_container_width=True):
            st.session_state.chat_messages = []
            st.rerun()

    # Welcome or chat history
    if not st.session_state.chat_messages:
        welcome_msgs = {
            "en":"🙏 Namaste! I'm your Kisan AI Plant Doctor.\n\nI can help you with:\n• 📸 Disease diagnosis from photos\n• 💊 Treatment recommendations\n• 💰 Cost & ROI calculations\n• 🔄 Crop rotation planning\n• 🌾 Any farming question\n\nAsk me anything!",
            "hi":"🙏 नमस्ते! मैं किसान AI हूं।\n\n• 📸 फोटो से बीमारी पहचान\n• 💊 इलाज की सलाह\n• 💰 लागत और मुनाफा\n• 🔄 फसल चक्र\n\nकुछ भी पूछें!",
            "pa":"🙏 ਸਤ ਸ੍ਰੀ ਅਕਾਲ! ਕਿਸਾਨ AI ਹਾਂ।\n\n• 📸 ਬਿਮਾਰੀ ਪਛਾਣ\n• 💊 ਇਲਾਜ ਦੀ ਸਲਾਹ\n• 💰 ਲਾਗਤ ਅਤੇ ਮੁਨਾਫਾ\n\nਕੁਝ ਵੀ ਪੁੱਛੋ!",
            "ur":"🙏 آداب! میں کسان AI ہوں۔\n\n• 📸 بیماری کی تشخیص\n• 💊 علاج کی سفارش\n• 💰 لاگت اور منافع\n\nکچھ بھی پوچھیں!",
            "mr":"🙏 नमस्कार! मी किसान AI आहे.\n\n• 📸 रोग ओळख\n• 💊 उपचाराची शिफारस\n• 💰 खर्च आणि नफा\n\nकाहीही विचारा!",
            "te":"🙏 నమస్కారం! నేను కిసాన్ AI.\n\n• 📸 వ్యాధి గుర్తింపు\n• 💊 చికిత్స సూచనలు\n\nఏదైనా అడగండి!",
            "bn":"🙏 নমস্কার! আমি কিসান AI.\n\n• 📸 রোগ শনাক্তকরণ\n• 💊 চিকিৎসার পরামর্শ\n\nযেকোনো প্রশ্ন করুন!",
        }
        msg = welcome_msgs.get(lang_code, welcome_msgs["en"])
        st.html(f"""<div class="chat-box">
          <div class="msg-bot">
            <div class="av av-bot">🌿</div>
            <div class="bubble bubble-bot" style="white-space:pre-line;">{msg}</div>
          </div></div>""")
    else:
        html_parts = ['<div class="chat-box">']
        for m in st.session_state.chat_messages[-30:]:
            if m["role"] == "user":
                html_parts.append(f'''<div class="msg-user"><div class="av av-user">👤</div>
                  <div class="bubble bubble-user">{m["content"]}</div></div>''')
            else:
                html_parts.append(f'''<div class="msg-bot"><div class="av av-bot">🌿</div>
                  <div class="bubble bubble-bot" style="white-space:pre-line;">{m["content"]}</div></div>''')
        html_parts.append("</div>")
        st.html("".join(html_parts))

    st.html("<div style='height:8px;'></div>")
    st.html('<div class="input-wrap">')
    inp_c, btn_c = st.columns([6,1])
    with inp_c:
        placeholders = {"en":"Ask about your crop, disease, treatment, cost...","hi":"अपनी फसल के बारे में पूछें...","pa":"ਆਪਣੀ ਫਸਲ ਬਾਰੇ ਪੁੱਛੋ...","ur":"اپنی فصل کے بارے میں پوچھیں..."}
        user_text = st.text_input("msg", placeholder=placeholders.get(lang_code,"Ask anything..."),
                                   label_visibility="collapsed", key="chat_input")
    with btn_c:
        send = st.button("Send ➤", use_container_width=True, key="send_btn")
    st.html("</div>")

    if send and user_text.strip():
        st.session_state.chat_messages.append({"role":"user","content":user_text.strip()})
        try:
            ans = get_kisan_response(user_text.strip(), diag)
            st.session_state.chat_messages.append({"role":"bot","content":ans})
        except Exception as e:
            st.session_state.chat_messages.append({"role":"bot","content":f"Error: {e}"})
        st.rerun()

# ══════════════════════════════════════════════════════════════
# PAGE: CROP ROTATION
# ══════════════════════════════════════════════════════════════
elif st.session_state.page == "rotation":
    st.html("""
    <div style="padding:28px 0 16px;">
      <div style="font-family:'Syne',sans-serif;font-size:1.8rem;font-weight:800;color:var(--text);margin-bottom:6px;">🌱 Crop Rotation Advisor</div>
      <div style="color:var(--text2);font-size:0.9rem;">Plan a sustainable 3-year rotation to break disease cycles & improve yield</div>
    </div>""")

    diag = st.session_state.last_diagnosis
    default_plant = diag["plant_type"] if diag and diag.get("plant_type") else None

    ri1, ri2 = st.columns(2)
    with ri1:
        st.html('<div class="card">')
        st.html('<div class="sec-label">🌱 Current Crop</div>')
        use_last = False
        if default_plant:
            use_last = st.checkbox(f"Use diagnosed plant: {default_plant}", value=True, key="use_last_plant")
        if use_last and default_plant:
            plant_type_rot = default_plant
            st.html(f'<div class="alert-ok">Using: {plant_type_rot}</div>')
        else:
            plant_opts = sorted(list(PLANT_COMMON_DISEASES.keys())) + ["Other (type below)"]
            sel = st.selectbox("Select plant", plant_opts, label_visibility="collapsed", key="rot_plant_sel")
            if sel == "Other (type below)":
                plant_type_rot = st.text_input("Enter plant name", placeholder="e.g. Banana, Mango, Ginger", label_visibility="collapsed", key="rot_custom")
            else:
                plant_type_rot = sel
        st.html("</div>")

    with ri2:
        st.html('<div class="card">')
        st.html('<div class="sec-label">📍 Field Details</div>')
        region_rot = st.selectbox("Region", REGIONS, label_visibility="collapsed", key="rot_region")
        soil_rot = st.selectbox("Soil Type", SOIL_TYPES, label_visibility="collapsed", key="rot_soil")
        market_rot = st.selectbox("Market Focus", MARKET_FOCUS, label_visibility="collapsed", key="rot_market")
        st.html("</div>")

    st.html("<div style='height:8px;'></div>")
    _, rb, _ = st.columns([1,2,1])
    with rb:
        if st.button("📋 Generate Rotation Plan", use_container_width=True, key="gen_rot"):
            if plant_type_rot:
                with st.spinner(f"Generating rotation plan for {plant_type_rot}..."):
                    rotations = generate_rotation_plan(plant_type_rot, region_rot, soil_rot, market_rot)
                    st.session_state.crop_rotation_result = {
                        "plant_type": plant_type_rot, "rotations": rotations.get("rotations",[]),
                        "info": rotations.get("info",{}), "region": region_rot, "soil": soil_rot,
                    }
            else:
                st.warning("Please select or enter a plant name.")

    rr = st.session_state.crop_rotation_result
    if rr:
        rots = rr["rotations"]; info_d = rr["info"]
        st.html("<div style='height:8px;'></div>")
        st.html('<div class="sec-label">📅 Your 3-Year Rotation Strategy</div>')
        rc1,rc2,rc3 = st.columns(3)
        entries = [
            (rc1,"📌 Year 1 · Now", rr["plant_type"], info_d.get(rr["plant_type"],"Primary crop for cultivation.")),
            (rc2,"🔄 Year 2 · Next", rots[0] if rots else "—", info_d.get(rots[0],"Rotation crop.") if rots else ""),
            (rc3,"🌿 Year 3 · Third", rots[1] if len(rots)>1 else "—", info_d.get(rots[1],"Alternative crop.") if len(rots)>1 else ""),
        ]
        for col,yr,crop,desc in entries:
            with col: col.html(f'<div class="rot-card"><div class="rot-yr">{yr}</div><div class="rot-crop">{crop}</div><div class="rot-desc">{desc}</div></div>')

        if len(rots) > 2:
            st.html('<div class="sec-label" style="margin-top:16px;">🔄 Extended Rotation Options</div>')
            ex_cols = st.columns(len(rots)-2)
            for i, (col, r) in enumerate(zip(ex_cols, rots[2:])):
                with col: col.html(f'<div class="rot-card"><div class="rot-yr">Option {i+4}</div><div class="rot-crop">{r}</div><div class="rot-desc">{info_d.get(r,"Alternative rotation option.")}</div></div>')

        st.html("""<div class="card" style="margin-top:16px;border-left:3px solid var(--green2);">
          <div class="sec-label">✅ Benefits of Crop Rotation</div>
          <div style="color:var(--text2);font-size:0.88rem;line-height:1.8;">
            • 60-80% reduction in pathogen buildup<br>
            • Improved soil health and nitrogen levels<br>
            • Lower chemical input costs over time<br>
            • More resilient farming ecosystem<br>
            • Enhanced biodiversity and beneficial insects
          </div></div>""")

# ══════════════════════════════════════════════════════════════
# PAGE: COST & ROI
# ══════════════════════════════════════════════════════════════
elif st.session_state.page == "roi":
    st.html("""
    <div style="padding:28px 0 16px;">
      <div style="font-family:'Syne',sans-serif;font-size:1.8rem;font-weight:800;color:var(--text);margin-bottom:6px;">📊 Cost Calculator & ROI</div>
      <div style="color:var(--text2);font-size:0.9rem;">Investment analysis for your treatment options</div>
    </div>""")

    diag = st.session_state.last_diagnosis
    if not diag:
        st.html('<div class="alert-warn">⚠️ No diagnosis data found. Run AI Plant Doctor first to get disease and treatment information.</div>')
    else:
        plant_name = diag.get("plant_type","Unknown")
        disease_name = diag.get("disease_name","Unknown")
        infected_count = diag.get("infected_count",50)
        total_plants = diag.get("total_plants",100)
        result = diag.get("result",{})
        severity = diag.get("severity","moderate")

        # Diagnosis summary
        dm1,dm2,dm3,dm4,dm5 = st.columns(5)
        for col, lbl, val in [
            (dm1,"Plant",plant_name),(dm2,"Disease",disease_name[:12]+"..."),
            (dm3,"Severity",severity.title()),(dm4,"Confidence",f'{diag.get("confidence",0)}%'),
            (dm5,"Infected",str(infected_count))
        ]:
            with col: col.html(f'<div class="stat-card"><div class="stat-lbl">{lbl}</div><div class="stat-val" style="font-size:1.1rem;">{val}</div></div>')

        st.html("<div style='height:12px;'></div>")
        st.html('<div class="sec-label">🔧 Treatment Selection for Cost Calc</div>')

        tc1, tc2 = st.columns(2)
        with tc1:
            treatment_choice = st.radio("Treatment type to use", ["Organic","Chemical"], horizontal=True, key="roi_treat_type")
            selected_type = "organic" if treatment_choice == "Organic" else "chemical"
        with tc2:
            treat_list = result.get(f"{'organic' if selected_type=='organic' else 'chemical'}_treatments",[])
            treat_names = [normalize_name(t) for t in treat_list if isinstance(t,str)]
            if treat_names:
                sel_treat = st.selectbox("Select treatment", treat_names, label_visibility="visible", key="roi_treat_sel")
                t_info = get_treatment_info(selected_type, sel_treat)
                unit_cost = t_info["cost"]
                total_treat_cost = int(unit_cost * max(infected_count,1) / 100)
                st.html(f'<div class="alert-ok" style="font-size:0.83rem;">Estimated: <b>₹{total_treat_cost}</b> for {infected_count} plants · {t_info["quantity"]}</div>')
            else:
                total_treat_cost = 300 if selected_type=="organic" else 250

        st.html("<div style='height:12px;'></div>")
        st.html('<div class="sec-label">📈 Yield & Market Data</div>')

        ci1,ci2,ci3,ci4 = st.columns(4)
        with ci1: org_cost_in = st.number_input("Organic cost (₹)", value=total_treat_cost if selected_type=="organic" else 0, min_value=0, step=100, key="roi_org_cost")
        with ci2: chem_cost_in = st.number_input("Chemical cost (₹)", value=total_treat_cost if selected_type=="chemical" else 0, min_value=0, step=100, key="roi_chem_cost")
        with ci3: yield_kg = st.number_input("Expected yield (kg)", value=1000, min_value=100, step=100, key="roi_yield")
        with ci4: market_price = st.number_input("Market price (₹/kg)", value=40, min_value=1, step=5, key="roi_mkt")

        if st.button("📊 Calculate ROI", use_container_width=True, key="calc_roi_btn"):
            auto_loss = calc_loss_pct(severity, infected_count, total_plants)
            total_rev = int(yield_kg * market_price)
            pot_loss = int(total_rev * auto_loss / 100)
            org_benefit = pot_loss - org_cost_in
            chem_benefit = pot_loss - chem_cost_in
            org_roi = int(org_benefit / max(org_cost_in,1) * 100) if org_cost_in > 0 else 0
            chem_roi = int(chem_benefit / max(chem_cost_in,1) * 100) if chem_cost_in > 0 else 0
            st.session_state.cost_roi_result = {
                "total_revenue": total_rev, "potential_loss": pot_loss, "loss_pct": auto_loss,
                "org_cost": org_cost_in, "chem_cost": chem_cost_in,
                "org_roi": org_roi, "chem_roi": chem_roi,
                "org_benefit": org_benefit, "chem_benefit": chem_benefit,
            }

        roi = st.session_state.cost_roi_result
        if roi:
            st.html("<div style='height:12px;'></div>")
            st.html('<div class="sec-label">📊 Analysis Results</div>')

            rm1,rm2,rm3 = st.columns(3)
            rm1.html(f'<div class="stat-card"><div class="stat-lbl">Total Yield Value</div><div class="stat-val">₹{roi["total_revenue"]:,}</div></div>')
            rm2.html(f'<div class="stat-card"><div class="stat-lbl">Loss if Untreated ({roi["loss_pct"]}%)</div><div class="stat-val" style="color:#f87171;">₹{roi["potential_loss"]:,}</div></div>')
            rm3.html(f'<div class="stat-card"><div class="stat-lbl">Infected / Total</div><div class="stat-val">{infected_count}/{total_plants}</div></div>')

            st.html("<div style='height:10px;'></div>")
            st.html('<div class="sec-label">🆚 ROI Comparison</div>')
            rr1, rr2 = st.columns(2)
            org_c = "#4ade80" if roi["org_roi"] >= roi["chem_roi"] else "var(--text2)"
            chm_c = "#60a5fa" if roi["chem_roi"] > roi["org_roi"] else "var(--text2)"
            rr1.html(f'<div class="stat-card"><div class="stat-lbl">🌿 Organic ROI</div><div class="stat-val" style="color:{org_c};">{roi["org_roi"]}%</div><div style="font-size:0.78rem;color:var(--text2);">Cost: ₹{roi["org_cost"]:,} · Net: ₹{roi["org_benefit"]:,}</div></div>')
            rr2.html(f'<div class="stat-card"><div class="stat-lbl">⚗️ Chemical ROI</div><div class="stat-val" style="color:{chm_c};">{roi["chem_roi"]}%</div><div style="font-size:0.78rem;color:var(--text2);">Cost: ₹{roi["chem_cost"]:,} · Net: ₹{roi["chem_benefit"]:,}</div></div>')

            st.html("<div style='height:10px;'></div>")
            if roi["org_roi"] > roi["chem_roi"]:
                st.html(f'<div class="alert-ok">✅ Organic treatment provides better ROI ({roi["org_roi"]}% vs {roi["chem_roi"]}%). Invest in organic for sustainable farming and long-term soil health.</div>')
            elif roi["chem_roi"] > roi["org_roi"]:
                st.html(f'<div class="alert-ok">✅ Chemical treatment offers higher immediate ROI ({roi["chem_roi"]}% vs {roi["org_roi"]}%). Consider organic for long-term sustainability.</div>')
            else:
                st.html('<div class="alert-ok">✅ Both treatments have similar ROI. Choose based on your farming preference and sustainability goals.</div>')
