# pip install streamlit pyogrio geopandas pandas requests folium streamlit-folium openpyxl
import glob
import io
import json
import os
import tempfile
import time
import zipfile
import zlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone

import folium
import geopandas as gpd
import pandas as pd
import pyogrio
import requests
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(page_title="Tobacco Plot Management | ระบบจัดการแปลงยาสูบ", layout="wide", initial_sidebar_state="expanded")

# ---------------------------------------------------------
# ภาษา / Language (ไทย | English)
# ---------------------------------------------------------
LANG = "EN" if st.session_state.get("lang_choice") == "English" else "TH"
LANGCODE = "en" if LANG == "EN" else "th"

EN = {
# ---- theme / mode / misc ----
"เขียว": "Green", "น้ำเงิน": "Blue", "ส้ม": "Orange", "ม่วง": "Purple",
"มืด": "Dark", "สว่าง": "Light", "ตามระบบ": "System",
"สำนักงาน": "Office", "จุดเริ่มต้น": "Starting point",
"ระบบจัดการแปลงยาสูบ": "Tobacco Plot Management System",
'<div class="hero"><div class="hero-title">ระบบจัดการแปลงยาสูบ</div><p class="hero-sub">จัดการข้อมูลแปลง ตรวจสอบพิกัด และประเมินระยะทางกับค่าน้ำมันในการเดินทาง</p></div>':
    '<div class="hero"><div class="hero-title">Tobacco Plot Management System</div><p class="hero-sub">Manage plot data, check coordinates, and estimate travel distance and fuel cost</p></div>',
"1. นำเข้าไฟล์ KMZ": "1. Import KMZ files",
"2. จำแนกหมู่บ้าน": "2. Classify villages",
"3. วิเคราะห์ข้อมูล": "3. Analyze data",
# ---- tracking / generic words ----
"เสร็จแล้ว": "Done", "ยังไม่เสร็จ": "Not done", "วันที่เสร็จ": "Date done", "หมายเหตุ": "Note",
"ความคืบหน้า": "Progress", "คงเหลือ": "Remaining", "% เสร็จ": "% done", "สถานะ": "Status",
"ทั้งหมด": "All", "แสดง": "Show", "ลบ": "Delete",
"หมู่บ้าน": "Village", "เลขแปลง": "Plot no.", "ไฟล์": "File", "จำนวนแปลง": "Plots",
"จำนวนแปลงทั้งหมด": "Total plots", "จำนวนหมู่บ้าน": "Villages", "จำนวนไฟล์": "Files",
"สรุปรายหมู่บ้าน": "Village summary", "รายงานรายแปลง": "Plot report",
"ไฟล์ KMZ": "KMZ file", "ชื่อหมู่บ้าน": "Village name", "รหัส Group": "Group code",
"ต้นทาง": "Origin", "ปลายทาง": "Destination", "เป้าหมาย": "Target", "ที่ต้องการไป": "to visit",
# ---- route / money ----
"ระยะทางขับขี่": "Driving distance", "เวลาโดยประมาณ": "Estimated time",
"ค่าน้ำมันโดยประมาณ": "Estimated fuel cost", "รวมค่าทางด่วน": "Total incl. tolls",
"ไม่พบเส้นทางขับขี่ระหว่างพิกัดที่เลือก": "No driving route found between the selected points",
"เซิร์ฟเวอร์เส้นทางไม่รองรับการเลี่ยงทางด่วน ระบบแสดงเส้นทางปกติ (ปุ่ม Google Maps ยังเลี่ยงทางด่วนให้ตามที่เลือก)":
    "The routing server does not support avoiding tolls, so the normal route is shown (the Google Maps button still avoids tolls as selected)",
"ไม่พบทางด่วนในเส้นทางนี้ (ค่าทางด่วน 0 บาท)": "No toll roads on this route (toll cost 0 THB)",
"ทางด่วนที่ผ่าน": "Toll roads passed", "ค่าผ่านทาง (บาท)": "Toll fee (THB)",
"**พบทางด่วนในเส้นทางนี้**": "**Toll roads found on this route**",
"บันทึกค่าผ่านทางนี้ไว้ใช้ครั้งต่อไป": "Save this toll fee for next time",
"บันทึกค่าผ่านทางแล้ว": "Toll fee saved",
"ทางด่วน (ไม่ทราบชื่อ)": "Toll road (unnamed)",
"หลีกเลี่ยงทางด่วน": "Avoid tolls",
# ---- sidebar ----
"ตั้งค่าระบบ": "Settings", "สีของหน้าเว็บ": "Page colors", "โหมด": "Mode", "โทนสี": "Color tone",
"จุดเริ่มต้นการเดินทาง": "Trip starting point", "ชื่อจุดเริ่มต้น": "Starting point name",
"ละติจูด": "Latitude", "ลองจิจูด": "Longitude",
"หรือวางพิกัดจาก Google Maps": "Or paste coordinates from Google Maps",
"ใช้พิกัดที่วาง": "Use pasted coordinates",
"เปิดจุดเริ่มต้นใน Google Maps": "Open starting point in Google Maps",
'เลือกจากแผนที่ได้ที่แท็บ "เลือกจุดเริ่มต้น"': 'You can also pick it on the map in the "Pick starting point" tab',
"ค่าน้ำมัน": "Fuel cost", "ราคาน้ำมัน (บาท/ลิตร)": "Fuel price (THB/liter)",
"อัตราสิ้นเปลือง (กม./ลิตร)": "Fuel efficiency (km/liter)", "ค่าน้ำมันต่อกิโลเมตร": "Fuel cost per km",
"บันทึกพิกัดใหม่แล้ว": "New coordinates saved",
"รูปแบบไม่ถูกต้อง ตัวอย่าง: 13.685963, 100.621783": "Invalid format. Example: 13.685963, 100.621783",
"รูปแบบพิกัดไม่ถูกต้อง ตัวอย่าง: 13.685963, 100.621783": "Invalid coordinate format. Example: 13.685963, 100.621783",
"ตั้งเป็นจุดเริ่มต้นแล้ว (อย่าลืมกดคำนวณระยะทางใหม่)": "Set as the starting point (remember to recalculate distances)",
# ---- point input / quick calc ----
"ค้นหาชื่อสถานที่": "Search by place name", "วางพิกัดจาก Google Maps": "Paste coordinates from Google Maps",
"ใช้จุดเริ่มต้นในแถบด้านซ้าย": "Use starting point from the sidebar",
"ชื่อสถานที่": "Place name", "ค้นหา": "Search", "ผลการค้นหา": "Search results", "พิกัด": "Coordinates",
"เช่น ตลาดศรีเทพ เพชรบูรณ์": "e.g. Sri Thep Market, Phetchabun",
"ไม่พบสถานที่ที่ค้นหา": "No matching place found",
"ไป-กลับ": "Round trip", "จำนวนเที่ยว": "Number of trips",
"คำนวณระยะทางและค่าเดินทาง": "Calculate distance and travel cost",
"กรุณาระบุทั้งต้นทางและปลายทาง": "Please specify both origin and destination",
'<div class="note">คำนวณระยะทาง เวลา และค่าน้ำมันระหว่างสองจุดใดก็ได้ ไม่ต้องอัปโหลดไฟล์ KMZ (ราคาน้ำมันและอัตราสิ้นเปลืองตั้งที่แถบด้านซ้าย)</div>':
    '<div class="note">Calculate distance, time and fuel cost between any two points. No KMZ upload needed (set fuel price and efficiency in the sidebar).</div>',
"เปิดนำทางใน Google Maps": "Open navigation in Google Maps",
# ---- upload / classify ----
"นำเข้าไฟล์ KMZ": "Import KMZ files",
'<div class="note">เลือกได้หลายไฟล์พร้อมกัน เช่น หนึ่งไฟล์ต่อหนึ่งหมู่บ้าน</div>':
    '<div class="note">You can choose several files at once, e.g. one file per village</div>',
"แหล่งข้อมูล": "Data source", "อัปโหลดไฟล์": "Upload files", "โฟลเดอร์ในเครื่อง": "Local folder",
"เลือกไฟล์ KMZ": "Choose KMZ files", "Path ของโฟลเดอร์": "Folder path",
"ไม่พบโฟลเดอร์ที่ระบุ": "Folder not found",
"โหลดไฟล์และไปขั้นตอนถัดไป": "Load files and continue",
"กรุณาเลือกไฟล์ KMZ อย่างน้อยหนึ่งไฟล์": "Please choose at least one KMZ file",
"ไม่พบข้อมูลแปลงที่ใช้งานได้ในไฟล์ที่เลือก": "No usable plot data found in the selected files",
"คำนวณระยะทางและค่าเดินทางทั่วไป (ไม่ต้องใช้ไฟล์ KMZ)": "General distance and travel cost calculator (no KMZ needed)",
"คำนวณระยะทางและค่าเดินทางทั่วไป": "General distance and travel cost calculator",
"ย้อนกลับ": "Back", "จำแนกหมู่บ้าน": "Classify villages",
"ยืนยันและเข้าสู่หน้าวิเคราะห์": "Confirm and go to analysis",
"กำลังอ่านไฟล์...": "Reading files...",
'<div class="note">พิมพ์แก้ชื่อหมู่บ้านและรหัส Group ในตารางได้โดยตรง ไฟล์ที่เป็นหมู่บ้านเดียวกันให้ใส่ชื่อเหมือนกัน</div>':
    '<div class="note">Edit village names and Group codes directly in the table. Files from the same village should use the same name.</div>',
# ---- workspace ----
"อัปโหลดไฟล์ใหม่": "Upload new files",
"ตารางข้อมูล": "Data table", "เลือกจุดเริ่มต้น": "Pick starting point",
"สำนักงานไปยังแปลง": "Office to plots", "ระหว่างแปลง": "Between plots",
"แผนที่นำทาง": "Navigation map", "ติดตามงาน": "Progress tracking",
"จัดการหมู่บ้าน": "Manage villages", "คำนวณทั่วไป": "General calculator",
"กรองตามหมู่บ้าน": "Filter by village", "ค้นหาเลขแปลง": "Search plot number",
"เปิดแผนที่": "Open map", "ดาวน์โหลด CSV": "Download CSV",
"##### สรุปรายหมู่บ้าน": "##### Summary by village",
"#### เลือกจุดเริ่มต้นจากแผนที่": "#### Pick the starting point on the map",
'<div class="note">คลิกบนแผนที่เพื่อปักหมุด หรือค้นหาชื่อสถานที่ แล้วกด "ใช้จุดนี้เป็นจุดเริ่มต้น" (สลับดาวเทียมได้ที่มุมขวาบนของแผนที่)</div>':
    '<div class="note">Click on the map to drop a pin, or search for a place, then press "Use this point as the starting point" (switch to satellite at the top right of the map)</div>',
"ค้นหาสถานที่": "Search for a place",
"ตั้งชื่อจุดเริ่มต้น (ไม่บังคับ)": "Name the starting point (optional)",
"ใช้จุดนี้เป็นจุดเริ่มต้น": "Use this point as the starting point",
"เปิดใน Google Maps": "Open in Google Maps",
"ยังไม่ได้เลือกจุด คลิกบนแผนที่หรือค้นหาสถานที่ได้เลย": "No point selected yet. Click on the map or search for a place.",
"จุดที่เลือก": "Selected point",
"Google แผนที่ถนน": "Google Road map", "Google ดาวเทียม": "Google Satellite",
"คำนวณระยะทางทั้งหมด": "Calculate all distances", "กำลังคำนวณ...": "Calculating...",
"จุดเริ่มต้นถูกเปลี่ยนหลังคำนวณ กรุณากดคำนวณใหม่": "The starting point changed after calculation. Please recalculate.",
"แปลงที่คำนวณได้": "Plots calculated", "ระยะทางเฉลี่ย": "Average distance",
"ค่าน้ำมันเฉลี่ย": "Average fuel cost", "ยังไม่มีผลการคำนวณ": "No results yet",
"##### เลือกเส้นทางไปยังแปลงใน Google Maps": "##### Choose a route to a plot in Google Maps",
"เปิดเส้นทางใน Google Maps": "Open route in Google Maps",
"#### ระยะทางระหว่างแปลง (ในหมู่บ้านเดียวกันหรือข้ามหมู่บ้าน)": "#### Distance between plots (same village or across villages)",
"คำนวณระยะทาง": "Calculate distance", "ค้นหาเส้นทางและแสดงแผนที่": "Find route and show map",
"##### ทำเครื่องหมายแปลงที่ไปเสร็จแล้ว": "##### Mark plots that have been visited",
"บันทึกสถานะ": "Save status", "บันทึกสถานะแล้ว": "Status saved",
"ยกเลิกสถานะเสร็จของแปลงนี้": "Unmark this plot as done",
"ยังไม่มีแปลงที่ทำเครื่องหมายว่าเสร็จ": "No plots marked as done yet",
"##### รายงาน": "##### Report",
"ดาวน์โหลดรายงานสรุปรายหมู่บ้าน (Excel)": "Download village summary report (Excel)",
"ดาวน์โหลดรายงานรายแปลง (Excel)": "Download plot report (Excel)",
"ดาวน์โหลดรายงานสรุปรายหมู่บ้าน (CSV)": "Download village summary report (CSV)",
"ดาวน์โหลดรายงานรายแปลง (CSV)": "Download plot report (CSV)",
"ยังไม่ได้ติดตั้ง openpyxl จึงดาวน์โหลดเป็น CSV แทน (ติดตั้งด้วย pip install openpyxl)":
    "openpyxl is not installed, so downloads are CSV instead (install it with pip install openpyxl)",
"#### แก้ไขการจำแนกหมู่บ้าน": "#### Edit village classification",
"บันทึกและอัปเดตข้อมูล": "Save and update data",
"อัปเดตการจำแนกหมู่บ้านแล้ว (ต้องคำนวณระยะทางทั้งหมดใหม่)": "Village classification updated (recalculate all distances)",
"หมายเหตุ: ระยะทางและเวลาเป็นค่าประมาณจาก OSRM ค่าน้ำมันคำนวณจากค่าที่ตั้งไว้ในแถบด้านซ้าย":
    "Note: distance and time are estimates from OSRM; fuel cost is calculated from the values set in the sidebar",
# ---- templates (f-strings) ----
"{0:.2f} กม.": "{0:.2f} km", "{0:.0f} นาที": "{0:.0f} min",
"{0} ชั่วโมง": "{0} hr", "{0} ชั่วโมง {1} นาที": "{0} hr {1} min",
"{0:,.2f} บาท": "{0:,.2f} THB", "{0:.2f} บาท": "{0:.2f} THB",
"หมู่บ้าน{0}": "Village ({0})", "เลขแปลง{0}": "Plot no. ({0})", "{0} แปลง {1}": "{0} plot {1}",
"ค่าน้ำมัน {0:,.2f} + ค่าทางด่วน {1:,.2f} บาท": "Fuel {0:,.2f} + tolls {1:,.2f} THB",
"มี {0} ช่วงที่ยังไม่ได้ใส่ค่าผ่านทาง กรอกครั้งเดียวแล้วกดบันทึก ครั้งต่อไปที่ผ่านทางเดิม (เข้า-ออกเดิม) ระบบจะใส่ให้อัตโนมัติ":
    "{0} segment(s) have no toll fee yet. Enter it once and press save; next time you pass the same road (same entry and exit) it will be filled in automatically.",
"จาก {0} ไปยัง {1}": "From {0} to {1}",
"ระยะทางเที่ยวเดียว {0:.2f} กม. × {1} เที่ยว (ไป-กลับนับเป็น 2 เที่ยว)":
    "One-way distance {0:.2f} km × {1} trips (round trip counts as 2 trips)",
"อ่านแล้ว {0}/{1} ไฟล์": "Read {0}/{1} files",
"{0} ({1:.1f} กม.)": "{0} ({1:.1f} km)",
"อ่านไฟล์สำเร็จ {0} ไฟล์": "Read {0} files successfully",
"จุดเริ่มต้นปัจจุบัน: {0} ({1:.6f}, {2:.6f}) แก้ไขได้ที่แถบด้านซ้าย":
    "Current starting point: {0} ({1:.6f}, {2:.6f}). Edit it in the sidebar.",
"{0:,} แปลง": "{0:,} plots", "{0:,} หมู่บ้าน": "{0:,} villages", "{0:,} ไฟล์": "{0:,} files",
"พบไฟล์ KMZ {0} ไฟล์": "Found {0} KMZ files",
"#### ระยะทางจาก{0}ไปยังทุกแปลง": "#### Distance from {0} to every plot",
"เปิดเส้นทางจาก{0}ไป {1} ใน Google Maps": "Open route from {0} to {1} in Google Maps",
"#### เส้นทางจาก{0}ไปยังแปลงเป้าหมาย": "#### Route from {0} to the target plot",
"##### แปลงที่เสร็จแล้ว ({0:,} แปลง)": "##### Completed plots ({0:,})",
"ณ วันที่ {0} เสร็จแล้ว {1:,} จาก {2:,} แปลง ({3} จาก {4} หมู่บ้านเสร็จครบ)":
    "As of {0}: {1:,} of {2:,} plots done ({3} of {4} villages fully done)",
"ค้นหาไม่สำเร็จ: {0}": "Search failed: {0}",
"ไม่สามารถคำนวณเส้นทางได้: {0}": "Could not calculate the route: {0}",
"ข้อผิดพลาดขณะอ่านไฟล์ ({0})": "Errors while reading files ({0})",
"**จุดที่เลือก:** {0:.6f}, {1:.6f}": "**Selected point:** {0:.6f}, {1:.6f}",
"ใช้เวลา {0:.1f} วินาที": "Took {0:.1f} seconds",
"{0}: ระยะทางขับขี่ประมาณ {1:.2f} กม. ค่าน้ำมันประมาณ {2:.2f} บาท":
    "{0}: driving distance about {1:.2f} km, fuel cost about {2:.2f} THB",
"{0}: ไม่พบไฟล์ KML ภายใน KMZ": "{0}: no KML file found inside the KMZ",
"คำนวณไม่ได้ {0} แปลง (อาจอยู่ไกลถนน หรือเซิร์ฟเวอร์ตอบช้า) กดคำนวณใหม่ได้":
    "{0} plots could not be calculated (they may be far from a road, or the server was slow). You can recalculate.",
"จุดเริ่มต้นปัจจุบัน: {0}": "Current starting point: {0}",
"คำนวณแล้ว {0:,}/{1:,} แปลง": "Calculated {0:,}/{1:,} plots",
"ไม่สามารถสร้างเส้นทางได้: {0}": "Could not create the route: {0}",
"ยกเลิกสถานะ {0} แปลง {1} แล้ว": "Unmarked {0} plot {1}",
}


