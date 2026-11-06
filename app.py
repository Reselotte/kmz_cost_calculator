# pip install streamlit pyogrio geopandas pandas requests folium streamlit-folium openpyxl
import glob
import io
import json
import os
import tempfile
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone

import folium
import geopandas as gpd
import pandas as pd
import pyogrio
import requests
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(page_title="ระบบจัดการแปลงยาสูบ", layout="wide", initial_sidebar_state="expanded")

# ---------------------------------------------------------
# Theme (สว่าง / มืด) : ตามเมนู Settings ของ Streamlit
# ---------------------------------------------------------
LIGHT = dict(bg="#F7F3EA", card="#FFFFFF", txt="#23302A", mut="#4A5A50", line="#DDD3BE",
             pri="#2E6B4F", head="#1F4D38", soft="#E9F1EA", side="#EFE8D8",
             inp="#FFFFFF", inpb="#B9AE96", gold="#C98A2B", btn="#2E6B4F")
DARK = dict(bg="#111A15", card="#1B2922", txt="#EDF3EA", mut="#B4C3B9", line="#3B4D43",
            pri="#4FA77B", head="#9BE0BC", soft="#24372D", side="#0C130F",
            inp="#16221C", inpb="#5B7266", gold="#E2A93F", btn="#3C8A64")

# ต้องใช้ Streamlit >= 1.46
try:
    IS_DARK = st.context.theme.type == "dark"
except Exception:
    IS_DARK = False
P = DARK if IS_DARK else LIGHT

STATIC_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;500;600;700&display=swap');
html,body,.stApp,[class*="css"]{font-family:'Sarabun',sans-serif;font-size:18px;}
.block-container{max-width:1200px;padding-top:5.5rem !important;padding-bottom:4rem;}

/* ซ่อนเฉพาะปุ่ม Deploy (เก็บเมนู 3 จุดไว้ เพราะใช้สลับสว่าง/มืดจากเมนู Settings) */
[data-testid="stAppDeployButton"],[data-testid="stDeployButton"],.stDeployButton,.stAppDeployButton{
      display:none !important;}

html body .stApp,html body [data-testid="stAppViewContainer"],html body [data-testid="stMain"],
html body [data-testid="stHeader"]{background:var(--bg) !important;color:var(--txt) !important;}
html body [data-testid="stSidebar"],html body [data-testid="stSidebar"]>div{background:var(--side) !important;
      border-right:1px solid var(--line);}
html body [data-testid="stHeader"] *{color:var(--mut) !important;}

/* ข้อความทั้งหมด */
html body .stApp p,html body .stApp li,html body .stApp label,html body .stApp span,html body .stApp small,
html body .stApp [data-testid="stMarkdownContainer"] *,html body .stApp [data-testid="stWidgetLabel"] *,
html body .stApp [data-testid="stRadio"] *,html body .stApp [data-testid="stCheckbox"] *,
html body .stApp [data-testid="stExpander"] summary *,html body [data-testid="stSidebar"] *{
      color:var(--txt) !important;-webkit-text-fill-color:var(--txt) !important;opacity:1 !important;}
html body .stApp h1,html body .stApp h2,html body .stApp h3,html body .stApp h4,html body .stApp h5,
html body .stApp h1 *,html body .stApp h2 *,html body .stApp h3 *,html body .stApp h4 *,html body .stApp h5 *{
      color:var(--head) !important;-webkit-text-fill-color:var(--head) !important;font-weight:700;}
html body .stApp [data-testid="stCaptionContainer"] *,html body .stApp .note{
      color:var(--mut) !important;-webkit-text-fill-color:var(--mut) !important;}
.note{margin:-.3rem 0 1rem 0;}