def tr(s):
    """แปลข้อความ UI (ไทย -> อังกฤษ) ถ้าไม่มีคำแปลจะคืนข้อความเดิม"""
    return EN.get(s, s) if (LANG == "EN" and isinstance(s, str)) else s


def trx(x):
    """แปลค่าที่ใช้แสดงผล (ตัวเลือก/ค่าที่แทรกในประโยค) เฉพาะที่ตรงทั้งข้อความ"""
    return tr(str(x) if isinstance(x, BaseException) else x)


def fmt_duration(minutes):
    """แปลงจำนวนนาทีเป็นข้อความเวลา: ต่ำกว่า 60 นาทีแสดงเป็นนาที, ตั้งแต่ 60 ขึ้นไปแสดงเป็นชั่วโมง+นาที
    เช่น 45 -> 45 นาที, 60 -> 1 ชั่วโมง, 202 -> 3 ชั่วโมง 22 นาที"""
    total = int(round(float(minutes)))  # ปัดเป็นนาทีเต็มก่อน กัน 59.6 กลายเป็น "60 นาที"
    h, m = divmod(total, 60)
    if h == 0:
        return tr("{0:.0f} นาที").format(trx(m))
    if m == 0:
        return tr("{0} ชั่วโมง").format(trx(h))
    return tr("{0} ชั่วโมง {1} นาที").format(trx(h), trx(m))