/* Hero (ใช้ div ไม่ใช่ h1 เพื่อไม่ให้ถูกสีหัวข้อทับ) */
.hero{background:linear-gradient(120deg,#12382A,#2E6B4F);border-radius:18px;
      padding:1.6rem 1.8rem;margin-bottom:1.2rem;}
html body .stApp .hero .hero-title{color:#FFFFFF !important;-webkit-text-fill-color:#FFFFFF !important;
      font-size:2rem;font-weight:700;margin:0 0 .3rem 0;line-height:1.3;}
html body .stApp .hero .hero-sub{color:#EAF4EE !important;-webkit-text-fill-color:#EAF4EE !important;
      font-size:1.05rem;margin:0;}

/* ขั้นตอน */
.steps{display:flex;gap:.6rem;margin-bottom:1.2rem;flex-wrap:wrap;}
html body .stApp .step{flex:1;min-width:180px;padding:.7rem 1rem;border-radius:12px;background:var(--card);
      border:2px solid var(--line);color:var(--mut) !important;-webkit-text-fill-color:var(--mut) !important;font-weight:600;}
html body .stApp .step.on{background:var(--soft);border-color:var(--pri);
      color:var(--head) !important;-webkit-text-fill-color:var(--head) !important;}
html body .stApp .step.done{border-color:var(--gold);}

/* Metric */
html body .stApp div[data-testid="stMetric"]{background:var(--card);border:1px solid var(--line);
      border-left:6px solid var(--gold);padding:14px 18px;border-radius:12px;}
html body .stApp div[data-testid="stMetricValue"] *{font-size:2rem;color:var(--head) !important;
      -webkit-text-fill-color:var(--head) !important;}

/* ปุ่ม */
html body .stApp div.stButton>button,html body .stApp [data-testid="stDownloadButton"] button,
html body .stApp [data-testid="stLinkButton"] a{min-height:3.2rem;font-size:1.1rem;font-weight:600;
      border-radius:12px;border:2px solid var(--pri) !important;background:var(--card) !important;}
html body .stApp div.stButton>button *,html body .stApp [data-testid="stDownloadButton"] button *,
html body .stApp [data-testid="stLinkButton"] a *{color:var(--head) !important;-webkit-text-fill-color:var(--head) !important;}
html body .stApp button[kind="primary"],html body .stApp [data-testid="stBaseButton-primary"]{
      background:var(--btn) !important;border:2px solid var(--btn) !important;}
html body .stApp button[kind="primary"] *,html body .stApp [data-testid="stBaseButton-primary"] *{
      color:#FFFFFF !important;-webkit-text-fill-color:#FFFFFF !important;}

/* ช่องกรอก / dropdown / tag */
html body .stApp [data-baseweb="input"],html body .stApp [data-baseweb="base-input"],
html body .stApp [data-baseweb="textarea"],html body .stApp [data-baseweb="select"]>div{
      background:var(--inp) !important;border:2px solid var(--inpb) !important;border-radius:10px !important;
      min-height:2.9rem;font-size:1.05rem;}
html body .stApp input,html body .stApp textarea{background:var(--inp) !important;color:var(--txt) !important;
      -webkit-text-fill-color:var(--txt) !important;caret-color:var(--txt) !important;opacity:1 !important;}
html body .stApp input::placeholder{color:var(--mut) !important;-webkit-text-fill-color:var(--mut) !important;opacity:.8 !important;}
html body .stApp [data-baseweb="select"] *{color:var(--txt) !important;-webkit-text-fill-color:var(--txt) !important;}
html body .stApp [data-baseweb="select"] svg{fill:var(--txt) !important;}
html body .stApp [data-baseweb="tag"]{background:var(--pri) !important;border-radius:8px;}
html body .stApp [data-baseweb="tag"] *{color:#FFFFFF !important;-webkit-text-fill-color:#FFFFFF !important;}
html body [data-baseweb="popover"] *,html body [role="listbox"] *{background:var(--card) !important;
      color:var(--txt) !important;-webkit-text-fill-color:var(--txt) !important;}
html body [role="option"]:hover,html body [role="option"][aria-selected="true"]{background:var(--soft) !important;}
html body .stApp [data-testid="stNumberInput"] button{background:var(--soft) !important;}
html body .stApp [data-testid="stNumberInput"] button *{color:var(--head) !important;fill:var(--head) !important;}

/* แท็บ / uploader / expander / alert / container */
html body .stApp button[data-baseweb="tab"]{font-size:1.1rem;font-weight:600;padding:.8rem 1.1rem;}
html body .stApp button[data-baseweb="tab"] *{color:var(--mut) !important;-webkit-text-fill-color:var(--mut) !important;}
html body .stApp button[data-baseweb="tab"][aria-selected="true"] *{color:var(--head) !important;-webkit-text-fill-color:var(--head) !important;}
html body .stApp [data-testid="stFileUploaderDropzone"]{background:var(--soft) !important;border:2px dashed var(--pri) !important;border-radius:14px;}
html body .stApp [data-testid="stFileUploaderDropzone"] button{background:var(--card) !important;border:2px solid var(--pri) !important;}
html body .stApp [data-testid="stExpander"],html body .stApp [data-testid="stExpander"] details{
      background:var(--card) !important;border:1px solid var(--line) !important;}
html body .stApp [data-testid="stVerticalBlockBorderWrapper"]{background:var(--card);border-radius:14px;}
html body .stApp [data-testid="stAlert"] *{color:var(--txt) !important;-webkit-text-fill-color:var(--txt) !important;}
html body .stApp [data-testid="stDataFrame"],html body .stApp [data-testid="stDataEditor"]{
      border:1px solid var(--line);border-radius:10px;overflow:hidden;}
"""

vars_css = ":root{" + "".join(f"--{k}:{v};" for k, v in P.items()) + \
           f"color-scheme:{'dark' if IS_DARK else 'light'};}}"
st.markdown(f"<style>{vars_css}{STATIC_CSS}</style>", unsafe_allow_html=True)

OSRM_URL = "https://router.project-osrm.org/route/v1/driving"
OSRM_TABLE = "https://router.project-osrm.org/table/v1/driving"

DEFAULTS = {
    "page": "upload", "sources": [], "meta": None, "df": None, "errors": [],
    "office_name": "สำนักงาน", "office_lat": 13.685963, "office_lon": 100.621783,
    "route_map": None, "route_summary": None, "route_link": None, "calc_origin": None,
    "pick_point": None, "geo_results": [],
}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)

# ---------------------------------------------------------
# Progress tracking helpers
# ---------------------------------------------------------
PROGRESS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plot_progress.json")
GREEN = "background-color:#2E8B57;color:#FFFFFF"
TH_TZ = timezone(timedelta(hours=7))


def now_th():
    return datetime.now(TH_TZ)


def load_progress():
    try:
        with open(PROGRESS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_progress(data):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def plot_key(village, attr):
    return f"{village}|{attr}"


def tracking_df(df, prog):
    t = df[["No.", "Village", "Group", "Attribute", "Latitude", "Longitude"]].copy()
    keys = [plot_key(v, str(a)) for v, a in zip(t["Village"], t["Attribute"])]
    t["เสร็จแล้ว"] = [k in prog for k in keys]
    t["วันที่เสร็จ"] = [prog.get(k, {}).get("at", "") for k in keys]
    t["หมายเหตุ"] = [prog.get(k, {}).get("note", "") for k in keys]
    t["_key"] = keys
    return t


def to_xlsx(sheets, green_col=None):
    """sheets = {ชื่อชีต: DataFrame} -> bytes ของไฟล์ xlsx (ตั้งความกว้างคอลัมน์ให้อัตโนมัติ)"""
    from openpyxl.styles import Font, PatternFill
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        for name, d in sheets.items():
            d.to_excel(xw, sheet_name=name, index=False)
            ws = xw.sheets[name]
            ws.freeze_panes = "A2"
            for i, col in enumerate(d.columns, 1):
                w = max([len(str(col))] + [len(str(v)) for v in d[col].head(500)])
                ws.column_dimensions[ws.cell(1, i).column_letter].width = min(max(w + 3, 10), 40)
            if green_col and green_col in d.columns:
                gi = list(d.columns).index(green_col)
                fill = PatternFill("solid", fgColor="2E8B57")
                for row in ws.iter_rows(min_row=2):
                    if row[gi].value == "เสร็จแล้ว":
                        for cell in row:
                            cell.fill = fill
                            cell.font = Font(color="FFFFFF")
    return buf.getvalue()


st.session_state.setdefault("progress", load_progress())
st.session_state.setdefault("trk_ver", 0)


# ---------------------------------------------------------
# Data helpers
# ---------------------------------------------------------
def read_kmz_file(file_obj, name):
    loaded, errors = [], []
    try:
        with tempfile.TemporaryDirectory() as tmp:
            with zipfile.ZipFile(file_obj, "r") as kmz:
                kmls = [n for n in kmz.namelist()
                        if n.lower().endswith(".kml") and not n.startswith("__MACOSX/")]
                if not kmls:
                    return [], [f"{name}: ไม่พบไฟล์ KML ภายใน KMZ"]
                for i, kml in enumerate(kmls):
                    path = os.path.join(tmp, f"layer_{i}.kml")
                    with open(path, "wb") as f:
                        f.write(kmz.read(kml))
                    try:
                        for layer_name, _geom_type in pyogrio.list_layers(path):
                            gdf = gpd.read_file(path, layer=str(layer_name), engine="pyogrio")
                            if not gdf.empty:
                                loaded.append(gdf)
                    except Exception as exc:
                        errors.append(f"{name} ({kml}): {exc}")
    except Exception as exc:
        errors.append(f"{name}: {exc}")
    return loaded, errors


def load_sources(items):
    """items = [(filename, file_object)] -> one source per KMZ file."""
    sources, errors = [], []
    bar = st.progress(0, text="กำลังอ่านไฟล์...")
    for i, (name, obj) in enumerate(items):
        gdfs, errs = read_kmz_file(obj, name)
        errors += errs
        if gdfs:
            sources.append({"name": name, "gdfs": gdfs})
        bar.progress((i + 1) / len(items), text=f"อ่านแล้ว {i + 1}/{len(items)} ไฟล์")
    st.session_state.sources = sources
    st.session_state.errors = errors
    st.session_state.meta = pd.DataFrame({
        "ไฟล์": [s["name"] for s in sources],
        "หมู่บ้าน": [os.path.splitext(s["name"])[0] for s in sources],
        "Group": [f"{i + 1:03d}" for i in range(len(sources))],
        "Section": ["1"] * len(sources),
    })
    return bool(sources)


def build_df(sources, meta):
    parts = []
    for i, src in enumerate(sources):
        m = meta.iloc[i]
        for gdf in src["gdfs"]:
            gdf = gdf.copy()
            gdf = gdf.set_crs("EPSG:4326") if gdf.crs is None else gdf.to_crs("EPSG:4326")
            if "Name" in gdf.columns and "Attribute" not in gdf.columns:
                gdf = gdf.rename(columns={"Name": "Attribute"})
            if "Attribute" not in gdf.columns:
                gdf["Attribute"] = [str(n + 1) for n in range(len(gdf))]
            gdf["Group"] = str(m["Group"]).strip().zfill(3)
            gdf["Village"] = str(m["หมู่บ้าน"]).strip() or os.path.splitext(src["name"])[0]
            gdf["Section"] = str(m["Section"])
            gdf["ไฟล์"] = src["name"]
            parts.append(gdf[["Group", "Village", "Section", "Attribute", "ไฟล์", "geometry"]])
    if not parts:
        return None
    res = gpd.GeoDataFrame(pd.concat(parts, ignore_index=True), geometry="geometry", crs="EPSG:4326")
    cen = res.to_crs("EPSG:3857").geometry.centroid.to_crs("EPSG:4326")
    res["Latitude"], res["Longitude"] = cen.y, cen.x
    res = res.sort_values(["Village", "Group", "Section", "Attribute"], key=lambda c: c.astype(str))
    res = res.reset_index(drop=True)
    res.insert(0, "No.", range(1, len(res) + 1))
    return res


# ---------------------------------------------------------
# Routing helpers
# ---------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def get_route(lon1, lat1, lon2, lat2, with_geometry=False):
    overview, geom = ("full", "geojson") if with_geometry else ("false", "polyline")
    url = f"{OSRM_URL}/{lon1},{lat1};{lon2},{lat2}?overview={overview}&geometries={geom}"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    data = r.json()
    if data.get("code") != "Ok" or not data.get("routes"):
        raise ValueError("ไม่พบเส้นทางขับขี่ระหว่างพิกัดที่เลือก")
    rt = data["routes"][0]
    return {"distance_km": rt["distance"] / 1000, "duration_min": rt["duration"] / 60,
            "geometry": rt.get("geometry")}


def _fetch_chunk(olon, olat, pts):
    """OSRM Table API: ต้นทาง 1 จุด -> ปลายทางหลายจุด ในคำขอเดียว"""
    coords = f"{olon:.6f},{olat:.6f};" + ";".join(f"{lo:.6f},{la:.6f}" for lo, la in pts)
    last = None
    for _ in range(3):
        try:
            r = requests.get(f"{OSRM_TABLE}/{coords}",
                             params={"sources": 0, "annotations": "distance"}, timeout=40)
            r.raise_for_status()
            d = r.json()
            if d.get("code") != "Ok":
                raise ValueError(d.get("code"))
            return [None if v is None else v / 1000 for v in d["distances"][0][1:]]
        except Exception as exc:
            last = exc
            time.sleep(0.6)
    raise last


def office_distances(olon, olat, lons, lats, on_progress=None, chunk=90, workers=4):
    """คำนวณระยะทางจากจุดเดียวไปทุกแปลง แบบแบ่งก้อน + ยิงขนาน"""
    pts = list(zip(lons, lats))
    chunks = [pts[i:i + chunk] for i in range(0, len(pts), chunk)]
    out = [None] * len(chunks)
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_fetch_chunk, olon, olat, c): i for i, c in enumerate(chunks)}
        for f in as_completed(futs):
            i = futs[f]
            try:
                out[i] = f.result()
            except Exception:
                out[i] = [None] * len(chunks[i])
            done += len(chunks[i])
            if on_progress:
                on_progress(done, len(pts))
    return [v for part in out for v in part]


# ---------------------------------------------------------
# Map helpers (Google tiles)
# ---------------------------------------------------------
def base_map(center, zoom=12):
    m = folium.Map(location=center, zoom_start=zoom, tiles=None, control_scale=True)
    folium.TileLayer("https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}", attr="Google",
                     name="Google แผนที่ถนน", max_zoom=20).add_to(m)
    folium.TileLayer("https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}", attr="Google",
                     name="Google ดาวเทียม", max_zoom=20).add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    return m


def make_route_map(p1, p2, l1, l2, geometry):
    m = base_map([(p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2], 11)
    folium.Marker(p1, tooltip=l1, icon=folium.Icon(color="blue", icon="home")).add_to(m)
    folium.Marker(p2, tooltip=l2, icon=folium.Icon(color="green", icon="flag")).add_to(m)
    if geometry:
        coords = [[la, lo] for lo, la in geometry["coordinates"]]
        folium.PolyLine(coords, color="#2E6B4F", weight=6, opacity=0.9).add_to(m)
        m.fit_bounds(coords)
    return m


def gmaps(lat1, lon1, lat2, lon2, avoid_tolls=False):
    u = (f"https://www.google.com/maps/dir/?api=1&origin={lat1},{lon1}"
         f"&destination={lat2},{lon2}&travelmode=driving")
    return u + "&avoid=tolls" if avoid_tolls else u


def gmaps_point(lat, lon):
    return f"https://www.google.com/maps?q={lat},{lon}"


@st.cache_data(ttl=86400, show_spinner=False)
def geocode(q):
    r = requests.get("https://nominatim.openstreetmap.org/search",
                     params={"q": q, "format": "json", "limit": 6, "countrycodes": "th",
                             "accept-language": "th"},
                     headers={"User-Agent": "tobacco-plot-app/1.0"}, timeout=15)
    r.raise_for_status()
    return [(x["display_name"], float(x["lat"]), float(x["lon"])) for x in r.json()]


# ---------------------------------------------------------
# UI helpers
# ---------------------------------------------------------
def show_route(route, cost_per_km, toll=0.0):
    fuel = route["distance_km"] * cost_per_km
    cols = st.columns(4 if toll else 3)
    cols[0].metric("ระยะทางขับขี่", f"{route['distance_km']:.2f} กม.")
    cols[1].metric("เวลาโดยประมาณ", f"{route['duration_min']:.0f} นาที")
    cols[2].metric("ค่าน้ำมันโดยประมาณ", f"{fuel:,.2f} บาท")
    if toll:
        cols[3].metric("รวมค่าทางด่วน", f"{fuel + toll:,.2f} บาท")
        st.caption(f"ค่าน้ำมัน {fuel:,.2f} + ค่าทางด่วน {toll:,.2f} บาท")


def toll_input(key):
    return st.number_input("ค่าทางด่วนเที่ยวเดียว (บาท)", min_value=0.0, value=0.0, step=5.0,
                           key=key, help="กรอกเองตามเส้นทางที่ใช้จริง ใส่ 0 ถ้าไม่ใช้ทางด่วน")


def plot_picker(df, label, key):
    c1, c2 = st.columns(2)
    village = c1.selectbox(f"หมู่บ้าน{label}", sorted(df["Village"].unique()), key=f"{key}_v")
    attrs = sorted(df.loc[df["Village"] == village, "Attribute"].astype(str).unique())
    attr = c2.selectbox(f"เลขแปลง{label}", attrs, key=f"{key}_a")
    row = df[(df["Village"] == village) & (df["Attribute"].astype(str) == attr)].iloc[0]
    return row, f"{village} แปลง {attr}"


def header(step):
    st.markdown(
        '<div class="hero"><div class="hero-title">ระบบจัดการแปลงยาสูบ</div>'
        '<p class="hero-sub">จัดการข้อมูลแปลง ตรวจสอบพิกัด และประเมินระยะทางกับค่าน้ำมันในการเดินทาง</p></div>',
        unsafe_allow_html=True,
    )
    if not step:
        return
    names = ["1. นำเข้าไฟล์ KMZ", "2. จำแนกหมู่บ้าน", "3. วิเคราะห์ข้อมูล"]
    html = '<div class="steps">'
    for i, n in enumerate(names, 1):
        cls = "on" if i == step else ("done" if i < step else "")
        html += f'<div class="step {cls}">{n}</div>'
    st.markdown(html + "</div>", unsafe_allow_html=True)


def meta_editor(key):
    st.markdown('<div class="note">พิมพ์แก้ชื่อหมู่บ้านและรหัส Group ในตารางได้โดยตรง '
                "ไฟล์ที่เป็นหมู่บ้านเดียวกันให้ใส่ชื่อเหมือนกัน</div>", unsafe_allow_html=True)
    return st.data_editor(
        st.session_state.meta, key=key, hide_index=True, use_container_width=True,
        disabled=["ไฟล์"],
        column_config={
            "ไฟล์": st.column_config.TextColumn("ไฟล์ KMZ"),
            "หมู่บ้าน": st.column_config.TextColumn("ชื่อหมู่บ้าน", required=True),
            "Group": st.column_config.TextColumn("รหัส Group", required=True),
            "Section": st.column_config.TextColumn("Section"),
        },
    )


# ---------------------------------------------------------
# Sidebar: editable office origin + fuel cost
# ---------------------------------------------------------
def apply_pasted_coord():
    try:
        lat, lon = [float(x) for x in st.session_state.paste_coord.replace(" ", "").split(",")]
        st.session_state.office_lat, st.session_state.office_lon = lat, lon
        st.session_state.paste_msg = "บันทึกพิกัดใหม่แล้ว"
    except Exception:
        st.session_state.paste_msg = "รูปแบบไม่ถูกต้อง ตัวอย่าง: 13.685963, 100.621783"


def apply_pick():
    p = st.session_state.pick_point
    if not p:
        return
    st.session_state.office_lat, st.session_state.office_lon = round(p[0], 6), round(p[1], 6)
    name = (st.session_state.get("pick_name") or "").strip()
    if name:
        st.session_state.office_name = name
    st.session_state.pick_msg = "ตั้งเป็นจุดเริ่มต้นแล้ว (อย่าลืมกดคำนวณระยะทางใหม่)"


def apply_geo_choice():
    sel = st.session_state.get("geo_choice")
    for name, lat, lon in st.session_state.geo_results:
        if name == sel:
            st.session_state.pick_point = (lat, lon)


with st.sidebar:
    st.header("ตั้งค่าระบบ")
    st.subheader("จุดเริ่มต้นการเดินทาง")
    st.text_input("ชื่อจุดเริ่มต้น", key="office_name")
    st.number_input("ละติจูด", key="office_lat", format="%.6f", step=0.0001)
    st.number_input("ลองจิจูด", key="office_lon", format="%.6f", step=0.0001)
    st.text_input("หรือวางพิกัดจาก Google Maps", key="paste_coord", placeholder="13.685963, 100.621783")
    st.button("ใช้พิกัดที่วาง", on_click=apply_pasted_coord, use_container_width=True)
    if st.session_state.get("paste_msg"):
        st.caption(st.session_state.paste_msg)
    st.link_button("เปิดจุดเริ่มต้นใน Google Maps",
                   gmaps_point(st.session_state.office_lat, st.session_state.office_lon),
                   use_container_width=True)
    st.caption("เลือกจากแผนที่ได้ที่แท็บ \"เลือกจุดเริ่มต้น\"")
    st.divider()
    st.subheader("ค่าน้ำมัน")
    fuel_price = st.number_input("ราคาน้ำมัน (บาท/ลิตร)", min_value=0.0, value=33.5, step=0.1)
    fuel_eff = st.number_input("อัตราสิ้นเปลือง (กม./ลิตร)", min_value=0.1, value=12.0, step=0.5)
    cost_per_km = fuel_price / fuel_eff
    st.metric("ค่าน้ำมันต่อกิโลเมตร", f"{cost_per_km:.2f} บาท")

OLAT, OLON = st.session_state.office_lat, st.session_state.office_lon
ONAME = st.session_state.office_name or "จุดเริ่มต้น"


# ---------------------------------------------------------
# Quick calculator (ไม่ต้องใช้ไฟล์ KMZ)
# ---------------------------------------------------------
def parse_coord(s):
    try:
        lat, lon = [float(x) for x in s.replace(" ", "").split(",")]
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return lat, lon
    except Exception:
        pass
    return None


def point_input(title, key, default=None):
    """คืนค่า (lat, lon, ชื่อ) หรือ None ถ้ายังระบุไม่ครบ"""
    st.markdown(f"**{title}**")
    modes = (["ใช้จุดเริ่มต้นในแถบด้านซ้าย"] if default else []) + \
            ["ค้นหาชื่อสถานที่", "วางพิกัดจาก Google Maps"]
    mode = st.radio(title, modes, key=f"{key}_mode", horizontal=True, label_visibility="collapsed")
    if default and mode == modes[0]:
        st.caption(f"{default[2]} ({default[0]:.6f}, {default[1]:.6f})")
        return default
    if mode == "ค้นหาชื่อสถานที่":
        c1, c2 = st.columns([3, 1])
        q = c1.text_input("ชื่อสถานที่", key=f"{key}_q", label_visibility="collapsed",
                          placeholder="เช่น ตลาดศรีเทพ เพชรบูรณ์")
        if c2.button("ค้นหา", key=f"{key}_go", use_container_width=True):
            try:
                st.session_state[f"{key}_res"] = geocode(q.strip()) if q.strip() else []
                if not st.session_state[f"{key}_res"]:
                    st.warning("ไม่พบสถานที่ที่ค้นหา")
            except Exception as exc:
                st.error(f"ค้นหาไม่สำเร็จ: {exc}")
        res = st.session_state.get(f"{key}_res", [])
        if res:
            name = st.selectbox("ผลการค้นหา", [r[0] for r in res], key=f"{key}_sel")
            for n, la, lo in res:
                if n == name:
                    return la, lo, n
        return None
    txt = st.text_input("พิกัด", key=f"{key}_xy", label_visibility="collapsed",
                        placeholder="13.685963, 100.621783")
    if txt.strip():
        p = parse_coord(txt)
        if p:
            return p[0], p[1], f"{p[0]:.5f}, {p[1]:.5f}"
        st.warning("รูปแบบพิกัดไม่ถูกต้อง ตัวอย่าง: 13.685963, 100.621783")
    return None


def quick_calc():
    st.markdown('<div class="note">คำนวณระยะทาง เวลา และค่าน้ำมันระหว่างสองจุดใดก็ได้ '
                "ไม่ต้องอัปโหลดไฟล์ KMZ (ราคาน้ำมันและอัตราสิ้นเปลืองตั้งที่แถบด้านซ้าย)</div>",
                unsafe_allow_html=True)
    with st.container(border=True):
        o = point_input("ต้นทาง", "qo", (OLAT, OLON, ONAME))
        st.divider()
        d = point_input("ปลายทาง", "qd")
        st.divider()
        c1, c2 = st.columns(2)
        round_trip = c1.checkbox("ไป-กลับ", key="q_round")
        trips = c2.number_input("จำนวนเที่ยว", min_value=1, value=1, step=1, key="q_trips")
        avoid = st.checkbox("หลีกเลี่ยงทางด่วนใน Google Maps", value=True, key="q_avoid")
        toll = toll_input("q_toll")
    if st.button("คำนวณระยะทางและค่าเดินทาง", type="primary", use_container_width=True, key="q_go"):
        if not o or not d:
            st.warning("กรุณาระบุทั้งต้นทางและปลายทาง")
        else:
            try:
                st.session_state.quick = {
                    "route": get_route(o[1], o[0], d[1], d[0], True), "o": o, "d": d}
            except Exception as exc:
                st.error(f"ไม่สามารถคำนวณเส้นทางได้: {exc}")
    q = st.session_state.get("quick")
    if q:
        rt, o2, d2 = q["route"], q["o"], q["d"]
        mult = (2 if round_trip else 1) * int(trips)
        st.caption(f"จาก {o2[2]} ไปยัง {d2[2]}")
        show_route({"distance_km": rt["distance_km"] * mult,
                    "duration_min": rt["duration_min"] * mult}, cost_per_km, toll * mult)
        st.caption(f"ระยะทางเที่ยวเดียว {rt['distance_km']:.2f} กม. × {mult} เที่ยว "
                   "(ไป-กลับนับเป็น 2 เที่ยว)")
        st.link_button("เปิดนำทางใน Google Maps",
                       gmaps(o2[0], o2[1], d2[0], d2[1], avoid), use_container_width=True)
        st_folium(make_route_map((o2[0], o2[1]), (d2[0], d2[1]), o2[2], d2[2], rt["geometry"]),
                  use_container_width=True, height=520, key="quick_map", returned_objects=[])


# =========================================================
# PAGE 1: upload
# =========================================================
if st.session_state.page == "upload":
    header(1)
    st.subheader("นำเข้าไฟล์ KMZ")
    st.markdown('<div class="note">เลือกได้หลายไฟล์พร้อมกัน เช่น หนึ่งไฟล์ต่อหนึ่งหมู่บ้าน</div>',
                unsafe_allow_html=True)
    mode = st.radio("แหล่งข้อมูล", ["อัปโหลดไฟล์", "โฟลเดอร์ในเครื่อง"], horizontal=True)
    items = []
    with st.container(border=True):
        if mode == "อัปโหลดไฟล์":
            files = st.file_uploader("เลือกไฟล์ KMZ", type=["kmz"], accept_multiple_files=True)
            items = [(f.name, f) for f in files or []]
        else:
            folder = st.text_input("Path ของโฟลเดอร์", placeholder="C:/Users/Admin/Desktop/Tobacco")
            if folder.strip() and os.path.isdir(folder):
                paths = sorted(glob.glob(os.path.join(folder, "**", "*.kmz"), recursive=True))
                items = [(os.path.basename(p), open(p, "rb")) for p in paths]
                st.caption(f"พบไฟล์ KMZ {len(paths)} ไฟล์")
            elif folder.strip():
                st.warning("ไม่พบโฟลเดอร์ที่ระบุ")
        if st.button("โหลดไฟล์และไปขั้นตอนถัดไป", type="primary", use_container_width=True):
            if not items:
                st.warning("กรุณาเลือกไฟล์ KMZ อย่างน้อยหนึ่งไฟล์")
            elif load_sources(items):
                st.session_state.page = "classify"
                st.rerun()
            else:
                st.error("ไม่พบข้อมูลแปลงที่ใช้งานได้ในไฟล์ที่เลือก")
    for e in st.session_state.errors:
        st.warning(e)
    st.divider()
    if st.button("คำนวณระยะทางและค่าเดินทางทั่วไป (ไม่ต้องใช้ไฟล์ KMZ)",
                 use_container_width=True, key="goto_quick"):
        st.session_state.page = "quick"
        st.rerun()

# =========================================================
# PAGE: quick calculator (ไม่ต้องใช้ไฟล์ KMZ)
# =========================================================
elif st.session_state.page == "quick":
    header(0)
    st.subheader("คำนวณระยะทางและค่าเดินทางทั่วไป")
    quick_calc()
    if st.button("ย้อนกลับ", use_container_width=True, key="q_back"):
        st.session_state.page = "workspace" if st.session_state.df is not None else "upload"
        st.rerun()

# =========================================================
# PAGE 2: classify villages
# =========================================================
elif st.session_state.page == "classify":
    header(2)
    st.subheader("จำแนกหมู่บ้าน")
    st.success(f"อ่านไฟล์สำเร็จ {len(st.session_state.sources)} ไฟล์")
    with st.container(border=True):
        edited = meta_editor("meta_classify")
    c1, c2 = st.columns(2)
    if c1.button("ย้อนกลับ", use_container_width=True):
        st.session_state.page = "upload"
        st.rerun()
    if c2.button("ยืนยันและเข้าสู่หน้าวิเคราะห์", type="primary", use_container_width=True):
        st.session_state.meta = edited
        st.session_state.df = build_df(st.session_state.sources, edited)
        st.session_state.page = "workspace"
        st.rerun()
    if st.session_state.errors:
        with st.expander(f"ข้อผิดพลาดขณะอ่านไฟล์ ({len(st.session_state.errors)})"):
            for e in st.session_state.errors:
                st.warning(e)

# =========================================================
# PAGE 3: workspace
# =========================================================
else:
    df = st.session_state.df
    if df is None or df.empty:
        st.session_state.page = "upload"
        st.rerun()

    header(3)
    top1, top2 = st.columns([3, 1])
    top1.caption(f"จุดเริ่มต้นปัจจุบัน: {ONAME} ({OLAT:.6f}, {OLON:.6f}) แก้ไขได้ที่แถบด้านซ้าย")
    if top2.button("อัปโหลดไฟล์ใหม่", use_container_width=True):
        st.session_state.page = "upload"
        st.session_state.df = None
        st.rerun()

    m1, m2, m3 = st.columns(3)
    m1.metric("จำนวนแปลงทั้งหมด", f"{len(df):,} แปลง")
    m2.metric("จำนวนหมู่บ้าน", f"{df['Village'].nunique():,} หมู่บ้าน")
    m3.metric("จำนวนไฟล์", f"{df['ไฟล์'].nunique():,} ไฟล์")

    t_over, t_origin, t_office, t_pair, t_map, t_track, t_vil, t_quick = st.tabs([
        "ตารางข้อมูล", "เลือกจุดเริ่มต้น", "สำนักงานไปยังแปลง", "ระหว่างแปลง",
        "แผนที่นำทาง", "ติดตามงาน", "จัดการหมู่บ้าน", "คำนวณทั่วไป",
    ])

    # ---- Table with village filter + Google Maps link per plot
    with t_over:
        c1, c2 = st.columns([1, 1])
        vsel = c1.multiselect("กรองตามหมู่บ้าน", sorted(df["Village"].unique()))
        term = c2.text_input("ค้นหาเลขแปลง")
        view = df.drop(columns=["geometry"])
        if vsel:
            view = view[view["Village"].isin(vsel)]
        if term.strip():
            view = view[view["Attribute"].astype(str).str.contains(term.strip(), case=False, na=False)]
        view = view.copy()
        view["Google Maps"] = ("https://www.google.com/maps?q=" + view["Latitude"].astype(str)
                               + "," + view["Longitude"].astype(str))
        st.dataframe(view, use_container_width=True, hide_index=True,
                     column_config={"Google Maps": st.column_config.LinkColumn(
                         "Google Maps", display_text="เปิดแผนที่")})
        st.download_button("ดาวน์โหลด CSV", view.to_csv(index=False).encode("utf-8-sig"),
                           "tobacco_plots.csv", "text/csv")
        st.markdown("##### สรุปรายหมู่บ้าน")
        st.dataframe(df.groupby(["Village", "Group"]).size().reset_index(name="จำนวนแปลง"),
                     use_container_width=True, hide_index=True)

    # ---- Pick origin on a Google-style map
    with t_origin:
        st.markdown("#### เลือกจุดเริ่มต้นจากแผนที่")
        st.markdown('<div class="note">คลิกบนแผนที่เพื่อปักหมุด หรือค้นหาชื่อสถานที่ '
                    "แล้วกด \"ใช้จุดนี้เป็นจุดเริ่มต้น\" (สลับดาวเทียมได้ที่มุมขวาบนของแผนที่)</div>",
                    unsafe_allow_html=True)
        s1, s2 = st.columns([3, 1])
        q = s1.text_input("ค้นหาสถานที่", key="geo_q", placeholder="เช่น ตลาดศรีเทพ เพชรบูรณ์")
        s2.markdown("<div style='height:1.9rem'></div>", unsafe_allow_html=True)
        if s2.button("ค้นหา", use_container_width=True, key="geo_go"):
            try:
                st.session_state.geo_results = geocode(q.strip()) if q.strip() else []
                if not st.session_state.geo_results:
                    st.warning("ไม่พบสถานที่ที่ค้นหา")
            except Exception as exc:
                st.error(f"ค้นหาไม่สำเร็จ: {exc}")
        if st.session_state.geo_results:
            st.selectbox("ผลการค้นหา", [r[0] for r in st.session_state.geo_results],
                         key="geo_choice", on_change=apply_geo_choice)
            if st.session_state.pick_point is None:
                apply_geo_choice()

        pick = st.session_state.pick_point
        center = list(pick) if pick else [OLAT, OLON]
        pm = base_map(center, 14 if pick else 12)
        folium.Marker([OLAT, OLON], tooltip=f"จุดเริ่มต้นปัจจุบัน: {ONAME}",
                      icon=folium.Icon(color="blue", icon="home")).add_to(pm)
        if pick:
            folium.Marker(list(pick), tooltip="จุดที่เลือก",
                          icon=folium.Icon(color="red", icon="map-marker")).add_to(pm)
        out = st_folium(pm, use_container_width=True, height=520, key="origin_map",
                        returned_objects=["last_clicked"])
        clicked = (out or {}).get("last_clicked")
        if clicked:
            newp = (round(clicked["lat"], 6), round(clicked["lng"], 6))
            if newp != st.session_state.pick_point:
                st.session_state.pick_point = newp
                st.rerun()

        if pick:
            st.markdown(f"**จุดที่เลือก:** {pick[0]:.6f}, {pick[1]:.6f}")
            n1, n2, n3 = st.columns([2, 1.2, 1.2])
            n1.text_input("ตั้งชื่อจุดเริ่มต้น (ไม่บังคับ)", key="pick_name", placeholder=ONAME)
            n2.markdown("<div style='height:1.9rem'></div>", unsafe_allow_html=True)
            n2.button("ใช้จุดนี้เป็นจุดเริ่มต้น", type="primary", on_click=apply_pick,
                      use_container_width=True)
            n3.markdown("<div style='height:1.9rem'></div>", unsafe_allow_html=True)
            n3.link_button("เปิดใน Google Maps", gmaps_point(*pick), use_container_width=True)
        else:
            st.caption("ยังไม่ได้เลือกจุด คลิกบนแผนที่หรือค้นหาสถานที่ได้เลย")
        if st.session_state.get("pick_msg"):
            st.success(st.session_state.pick_msg)

    # ---- Office to all plots (fast: batched OSRM table API)
    with t_office:
        st.markdown(f"#### ระยะทางจาก{ONAME}ไปยังทุกแปลง")
        if st.button("คำนวณระยะทางทั้งหมด", type="primary", key="calc_all"):
            bar = st.progress(0, text="กำลังคำนวณ...")
            t0 = time.time()

            def _cb(done, total):
                bar.progress(done / total, text=f"คำนวณแล้ว {done:,}/{total:,} แปลง")

            res = office_distances(OLON, OLAT, df["Longitude"].tolist(), df["Latitude"].tolist(), _cb)
            bar.empty()
            df = df.copy()
            df["distance_km"] = res
            df["travel_cost_thb"] = df["distance_km"] * cost_per_km
            st.session_state.df = df
            st.session_state.calc_origin = (OLAT, OLON)
            st.caption(f"ใช้เวลา {time.time() - t0:.1f} วินาที")
        if "distance_km" in df.columns:
            if st.session_state.calc_origin != (OLAT, OLON):
                st.warning("จุดเริ่มต้นถูกเปลี่ยนหลังคำนวณ กรุณากดคำนวณใหม่")
            ok = df["distance_km"].dropna()
            if len(ok) < len(df):
                st.info(f"คำนวณไม่ได้ {len(df) - len(ok)} แปลง (อาจอยู่ไกลถนน หรือเซิร์ฟเวอร์ตอบช้า) กดคำนวณใหม่ได้")
            a, b, c = st.columns(3)
            a.metric("แปลงที่คำนวณได้", f"{len(ok):,} / {len(df):,}")
            b.metric("ระยะทางเฉลี่ย", f"{ok.mean():.2f} กม." if len(ok) else "-")
            c.metric("ค่าน้ำมันเฉลี่ย", f"{df['travel_cost_thb'].mean():.2f} บาท" if len(ok) else "-")
            cols = ["No.", "Village", "Group", "Attribute", "distance_km", "travel_cost_thb"]
            st.dataframe(df[cols], use_container_width=True, hide_index=True)
        else:
            st.caption("ยังไม่มีผลการคำนวณ")

        st.markdown("##### เลือกเส้นทางไปยังแปลงใน Google Maps")
        with st.container(border=True):
            gp, gn = plot_picker(df, "ที่ต้องการไป", "office_gm")
            g_avoid = st.checkbox("หลีกเลี่ยงทางด่วน", value=True, key="office_gm_avoid")
        if "distance_km" in df.columns and pd.notna(gp["distance_km"]):
            st.caption(f"{gn}: ระยะทางขับขี่ประมาณ {gp['distance_km']:.2f} กม. "
                       f"ค่าน้ำมันประมาณ {gp['travel_cost_thb']:.2f} บาท")
        st.link_button(f"เปิดเส้นทางจาก{ONAME}ไป {gn} ใน Google Maps",
                       gmaps(OLAT, OLON, gp["Latitude"], gp["Longitude"], g_avoid),
                       use_container_width=True)

    # ---- Plot to plot (any village)
    with t_pair:
        st.markdown("#### ระยะทางระหว่างแปลง (ในหมู่บ้านเดียวกันหรือข้ามหมู่บ้าน)")
        with st.container(border=True):
            p1, n1 = plot_picker(df, "ต้นทาง", "pp1")
            p2, n2 = plot_picker(df, "ปลายทาง", "pp2")
            toll = toll_input("pp_toll")
        if st.button("คำนวณระยะทาง", type="primary", key="calc_pair"):
            try:
                rt = get_route(p1["Longitude"], p1["Latitude"], p2["Longitude"], p2["Latitude"])
                st.caption(f"จาก {n1} ไปยัง {n2}")
                show_route(rt, cost_per_km, toll)
                st.link_button("เปิดเส้นทางใน Google Maps",
                               gmaps(p1["Latitude"], p1["Longitude"], p2["Latitude"], p2["Longitude"]),
                               use_container_width=True)
            except Exception as exc:
                st.error(f"ไม่สามารถคำนวณเส้นทางได้: {exc}")

    # ---- Navigation map
    with t_map:
        st.markdown(f"#### เส้นทางจาก{ONAME}ไปยังแปลงเป้าหมาย")
        with st.container(border=True):
            tp, tn = plot_picker(df, "เป้าหมาย", "nav")
            avoid = st.checkbox("หลีกเลี่ยงทางด่วนใน Google Maps", value=True)
            nav_toll = toll_input("nav_toll")
        if st.button("ค้นหาเส้นทางและแสดงแผนที่", type="primary", key="nav_go"):
            try:
                rt = get_route(OLON, OLAT, tp["Longitude"], tp["Latitude"], True)
                st.session_state.route_summary = rt
                st.session_state.route_map = make_route_map(
                    (OLAT, OLON), (tp["Latitude"], tp["Longitude"]), ONAME, tn, rt["geometry"])
                st.session_state.route_link = gmaps(OLAT, OLON, tp["Latitude"], tp["Longitude"], avoid)
            except Exception as exc:
                st.error(f"ไม่สามารถสร้างเส้นทางได้: {exc}")
        if st.session_state.route_summary:
            show_route(st.session_state.route_summary, cost_per_km, nav_toll)
            st.link_button("เปิดนำทางใน Google Maps", st.session_state.route_link,
                           use_container_width=True)
            st_folium(st.session_state.route_map, use_container_width=True, height=520,
                      key="route_map_view", returned_objects=[])

    # ---- Progress tracking + report
    with t_track:
        prog = st.session_state.progress
        trk = tracking_df(df, prog)
        total = len(trk)
        done_n = int(trk["เสร็จแล้ว"].sum())

        if st.session_state.get("trk_msg"):
            st.success(st.session_state.pop("trk_msg"))

        a, b, c = st.columns(3)
        a.metric("เสร็จแล้ว", f"{done_n:,} แปลง")
        b.metric("ยังไม่เสร็จ", f"{total - done_n:,} แปลง")
        c.metric("ความคืบหน้า", f"{done_n / total * 100:.1f}%")
        st.progress(done_n / total if total else 0.0)

        # สรุปรายหมู่บ้าน (หมู่บ้านที่เสร็จครบทุกแปลงจะเป็นสีเขียว)
        summ = trk.groupby(["Village", "Group"])["เสร็จแล้ว"].agg(["size", "sum"]).reset_index()
        summ.columns = ["หมู่บ้าน", "Group", "จำนวนแปลงทั้งหมด", "เสร็จแล้ว"]
        summ["เสร็จแล้ว"] = summ["เสร็จแล้ว"].astype(int)
        summ["คงเหลือ"] = summ["จำนวนแปลงทั้งหมด"] - summ["เสร็จแล้ว"]
        summ["% เสร็จ"] = (summ["เสร็จแล้ว"] / summ["จำนวนแปลงทั้งหมด"] * 100).round(1)
        st.markdown("##### สรุปรายหมู่บ้าน")
        st.dataframe(
            summ.style.apply(lambda r: [GREEN] * len(r) if r["คงเหลือ"] == 0 else [""] * len(r), axis=1),
            use_container_width=True, hide_index=True)

        # ติ๊กสถานะแปลง
        st.markdown("##### ทำเครื่องหมายแปลงที่ไปเสร็จแล้ว")
        f1, f2, f3 = st.columns([2, 1, 1])
        vsel = f1.multiselect("กรองตามหมู่บ้าน", sorted(df["Village"].unique()), key="trk_v")
        stat = f2.selectbox("แสดง", ["ทั้งหมด", "ยังไม่เสร็จ", "เสร็จแล้ว"], key="trk_s")
        term = f3.text_input("ค้นหาเลขแปลง", key="trk_t")
        view = trk
        if vsel:
            view = view[view["Village"].isin(vsel)]
        if stat == "ยังไม่เสร็จ":
            view = view[~view["เสร็จแล้ว"]]
        elif stat == "เสร็จแล้ว":
            view = view[view["เสร็จแล้ว"]]
        if term.strip():
            view = view[view["Attribute"].astype(str).str.contains(term.strip(), case=False, na=False)]

        ed_key = f"trk_ed_{st.session_state.trk_ver}_{'|'.join(vsel)}_{stat}_{term}"
        edited = st.data_editor(
            view[["Village", "Attribute", "เสร็จแล้ว", "วันที่เสร็จ", "หมายเหตุ", "_key"]],
            key=ed_key, hide_index=True, use_container_width=True,
            disabled=["Village", "Attribute", "วันที่เสร็จ"],
            column_config={
                "_key": None,
                "Village": st.column_config.TextColumn("หมู่บ้าน"),
                "Attribute": st.column_config.TextColumn("เลขแปลง"),
                "เสร็จแล้ว": st.column_config.CheckboxColumn("เสร็จแล้ว"),
            })
        if st.button("บันทึกสถานะ", type="primary", use_container_width=True, key="trk_save"):
            now = now_th().strftime("%Y-%m-%d %H:%M")
            for _, r in edited.iterrows():
                k = r["_key"]
                note = "" if pd.isna(r["หมายเหตุ"]) else str(r["หมายเหตุ"]).strip()
                if r["เสร็จแล้ว"]:
                    old = prog.get(k)
                    prog[k] = {"at": old["at"] if old else now, "note": note}
                else:
                    prog.pop(k, None)
            save_progress(prog)
            st.session_state.trk_ver += 1
            st.session_state.trk_msg = "บันทึกสถานะแล้ว"
            st.rerun()

        with st.expander("ลบ / ยกเลิกสถานะที่บันทึกผิด"):
            ver = st.session_state.trk_ver

            def _finish(msg):
                save_progress(prog)
                st.session_state.trk_ver += 1
                st.session_state.trk_msg = msg
                st.rerun()

            # 1) ยกเลิกเฉพาะแปลงที่ติ๊กผิด
            done_rows = trk[trk["เสร็จแล้ว"]]
            labels = {f"{v} แปลง {a}": k for v, a, k in
                      zip(done_rows["Village"], done_rows["Attribute"], done_rows["_key"])}
            undo = st.multiselect("เลือกแปลงที่ต้องการยกเลิกสถานะเสร็จ", list(labels),
                                  key=f"trk_undo_{ver}")
            if st.button("ยกเลิกแปลงที่เลือก", key=f"trk_undo_go_{ver}", disabled=not undo,
                         use_container_width=True):
                for p in undo:
                    prog.pop(labels[p], None)
                _finish(f"ยกเลิกสถานะ {len(undo)} แปลงแล้ว")

            st.divider()
            # 2) ล้างทั้งหมู่บ้าน
            vclear = st.multiselect("ล้างสถานะทั้งหมู่บ้าน", sorted(df["Village"].unique()),
                                    key=f"trk_vclear_{ver}")
            ok_v = st.checkbox("ยืนยันการล้างหมู่บ้านที่เลือก", key=f"trk_vok_{ver}")
            if st.button("ล้างสถานะหมู่บ้านที่เลือก", key=f"trk_vgo_{ver}",
                         disabled=not (vclear and ok_v), use_container_width=True):
                for k in [k for k in prog if k.split("|", 1)[0] in vclear]:
                    prog.pop(k)
                _finish(f"ล้างสถานะ {len(vclear)} หมู่บ้านแล้ว")

            st.divider()
            # 3) ล้างทั้งหมด
            ok_all = st.checkbox("ยืนยันการล้างสถานะทั้งหมด (ย้อนกลับไม่ได้)", key=f"trk_aok_{ver}")
            if st.button("ล้างสถานะทั้งหมด", key=f"trk_ago_{ver}",
                         disabled=not ok_all, use_container_width=True):
                prog.clear()
                _finish("ล้างสถานะทั้งหมดแล้ว")

        # แปลงที่เสร็จแล้ว (สีเขียว)
        done_view = trk[trk["เสร็จแล้ว"]][["Village", "Group", "Attribute", "วันที่เสร็จ", "หมายเหตุ"]]
        st.markdown(f"##### แปลงที่เสร็จแล้ว ({len(done_view):,} แปลง)")
        if len(done_view):
            st.dataframe(done_view.style.apply(lambda r: [GREEN] * len(r), axis=1),
                         use_container_width=True, hide_index=True)
        else:
            st.caption("ยังไม่มีแปลงที่ทำเครื่องหมายว่าเสร็จ")

        # รายงาน
        st.markdown("##### รายงาน")
        st.caption(f"ณ วันที่ {now_th().strftime('%d/%m/%Y %H:%M')} "
                   f"เสร็จแล้ว {done_n:,} จาก {total:,} แปลง "
                   f"({int((summ['คงเหลือ'] == 0).sum())} จาก {len(summ)} หมู่บ้านเสร็จครบ)")
        rep = trk.drop(columns=["_key"]).copy()
        rep["สถานะ"] = rep["เสร็จแล้ว"].map({True: "เสร็จแล้ว", False: "ยังไม่เสร็จ"})
        rep = rep.drop(columns=["เสร็จแล้ว"])
        stamp = now_th().strftime("%Y%m%d_%H%M")
        d1, d2 = st.columns(2)
        try:
            mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            d1.download_button("ดาวน์โหลดรายงานสรุปรายหมู่บ้าน (Excel)",
                               to_xlsx({"สรุปรายหมู่บ้าน": summ}),
                               f"report_summary_{stamp}.xlsx", mime, use_container_width=True)
            d2.download_button("ดาวน์โหลดรายงานรายแปลง (Excel)",
                               to_xlsx({"รายงานรายแปลง": rep}, green_col="สถานะ"),
                               f"report_plots_{stamp}.xlsx", mime, use_container_width=True)
        except ImportError:
            st.warning("ยังไม่ได้ติดตั้ง openpyxl จึงดาวน์โหลดเป็น CSV แทน (ติดตั้งด้วย pip install openpyxl)")
            d1.download_button("ดาวน์โหลดรายงานสรุปรายหมู่บ้าน (CSV)",
                               summ.to_csv(index=False).encode("utf-8-sig"),
                               f"report_summary_{stamp}.csv", "text/csv", use_container_width=True)
            d2.download_button("ดาวน์โหลดรายงานรายแปลง (CSV)",
                               rep.to_csv(index=False).encode("utf-8-sig"),
                               f"report_plots_{stamp}.csv", "text/csv", use_container_width=True)

    # ---- Re-classify villages any time
    with t_vil:
        st.markdown("#### แก้ไขการจำแนกหมู่บ้าน")
        edited = meta_editor("meta_workspace")
        if st.button("บันทึกและอัปเดตข้อมูล", type="primary", key="save_meta"):
            st.session_state.meta = edited
            st.session_state.df = build_df(st.session_state.sources, edited)
            st.session_state.route_map = st.session_state.route_summary = None
            st.success("อัปเดตการจำแนกหมู่บ้านแล้ว (ต้องคำนวณระยะทางทั้งหมดใหม่)")
            st.rerun()

    # ---- Quick calculator
    with t_quick:
        quick_calc()

    st.caption("หมายเหตุ: ระยะทางและเวลาเป็นค่าประมาณจาก OSRM ค่าน้ำมันคำนวณจากค่าที่ตั้งไว้ในแถบด้านซ้าย")