def dfx(d, vals_col=None):
    """แปลหัวตาราง (และค่าในคอลัมน์สถานะ) ก่อนแสดง/ส่งออก"""
    if LANG != "EN":
        return d
    try:
        if hasattr(d, "relabel_index"):  # pandas Styler
            return d.relabel_index([tr(c) for c in d.data.columns], axis=1)
        d = d.copy()
        if vals_col and vals_col in d.columns:
            d[vals_col] = d[vals_col].map(trx)
        return d.rename(columns=lambda c: tr(c))
    except Exception:
        return d


# ---------------------------------------------------------
# Theme (สว่าง / มืด) : ตามเมนู Settings ของ Streamlit
# ---------------------------------------------------------
# แต่ละธีมมีชุดสีเต็ม (พื้นหลัง/การ์ด/ตัวอักษร/ปุ่ม) ทั้งโหมดสว่างและมืด
THEMES = {
    "เขียว": dict(
        light=dict(bg="#F7F3EA", card="#FFFFFF", txt="#23302A", mut="#4A5A50", line="#DDD3BE",
                   pri="#2E6B4F", head="#1F4D38", soft="#E9F1EA", side="#EFE8D8",
                   inp="#FFFFFF", inpb="#B9AE96", gold="#C98A2B", btn="#2E6B4F", h1="#12382A", h2="#2E6B4F"),
        dark=dict(bg="#111A15", card="#1B2922", txt="#EDF3EA", mut="#B4C3B9", line="#3B4D43",
                  pri="#4FA77B", head="#9BE0BC", soft="#24372D", side="#0C130F",
                  inp="#16221C", inpb="#5B7266", gold="#E2A93F", btn="#3C8A64", h1="#12382A", h2="#2E6B4F")),
    "น้ำเงิน": dict(
        light=dict(bg="#EEF3F9", card="#FFFFFF", txt="#1F2A37", mut="#4A5A6E", line="#CBD8E8",
                   pri="#2563A8", head="#173F6E", soft="#E6EEF8", side="#E1EAF4",
                   inp="#FFFFFF", inpb="#9DB2CC", gold="#C98A2B", btn="#2563A8", h1="#10294A", h2="#2563A8"),
        dark=dict(bg="#0F1620", card="#18222F", txt="#E8EFF8", mut="#B0C0D4", line="#34475F",
                  pri="#5A9BE0", head="#A9CDF5", soft="#1F2F45", side="#0A1018",
                  inp="#141E2B", inpb="#566C88", gold="#E2A93F", btn="#3C79BF", h1="#10294A", h2="#2563A8")),
    "ส้ม": dict(
        light=dict(bg="#FAF3EC", card="#FFFFFF", txt="#33261C", mut="#6B5646", line="#E6D3C0",
                   pri="#C2571A", head="#7A3410", soft="#FBEBDD", side="#F3E5D6",
                   inp="#FFFFFF", inpb="#CDB297", gold="#2E6B8F", btn="#C2571A", h1="#6B2E0C", h2="#C2571A"),
        dark=dict(bg="#1A130E", card="#271C15", txt="#F6ECE4", mut="#CDB9A9", line="#55402F",
                  pri="#E58A4B", head="#F8C9A3", soft="#3A2A1E", side="#120C08",
                  inp="#20160F", inpb="#7A5F49", gold="#5FB3E0", btn="#C96F32", h1="#6B2E0C", h2="#C2571A")),
    "ม่วง": dict(
        light=dict(bg="#F5F0FA", card="#FFFFFF", txt="#2A2033", mut="#5E4E70", line="#DACBE8",
                   pri="#7A3FA8", head="#4E2670", soft="#F0E7F8", side="#ECE2F5",
                   inp="#FFFFFF", inpb="#B7A3CC", gold="#C98A2B", btn="#7A3FA8", h1="#3B1D56", h2="#7A3FA8"),
        dark=dict(bg="#15101C", card="#211A2B", txt="#F1EBF8", mut="#C3B5D4", line="#46385A",
                  pri="#A878D6", head="#D8BEF2", soft="#2E2438", side="#0E0A14",
                  inp="#1A1423", inpb="#6B5A82", gold="#E2A93F", btn="#8E5BBF", h1="#3B1D56", h2="#7A3FA8")),
}

# โหมดสว่าง/มืดเลือกได้ที่แถบด้านซ้าย (ค่าถูกเก็บใน session_state ตั้งแต่รอบก่อน)
_mode = st.session_state.get("theme_mode", "มืด")
if _mode == "ตามระบบ":
    # ต้องใช้ Streamlit >= 1.46
    try:
        IS_DARK = st.context.theme.type == "dark"
    except Exception:
        IS_DARK = False
else:
    IS_DARK = _mode == "มืด"
P = THEMES.get(st.session_state.get("theme_accent", "เขียว"), THEMES["เขียว"])["dark" if IS_DARK else "light"]

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
.hero{background:linear-gradient(120deg,var(--h1),var(--h2));border-radius:18px;
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
html body .stApp [data-testid="stAlert"],html body .stApp [data-testid="stAlertContainer"]{
      background:var(--soft) !important;border:1px solid var(--pri) !important;border-radius:12px;}
html body .stApp [data-testid="stAlert"] *{color:var(--txt) !important;-webkit-text-fill-color:var(--txt) !important;}
html body .stApp [data-testid="stToast"],html body .stApp [data-testid="stToast"] *{
      background:var(--card) !important;color:var(--txt) !important;-webkit-text-fill-color:var(--txt) !important;}
/* ปุ่ม ✕ สีแดงเรืองแสง */
html body .stApp.stApp [class*="st-key-del"] button{min-height:2.1rem;padding:0 .6rem;
      background:#FF1744 !important;background-color:#FF1744 !important;border:2px solid #FF8A9B !important;
      border-radius:8px;
      box-shadow:0 0 6px #FF1744,0 0 14px rgba(255,23,68,.75),0 0 28px rgba(255,23,68,.45) !important;
      transition:box-shadow .15s,transform .15s;}
html body .stApp.stApp [class*="st-key-del"] button:hover{
      box-shadow:0 0 10px #FF1744,0 0 24px #FF1744,0 0 42px rgba(255,23,68,.8) !important;transform:scale(1.08);}
html body .stApp.stApp [class*="st-key-del"] button *{color:#FFFFFF !important;
      -webkit-text-fill-color:#FFFFFF !important;font-weight:700;text-shadow:0 0 6px #FFFFFF;}
html body .stApp [data-testid="stDataFrame"],html body .stApp [data-testid="stDataEditor"]{
      border:1px solid var(--line);border-radius:10px;overflow:hidden;}

/* ================= Animation & Hover (เคลื่อนไหวช้า นุ่ม) ================= */
@keyframes fadeUp{from{opacity:0;transform:translateY(14px);}to{opacity:1;transform:none;}}
@keyframes heroflow{0%{background-position:0% 50%;}50%{background-position:100% 50%;}100%{background-position:0% 50%;}}
@keyframes pulseRing{0%,100%{box-shadow:0 0 0 0 transparent;}50%{box-shadow:0 0 0 6px var(--soft);}}

/* Hero: ไล่เฉดสีขยับช้า ๆ */
html body .stApp .hero{background:linear-gradient(120deg,var(--h1),var(--h2),var(--h1)) !important;
      background-size:220% 220%;animation:heroflow 18s ease infinite,fadeUp .9s ease both;
      box-shadow:0 8px 24px rgba(0,0,0,.18);}

/* องค์ประกอบที่โผล่ใหม่ค่อย ๆ เลื่อนขึ้น */
html body .stApp div[data-testid="stMetric"],html body .stApp [data-testid="stAlert"],
html body .stApp .steps{animation:fadeUp .9s ease both;}

/* ขั้นตอน */
html body .stApp .step{transition:transform .7s cubic-bezier(.22,.61,.36,1),border-color .7s ease,box-shadow .7s ease;}
html body .stApp .step:hover{transform:translateY(-2px);border-color:var(--pri);
      box-shadow:0 6px 16px rgba(0,0,0,.16);}
html body .stApp .step.on{animation:pulseRing 3.4s ease-in-out infinite;}

/* การ์ดตัวเลข */
html body .stApp div[data-testid="stMetric"]{
      transition:transform .8s cubic-bezier(.22,.61,.36,1),box-shadow .8s ease,border-color .8s ease;}
html body .stApp div[data-testid="stMetric"]:hover{transform:translateY(-3px);
      border-color:var(--pri);border-left-color:var(--gold);
      box-shadow:0 10px 24px rgba(0,0,0,.2),0 0 0 1px var(--pri);}

/* ปุ่มทั้งหมด */
html body .stApp div.stButton>button,html body .stApp [data-testid="stDownloadButton"] button,
html body .stApp [data-testid="stLinkButton"] a{
      transition:background-color .6s ease,border-color .6s ease,box-shadow .6s ease,
                 transform .6s cubic-bezier(.22,.61,.36,1),filter .6s ease;}
html body .stApp div.stButton>button:hover,html body .stApp [data-testid="stDownloadButton"] button:hover,
html body .stApp [data-testid="stLinkButton"] a:hover{transform:translateY(-2px);
      background:var(--soft) !important;border-color:var(--head) !important;
      box-shadow:0 8px 18px rgba(0,0,0,.22);}
html body .stApp div.stButton>button[kind="primary"]:hover,
html body .stApp div.stButton>button[data-testid="stBaseButton-primary"]:hover{
      background:var(--btn) !important;filter:brightness(1.12);
      box-shadow:0 8px 20px rgba(0,0,0,.28),0 0 14px var(--pri);}
html body .stApp div.stButton>button:active,html body .stApp [data-testid="stDownloadButton"] button:active,
html body .stApp [data-testid="stLinkButton"] a:active{transform:translateY(0) scale(.98);box-shadow:none;
      transition-duration:.15s;}

/* ช่องกรอก */
html body .stApp [data-baseweb="input"],html body .stApp [data-baseweb="base-input"],
html body .stApp [data-baseweb="select"]>div{transition:border-color .7s ease,box-shadow .7s ease;}
html body .stApp [data-baseweb="input"]:hover,html body .stApp [data-baseweb="select"]>div:hover{
      border-color:var(--pri) !important;}
html body .stApp [data-baseweb="input"]:focus-within,html body .stApp [data-baseweb="base-input"]:focus-within,
html body .stApp [data-baseweb="select"]>div:focus-within{border-color:var(--pri) !important;
      box-shadow:0 0 0 3px var(--soft),0 0 14px var(--pri);}

/* แท็บ / ตัวเลือก / expander / ตาราง */
html body .stApp button[data-baseweb="tab"]{transition:background-color .7s ease,transform .7s cubic-bezier(.22,.61,.36,1);
      border-radius:10px 10px 0 0;}
html body .stApp button[data-baseweb="tab"]:hover{background:var(--soft) !important;transform:translateY(-1px);}
html body .stApp [data-testid="stRadio"] label,html body .stApp [data-testid="stCheckbox"] label{
      transition:transform .6s cubic-bezier(.22,.61,.36,1);}
html body .stApp [data-testid="stRadio"] label:hover,html body .stApp [data-testid="stCheckbox"] label:hover{
      transform:translateX(2px);}
html body .stApp [data-testid="stExpander"],html body .stApp [data-testid="stVerticalBlockBorderWrapper"],
html body .stApp [data-testid="stDataFrame"],html body .stApp [data-testid="stDataEditor"]{
      transition:border-color .8s ease,box-shadow .8s ease;}
html body .stApp [data-testid="stExpander"]:hover{border-color:var(--pri) !important;
      box-shadow:0 4px 14px rgba(0,0,0,.14);}
html body .stApp [data-testid="stVerticalBlockBorderWrapper"]:hover{border-color:var(--pri);}
html body .stApp [data-testid="stDataFrame"]:hover,html body .stApp [data-testid="stDataEditor"]:hover{
      border-color:var(--pri);box-shadow:0 6px 18px rgba(0,0,0,.16);}

/* ลดแอนิเมชันสำหรับคนที่ปิดเอฟเฟกต์ในระบบ */
@media (prefers-reduced-motion:reduce){
  html body .stApp *,html body .stApp *::before,html body .stApp *::after,html body :root{
      animation:none !important;transition:none !important;}}
"""

# ลงทะเบียนตัวแปรสีเป็นชนิด <color> เพื่อให้ "ไล่สี" (fade) ได้ทั้งหน้าพร้อมกัน
_props = "".join(f"@property --{k}{{syntax:'<color>';inherits:true;initial-value:{v};}}" for k, v in P.items())
_fade = ",".join(f"--{k} 1.2s ease-in-out" for k in P)
vars_css = _props + ":root{" + "".join(f"--{k}:{v};" for k, v in P.items()) + \
           f"color-scheme:{'dark' if IS_DARK else 'light'};transition:{_fade};}}"
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
        gc = tr(green_col) if green_col else None
        for name, d in sheets.items():
            name = tr(name)[:31]
            d = dfx(d, green_col)
            d.to_excel(xw, sheet_name=name, index=False)
            ws = xw.sheets[name]
            ws.freeze_panes = "A2"
            for i, col in enumerate(d.columns, 1):
                w = max([len(str(col))] + [len(str(v)) for v in d[col].head(500)])
                ws.column_dimensions[ws.cell(1, i).column_letter].width = min(max(w + 3, 10), 40)
            if gc and gc in d.columns:
                gi = list(d.columns).index(gc)
                fill = PatternFill("solid", fgColor="2E8B57")
                for row in ws.iter_rows(min_row=2):
                    if row[gi].value == tr("เสร็จแล้ว"):
                        for cell in row:
                            cell.fill = fill
                            cell.font = Font(color="FFFFFF")
    return buf.getvalue()


TOLL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "toll_rates.json")


def load_toll_rates():
    try:
        with open(TOLL_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_toll_rates(data):
    with open(TOLL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


st.session_state.setdefault("toll_rates", load_toll_rates())
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
                    return [], [tr("{0}: ไม่พบไฟล์ KML ภายใน KMZ").format(trx(name))]
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
    bar = st.progress(0, text=tr("กำลังอ่านไฟล์..."))
    for i, (name, obj) in enumerate(items):
        gdfs, errs = read_kmz_file(obj, name)
        errors += errs
        if gdfs:
            sources.append({"name": name, "gdfs": gdfs})
        bar.progress((i + 1) / len(items), text=tr("อ่านแล้ว {0}/{1} ไฟล์").format(trx(i + 1), trx(len(items))))
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
def extract_tolls(rt):
    """หาช่วงทางด่วนที่เส้นทางผ่าน จาก class 'toll' ของ OSRM (ข้อมูลมาจาก OpenStreetMap)"""
    segs, cur = [], None

    def close():
        if cur and cur["km"] > 0.05:
            names = list(dict.fromkeys(cur["names"])) or ["ทางด่วน (ไม่ทราบชื่อ)"]
            a, b = cur["in"], cur["out"]
            segs.append({
                "id": f"{a[1]:.3f},{a[0]:.3f}>{b[1]:.3f},{b[0]:.3f}",
                "label": " → ".join(names), "km": cur["km"]})

    for leg in rt.get("legs", []):
        for s in leg.get("steps", []):
            inter = s.get("intersections") or []
            if any("toll" in (i.get("classes") or []) for i in inter):
                if cur is None:
                    cur = {"km": 0.0, "names": [], "in": inter[0]["location"]}
                cur["km"] += s.get("distance", 0) / 1000
                cur["out"] = inter[-1]["location"]
                nm = (s.get("name") or s.get("ref") or "").strip()
                if nm:
                    cur["names"].append(nm)
            elif cur is not None:
                close()
                cur = None
    if cur is not None:
        close()
    return segs


@st.cache_data(ttl=3600, show_spinner=False)
def get_route(lon1, lat1, lon2, lat2, with_geometry=False, avoid_tolls=False):
    overview, geom = ("full", "geojson") if with_geometry else ("false", "polyline")
    base = (f"{OSRM_URL}/{lon1},{lat1};{lon2},{lat2}"
            f"?overview={overview}&geometries={geom}&steps=true")
    urls = ([base + "&exclude=toll"] if avoid_tolls else []) + [base]
    data, avoid_ok = None, False
    for i, u in enumerate(urls):
        try:
            r = requests.get(u, timeout=20)
            if r.status_code != 200:
                continue
            d = r.json()
            if d.get("code") == "Ok" and d.get("routes"):
                data, avoid_ok = d, (avoid_tolls and i == 0)
                break
        except Exception:
            continue
    if data is None:
        raise ValueError("ไม่พบเส้นทางขับขี่ระหว่างพิกัดที่เลือก")
    rt = data["routes"][0]
    return {"distance_km": rt["distance"] / 1000, "duration_min": rt["duration"] / 60,
            "geometry": rt.get("geometry"), "tolls": extract_tolls(rt),
            "avoid_req": avoid_tolls, "avoid_ok": avoid_ok}


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
                     name=tr("Google แผนที่ถนน"), max_zoom=20).add_to(m)
    folium.TileLayer("https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}", attr="Google",
                     name=tr("Google ดาวเทียม"), max_zoom=20).add_to(m)
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
def geocode(q, lang="th"):
    r = requests.get("https://nominatim.openstreetmap.org/search",
                     params={"q": q, "format": "json", "limit": 6, "countrycodes": "th",
                             "accept-language": lang},
                     headers={"User-Agent": "tobacco-plot-app/1.0"}, timeout=15)
    r.raise_for_status()
    return [(x["display_name"], float(x["lat"]), float(x["lon"])) for x in r.json()]


# ---------------------------------------------------------
# UI helpers
# ---------------------------------------------------------
def show_route(route, cost_per_km, toll=0.0, show_toll=False):
    fuel = route["distance_km"] * cost_per_km
    show_toll = show_toll or bool(toll)
    cols = st.columns(4 if show_toll else 3)
    cols[0].metric(tr("ระยะทางขับขี่"), tr("{0:.2f} กม.").format(trx(route['distance_km'])))
    cols[1].metric(tr("เวลาโดยประมาณ"), fmt_duration(route['duration_min']))
    cols[2].metric(tr("ค่าน้ำมันโดยประมาณ"), tr("{0:,.2f} บาท").format(trx(fuel)))
    if show_toll:
        cols[3].metric(tr("รวมค่าทางด่วน"), tr("{0:,.2f} บาท").format(trx(fuel + toll)))
        st.caption(tr("ค่าน้ำมัน {0:,.2f} + ค่าทางด่วน {1:,.2f} บาท").format(trx(fuel), trx(toll)))


def toll_panel(rt, key):
    """ตรวจจับทางด่วนที่เส้นทางผ่าน + ดึงค่าผ่านทางที่เคยบันทึกไว้ คืนค่าทางด่วนเที่ยวเดียว (บาท)"""
    if rt.get("avoid_req") and not rt.get("avoid_ok"):
        st.warning(tr("เซิร์ฟเวอร์เส้นทางไม่รองรับการเลี่ยงทางด่วน ระบบแสดงเส้นทางปกติ "
                   "(ปุ่ม Google Maps ยังเลี่ยงทางด่วนให้ตามที่เลือก)"))
    segs = rt.get("tolls") or []
    if not segs:
        st.caption(tr("ไม่พบทางด่วนในเส้นทางนี้ (ค่าทางด่วน 0 บาท)"))
        return 0.0
    rates = st.session_state.toll_rates
    table = pd.DataFrame({
        "ทางด่วนที่ผ่าน": [tr("{0} ({1:.1f} กม.)").format(trx(s['label']), trx(s['km'])) for s in segs],
        "ค่าผ่านทาง (บาท)": [rates.get(s["id"], {}).get("fee") for s in segs],
    })
    sig = zlib.crc32("|".join(s["id"] for s in segs).encode())
    st.markdown(tr("**พบทางด่วนในเส้นทางนี้**"))
    ed = st.data_editor(
        table, key=f"{key}_toll_{sig}", hide_index=True, use_container_width=True,
        disabled=["ทางด่วนที่ผ่าน"],
        column_config={"ทางด่วนที่ผ่าน": st.column_config.TextColumn(tr("ทางด่วนที่ผ่าน")),
                       "ค่าผ่านทาง (บาท)": st.column_config.NumberColumn(
            tr("ค่าผ่านทาง (บาท)"), min_value=0.0, step=5.0, format="%.0f")})
    fees = [0.0 if pd.isna(v) else float(v) for v in ed["ค่าผ่านทาง (บาท)"]]
    missing = [s for s, v in zip(segs, ed["ค่าผ่านทาง (บาท)"]) if pd.isna(v)]
    if missing:
        st.info(tr("มี {0} ช่วงที่ยังไม่ได้ใส่ค่าผ่านทาง กรอกครั้งเดียวแล้วกดบันทึก ครั้งต่อไปที่ผ่านทางเดิม (เข้า-ออกเดิม) ระบบจะใส่ให้อัตโนมัติ").format(trx(len(missing))))
    if st.button(tr("บันทึกค่าผ่านทางนี้ไว้ใช้ครั้งต่อไป"), key=f"{key}_toll_save_{sig}"):
        for s, v in zip(segs, ed["ค่าผ่านทาง (บาท)"]):
            if not pd.isna(v):
                rates[s["id"]] = {"label": s["label"], "fee": float(v)}
        save_toll_rates(rates)
        st.toast(tr("บันทึกค่าผ่านทางแล้ว"))
    return sum(fees)


def plot_picker(df, label, key):
    c1, c2 = st.columns(2)
    village = c1.selectbox(tr("หมู่บ้าน{0}").format(trx(label)), sorted(df["Village"].unique()), key=f"{key}_v", format_func=trx)
    attrs = sorted(df.loc[df["Village"] == village, "Attribute"].astype(str).unique())
    attr = c2.selectbox(tr("เลขแปลง{0}").format(trx(label)), attrs, key=f"{key}_a", format_func=trx)
    row = df[(df["Village"] == village) & (df["Attribute"].astype(str) == attr)].iloc[0]
    return row, tr("{0} แปลง {1}").format(trx(village), trx(attr))


def header(step):
    st.markdown(
        tr('<div class="hero"><div class="hero-title">ระบบจัดการแปลงยาสูบ</div>'
        '<p class="hero-sub">จัดการข้อมูลแปลง ตรวจสอบพิกัด และประเมินระยะทางกับค่าน้ำมันในการเดินทาง</p></div>'),
        unsafe_allow_html=True,
    )
    if not step:
        return
    names = ["1. นำเข้าไฟล์ KMZ", "2. จำแนกหมู่บ้าน", "3. วิเคราะห์ข้อมูล"]
    html = '<div class="steps">'
    for i, n in enumerate(names, 1):
        cls = "on" if i == step else ("done" if i < step else "")
        html += f'<div class="step {cls}">{tr(n)}</div>'
    st.markdown(html + "</div>", unsafe_allow_html=True)


def meta_editor(key):
    st.markdown(tr('<div class="note">พิมพ์แก้ชื่อหมู่บ้านและรหัส Group ในตารางได้โดยตรง '
                "ไฟล์ที่เป็นหมู่บ้านเดียวกันให้ใส่ชื่อเหมือนกัน</div>"), unsafe_allow_html=True)
    return st.data_editor(
        st.session_state.meta, key=key, hide_index=True, use_container_width=True,
        disabled=["ไฟล์"],
        column_config={
            "ไฟล์": st.column_config.TextColumn(tr("ไฟล์ KMZ")),
            "หมู่บ้าน": st.column_config.TextColumn(tr("ชื่อหมู่บ้าน"), required=True),
            "Group": st.column_config.TextColumn(tr("รหัส Group"), required=True),
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
        st.session_state.paste_msg = tr("บันทึกพิกัดใหม่แล้ว")
    except Exception:
        st.session_state.paste_msg = tr("รูปแบบไม่ถูกต้อง ตัวอย่าง: 13.685963, 100.621783")


def apply_pick():
    p = st.session_state.pick_point
    if not p:
        return
    st.session_state.office_lat, st.session_state.office_lon = round(p[0], 6), round(p[1], 6)
    name = (st.session_state.get("pick_name") or "").strip()
    if name:
        st.session_state.office_name = name
    st.session_state.pick_msg = tr("ตั้งเป็นจุดเริ่มต้นแล้ว (อย่าลืมกดคำนวณระยะทางใหม่)")


def apply_geo_choice():
    sel = st.session_state.get("geo_choice")
    for name, lat, lon in st.session_state.geo_results:
        if name == sel:
            st.session_state.pick_point = (lat, lon)


with st.sidebar:
    st.radio("ภาษา / Language", ["ไทย", "English"], key="lang_choice", horizontal=True,
             label_visibility="collapsed")
    st.subheader(tr("ตั้งค่าระบบ"))

    # แต่ละหมวดพับเก็บไว้ กดเปิดเฉพาะตอนต้องใช้ (ค่าที่ตั้งไว้ยังทำงานตามปกติแม้พับอยู่)
    with st.expander(tr("สีของหน้าเว็บ"), expanded=False):
        st.radio(tr("โหมด"), ["มืด", "สว่าง", "ตามระบบ"], key="theme_mode", horizontal=True, format_func=trx)
        st.radio(tr("โทนสี"), list(THEMES), key="theme_accent", horizontal=True, format_func=trx)

    with st.expander(tr("จุดเริ่มต้นการเดินทาง"), expanded=False):
        st.text_input(tr("ชื่อจุดเริ่มต้น"), key="office_name")
        st.number_input(tr("ละติจูด"), key="office_lat", format="%.6f", step=0.0001)
        st.number_input(tr("ลองจิจูด"), key="office_lon", format="%.6f", step=0.0001)
        st.text_input(tr("หรือวางพิกัดจาก Google Maps"), key="paste_coord", placeholder="13.685963, 100.621783")
        st.button(tr("ใช้พิกัดที่วาง"), on_click=apply_pasted_coord, use_container_width=True)
        if st.session_state.get("paste_msg"):
            st.caption(st.session_state.paste_msg)
        st.link_button(tr("เปิดจุดเริ่มต้นใน Google Maps"),
                       gmaps_point(st.session_state.office_lat, st.session_state.office_lon),
                       use_container_width=True)
        st.caption(tr("เลือกจากแผนที่ได้ที่แท็บ \"เลือกจุดเริ่มต้น\""))

    with st.expander(tr("ค่าน้ำมัน"), expanded=False):
        fuel_price = st.number_input(tr("ราคาน้ำมัน (บาท/ลิตร)"), min_value=0.0, value=33.5, step=0.1)
        fuel_eff = st.number_input(tr("อัตราสิ้นเปลือง (กม./ลิตร)"), min_value=0.1, value=12.0, step=0.5)
    cost_per_km = fuel_price / fuel_eff
    st.caption(f"{tr('ค่าน้ำมันต่อกิโลเมตร')}: {tr('{0:.2f} บาท').format(trx(cost_per_km))}")
    st.caption(f"📍 {trx(st.session_state.office_name) or tr('จุดเริ่มต้น')}")

OLAT, OLON = st.session_state.office_lat, st.session_state.office_lon
ONAME = trx(st.session_state.office_name) or tr("จุดเริ่มต้น")


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
    st.markdown(f"**{trx(title)}**")
    modes = (["ใช้จุดเริ่มต้นในแถบด้านซ้าย"] if default else []) + \
            ["ค้นหาชื่อสถานที่", "วางพิกัดจาก Google Maps"]
    mode = st.radio(title, modes, key=f"{key}_mode", horizontal=True, label_visibility="collapsed", format_func=trx)
    if default and mode == modes[0]:
        st.caption(f"{default[2]} ({default[0]:.6f}, {default[1]:.6f})")
        return default
    if mode == "ค้นหาชื่อสถานที่":
        c1, c2 = st.columns([3, 1])
        q = c1.text_input(tr("ชื่อสถานที่"), key=f"{key}_q", label_visibility="collapsed",
                          placeholder=tr("เช่น ตลาดศรีเทพ เพชรบูรณ์"))
        if c2.button(tr("ค้นหา"), key=f"{key}_go", use_container_width=True):
            try:
                st.session_state[f"{key}_res"] = geocode(q.strip(), LANGCODE) if q.strip() else []
                if not st.session_state[f"{key}_res"]:
                    st.warning(tr("ไม่พบสถานที่ที่ค้นหา"))
            except Exception as exc:
                st.error(tr("ค้นหาไม่สำเร็จ: {0}").format(trx(exc)))
        res = st.session_state.get(f"{key}_res", [])
        if res:
            name = st.selectbox(tr("ผลการค้นหา"), [r[0] for r in res], key=f"{key}_sel", format_func=trx)
            for n, la, lo in res:
                if n == name:
                    return la, lo, n
        return None
    txt = st.text_input(tr("พิกัด"), key=f"{key}_xy", label_visibility="collapsed",
                        placeholder="13.685963, 100.621783")
    if txt.strip():
        p = parse_coord(txt)
        if p:
            return p[0], p[1], f"{p[0]:.5f}, {p[1]:.5f}"
        st.warning(tr("รูปแบบพิกัดไม่ถูกต้อง ตัวอย่าง: 13.685963, 100.621783"))
    return None


def quick_calc():
    st.markdown(tr('<div class="note">คำนวณระยะทาง เวลา และค่าน้ำมันระหว่างสองจุดใดก็ได้ '
                "ไม่ต้องอัปโหลดไฟล์ KMZ (ราคาน้ำมันและอัตราสิ้นเปลืองตั้งที่แถบด้านซ้าย)</div>"),
                unsafe_allow_html=True)
    with st.container(border=True):
        o = point_input("ต้นทาง", "qo", (OLAT, OLON, ONAME))
        st.divider()
        d = point_input("ปลายทาง", "qd")
        st.divider()
        c1, c2 = st.columns(2)
        round_trip = c1.checkbox(tr("ไป-กลับ"), key="q_round")
        trips = c2.number_input(tr("จำนวนเที่ยว"), min_value=1, value=1, step=1, key="q_trips")
        avoid = st.checkbox(tr("หลีกเลี่ยงทางด่วน"), value=False, key="q_avoid")
    if st.button(tr("คำนวณระยะทางและค่าเดินทาง"), type="primary", use_container_width=True, key="q_go"):
        if not o or not d:
            st.warning(tr("กรุณาระบุทั้งต้นทางและปลายทาง"))
        else:
            try:
                st.session_state.quick = {
                    "route": get_route(o[1], o[0], d[1], d[0], True, avoid), "o": o, "d": d}
            except Exception as exc:
                st.error(tr("ไม่สามารถคำนวณเส้นทางได้: {0}").format(trx(exc)))
    q = st.session_state.get("quick")
    if q:
        rt, o2, d2 = q["route"], q["o"], q["d"]
        mult = (2 if round_trip else 1) * int(trips)
        st.caption(tr("จาก {0} ไปยัง {1}").format(trx(o2[2]), trx(d2[2])))
        slot = st.container()
        toll = toll_panel(rt, "q")
        with slot:
            show_route({"distance_km": rt["distance_km"] * mult,
                        "duration_min": rt["duration_min"] * mult},
                       cost_per_km, toll * mult, bool(rt["tolls"]))
        st.caption(tr("ระยะทางเที่ยวเดียว {0:.2f} กม. × {1} เที่ยว (ไป-กลับนับเป็น 2 เที่ยว)").format(trx(rt['distance_km']), trx(mult)))
        st.link_button(tr("เปิดนำทางใน Google Maps"),
                       gmaps(o2[0], o2[1], d2[0], d2[1], avoid), use_container_width=True)
        st_folium(make_route_map((o2[0], o2[1]), (d2[0], d2[1]), o2[2], d2[2], rt["geometry"]),
                  use_container_width=True, height=520, key="quick_map", returned_objects=[])


# =========================================================
# PAGE 1: upload
# =========================================================
if st.session_state.page == "upload":
    header(1)
    st.subheader(tr("นำเข้าไฟล์ KMZ"))
    st.markdown(tr('<div class="note">เลือกได้หลายไฟล์พร้อมกัน เช่น หนึ่งไฟล์ต่อหนึ่งหมู่บ้าน</div>'),
                unsafe_allow_html=True)
    mode = st.radio(tr("แหล่งข้อมูล"), ["อัปโหลดไฟล์", "โฟลเดอร์ในเครื่อง"], horizontal=True, format_func=trx)
    items = []
    with st.container(border=True):
        if mode == "อัปโหลดไฟล์":
            files = st.file_uploader(tr("เลือกไฟล์ KMZ"), type=["kmz"], accept_multiple_files=True)
            items = [(f.name, f) for f in files or []]
        else:
            folder = st.text_input(tr("Path ของโฟลเดอร์"), placeholder="C:/Users/Admin/Desktop/Tobacco")
            if folder.strip() and os.path.isdir(folder):
                paths = sorted(glob.glob(os.path.join(folder, "**", "*.kmz"), recursive=True))
                items = [(os.path.basename(p), open(p, "rb")) for p in paths]
                st.caption(tr("พบไฟล์ KMZ {0} ไฟล์").format(trx(len(paths))))
            elif folder.strip():
                st.warning(tr("ไม่พบโฟลเดอร์ที่ระบุ"))
        if st.button(tr("โหลดไฟล์และไปขั้นตอนถัดไป"), type="primary", use_container_width=True):
            if not items:
                st.warning(tr("กรุณาเลือกไฟล์ KMZ อย่างน้อยหนึ่งไฟล์"))
            elif load_sources(items):
                st.session_state.page = "classify"
                st.rerun()
            else:
                st.error(tr("ไม่พบข้อมูลแปลงที่ใช้งานได้ในไฟล์ที่เลือก"))
    for e in st.session_state.errors:
        st.warning(e)
    st.divider()
    if st.button(tr("คำนวณระยะทางและค่าเดินทางทั่วไป (ไม่ต้องใช้ไฟล์ KMZ)"),
                 use_container_width=True, key="goto_quick"):
        st.session_state.page = "quick"
        st.rerun()

# =========================================================
# PAGE: quick calculator (ไม่ต้องใช้ไฟล์ KMZ)
# =========================================================
elif st.session_state.page == "quick":
    header(0)
    st.subheader(tr("คำนวณระยะทางและค่าเดินทางทั่วไป"))
    quick_calc()
    if st.button(tr("ย้อนกลับ"), use_container_width=True, key="q_back"):
        st.session_state.page = "workspace" if st.session_state.df is not None else "upload"
        st.rerun()

# =========================================================
# PAGE 2: classify villages
# =========================================================
elif st.session_state.page == "classify":
    header(2)
    st.subheader(tr("จำแนกหมู่บ้าน"))
    st.success(tr("อ่านไฟล์สำเร็จ {0} ไฟล์").format(trx(len(st.session_state.sources))))
    with st.container(border=True):
        edited = meta_editor("meta_classify")
    c1, c2 = st.columns(2)
    if c1.button(tr("ย้อนกลับ"), use_container_width=True):
        st.session_state.page = "upload"
        st.rerun()
    if c2.button(tr("ยืนยันและเข้าสู่หน้าวิเคราะห์"), type="primary", use_container_width=True):
        st.session_state.meta = edited
        st.session_state.df = build_df(st.session_state.sources, edited)
        st.session_state.page = "workspace"
        st.rerun()
    if st.session_state.errors:
        with st.expander(tr("ข้อผิดพลาดขณะอ่านไฟล์ ({0})").format(trx(len(st.session_state.errors)))):
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
    top1.caption(tr("จุดเริ่มต้นปัจจุบัน: {0} ({1:.6f}, {2:.6f}) แก้ไขได้ที่แถบด้านซ้าย").format(trx(ONAME), trx(OLAT), trx(OLON)))
    if top2.button(tr("อัปโหลดไฟล์ใหม่"), use_container_width=True):
        st.session_state.page = "upload"
        st.session_state.df = None
        st.rerun()

    m1, m2, m3 = st.columns(3)
    m1.metric(tr("จำนวนแปลงทั้งหมด"), tr("{0:,} แปลง").format(trx(len(df))))
    m2.metric(tr("จำนวนหมู่บ้าน"), tr("{0:,} หมู่บ้าน").format(trx(df['Village'].nunique())))
    m3.metric(tr("จำนวนไฟล์"), tr("{0:,} ไฟล์").format(trx(df['ไฟล์'].nunique())))

    t_over, t_origin, t_office, t_pair, t_map, t_track, t_vil, t_quick = st.tabs([
        tr("ตารางข้อมูล"), tr("เลือกจุดเริ่มต้น"), tr("สำนักงานไปยังแปลง"), tr("ระหว่างแปลง"),
        tr("แผนที่นำทาง"), tr("ติดตามงาน"), tr("จัดการหมู่บ้าน"), tr("คำนวณทั่วไป"),
    ])

    # ---- Table with village filter + Google Maps link per plot
    with t_over:
        c1, c2 = st.columns([1, 1])
        vsel = c1.multiselect(tr("กรองตามหมู่บ้าน"), sorted(df["Village"].unique()), format_func=trx)
        term = c2.text_input(tr("ค้นหาเลขแปลง"))
        view = df.drop(columns=["geometry"])
        if vsel:
            view = view[view["Village"].isin(vsel)]
        if term.strip():
            view = view[view["Attribute"].astype(str).str.contains(term.strip(), case=False, na=False)]
        view = view.copy()
        view["Google Maps"] = ("https://www.google.com/maps?q=" + view["Latitude"].astype(str)
                               + "," + view["Longitude"].astype(str))
        st.dataframe(dfx(view), use_container_width=True, hide_index=True,
                     column_config={"Google Maps": st.column_config.LinkColumn(
                         "Google Maps", display_text=tr("เปิดแผนที่"))})
        st.download_button(tr("ดาวน์โหลด CSV"), view.to_csv(index=False).encode("utf-8-sig"),
                           "tobacco_plots.csv", "text/csv")
        st.markdown(tr("##### สรุปรายหมู่บ้าน"))
        st.dataframe(dfx(df.groupby(["Village", "Group"]).size().reset_index(name="จำนวนแปลง")),
                     use_container_width=True, hide_index=True)

    # ---- Pick origin on a Google-style map
    with t_origin:
        st.markdown(tr("#### เลือกจุดเริ่มต้นจากแผนที่"))
        st.markdown(tr('<div class="note">คลิกบนแผนที่เพื่อปักหมุด หรือค้นหาชื่อสถานที่ '
                    "แล้วกด \"ใช้จุดนี้เป็นจุดเริ่มต้น\" (สลับดาวเทียมได้ที่มุมขวาบนของแผนที่)</div>"),
                    unsafe_allow_html=True)
        s1, s2 = st.columns([3, 1])
        q = s1.text_input(tr("ค้นหาสถานที่"), key="geo_q", placeholder=tr("เช่น ตลาดศรีเทพ เพชรบูรณ์"))
        s2.markdown("<div style='height:1.9rem'></div>", unsafe_allow_html=True)
        if s2.button(tr("ค้นหา"), use_container_width=True, key="geo_go"):
            try:
                st.session_state.geo_results = geocode(q.strip(), LANGCODE) if q.strip() else []
                if not st.session_state.geo_results:
                    st.warning(tr("ไม่พบสถานที่ที่ค้นหา"))
            except Exception as exc:
                st.error(tr("ค้นหาไม่สำเร็จ: {0}").format(trx(exc)))
        if st.session_state.geo_results:
            st.selectbox(tr("ผลการค้นหา"), [r[0] for r in st.session_state.geo_results],
                         key="geo_choice", on_change=apply_geo_choice, format_func=trx)
            if st.session_state.pick_point is None:
                apply_geo_choice()

        pick = st.session_state.pick_point
        center = list(pick) if pick else [OLAT, OLON]
        pm = base_map(center, 14 if pick else 12)
        folium.Marker([OLAT, OLON], tooltip=tr("จุดเริ่มต้นปัจจุบัน: {0}").format(trx(ONAME)),
                      icon=folium.Icon(color="blue", icon="home")).add_to(pm)
        if pick:
            folium.Marker(list(pick), tooltip=tr("จุดที่เลือก"),
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
            st.markdown(tr("**จุดที่เลือก:** {0:.6f}, {1:.6f}").format(trx(pick[0]), trx(pick[1])))
            n1, n2, n3 = st.columns([2, 1.2, 1.2])
            n1.text_input(tr("ตั้งชื่อจุดเริ่มต้น (ไม่บังคับ)"), key="pick_name", placeholder=ONAME)
            n2.markdown("<div style='height:1.9rem'></div>", unsafe_allow_html=True)
            n2.button(tr("ใช้จุดนี้เป็นจุดเริ่มต้น"), type="primary", on_click=apply_pick,
                      use_container_width=True)
            n3.markdown("<div style='height:1.9rem'></div>", unsafe_allow_html=True)
            n3.link_button(tr("เปิดใน Google Maps"), gmaps_point(*pick), use_container_width=True)
        else:
            st.caption(tr("ยังไม่ได้เลือกจุด คลิกบนแผนที่หรือค้นหาสถานที่ได้เลย"))
        if st.session_state.get("pick_msg"):
            st.success(st.session_state.pick_msg)

    # ---- Office to all plots (fast: batched OSRM table API)
    with t_office:
        st.markdown(tr("#### ระยะทางจาก{0}ไปยังทุกแปลง").format(trx(ONAME)))
        if st.button(tr("คำนวณระยะทางทั้งหมด"), type="primary", key="calc_all"):
            bar = st.progress(0, text=tr("กำลังคำนวณ..."))
            t0 = time.time()

            def _cb(done, total):
                bar.progress(done / total, text=tr("คำนวณแล้ว {0:,}/{1:,} แปลง").format(trx(done), trx(total)))

            res = office_distances(OLON, OLAT, df["Longitude"].tolist(), df["Latitude"].tolist(), _cb)
            bar.empty()
            df = df.copy()
            df["distance_km"] = res
            df["travel_cost_thb"] = df["distance_km"] * cost_per_km
            st.session_state.df = df
            st.session_state.calc_origin = (OLAT, OLON)
            st.caption(tr("ใช้เวลา {0:.1f} วินาที").format(trx(time.time() - t0)))
        if "distance_km" in df.columns:
            if st.session_state.calc_origin != (OLAT, OLON):
                st.warning(tr("จุดเริ่มต้นถูกเปลี่ยนหลังคำนวณ กรุณากดคำนวณใหม่"))
            ok = df["distance_km"].dropna()
            if len(ok) < len(df):
                st.info(tr("คำนวณไม่ได้ {0} แปลง (อาจอยู่ไกลถนน หรือเซิร์ฟเวอร์ตอบช้า) กดคำนวณใหม่ได้").format(trx(len(df) - len(ok))))
            a, b, c = st.columns(3)
            a.metric(tr("แปลงที่คำนวณได้"), f"{len(ok):,} / {len(df):,}")
            b.metric(tr("ระยะทางเฉลี่ย"), tr("{0:.2f} กม.").format(trx(ok.mean())) if len(ok) else "-")
            c.metric(tr("ค่าน้ำมันเฉลี่ย"), tr("{0:.2f} บาท").format(trx(df['travel_cost_thb'].mean())) if len(ok) else "-")
            cols = ["No.", "Village", "Group", "Attribute", "distance_km", "travel_cost_thb"]
            st.dataframe(dfx(df[cols]), use_container_width=True, hide_index=True)
        else:
            st.caption(tr("ยังไม่มีผลการคำนวณ"))

        st.markdown(tr("##### เลือกเส้นทางไปยังแปลงใน Google Maps"))
        with st.container(border=True):
            gp, gn = plot_picker(df, "ที่ต้องการไป", "office_gm")
            g_avoid = st.checkbox(tr("หลีกเลี่ยงทางด่วน"), value=False, key="office_gm_avoid")
        if "distance_km" in df.columns and pd.notna(gp["distance_km"]):
            st.caption(tr("{0}: ระยะทางขับขี่ประมาณ {1:.2f} กม. ค่าน้ำมันประมาณ {2:.2f} บาท").format(trx(gn), trx(gp['distance_km']), trx(gp['travel_cost_thb'])))
        st.link_button(tr("เปิดเส้นทางจาก{0}ไป {1} ใน Google Maps").format(trx(ONAME), trx(gn)),
                       gmaps(OLAT, OLON, gp["Latitude"], gp["Longitude"], g_avoid),
                       use_container_width=True)

    # ---- Plot to plot (any village)
    with t_pair:
        st.markdown(tr("#### ระยะทางระหว่างแปลง (ในหมู่บ้านเดียวกันหรือข้ามหมู่บ้าน)"))
        with st.container(border=True):
            p1, n1 = plot_picker(df, "ต้นทาง", "pp1")
            p2, n2 = plot_picker(df, "ปลายทาง", "pp2")
            pp_avoid = st.checkbox(tr("หลีกเลี่ยงทางด่วน"), value=False, key="pp_avoid")
        if st.button(tr("คำนวณระยะทาง"), type="primary", key="calc_pair"):
            try:
                st.session_state.pair_res = {
                    "rt": get_route(p1["Longitude"], p1["Latitude"], p2["Longitude"], p2["Latitude"],
                                    False, pp_avoid),
                    "n1": n1, "n2": n2, "avoid": pp_avoid,
                    "a": (p1["Latitude"], p1["Longitude"]), "b": (p2["Latitude"], p2["Longitude"])}
            except Exception as exc:
                st.error(tr("ไม่สามารถคำนวณเส้นทางได้: {0}").format(trx(exc)))
        pr = st.session_state.get("pair_res")
        if pr:
            st.caption(tr("จาก {0} ไปยัง {1}").format(trx(pr['n1']), trx(pr['n2'])))
            slot = st.container()
            toll = toll_panel(pr["rt"], "pp")
            with slot:
                show_route(pr["rt"], cost_per_km, toll, bool(pr["rt"]["tolls"]))
            st.link_button(tr("เปิดเส้นทางใน Google Maps"),
                           gmaps(*pr["a"], *pr["b"], pr["avoid"]), use_container_width=True)

    # ---- Navigation map
    with t_map:
        st.markdown(tr("#### เส้นทางจาก{0}ไปยังแปลงเป้าหมาย").format(trx(ONAME)))
        with st.container(border=True):
            tp, tn = plot_picker(df, "เป้าหมาย", "nav")
            avoid = st.checkbox(tr("หลีกเลี่ยงทางด่วน"), value=False)
        if st.button(tr("ค้นหาเส้นทางและแสดงแผนที่"), type="primary", key="nav_go"):
            try:
                rt = get_route(OLON, OLAT, tp["Longitude"], tp["Latitude"], True, avoid)
                st.session_state.route_summary = rt
                st.session_state.route_map = make_route_map(
                    (OLAT, OLON), (tp["Latitude"], tp["Longitude"]), ONAME, tn, rt["geometry"])
                st.session_state.route_link = gmaps(OLAT, OLON, tp["Latitude"], tp["Longitude"], avoid)
            except Exception as exc:
                st.error(tr("ไม่สามารถสร้างเส้นทางได้: {0}").format(trx(exc)))
        if st.session_state.route_summary:
            rs = st.session_state.route_summary
            slot = st.container()
            nav_toll = toll_panel(rs, "nav")
            with slot:
                show_route(rs, cost_per_km, nav_toll, bool(rs["tolls"]))
            st.link_button(tr("เปิดนำทางใน Google Maps"), st.session_state.route_link,
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
        a.metric(tr("เสร็จแล้ว"), tr("{0:,} แปลง").format(trx(done_n)))
        b.metric(tr("ยังไม่เสร็จ"), tr("{0:,} แปลง").format(trx(total - done_n)))
        c.metric(tr("ความคืบหน้า"), f"{done_n / total * 100:.1f}%")
        st.progress(done_n / total if total else 0.0)

        # สรุปรายหมู่บ้าน (หมู่บ้านที่เสร็จครบทุกแปลงจะเป็นสีเขียว)
        summ = trk.groupby(["Village", "Group"])["เสร็จแล้ว"].agg(["size", "sum"]).reset_index()
        summ.columns = ["หมู่บ้าน", "Group", "จำนวนแปลงทั้งหมด", "เสร็จแล้ว"]
        summ["เสร็จแล้ว"] = summ["เสร็จแล้ว"].astype(int)
        summ["คงเหลือ"] = summ["จำนวนแปลงทั้งหมด"] - summ["เสร็จแล้ว"]
        summ["% เสร็จ"] = (summ["เสร็จแล้ว"] / summ["จำนวนแปลงทั้งหมด"] * 100).round(1)
        st.markdown(tr("##### สรุปรายหมู่บ้าน"))
        st.dataframe(
            dfx(summ.style.apply(lambda r: [GREEN] * len(r) if r["คงเหลือ"] == 0 else [""] * len(r), axis=1)),
            use_container_width=True, hide_index=True)

        # ติ๊กสถานะแปลง
        st.markdown(tr("##### ทำเครื่องหมายแปลงที่ไปเสร็จแล้ว"))
        f1, f2, f3 = st.columns([2, 1, 1])
        vsel = f1.multiselect(tr("กรองตามหมู่บ้าน"), sorted(df["Village"].unique()), key="trk_v", format_func=trx)
        stat = f2.selectbox(tr("แสดง"), ["ทั้งหมด", "ยังไม่เสร็จ", "เสร็จแล้ว"], key="trk_s", format_func=trx)
        term = f3.text_input(tr("ค้นหาเลขแปลง"), key="trk_t")
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
                "Village": st.column_config.TextColumn(tr("หมู่บ้าน")),
                "Attribute": st.column_config.TextColumn(tr("เลขแปลง")),
                "เสร็จแล้ว": st.column_config.CheckboxColumn(tr("เสร็จแล้ว")),
                "วันที่เสร็จ": st.column_config.TextColumn(tr("วันที่เสร็จ")),
                "หมายเหตุ": st.column_config.TextColumn(tr("หมายเหตุ")),
            })
        if st.button(tr("บันทึกสถานะ"), type="primary", use_container_width=True, key="trk_save"):
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
            st.session_state.trk_msg = tr("บันทึกสถานะแล้ว")
            st.rerun()

        # แปลงที่เสร็จแล้ว (กด ✕ แดงท้ายแถวเพื่อยกเลิกสถานะที่ติ๊กผิด)
        done_view = trk[trk["เสร็จแล้ว"]].drop_duplicates("_key")
        st.markdown(tr("##### แปลงที่เสร็จแล้ว ({0:,} แปลง)").format(trx(len(done_view))))
        if len(done_view):
            W = [3, 1.3, 2, 2.5, 0.8]
            for c, t in zip(st.columns(W), ["หมู่บ้าน", "เลขแปลง", "วันที่เสร็จ", "หมายเหตุ", "ลบ"]):
                c.markdown(f"**{tr(t)}**")
            with st.container(height=420):
                for _, r in done_view.iterrows():
                    c = st.columns(W)
                    c[0].markdown(r["Village"])
                    c[1].markdown(str(r["Attribute"]))
                    c[2].markdown(r["วันที่เสร็จ"])
                    c[3].markdown(r["หมายเหตุ"] or "-")
                    if c[4].button("✕", key=f"del_{r['_key']}", help=tr("ยกเลิกสถานะเสร็จของแปลงนี้")):
                        prog.pop(r["_key"], None)
                        save_progress(prog)
                        st.session_state.trk_ver += 1
                        st.session_state.trk_msg = tr("ยกเลิกสถานะ {0} แปลง {1} แล้ว").format(trx(r['Village']), trx(r['Attribute']))
                        st.rerun()
        else:
            st.caption(tr("ยังไม่มีแปลงที่ทำเครื่องหมายว่าเสร็จ"))

        # รายงาน
        st.markdown(tr("##### รายงาน"))
        st.caption(tr("ณ วันที่ {0} เสร็จแล้ว {1:,} จาก {2:,} แปลง ({3} จาก {4} หมู่บ้านเสร็จครบ)").format(trx(now_th().strftime('%d/%m/%Y %H:%M')), trx(done_n), trx(total), trx(int((summ['คงเหลือ'] == 0).sum())), trx(len(summ))))
        rep = trk.drop(columns=["_key"]).copy()
        rep["สถานะ"] = rep["เสร็จแล้ว"].map({True: "เสร็จแล้ว", False: "ยังไม่เสร็จ"})
        rep = rep.drop(columns=["เสร็จแล้ว"])
        stamp = now_th().strftime("%Y%m%d_%H%M")
        d1, d2 = st.columns(2)
        try:
            mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            d1.download_button(tr("ดาวน์โหลดรายงานสรุปรายหมู่บ้าน (Excel)"),
                               to_xlsx({"สรุปรายหมู่บ้าน": summ}),
                               f"report_summary_{stamp}.xlsx", mime, use_container_width=True)
            d2.download_button(tr("ดาวน์โหลดรายงานรายแปลง (Excel)"),
                               to_xlsx({"รายงานรายแปลง": rep}, green_col="สถานะ"),
                               f"report_plots_{stamp}.xlsx", mime, use_container_width=True)
        except ImportError:
            st.warning(tr("ยังไม่ได้ติดตั้ง openpyxl จึงดาวน์โหลดเป็น CSV แทน (ติดตั้งด้วย pip install openpyxl)"))
            d1.download_button(tr("ดาวน์โหลดรายงานสรุปรายหมู่บ้าน (CSV)"),
                               summ.to_csv(index=False).encode("utf-8-sig"),
                               f"report_summary_{stamp}.csv", "text/csv", use_container_width=True)
            d2.download_button(tr("ดาวน์โหลดรายงานรายแปลง (CSV)"),
                               rep.to_csv(index=False).encode("utf-8-sig"),
                               f"report_plots_{stamp}.csv", "text/csv", use_container_width=True)

    # ---- Re-classify villages any time
    with t_vil:
        st.markdown(tr("#### แก้ไขการจำแนกหมู่บ้าน"))
        edited = meta_editor("meta_workspace")
        if st.button(tr("บันทึกและอัปเดตข้อมูล"), type="primary", key="save_meta"):
            st.session_state.meta = edited
            st.session_state.df = build_df(st.session_state.sources, edited)
            st.session_state.route_map = st.session_state.route_summary = None
            st.success(tr("อัปเดตการจำแนกหมู่บ้านแล้ว (ต้องคำนวณระยะทางทั้งหมดใหม่)"))
            st.rerun()

    # ---- Quick calculator
    with t_quick:
        quick_calc()

    st.caption(tr("หมายเหตุ: ระยะทางและเวลาเป็นค่าประมาณจาก OSRM ค่าน้ำมันคำนวณจากค่าที่ตั้งไว้ในแถบด้านซ้าย"))