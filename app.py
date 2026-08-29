import streamlit as st
import pandas as pd
import os
import io
import tempfile
import time
import datetime
from parser import InvoiceParser
from database import InvoiceDatabase, get_user_database
from exporter import InvoiceExporter
from i18n import t
import analytics
from auth import (
    init_auth_db, login_user, register_user,
    get_user_trial_info, get_all_registered_users, admin_extend_user_trial,
    admin_reset_user_password, admin_delete_user, user_forgot_password, delete_my_account
)

# Khởi tạo cơ sở dữ liệu xác thực
init_auth_db()

st.set_page_config(
    page_title="E-Invoice Hub | TT 91/2026/TT-BTC",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= QUẢN TRỊ TRẠNG THÁI (SESSION STATE) & CALLBACKS =================
def on_lang_change():
    if "hdr_sel_lang" in st.session_state and st.session_state["hdr_sel_lang"]:
        st.session_state["lang"] = st.session_state["hdr_sel_lang"]
    elif "lang_login" in st.session_state and st.session_state["lang_login"]:
        st.session_state["lang"] = st.session_state["lang_login"]

def on_theme_change():
    if "hdr_sel_theme" in st.session_state and st.session_state["hdr_sel_theme"]:
        st.session_state["theme"] = st.session_state["hdr_sel_theme"]
    elif "th_login" in st.session_state and st.session_state["th_login"]:
        st.session_state["theme"] = st.session_state["th_login"]

if "lang" not in st.session_state:
    st.session_state["lang"] = "vi"
if "logged_in_user" not in st.session_state:
    st.session_state["logged_in_user"] = None
if "theme" not in st.session_state:
    st.session_state["theme"] = "light"
if "is_temp_mode" not in st.session_state:
    st.session_state["is_temp_mode"] = False
if "custom_export_dir" not in st.session_state:
    st.session_state["custom_export_dir"] = os.path.join(os.path.expanduser("~"), "Downloads")
if "preview_data" not in st.session_state:
    st.session_state["preview_data"] = []
if "donated_confirmed" not in st.session_state:
    st.session_state["donated_confirmed"] = False

lang = st.session_state["lang"]
theme = st.session_state["theme"]
is_temp = st.session_state["is_temp_mode"]

# ================= BỘ PHONG CÁCH TƯƠNG PHẢN CAO TOÀN DIỆN (CHỐNG TRÙNG MÀU NỀN & CHỮ 100%) =================
if theme == "dark":
    css = """<style>
.stAppDeployButton, #MainMenu, header, footer, [data-testid="stHeader"] { display: none !important; }
.block-container {
    padding-top: 0.35rem !important;
    padding-bottom: 0.5rem !important;
    padding-left: 1.25rem !important;
    padding-right: 1.25rem !important;
    max-width: 99% !important;
}
[data-testid="stSidebarContent"] {
    padding-top: 0.35rem !important;
    padding-bottom: 0.5rem !important;
}
.stApp {
    background-color: #0B0F19 !important;
    color: #F8FAFC !important;
}
[data-testid="stSidebar"] {
    background-color: #111827 !important;
    border-right: 1px solid #1F2937 !important;
}
.stApp p, .stApp span, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
    color: #F8FAFC !important;
}
.main-header {
    font-size: 21px;
    font-weight: 800;
    color: #60A5FA !important;
    margin-bottom: 0px;
    line-height: 1.15;
}
.sub-header {
    font-size: 11.5px;
    color: #9CA3AF !important;
    margin-bottom: 6px;
}
.tt-badge {
    background-color: #064E3B !important;
    color: #6EE7B7 !important;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: bold;
    border: 1px solid #059669;
}
.user-badge {
    background-color: #1E3A8A !important;
    color: #BFDBFE !important;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: bold;
    border: 1px solid #3B82F6;
}
.pro-badge {
    background-color: #78350F !important;
    color: #FDE68A !important;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: bold;
    border: 1px solid #D97706;
}
.basic-badge {
    background-color: #374151 !important;
    color: #D1D5DB !important;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: bold;
}
[data-testid="stMetricValue"] {
    color: #38BDF8 !important;
    font-weight: 700 !important;
}
[data-testid="stMetricLabel"] {
    color: #9CA3AF !important;
}

/* INPUTS, TEXTAREAS & SELECTBOXES TRONG DARK MODE */
input, textarea, [data-baseweb="input"] input, [data-baseweb="textarea"] textarea {
    background-color: #1F2937 !important;
    color: #F9FAFB !important;
    -webkit-text-fill-color: #F9FAFB !important;
    border: 1px solid #4B5563 !important;
    border-radius: 6px !important;
}
[data-baseweb="input"], [data-baseweb="base-input"] {
    background-color: #1F2937 !important;
}
input::placeholder, textarea::placeholder {
    color: #9CA3AF !important;
    -webkit-text-fill-color: #9CA3AF !important;
}
[data-baseweb="select"] > div {
    background-color: #1F2937 !important;
    border-color: #4B5563 !important;
}
[data-baseweb="select"] * {
    color: #F9FAFB !important;
    -webkit-text-fill-color: #F9FAFB !important;
}
[data-baseweb="popover"], [data-baseweb="menu"], ul[role="listbox"], li[role="option"] {
    background-color: #1F2937 !important;
    color: #F9FAFB !important;
}
li[role="option"]:hover, li[role="option"][aria-selected="true"] {
    background-color: #374151 !important;
}

/* TABS TRONG DARK MODE */
button[data-baseweb="tab"] {
    color: #9CA3AF !important;
    background-color: transparent !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #60A5FA !important;
    font-weight: bold !important;
    border-bottom-color: #60A5FA !important;
}

[data-testid="stExpander"] {
    background-color: #111827 !important;
    border: 1px solid #374151 !important;
}
[data-testid="stExpander"] * {
    color: #F9FAFB !important;
}

/* NỔI BẬT NÚT UPLOAD & DROPZONE TRONG DARK MODE */
[data-testid="stFileUploaderDropzone"] {
    background-color: #1E293B !important;
    border: 2px dashed #3B82F6 !important;
    border-radius: 8px !important;
    padding: 10px 14px !important;
}
[data-testid="stFileUploaderDropzone"] * {
    color: #F8FAFC !important;
}
[data-testid="stFileUploaderDropzone"] button {
    background-color: #2563EB !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 6px 18px !important;
    box-shadow: 0 2px 6px rgba(37,99,235,0.4) !important;
}
[data-testid="stFileUploaderDropzone"] button:hover {
    background-color: #1D4ED8 !important;
}

/* NÚT BẤM (BUTTONS, POPOVER, DOWNLOAD, FORM) TRONG DARK MODE - CHỐNG NỀN TRẮNG CHỮ TRẮNG */
button:not([data-baseweb="tab"]),
.stButton button, 
div[data-testid="stButton"] button,
div[data-testid="stButton"] > button,
div[data-testid="stPopover"] button,
div[data-testid="stPopover"] > button,
div[data-testid="stDownloadButton"] button,
div[data-testid="stDownloadButton"] > button,
div[data-testid="stFormSubmitButton"] button,
button[data-testid="stBaseButton-secondary"],
button[data-baseweb="button"]:not([data-baseweb="tab"]) {
    background-color: #1F2937 !important;
    color: #F8FAFC !important;
    -webkit-text-fill-color: #F8FAFC !important;
    border: 1px solid #4B5563 !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
}

button:not([data-baseweb="tab"]):hover,
.stButton button:hover, 
div[data-testid="stButton"] button:hover,
div[data-testid="stButton"] > button:hover,
div[data-testid="stPopover"] button:hover,
div[data-testid="stPopover"] > button:hover,
div[data-testid="stDownloadButton"] button:hover,
div[data-testid="stDownloadButton"] > button:hover,
div[data-testid="stFormSubmitButton"] button:hover,
button[data-testid="stBaseButton-secondary"]:hover,
button[data-baseweb="button"]:not([data-baseweb="tab"]):hover {
    background-color: #374151 !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    border-color: #60A5FA !important;
}

button[kind="primary"],
.stButton button[kind="primary"], 
div[data-testid="stButton"] button[kind="primary"],
div[data-testid="stButton"] > button[kind="primary"],
div[data-testid="stDownloadButton"] button[kind="primary"],
div[data-testid="stDownloadButton"] > button[kind="primary"],
div[data-testid="stFormSubmitButton"] button[kind="primary"],
button[data-testid="stBaseButton-primary"] {
    background-color: #2563EB !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    border: 1px solid #3B82F6 !important;
}

button[kind="primary"]:hover,
.stButton button[kind="primary"]:hover, 
div[data-testid="stButton"] button[kind="primary"]:hover,
div[data-testid="stButton"] > button[kind="primary"]:hover,
div[data-testid="stDownloadButton"] button[kind="primary"]:hover,
div[data-testid="stDownloadButton"] > button[kind="primary"]:hover,
div[data-testid="stFormSubmitButton"] button[kind="primary"]:hover,
button[data-testid="stBaseButton-primary"]:hover {
    background-color: #1D4ED8 !important;
    border-color: #60A5FA !important;
}

div[data-testid="stPopoverBody"] {
    background-color: #111827 !important;
    border: 1px solid #374151 !important;
}
div[data-testid="stPopoverBody"] * {
    color: #F8FAFC !important;
}
</style>"""
elif theme == "sakura":
    css = """<style>
.stAppDeployButton, #MainMenu, header, footer, [data-testid="stHeader"] { display: none !important; }
.block-container {
    padding-top: 0.35rem !important;
    padding-bottom: 0.5rem !important;
    padding-left: 1.25rem !important;
    padding-right: 1.25rem !important;
    max-width: 99% !important;
}
[data-testid="stSidebarContent"] {
    padding-top: 0.35rem !important;
    padding-bottom: 0.5rem !important;
}
.stApp {
    background-color: #FFF1F2 !important;
    color: #4C0519 !important;
}
[data-testid="stSidebar"] {
    background-color: #FFF5F7 !important;
    border-right: 1px solid #FECDD3 !important;
}
.stApp p, .stApp span, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
    color: #4C0519 !important;
}
.main-header {
    font-size: 21px;
    font-weight: 800;
    color: #BE185D !important;
    margin-bottom: 0px;
    line-height: 1.15;
}
.sub-header {
    font-size: 11.5px;
    color: #9D174D !important;
    margin-bottom: 6px;
}
.tt-badge {
    background-color: #FFE4E6 !important;
    color: #9F1239 !important;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: bold;
    border: 1px solid #FDA4AF;
}
.user-badge {
    background-color: #FCE7F3 !important;
    color: #831843 !important;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: bold;
    border: 1px solid #F472B6;
}
.pro-badge {
    background-color: #FDF2F8 !important;
    color: #BE185D !important;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: bold;
    border: 1px solid #F43F5E;
}
.basic-badge {
    background-color: #FFF1F2 !important;
    color: #881337 !important;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: bold;
    border: 1px solid #FECDD3;
}
[data-testid="stMetricValue"] {
    color: #E11D48 !important;
    font-weight: 700 !important;
}
[data-testid="stMetricLabel"] {
    color: #9D174D !important;
}

/* INPUTS, TEXTAREAS & SELECTBOXES TRONG SAKURA MODE */
input, textarea, [data-baseweb="input"] input, [data-baseweb="textarea"] textarea {
    background-color: #FFFFFF !important;
    color: #4C0519 !important;
    -webkit-text-fill-color: #4C0519 !important;
    border: 1px solid #FECDD3 !important;
    border-radius: 6px !important;
}
[data-baseweb="input"], [data-baseweb="base-input"] {
    background-color: #FFFFFF !important;
}
input::placeholder, textarea::placeholder {
    color: #9D174D !important;
    -webkit-text-fill-color: #9D174D !important;
}
[data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    border-color: #FECDD3 !important;
}
[data-baseweb="select"] * {
    color: #4C0519 !important;
    -webkit-text-fill-color: #4C0519 !important;
}
[data-baseweb="popover"], [data-baseweb="menu"], ul[role="listbox"], li[role="option"] {
    background-color: #FFFFFF !important;
    color: #4C0519 !important;
}
li[role="option"]:hover, li[role="option"][aria-selected="true"] {
    background-color: #FFE4E6 !important;
}

/* TABS TRONG SAKURA MODE */
button[data-baseweb="tab"] {
    color: #9D174D !important;
    background-color: transparent !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #E11D48 !important;
    font-weight: bold !important;
    border-bottom-color: #E11D48 !important;
}

[data-testid="stExpander"] {
    background-color: #FFFFFF !important;
    border: 1px solid #FECDD3 !important;
}
[data-testid="stExpander"] * {
    color: #4C0519 !important;
}

/* NỔI BẬT NÚT UPLOAD & DROPZONE TRONG SAKURA MODE */
[data-testid="stFileUploaderDropzone"] {
    background-color: #FFF5F7 !important;
    border: 2px dashed #F43F5E !important;
    border-radius: 8px !important;
    padding: 10px 14px !important;
}
[data-testid="stFileUploaderDropzone"] * {
    color: #881337 !important;
}
[data-testid="stFileUploaderDropzone"] button {
    background-color: #E11D48 !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 6px 18px !important;
    box-shadow: 0 2px 6px rgba(225,29,72,0.3) !important;
}
[data-testid="stFileUploaderDropzone"] button:hover {
    background-color: #BE123C !important;
}

/* NÚT BẤM (BUTTONS, POPOVER, DOWNLOAD, FORM) TRONG SAKURA MODE */
button:not([data-baseweb="tab"]),
.stButton button, 
div[data-testid="stButton"] button,
div[data-testid="stButton"] > button,
div[data-testid="stPopover"] button,
div[data-testid="stPopover"] > button,
div[data-testid="stDownloadButton"] button,
div[data-testid="stDownloadButton"] > button,
div[data-testid="stFormSubmitButton"] button,
button[data-testid="stBaseButton-secondary"],
button[data-baseweb="button"]:not([data-baseweb="tab"]) {
    background-color: #FFFFFF !important;
    color: #4C0519 !important;
    -webkit-text-fill-color: #4C0519 !important;
    border: 1px solid #FECDD3 !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
}

button:not([data-baseweb="tab"]):hover,
.stButton button:hover, 
div[data-testid="stButton"] button:hover,
div[data-testid="stButton"] > button:hover,
div[data-testid="stPopover"] button:hover,
div[data-testid="stPopover"] > button:hover,
div[data-testid="stDownloadButton"] button:hover,
div[data-testid="stDownloadButton"] > button:hover,
div[data-testid="stFormSubmitButton"] button:hover,
button[data-testid="stBaseButton-secondary"]:hover,
button[data-baseweb="button"]:not([data-baseweb="tab"]):hover {
    background-color: #FFF1F2 !important;
    color: #BE185D !important;
    -webkit-text-fill-color: #BE185D !important;
    border-color: #F43F5E !important;
}

button[kind="primary"],
.stButton button[kind="primary"], 
div[data-testid="stButton"] button[kind="primary"],
div[data-testid="stButton"] > button[kind="primary"],
div[data-testid="stDownloadButton"] button[kind="primary"],
div[data-testid="stDownloadButton"] > button[kind="primary"],
div[data-testid="stFormSubmitButton"] button[kind="primary"],
button[data-testid="stBaseButton-primary"] {
    background-color: #E11D48 !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    border: 1px solid #F43F5E !important;
}

button[kind="primary"]:hover,
.stButton button[kind="primary"]:hover, 
div[data-testid="stButton"] button[kind="primary"]:hover,
div[data-testid="stButton"] > button[kind="primary"]:hover,
div[data-testid="stDownloadButton"] button[kind="primary"]:hover,
div[data-testid="stDownloadButton"] > button[kind="primary"]:hover,
div[data-testid="stFormSubmitButton"] button[kind="primary"]:hover,
button[data-testid="stBaseButton-primary"]:hover {
    background-color: #BE123C !important;
}

div[data-testid="stPopoverBody"] {
    background-color: #FFFFFF !important;
    border: 1px solid #FECDD3 !important;
}
div[data-testid="stPopoverBody"] * {
    color: #4C0519 !important;
}
</style>"""
else:
    css = """<style>
.stAppDeployButton, #MainMenu, header, footer, [data-testid="stHeader"] { display: none !important; }
.block-container {
    padding-top: 0.35rem !important;
    padding-bottom: 0.5rem !important;
    padding-left: 1.25rem !important;
    padding-right: 1.25rem !important;
    max-width: 99% !important;
}
[data-testid="stSidebarContent"] {
    padding-top: 0.35rem !important;
    padding-bottom: 0.5rem !important;
}
.stApp {
    background-color: #F8FAFC !important;
    color: #0F172A !important;
}
[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
    border-right: 1px solid #E2E8F0 !important;
}
.stApp p, .stApp span, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
    color: #0F172A !important;
}
.main-header {
    font-size: 21px;
    font-weight: 800;
    color: #1E3A8A !important;
    margin-bottom: 0px;
    line-height: 1.15;
}
.sub-header {
    font-size: 11.5px;
    color: #475569 !important;
    margin-bottom: 6px;
}
.tt-badge {
    background-color: #DCFCE7 !important;
    color: #166534 !important;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: bold;
    border: 1px solid #86EFAC;
}
.user-badge {
    background-color: #DBEAFE !important;
    color: #1E40AF !important;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: bold;
    border: 1px solid #93C5FD;
}
.pro-badge {
    background-color: #FEF3C7 !important;
    color: #92400E !important;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: bold;
    border: 1px solid #FCD34D;
}
.basic-badge {
    background-color: #F1F5F9 !important;
    color: #475569 !important;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: bold;
    border: 1px solid #CBD5E1;
}
[data-testid="stMetricValue"] {
    color: #1E3A8A !important;
    font-weight: 700 !important;
}
[data-testid="stMetricLabel"] {
    color: #475569 !important;
}

/* INPUTS, TEXTAREAS & SELECTBOXES TRONG LIGHT MODE */
input, textarea, [data-baseweb="input"] input, [data-baseweb="textarea"] textarea {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    -webkit-text-fill-color: #0F172A !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 6px !important;
}
[data-baseweb="input"], [data-baseweb="base-input"] {
    background-color: #FFFFFF !important;
}
input::placeholder, textarea::placeholder {
    color: #64748B !important;
    -webkit-text-fill-color: #64748B !important;
}
[data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    border-color: #CBD5E1 !important;
}
[data-baseweb="select"] * {
    color: #0F172A !important;
    -webkit-text-fill-color: #0F172A !important;
}
[data-baseweb="popover"], [data-baseweb="menu"], ul[role="listbox"], li[role="option"] {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
}
li[role="option"]:hover, li[role="option"][aria-selected="true"] {
    background-color: #EFF6FF !important;
}

/* TABS TRONG LIGHT MODE */
button[data-baseweb="tab"] {
    color: #475569 !important;
    background-color: transparent !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #2563EB !important;
    font-weight: bold !important;
    border-bottom-color: #2563EB !important;
}

[data-testid="stExpander"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
}
[data-testid="stExpander"] * {
    color: #0F172A !important;
}

/* NỔI BẬT NÚT UPLOAD & DROPZONE TRONG LIGHT MODE */
[data-testid="stFileUploaderDropzone"] {
    background-color: #EFF6FF !important;
    border: 2px dashed #2563EB !important;
    border-radius: 8px !important;
    padding: 10px 14px !important;
}
[data-testid="stFileUploaderDropzone"] * {
    color: #1E293B !important;
}
[data-testid="stFileUploaderDropzone"] button {
    background-color: #2563EB !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 6px 18px !important;
    box-shadow: 0 2px 6px rgba(37,99,235,0.25) !important;
}
[data-testid="stFileUploaderDropzone"] button:hover {
    background-color: #1D4ED8 !important;
}

/* NÚT BẤM (BUTTONS, POPOVER, DOWNLOAD, FORM) TRONG LIGHT MODE */
button:not([data-baseweb="tab"]),
.stButton button, 
div[data-testid="stButton"] button,
div[data-testid="stButton"] > button,
div[data-testid="stPopover"] button,
div[data-testid="stPopover"] > button,
div[data-testid="stDownloadButton"] button,
div[data-testid="stDownloadButton"] > button,
div[data-testid="stFormSubmitButton"] button,
button[data-testid="stBaseButton-secondary"],
button[data-baseweb="button"]:not([data-baseweb="tab"]) {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    -webkit-text-fill-color: #0F172A !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
}

button:not([data-baseweb="tab"]):hover,
.stButton button:hover, 
div[data-testid="stButton"] button:hover,
div[data-testid="stButton"] > button:hover,
div[data-testid="stPopover"] button:hover,
div[data-testid="stPopover"] > button:hover,
div[data-testid="stDownloadButton"] button:hover,
div[data-testid="stDownloadButton"] > button:hover,
div[data-testid="stFormSubmitButton"] button:hover,
button[data-testid="stBaseButton-secondary"]:hover,
button[data-baseweb="button"]:not([data-baseweb="tab"]):hover {
    background-color: #F8FAFC !important;
    color: #1E40AF !important;
    -webkit-text-fill-color: #1E40AF !important;
    border-color: #3B82F6 !important;
}

button[kind="primary"],
.stButton button[kind="primary"], 
div[data-testid="stButton"] button[kind="primary"],
div[data-testid="stButton"] > button[kind="primary"],
div[data-testid="stDownloadButton"] button[kind="primary"],
div[data-testid="stDownloadButton"] > button[kind="primary"],
div[data-testid="stFormSubmitButton"] button[kind="primary"],
button[data-testid="stBaseButton-primary"] {
    background-color: #2563EB !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    border: 1px solid #1D4ED8 !important;
}

button[kind="primary"]:hover,
.stButton button[kind="primary"]:hover, 
div[data-testid="stButton"] button[kind="primary"]:hover,
div[data-testid="stButton"] > button[kind="primary"]:hover,
div[data-testid="stDownloadButton"] button[kind="primary"]:hover,
div[data-testid="stDownloadButton"] > button[kind="primary"]:hover,
div[data-testid="stFormSubmitButton"] button[kind="primary"]:hover,
button[data-testid="stBaseButton-primary"]:hover {
    background-color: #1D4ED8 !important;
}

div[data-testid="stPopoverBody"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
}
div[data-testid="stPopoverBody"] * {
    color: #0F172A !important;
}
</style>"""

st.html(css)

# =========================================================================
# 🔒 MÀN HÌNH ĐĂNG NHẬP & ĐĂNG KÝ NHẬN 30 NGÀY DÙNG THỬ
# =========================================================================
if st.session_state.get("logged_in_user") is None:
    auth_h1, auth_h2 = st.columns([2, 1])
    with auth_h1:
        st.markdown(f"<h2 style='margin-bottom:2px; color:#2563EB;'>🧾 {t('auth_title', lang)}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:13px; color:#64748B; margin-top:0;'>{t('auth_subtitle', lang)}</p>", unsafe_allow_html=True)
    with auth_h2:
        c_l, c_t = st.columns(2)
        with c_l:
            sel_lang_login = st.selectbox(
                t("lang_label", lang),
                ["vi", "en", "zh"],
                format_func=lambda x: "🇻🇳 " + t("lang_opt_vi", lang) if x=="vi" else ("🇬🇧 " + t("lang_opt_en", lang) if x=="en" else "🇨🇳 " + t("lang_opt_zh", lang)),
                index=["vi","en","zh"].index(lang) if lang in ["vi","en","zh"] else 0,
                key="lang_login",
                on_change=on_lang_change
            )
        with c_t:
            sel_th_login = st.selectbox(
                t("theme_label", lang),
                ["light", "dark", "sakura"],
                format_func=lambda x: t("theme_light", lang) if x=="light" else (t("theme_dark", lang) if x=="dark" else t("theme_sakura", lang)),
                index=["light","dark","sakura"].index(theme) if theme in ["light","dark","sakura"] else 0,
                key="th_login",
                on_change=on_theme_change
            )
                
    st.markdown("---")
    
    auth_col1, auth_col2 = st.columns([1.1, 0.9])
    with auth_col1:
        box_bg = "#111827" if theme == "dark" else ("#FFF5F7" if theme == "sakura" else "#F8FAFC")
        box_border = "#1F2937" if theme == "dark" else ("#FECDD3" if theme == "sakura" else "#E2E8F0")
        box_title = "#60A5FA" if theme == "dark" else ("#BE185D" if theme == "sakura" else "#1E3A8A")
        card_item_bg = "#1E293B" if theme == "dark" else ("#FFFFFF" if theme == "sakura" else "#FFFFFF")
        card_item_border = "#334155" if theme == "dark" else ("#FECDD3" if theme == "sakura" else "#CBD5E1")
        
        st.markdown(f"""
        <div style="background: {box_bg}; border: 1px solid {box_border}; border-radius: 12px; padding: 18px; margin-bottom: 15px;">
            <h3 style="color: {box_title}; margin-top: 0; margin-bottom: 6px; font-size: 17px;">{t('trial_title', lang)}</h3>
            <p style="font-size: 13px; line-height: 1.4; color: {'#94A3B8' if theme=='dark' else '#64748B'}; margin-bottom: 12px;">
                {t('trial_desc', lang)}
            </p>
            <div style="display: flex; flex-direction: column; gap: 7px; font-size: 12.5px;">
                <div style="background: {card_item_bg}; border: 1px solid {card_item_border}; border-radius: 7px; padding: 7px 11px; display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 14px;">⚡</span> <b>{t('feat_1', lang)}</b>
                </div>
                <div style="background: {card_item_bg}; border: 1px solid {card_item_border}; border-radius: 7px; padding: 7px 11px; display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 14px;">📊</span> <b>{t('feat_2', lang)}</b>
                </div>
                <div style="background: {card_item_bg}; border: 1px solid {card_item_border}; border-radius: 7px; padding: 7px 11px; display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 14px;">💳</span> <b>{t('feat_3', lang)}</b>
                </div>
                <div style="background: {card_item_bg}; border: 1px solid {card_item_border}; border-radius: 7px; padding: 7px 11px; display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 14px;">🚨</span> <b>{t('feat_4', lang)}</b>
                </div>
                <div style="background: {card_item_bg}; border: 1px solid {card_item_border}; border-radius: 7px; padding: 7px 11px; display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 14px;">📈</span> <b>{t('feat_5', lang)}</b>
                </div>
                <div style="background: {card_item_bg}; border: 1px solid {card_item_border}; border-radius: 7px; padding: 7px 11px; display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 14px;">🔒</span> <b>{t('feat_6', lang)}</b>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with auth_col2:
        tab_login, tab_reg, tab_forgot = st.tabs([
            t("tab_signin", lang),
            t("tab_signup", lang),
            "🔄 " + ("Quên Mật Khẩu" if lang=="vi" else ("Forgot Password" if lang=="en" else "找回密码"))
        ])
        
        with tab_login:
            st.markdown(f"##### {t('signin_header', lang)}")
            log_user = st.text_input(t("lbl_username", lang), key="login_u", placeholder=t("ph_username", lang)).strip()
            log_pass = st.text_input(t("lbl_password", lang), type="password", key="login_p", placeholder=t("ph_password", lang)).strip()
            
            if st.button(t("btn_login", lang), type="primary", use_container_width=True):
                if not log_user or not log_pass:
                    st.error("Vui lòng nhập đầy đủ Tên đăng nhập và Mật khẩu!" if lang=="vi" else ("Please enter both username and password!" if lang=="en" else "请输入用户名和密码！"))
                else:
                    success, msg, udata = login_user(log_user, log_pass)
                    if success:
                        st.session_state["logged_in_user"] = udata
                        st.session_state["user_id"] = udata["username"]
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                        
            st.markdown("---")
            st.caption(t("quick_trial_caption", lang))
            c_d1, c_d2 = st.columns(2)
            with c_d1:
                if st.button(t("btn_demo_user", lang), use_container_width=True, help="Vào ngay tài khoản mẫu ketoan_demo"):
                    success, msg, udata = login_user("ketoan_demo", "123456")
                    if success:
                        st.session_state["logged_in_user"] = udata
                        st.session_state["user_id"] = "ketoan_demo"
                        st.rerun()
            with c_d2:
                if st.button(t("btn_admin_user", lang), use_container_width=True, help="Đăng nhập tài khoản Quản trị viên"):
                    success, msg, udata = login_user("hznguyen1997", "Anthumatmeo020922")
                    if success:
                        st.session_state["logged_in_user"] = udata
                        st.session_state["user_id"] = "hznguyen1997"
                        st.rerun()

        with tab_reg:
            st.markdown(f"##### {t('signup_header', lang)}")
            st.caption(t("signup_caption", lang))
            reg_u = st.text_input(t("lbl_reg_username", lang), key="reg_u", placeholder=t("ph_username", lang)).strip()
            reg_p = st.text_input(t("lbl_reg_password", lang), type="password", key="reg_p", placeholder=t("ph_reg_password", lang)).strip()
            reg_fn = st.text_input(t("lbl_fullname", lang), key="reg_fn", placeholder=t("ph_fullname", lang)).strip()
            reg_phone = st.text_input(t("lbl_phone", lang), key="reg_phone", placeholder="09xxxxxxxx").strip()
            reg_email = st.text_input(t("lbl_email", lang), key="reg_email", placeholder="email@company.com").strip()
            reg_comp = st.text_input(t("lbl_company", lang), key="reg_comp", placeholder="Company / Enterprise").strip()
            
            if st.button(t("btn_register_submit", lang), type="primary", use_container_width=True):
                if not reg_u or not reg_p or not reg_fn:
                    st.error("Vui lòng điền Tên đăng nhập, Mật khẩu và Họ tên!" if lang=="vi" else ("Please fill Username, Password, and Full Name!" if lang=="en" else "请填写用户名、密码和姓名！"))
                else:
                    success, msg, udata = register_user(
                        username=reg_u,
                        password=reg_p,
                        full_name=reg_fn,
                        email=reg_email,
                        phone=reg_phone,
                        company=reg_comp
                    )
                    if success:
                        st.session_state["logged_in_user"] = udata
                        st.session_state["user_id"] = udata["username"]
                        st.balloons()
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                        
        with tab_forgot:
            st.markdown(f"##### {t('forgot_header', lang)}")
            st.caption(t("forgot_caption", lang))
            fg_u = st.text_input(t("lbl_username", lang), key="fg_u", placeholder=t("ph_username", lang)).strip()
            fg_contact = st.text_input(t("lbl_forgot_contact", lang), key="fg_contact", placeholder=t("ph_forgot_contact", lang)).strip()
            fg_new_p = st.text_input(t("lbl_forgot_newpass", lang), type="password", key="fg_new_p", placeholder=t("ph_reg_password", lang)).strip()
            
            if st.button(t("btn_forgot_submit", lang), type="primary", use_container_width=True):
                if not fg_u or not fg_contact or not fg_new_p:
                    st.error(t("forgot_err_missing", lang))
                else:
                    ok_rst, rst_msg = user_forgot_password(fg_u, fg_contact, fg_new_p)
                    if ok_rst:
                        st.success(rst_msg)
                    else:
                        st.error(rst_msg)
            
            st.markdown("---")
            st.caption("📞 " + ("Nếu bạn quên cả SĐT/Email đăng ký, vui lòng liên hệ:" if lang=="vi" else ("If you forgot both Phone/Email, please contact:" if lang=="en" else "若遗忘注册信息，请联系：")))
            st.markdown("• **" + ("Quản trị viên:" if lang=="vi" else ("Administrator:" if lang=="en" else "系统管理员：")) + "** `Nguyễn Hoàng Giang`  \n• **" + ("SĐT / Zalo:" if lang=="vi" else ("Phone / Zalo:" if lang=="en" else "电话 / Zalo：")) + "** `09727 858 67`  \n• **Email:** `hznguyen1993@gmail.com`")
    st.stop()

# =========================================================================
# 👤 XÁC THỰC THÀNH CÔNG -> TẢI DỮ LIỆU TÀI KHOẢN
# =========================================================================
user_data = st.session_state.get("logged_in_user")
if not user_data:
    user_data = {"username": "ketoan_demo", "full_name": "Kế Toán Trải Nghiệm Mẫu"}
current_user = user_data["username"]
trial_info = get_user_trial_info(current_user)
plan = trial_info["plan"]
db = get_user_database(user_id=current_user, is_temp=is_temp)

# =========================================================================
# 🌟 BỐ CỤC HEADER & CỤM CÔNG CỤ 1/3 GÓC PHẢI (RIGHT 1/3 TOOLBAR)
# =========================================================================
head_left, head_right = st.columns([1.6, 1.4])

with head_left:
    if trial_info.get("is_admin"):
        plan_badge_txt = t("admin_perm_badge", lang)
    else:
        plan_badge_txt = f"🎁 {t('days_remaining_badge', lang).format(d=trial_info['days_remaining'])}"
    plan_badge = f"<span class='pro-badge'>{plan_badge_txt}</span>"
    st.markdown(f'<div class="main-header">🧾 {t("app_title", lang)} <span class="user-badge">👤 {trial_info["full_name"]}</span> {plan_badge}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">{t("app_subtitle", lang)}</div>', unsafe_allow_html=True)

with head_right:
    col_l, col_p, col_t, col_out = st.columns([1.1, 1.2, 1.0, 0.9])
    
    with col_l:
        lang_map = {
            "vi": "🇻🇳 " + t("lang_opt_vi", lang),
            "en": "🇬🇧 " + t("lang_opt_en", lang),
            "zh": "🇨🇳 " + t("lang_opt_zh", lang)
        }
        sel_lang = st.selectbox(
            t("lang_label", lang),
            options=list(lang_map.keys()),
            format_func=lambda k: lang_map[k],
            index=list(lang_map.keys()).index(lang) if lang in lang_map else 0,
            key="hdr_sel_lang",
            on_change=on_lang_change
        )

    with col_p:
        if trial_info.get("is_admin"):
            plan_badge_label = t("admin_perm_plan", lang)
        else:
            plan_badge_label = t("days_remaining_plan", lang).format(d=trial_info['days_remaining'])
        st.selectbox(
            t("plan_label", lang),
            options=[plan],
            format_func=lambda k: plan_badge_label,
            index=0,
            key="hdr_sel_plan"
        )

    with col_t:
        theme_map = {
            "light": t("theme_light", lang),
            "dark": t("theme_dark", lang),
            "sakura": t("theme_sakura", lang)
        }
        theme_options = ["light", "dark", "sakura"]
        theme_idx = theme_options.index(theme) if theme in theme_options else 0
        sel_theme = st.selectbox(
            t("theme_label", lang),
            options=theme_options,
            format_func=lambda k: theme_map[k],
            index=theme_idx,
            key="hdr_sel_theme",
            on_change=on_theme_change
        )

    with col_out:
        st.markdown("<div style='padding-top:24px;'>", unsafe_allow_html=True)
        if st.button(t("btn_logout", lang), key="btn_logout_top", help=t("btn_logout", lang)):
            st.session_state["logged_in_user"] = None
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================================
# 👤 THANH BÊN: LOGO CHUYÊN NGHIỆP CĂN ĐỈNH & HỒ SƠ DÙNG THỬ 30 NGÀY
# =========================================================================
with st.sidebar:
    logo_brand_color = "#60A5FA" if theme == "dark" else ("#BE185D" if theme == "sakura" else "#1E3A8A")
    logo_badge_gradient = "linear-gradient(135deg, #EC4899 0%, #BE185D 100%)" if theme == "sakura" else "linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)"
    logo_html = f"""
    <div style="display: flex; align-items: center; gap: 10px; margin-top: 0px; margin-bottom: 10px; padding: 0;">
        <div style="width: 38px; height: 38px; border-radius: 8px; background: {logo_badge_gradient}; display: flex; align-items: center; justify-content: center; box-shadow: 0 3px 8px rgba(37,99,235,0.3);">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
                <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
        </div>
        <div>
            <div style="font-weight: 800; font-size: 14px; letter-spacing: -0.3px; color: {logo_brand_color}; line-height: 1.15;">INVOICE HUB</div>
            <div style="font-size: 9.5px; font-weight: 700; color: {'#F43F5E' if theme == 'sakura' else '#3B82F6'}; letter-spacing: 0.5px;">FINTECH ENTERPRISE</div>
        </div>
    </div>
    """
    st.html(logo_html)
    
    st.title(t("sidebar_title", lang))
    
    # Thẻ thông tin tài khoản & Thời gian dùng thử
    card_bg = "rgba(37,99,235,0.08)" if theme != "dark" else "rgba(37,99,235,0.18)"
    card_border = "#3B82F6" if theme != "dark" else "#60A5FA"
    days_left = trial_info.get("days_remaining", 30)
    is_admin = trial_info.get("is_admin", False)
    
    st.markdown(
        f"""
        <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 8px; padding: 10px; font-size: 11.5px; line-height: 1.5; color: {'#93C5FD' if theme == 'dark' else '#1E40AF'}; margin-bottom: 10px;">
            <div style="font-weight: 700; font-size: 12px; margin-bottom: 4px; display: flex; justify-content: space-between;">
                <span>👤 {trial_info['full_name']}</span>
                <span style="font-size: 10px; opacity: 0.85;">@{current_user}</span>
            </div>
            <div>• <b>{t('card_trial_start', lang)}</b> {trial_info['trial_start_fmt']}</div>
            <div>• <b>{t('card_trial_end', lang)}</b> {trial_info['trial_end_fmt']}</div>
            <div>• <b>{t('card_trial_remain', lang)}</b> <b style="color: {'#60A5FA' if theme=='dark' else '#2563EB'}; font-size: 12px;">{days_left if not is_admin else t('card_trial_perm', lang)} {t('card_trial_days', lang) if not is_admin else ''}</b></div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    if not is_admin:
        used_days = max(0, 30 - days_left)
        st.caption(f"⏳ {t('card_trial_progress', lang)} `{used_days}/30 {t('card_trial_days', lang)}`")
        st.progress(min(1.0, max(0.0, used_days / 30.0)))
        
    is_temp_mode_input = st.checkbox(
        t("temp_mode_label", lang),
        value=is_temp,
        help=t("temp_mode_help", lang)
    )
    if is_temp_mode_input != is_temp:
        st.session_state["is_temp_mode"] = is_temp_mode_input
        st.session_state["preview_data"] = []
        st.rerun()

    if is_temp:
        st.info(t("temp_mode_active", lang))
        
    current_invs = db.get_all_invoices()
    st.metric(t("stored_invoices", lang), f"{len(current_invs)} HĐ")

    # ⚖️ KHỐI TRA CỨU PHÁP LÝ TINH GỌN CHÍNH XÁC 100% (ĐANG ÁP DỤNG THỰC TẾ)
    st.markdown("---")
    leg_card_bg = "#111827" if theme == "dark" else ("#FFF5F7" if theme == "sakura" else "#F1F5F9")
    leg_border = "#1F2937" if theme == "dark" else ("#FECDD3" if theme == "sakura" else "#E2E8F0")
    leg_title = "#60A5FA" if theme == "dark" else ("#BE185D" if theme == "sakura" else "#1E3A8A")
    leg_text = "#F3F4F6" if theme == "dark" else ("#4C0519" if theme == "sakura" else "#0F172A")
    leg_muted = "#9CA3AF" if theme == "dark" else ("#9D174D" if theme == "sakura" else "#64748B")
    
    legal_html = f"""
    <div style="background-color: {leg_card_bg}; border: 1px solid {leg_border}; border-radius: 8px; padding: 9px; font-size: 11px; line-height: 1.4; color: {leg_text}; margin-bottom: 10px;">
        <div style="font-weight: 700; font-size: 11px; color: {leg_title}; margin-bottom: 6px; letter-spacing: 0.3px;">
            ⚖️ CƠ SỞ PHÁP LÝ & TRA CỨU
        </div>
        
        <div style="margin-bottom: 6px; padding-bottom: 5px; border-bottom: 1px dashed {leg_border};">
            <div style="font-weight: 700; color: {leg_title};">📜 Nghị định 123/2020/NĐ-CP <span style="font-weight: 400; color: {leg_muted};">(Chính phủ)</span></div>
            <div>• <b>Ban hành:</b> 19/10/2020 | <b>Áp dụng:</b> 01/07/2022</div>
            <div style="color: {leg_muted};">• Quy định về hóa đơn, chứng từ</div>
            <div style="margin-top: 2px;"><a href="https://thuvienphapluat.vn/van-ban/Ke-toan-Kiem-toan/Nghi-dinh-123-2020-ND-CP-quy-dinh-hoa-don-chung-tu-445980.aspx" target="_blank" rel="noopener noreferrer" style="color: #2563EB; text-decoration: underline; font-weight: 700;">🔗 Toàn văn NĐ 123/2020/NĐ-CP ↗</a></div>
        </div>

        <div style="margin-bottom: 6px; padding-bottom: 5px; border-bottom: 1px dashed {leg_border};">
            <div style="font-weight: 700; color: {leg_title};">📜 Thông tư 78/2021/TT-BTC <span style="font-weight: 400; color: {leg_muted};">(Bộ Tài chính)</span></div>
            <div>• <b>Ban hành:</b> 17/09/2021 | <b>Áp dụng:</b> 01/07/2022</div>
            <div style="color: {leg_muted};">• Hướng dẫn thi hành NĐ 123 & Luật Quản lý thuế</div>
            <div style="margin-top: 2px;"><a href="https://thuvienphapluat.vn/van-ban/Thue-Phi-Le-Phi/Thong-tu-78-2021-TT-BTC-huong-dan-Luat-Quan-ly-thue-Nghi-dinh-123-2020-ND-CP-hoa-don-chung-tu-477966.aspx" target="_blank" rel="noopener noreferrer" style="color: #2563EB; text-decoration: underline; font-weight: 700;">🔗 Toàn văn TT 78/2021/TT-BTC ↗</a></div>
        </div>

        <div>
            <div style="font-weight: 700; color: {leg_title};">🌐 Cổng Hóa Đơn Điện Tử Quốc Gia <span style="font-weight: 400; color: {leg_muted};">(TCT)</span></div>
            <div>• <b>Cơ quan:</b> Tổng cục Thuế - Bộ Tài chính</div>
            <div style="color: {leg_muted};">• Tra cứu, tiếp nhận và cấp mã HĐĐT toàn quốc</div>
            <div style="margin-top: 2px;"><a href="https://hoadondientu.gdt.gov.vn/" target="_blank" rel="noopener noreferrer" style="color: #2563EB; text-decoration: underline; font-weight: 700;">🔗 hoadondientu.gdt.gov.vn ↗</a></div>
        </div>
    </div>
    """
    st.html(legal_html)

    st.markdown("---")
    st.markdown(f"### {t('clean_data_title', lang)}")
    if st.button(f"🧹 " + ("LÀM SẠCH HÓA ĐƠN ĐÃ NẠP" if lang=="vi" else ("CLEAR INVOICE DATA" if lang=="en" else "清空已上传发票")), use_container_width=True, help="Chỉ xóa dữ liệu hóa đơn đã tải lên, vẫn giữ tài khoản"):
        db.clear_all()
        if "preview_data" in st.session_state:
            del st.session_state["preview_data"]
        st.success(t("clean_data_success", lang))
        st.rerun()
        
    if current_user != "hznguyen1997":
        with st.popover("🗑️ " + ("XÓA VĨNH VIỄN TÀI KHOẢN NÀY" if lang=="vi" else ("DELETE THIS ACCOUNT" if lang=="en" else "彻底注销此账号")), use_container_width=True):
            st.warning("⚠️ " + ("Hành động này sẽ xóa vĩnh viễn tài khoản và toàn bộ dữ liệu kế toán liên quan khỏi hệ thống!" if lang=="vi" else ("This will permanently delete this account and all associated invoice data!" if lang=="en" else "此操作将永久注销该账号并删除所有相关发票数据！")))
            if st.button("🔥 " + ("Xác nhận Xóa Vĩnh Viễn" if lang=="vi" else ("Confirm Permanent Delete" if lang=="en" else "确认彻底注销")), type="primary", use_container_width=True):
                ok_del, msg_del = delete_my_account(current_user)
                if ok_del:
                    st.session_state["logged_in_user"] = None
                    st.session_state["preview_data"] = []
                    st.rerun()
                else:
                    st.error(msg_del)

# Initialize Session State for preview
if "preview_data" not in st.session_state:
    st.session_state["preview_data"] = []

# Danh sách Tab nghiệp vụ kế toán
main_tab_titles = [
    t("tab1", lang),
    t("tab2", lang),
    t("tab3", lang)
]
if plan == "pro":
    main_tab_titles.extend([
        t("tab4_bi", lang),
        t("tab5_ap", lang),
        t("tab6_risk", lang)
    ])

all_tabs = st.tabs(main_tab_titles)
tab1, tab2, tab3 = all_tabs[0], all_tabs[1], all_tabs[2]
if plan == "pro":
    tab4_bi, tab5_ap, tab6_risk = all_tabs[3], all_tabs[4], all_tabs[5]

# =========================================================================
# TAB 1: NẠP HÓA ĐƠN & PREVIEW
# =========================================================================
with tab1:
    st.subheader(t("upload_header", lang))
    
    uploaded_files = st.file_uploader(
        t("upload_drag_drop", lang),
        type=["pdf", "xml", "zip", "rar"],
        accept_multiple_files=True
    )

    if uploaded_files:
        if st.button(t("btn_start_parse", lang), type="primary"):
            # Phân loại số lượng tệp standard (PDF, XML) và archive (ZIP, RAR)
            std_files = [f for f in uploaded_files if os.path.splitext(f.name)[1].lower() in [".pdf", ".xml"]]
            arc_files = [f for f in uploaded_files if os.path.splitext(f.name)[1].lower() in [".zip", ".rar", ".7z", ".tar"]]
            
            q_res = db.check_fine_grained_quota(
                user_id=current_user,
                plan_type=plan,
                new_std_count=len(std_files),
                new_arc_count=len(arc_files)
            )
            
            if not q_res["allowed"]:
                st.error(f"❌ {q_res['reason']}")
                st.warning(f"💡 {t('quota_exceeded', lang)}")
            else:
                preview_results = []
                prog_bar = st.progress(0.0)
                status_txt = st.empty()
                success_cnt = 0
                err_cnt = 0
                
                for idx, up_file in enumerate(uploaded_files):
                    fname = up_file.name
                    fsize_kb = round(len(up_file.getvalue()) / 1024, 1)
                    fbytes = up_file.read()
                    
                    status_txt.text(f"{t('parsing_progress', lang)} [{idx+1}/{len(uploaded_files)}]: {fname} ({fsize_kb} KB)...")
                    ext = os.path.splitext(fname)[1].lower()
                    
                    parsed_invs = []
                    if ext == ".xml":
                        inv = InvoiceParser.parse_xml_content(fbytes, fname)
                        if inv:
                            parsed_invs.append(inv)
                    elif ext == ".pdf":
                        inv = InvoiceParser.parse_pdf_content(fbytes, fname)
                        if inv:
                            parsed_invs.append(inv)
                    elif ext == ".zip":
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
                            tmp.write(fbytes)
                            tmp_path = tmp.name
                        parsed_invs = InvoiceParser.parse_file(tmp_path)
                        try:
                            os.remove(tmp_path)
                        except Exception:
                            pass
                    elif ext == ".rar":
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".rar") as tmp:
                            tmp.write(fbytes)
                            tmp_path = tmp.name
                        parsed_invs = InvoiceParser.parse_file(tmp_path)
                        try:
                            os.remove(tmp_path)
                        except Exception:
                            pass
                    
                    if parsed_invs:
                        for inv in parsed_invs:
                            db.insert_invoice(inv, overwrite=True)
                            success_cnt += 1
                            preview_results.append({
                                "STT": len(preview_results) + 1,
                                "Tên tệp": fname,
                                "Định dạng": ext.upper().replace(".", ""),
                                "Số HĐ": inv.get("so_hd", ""),
                                "Ký hiệu": inv.get("kh_hd", ""),
                                "Ngày lập": inv.get("ngay_lap", ""),
                                "Nhà Cung Cấp": inv.get("ten_nban", ""),
                                "MST NCC": inv.get("mst_nban", ""),
                                "Chưa thuế (đ)": inv.get("tien_chua_thue", 0.0),
                                "Thuế GTGT (đ)": inv.get("tien_thue", 0.0),
                                "Tổng thanh toán (đ)": inv.get("tong_tien", 0.0),
                                "Chữ ký số": inv.get("sig_status", "Đã ký số"),
                                "Mã CQT": inv.get("ma_cqt", "Có mã CQT"),
                                "Đánh giá": inv.get("status_summary", "Hợp lệ")
                            })
                    else:
                        err_cnt += 1
                        preview_results.append({
                            "STT": len(preview_results) + 1,
                            "Tên tệp": fname,
                            "Định dạng": ext.upper().replace(".", ""),
                            "Số HĐ": "-",
                            "Ký hiệu": "-",
                            "Ngày lập": "-",
                            "Nhà Cung Cấp": "-",
                            "MST NCC": "-",
                            "Chưa thuế (đ)": 0.0,
                            "Thuế GTGT (đ)": 0.0,
                            "Tổng thanh toán (đ)": 0.0,
                            "Chữ ký số": "Chưa ký",
                            "Mã CQT": "-",
                            "Đánh giá": "Không có dữ liệu"
                        })
                    prog_bar.progress((idx + 1) / len(uploaded_files))
                    
                if std_files:
                    db.increment_daily_usage(current_user, count=len(std_files))
                if arc_files:
                    db.increment_weekly_archive_usage(current_user, count=len(arc_files))
                    
                status_txt.empty()
                st.session_state["preview_data"] = preview_results
                st.success(f"{t('parse_success', lang)} **{success_cnt}** {t('stored_invoices', lang)}.")

    # ================= BẢNG PREVIEW TÁC VỤ =================
    st.markdown(f"### {t('preview_header', lang)}")
    
    if st.session_state["preview_data"]:
        df_prev = pd.DataFrame(st.session_state["preview_data"])
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(t("metric_total_files", lang), f"{len(df_prev)}")
        ok_count = len(df_prev[df_prev["Đánh giá"] == "Hợp lệ"])
        c2.metric(t("metric_valid_invoices", lang), f"{ok_count} / {len(df_prev)}")
        c3.metric(t("metric_total_amount", lang), f"{df_prev['Tổng thanh toán (đ)'].sum():,.0f} đ")
        c4.metric(t("metric_total_vat", lang), f"{df_prev['Thuế GTGT (đ)'].sum():,.0f} đ")
        
        st.dataframe(
            df_prev.style.format({
                "Chưa thuế (đ)": "{:,.0f}",
                "Thuế GTGT (đ)": "{:,.0f}",
                "Tổng thanh toán (đ)": "{:,.0f}"
            }),
            use_container_width=True,
            height=320
        )
    else:
        st.info(t("preview_empty", lang))

# =========================================================================
# TAB 2: BẢNG KÊ & NHÀ CUNG CẤP
# =========================================================================
with tab2:
    all_invoices = db.get_all_invoices()
    
    if not all_invoices:
        st.warning(t("no_data_warning", lang))
    else:
        df_inv = pd.DataFrame(all_invoices)
        m1, m2, m3, m4 = st.columns(4)
        total_inv = len(df_inv)
        total_pre_tax = df_inv["tien_chua_thue"].sum()
        total_vat = df_inv["tien_thue"].sum()
        total_all = df_inv["tong_tien"].sum()
        
        m1.metric(t("metric_total_invs", lang), f"{total_inv:,}")
        m2.metric(t("metric_pretax_sales", lang), f"{total_pre_tax:,.0f} đ")
        m3.metric(t("metric_input_vat", lang), f"{total_vat:,.0f} đ")
        m4.metric(t("metric_total_payment", lang), f"{total_all:,.0f} đ")
        
        st.markdown("---")
        view_tab1, view_tab2 = st.tabs([t("subtab_summary", lang), t("subtab_detail", lang)])
        
        with view_tab1:
            s1, s2 = st.columns([2, 1])
            search_kw = s1.text_input(t("search_placeholder", lang), "")
            
            if search_kw:
                df_filtered = df_inv[
                    df_inv["ten_nban"].str.contains(search_kw, case=False, na=False) |
                    df_inv["mst_nban"].str.contains(search_kw, case=False, na=False) |
                    df_inv["so_hd"].str.contains(search_kw, case=False, na=False)
                ]
            else:
                df_filtered = df_inv

            show_cols = ["id", "so_hd", "kh_hd", "ngay_lap", "ten_nban", "mst_nban", "tien_chua_thue", "tien_thue", "tong_tien", "sig_status", "ma_cqt", "status_summary"]
            st.dataframe(
                df_filtered[show_cols].rename(columns={
                    "id": "ID", "so_hd": "Số HĐ", "kh_hd": "Ký hiệu", "ngay_lap": "Ngày lập",
                    "ten_nban": "Nhà Cung Cấp (Người bán)", "mst_nban": "MST NCC",
                    "tien_chua_thue": "Chưa thuế (đ)", "tien_thue": "Thuế GTGT (đ)",
                    "tong_tien": "Tổng thanh toán (đ)", "sig_status": "Chữ ký số",
                    "ma_cqt": "Mã CQT", "status_summary": "Đánh giá TT 91/2026"
                }),
                use_container_width=True,
                height=380
            )

        with view_tab2:
            st.markdown(f"#### {t('supplier_breakdown_title', lang)}")
            suppliers = df_inv["ten_nban"].unique().tolist()
            
            for sup in suppliers:
                df_sup_invs = df_inv[df_inv["ten_nban"] == sup]
                sup_mst = df_sup_invs["mst_nban"].iloc[0]
                sup_total = df_sup_invs["tong_tien"].sum()
                sup_vat = df_sup_invs["tien_thue"].sum()
                
                with st.expander(f"🏢 **{sup}** (MST: {sup_mst}) — **{len(df_sup_invs)} HĐ** | Tổng thanh toán: **{sup_total:,.0f} đ** (Thuế GTGT: **{sup_vat:,.0f} đ**)", expanded=True):
                    sup_items_list = []
                    for _, r_inv in df_sup_invs.iterrows():
                        inv_id = r_inv["id"]
                        items = db.get_invoice_items(inv_id)
                        if items:
                            for it in items:
                                sup_items_list.append({
                                    "Số HĐ": r_inv["so_hd"],
                                    "Ký hiệu": r_inv["kh_hd"],
                                    "Ngày lập": r_inv["ngay_lap"],
                                    "STT": it.get("stt", 1),
                                    "Tên hàng hóa / Dịch vụ": it.get("ten_hang", ""),
                                    "ĐVT": it.get("dvt", ""),
                                    "Số lượng": it.get("so_luong", 1),
                                    "Đơn giá (đ)": it.get("don_gia", 0.0),
                                    "Thành tiền (đ)": it.get("thanh_tien", 0.0),
                                    "Thuế suất": it.get("thue_suat", "0%"),
                                    "Tiền thuế (đ)": it.get("tien_thue", 0.0)
                                })
                        else:
                            sup_items_list.append({
                                "Số HĐ": r_inv["so_hd"],
                                "Ký hiệu": r_inv["kh_hd"],
                                "Ngày lập": r_inv["ngay_lap"],
                                "STT": 1,
                                "Tên hàng hóa / Dịch vụ": f"Dịch vụ theo HĐ {r_inv['so_hd']}",
                                "ĐVT": "Gói",
                                "Số lượng": 1,
                                "Đơn giá (đ)": r_inv["tien_chua_thue"],
                                "Thành tiền (đ)": r_inv["tien_chua_thue"],
                                "Thuế suất": "0%" if r_inv["tien_thue"] == 0 else "10%",
                                "Tiền thuế (đ)": r_inv["tien_thue"]
                            })
                            
                    df_sup_items = pd.DataFrame(sup_items_list)
                    st.dataframe(
                        df_sup_items.style.format({
                            "Đơn giá (đ)": "{:,.0f}",
                            "Thành tiền (đ)": "{:,.0f}",
                            "Tiền thuế (đ)": "{:,.0f}"
                        }),
                        use_container_width=True
                    )

# =========================================================================
# TAB 3: XUẤT BÁO CÁO EXCEL
# =========================================================================
with tab3:
    st.subheader(t("excel_title", lang))
    all_invs = db.get_all_invoices()
    
    if not all_invs:
        st.warning(t("no_data_warning", lang))
    else:
        st.write(f"Hiện có **{len(all_invs)}** {t('excel_ready_count', lang)}")
        
        c1, c2 = st.columns([3, 2])
        with c1:
            st.markdown(f"""
            ### 📑 Báo Cáo Excel 2 Sheet Tiêu Chuẩn Doanh Nghiệp:
            * **{t('excel_desc_1', lang)}**
            * **{t('excel_desc_2', lang)}**
            * **{t('excel_desc_3', lang)}**
            * **{t('excel_desc_4', lang)}**
            """)
            
            excel_lang_opts = {
                "vi": "Tiếng Việt",
                "en": "English",
                "zh": "中文",
                "bilingual_zh": "Song ngữ Việt - Trung (Bilingual VI/ZH)"
            }
            export_lang = st.selectbox(
                t("excel_lang_select", lang),
                options=list(excel_lang_opts.keys()),
                format_func=lambda k: excel_lang_opts[k],
                index=list(excel_lang_opts.keys()).index("bilingual_zh" if lang == "zh" else lang)
            )
            
            excel_bytes = InvoiceExporter.export_comprehensive_excel(all_invs, db, lang=export_lang)
            export_filename = f"Bao_Cao_Hoa_Don_{current_user}_{export_lang}_{time.strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            st.markdown("---")
            st.markdown("#### 💾 Tùy chọn Tải về / Lưu trữ:")
            
            # 1. Nút tải về qua trình duyệt
            st.download_button(
                label=f"{t('btn_download_excel', lang)} ({export_lang.upper()})",
                data=excel_bytes,
                file_name=export_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )
            
            # 2. Cá nhân hóa thư mục lưu trữ cục bộ
            st.markdown(f"**{t('custom_dir_label', lang)}**")
            target_dir_input = st.text_input(
                "Đường dẫn thư mục:",
                value=st.session_state.get("custom_export_dir", os.path.join(os.path.expanduser("~"), "Downloads")),
                help=t("custom_dir_help", lang),
                label_visibility="collapsed"
            ).strip()
            
            if st.button(t("btn_save_local", lang), use_container_width=True):
                if not target_dir_input:
                    st.warning("Vui lòng nhập đường dẫn thư mục hợp lệ!")
                else:
                    try:
                        os.makedirs(target_dir_input, exist_ok=True)
                        save_full_path = os.path.join(target_dir_input, export_filename)
                        with open(save_full_path, "wb") as f_out:
                            f_out.write(excel_bytes)
                        st.session_state["custom_export_dir"] = target_dir_input
                        st.success(f"{t('save_local_success', lang)} `{save_full_path}`")
                    except Exception as ex:
                        st.error(f"Lỗi khi lưu vào thư mục: {ex}")
            
        with c2:
            st.info("""
            📋 **Định dạng báo cáo:**
            * Header xanh navy chuẩn kế toán `#1F4E78`.
            * Kẻ khung viền mỏng tinh tế, định dạng số tiền `#,##0`.
            * Khớp 100% với mẫu biểu quản trị FDI và kiểm toán độc lập.
            """)

# =========================================================================
# TAB 4 (PRO): BI BIỂU ĐỒ TRỰC QUAN
# =========================================================================
if plan == "pro":
    with tab4_bi:
        st.subheader("📈 Phân Tích Dữ Liệu Tài Chính & Biểu Đồ BI Trực Quan (Pro Analytics)")
        all_invs = db.get_all_invoices()
        if not all_invs and st.session_state.get("preview_data"):
            all_invs = st.session_state["preview_data"]
        
        if not all_invs:
            st.info(t("no_data_warning", lang))
        else:
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                fig_sup = analytics.get_supplier_chart(all_invs, lang=lang)
                if fig_sup:
                    st.plotly_chart(fig_sup, use_container_width=True)
            with col_g2:
                fig_tax = analytics.get_tax_distribution_chart(all_invs, lang=lang)
                if fig_tax:
                    st.plotly_chart(fig_tax, use_container_width=True)
                    
            st.markdown("---")
            fig_trend = analytics.get_monthly_trend_chart(all_invs, lang=lang)
            if fig_trend:
                st.plotly_chart(fig_trend, use_container_width=True)

# =========================================================================
# TAB 5 (PRO): ĐỐI SOÁT CÔNG NỢ PHẢI TRẢ
# =========================================================================
if plan == "pro":
    with tab5_ap:
        st.subheader("💳 Đối Soát Công Nợ PhẢI Trả & Kế Hoạch Thanh Toán (AP Reconciliation)")
        all_invs = db.get_all_invoices()
        if not all_invs and st.session_state.get("preview_data"):
            all_invs = st.session_state["preview_data"]
        
        if not all_invs:
            st.info(t("no_data_warning", lang))
        else:
            c_term1, c_term2 = st.columns([1, 2])
            with c_term1:
                p_terms = st.selectbox("Kỳ hạn thanh toán hợp đồng chuẩn (DPO):", [15, 30, 45, 60, 90], index=1)
                
            ap_data = analytics.get_ap_debt_reconciliation(all_invs, payment_term_days=p_terms)
            df_ap = pd.DataFrame(ap_data)
            
            a1, a2, a3, a4 = st.columns(4)
            a1.metric("Tổng công nợ phải trả", f"{df_ap['tong_cong_no'].sum():,.0f} đ")
            a2.metric("Nợ trong hạn", f"{df_ap['trong_han'].sum():,.0f} đ")
            overdue_sum = df_ap['qua_han_1_30'].sum() + df_ap['qua_han_31_60'].sum() + df_ap['qua_han_tren_60'].sum()
            a3.metric("Nợ quá hạn", f"{overdue_sum:,.0f} đ", delta=f"-{overdue_sum:,.0f} đ" if overdue_sum > 0 else "0", delta_color="inverse")
            a4.metric("Số lượng NCC có số dư", f"{len(df_ap)} NCC")
            
            st.markdown("---")
            st.markdown("#### 📋 Bảng Phân Tuổi Nợ Chi Tiết Theo Từng Nhà Cung Cấp:")
            
            show_ap = df_ap.rename(columns={
                "ten_nban": "Nhà Cung Cấp",
                "mst_nban": "MST",
                "so_luong_hd": "Số HĐ",
                "tong_cong_no": "Tổng nợ (VND)",
                "trong_han": "Trong hạn (VND)",
                "qua_han_1_30": "Quá hạn 1-30 ngày",
                "qua_han_31_60": "Quá hạn 31-60 ngày",
                "qua_han_tren_60": "Quá hạn >60 ngày",
                "han_chot_gan_nhat": "Hạn chót gần nhất",
                "trang_thai": "Đánh giá rủi ro"
            })
            
            st.dataframe(
                show_ap.style.format({
                    "Tổng nợ (VND)": "{:,.0f}",
                    "Trong hạn (VND)": "{:,.0f}",
                    "Quá hạn 1-30 ngày": "{:,.0f}",
                    "Quá hạn 31-60 ngày": "{:,.0f}",
                    "Quá hạn >60 ngày": "{:,.0f}"
                }),
                use_container_width=True,
                height=350
            )

# =========================================================================
# TAB 6 (PRO): CẢNH BÁO GIAN LẬN & RỦI RO THUẾ
# =========================================================================
if plan == "pro":
    with tab6_risk:
        st.subheader("🚨 Rà Soát Rủi Ro Thuế & Cảnh Báo Gian Lận Hóa Đơn (Tax Compliance Engine)")
        all_invs = db.get_all_invoices()
        if not all_invs and st.session_state.get("preview_data"):
            all_invs = st.session_state["preview_data"]
        
        if not all_invs:
            st.info(t("no_data_warning", lang))
        else:
            risks = analytics.detect_tax_and_fraud_risks(all_invs)
            
            r1, r2, r3 = st.columns(3)
            high_risks = [r for r in risks if "CAO" in r["muc_do"]]
            med_risks = [r for r in risks if "TRUNG BÌNH" in r["muc_do"]]
            warn_risks = [r for r in risks if "CẢNH BÁO" in r["muc_do"]]
            
            r1.metric("🔴 Rủi ro Mức độ Cao", f"{len(high_risks)} mục")
            r2.metric("🟠 Rủi ro Trung bình", f"{len(med_risks)} mục")
            r3.metric("🟡 Cảnh báo Cần rà soát", f"{len(warn_risks)} mục")
            
            st.markdown("---")
            if not risks:
                st.success("🎉 **Tuyệt vời!** Toàn bộ hóa đơn trong cơ sở dữ liệu đều đáp ứng đầy đủ điều kiện pháp lý, không phát hiện rủi ro gian lận hay bất thường thuế.")
            else:
                st.markdown("#### 🔍 Danh Sách Chi Tiết Các Điểm Cần Xử Lý Trước Khi Kê Khai Thuế:")
                df_risks = pd.DataFrame(risks)
                st.dataframe(
                    df_risks.rename(columns={
                        "muc_do": "Mức độ rủi ro",
                        "loai_rui_ro": "Dấu hiệu bất thường",
                        "so_hd": "Số HĐ",
                        "nha_cung_cap": "Nhà Cung Cấp",
                        "mst": "Mã Số Thuế",
                        "so_tien": "Số tiền (VND)",
                        "chi_tiet": "Khuyến nghị xử lý kế toán"
                    }).style.format({
                        "Số tiền (VND)": "{:,.0f}"
                    }),
                    use_container_width=True,
                    height=350
                )

# =========================================================================
# 💬 CHÂN TRANG: BẢO MẬT & ĐÓNG GÓP Ý KIẾN (COMPACT FOOTER - FULL 1 MÀN HÌNH)
# =========================================================================
st.markdown("---")
b_left, b_mid, b_right = st.columns([2.2, 1.1, 1.1])

with b_left:
    st.markdown("<div style='display: flex; align-items: center; height: 100%; font-size: 12px; color: #64748B;'>🔒 <b>Bảo mật On-Device 100%</b>: Dữ liệu hóa đơn và báo cáo tài chính được xử lý hoàn toàn cục bộ trên máy tính của bạn.</div>", unsafe_allow_html=True)

with b_mid:
    with st.popover(t("feedback_btn", lang), use_container_width=True):
        st.markdown(f"### {t('feedback_title', lang)}")
        st.markdown(f"**{t('feedback_rating', lang)}**")
        star_rating = st.feedback("stars")
        rating_val = (star_rating + 1) if star_rating is not None else 5
        
        fb_categories = [
            t("feedback_cat_feature", lang),
            t("feedback_cat_bug", lang),
            t("feedback_cat_perf", lang),
            t("feedback_cat_other", lang)
        ]
        fb_cat = st.selectbox(t("feedback_category", lang), fb_categories)
        fb_comment = st.text_area(t("feedback_comment", lang), height=95)
        
        if st.button(t("btn_submit_feedback", lang), type="primary", use_container_width=True):
            if not fb_comment.strip():
                st.warning("Vui lòng nhập nội dung góp ý!")
            else:
                saved = db.save_feedback(
                    user_id=current_user,
                    rating=rating_val,
                    category=fb_cat,
                    comment=fb_comment.strip()
                )
                if saved:
                    st.success(t("feedback_success", lang))
                    st.rerun()
                    
        st.markdown("---")
        st.markdown(f"**{t('feedback_history', lang)}**")
        feedbacks = db.get_feedback_list(user_id=current_user)
        if feedbacks:
            from content_moderator import mask_profanity
            for fb in feedbacks[:5]:
                stars_str = "⭐" * fb.get("rating", 5)
                time_val = fb.get("created_at") or datetime.now().strftime("%d/%m/%Y - %H:%M")
                clean_cmt = mask_profanity(fb.get('comment', ''))
                st.markdown(
                    f"• **{fb.get('category')}** ({stars_str}) — <span style='font-size: 11px; color: #64748B;'>🕒 {time_val}</span>  \n  _{clean_cmt}_",
                    unsafe_allow_html=True
                )
        else:
            st.caption(t("feedback_empty", lang))

with b_right:
    with st.popover(t("donate_btn", lang), use_container_width=True):
        st.markdown(f"### {t('donate_title', lang)}")
        st.caption(t("donate_desc", lang))
        
        assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        qr_img_path = os.path.join(assets_dir, "donate_qr.png")
        panda_img_path = os.path.join(assets_dir, "thank_you_panda.png")
        
        if st.session_state.get("donated_confirmed"):
            if os.path.exists(panda_img_path):
                st.image(panda_img_path, caption=t("donate_panda_caption", lang), use_container_width=True)
            st.success(f"{t('donate_thanks_title', lang)}\n\n{t('donate_thanks_desc', lang)}")
            if st.button(t("donate_btn_show_qr", lang), use_container_width=True):
                st.session_state["donated_confirmed"] = False
                st.rerun()
        else:
            if os.path.exists(qr_img_path):
                st.image(qr_img_path, caption=t("donate_qr_caption", lang), use_container_width=True)
            
            st.markdown(f"""
            - {t('donate_info_owner', lang)}
            - {t('donate_info_method', lang)}
            """)
            
            if st.button(t("donate_btn_confirm", lang), type="primary", use_container_width=True):
                st.session_state["donated_confirmed"] = True
                st.balloons()
                st.rerun()

        st.markdown("---")
        st.markdown("---")
        with st.expander("🔒 Khu vực Quản trị viên (Quản Lý Tài Khoản, Thống Kê & Bình Luận)"):
            admin_pwd = st.text_input("Nhập mật khẩu Quản trị viên:", type="password", help="Chỉ quản trị viên hznguyen1997 mới có quyền quản lý.")
            if admin_pwd == "Anthumatmeo020922":
                st.success("🔓 **Xác thực Quản trị viên thành công!**")
                
                adm_t_user, adm_t1, adm_t2, adm_t3 = st.tabs([
                    "👥 Quản Lý Người Dùng & Dùng Thử 30 Ngày",
                    "💳 Thống Kê Giao Dịch & Duyệt Pro",
                    "📊 Báo Cáo Tổng Hợp Tuần",
                    "💬 Quản Lý Ý Kiến Đóng Góp"
                ])
                
                # TAB 0: QUẢN LÝ NGƯỜI DÙNG & KIỂM SOÁT 30 NGÀY DÙNG THỬ
                with adm_t_user:
                    col_head_u, col_btn_dl = st.columns([1.8, 2.2])
                    with col_head_u:
                        st.markdown("#### 👥 Danh Sách Tài Khoản Người Dùng:")
                    with col_btn_dl:
                        try:
                            from feedback_reporter import generate_admin_analytics_excel
                            excel_bytes = generate_admin_analytics_excel()
                            cur_time_str = datetime.datetime.now().strftime("%Y%m%d_%H%M")
                            st.download_button(
                                label="📥 XUẤT EXCEL PHÂN TÍCH HỆ THỐNG (4 SHEETS)",
                                data=excel_bytes,
                                file_name=f"Bao_Cao_Phan_Tich_Nguoi_Dung_{cur_time_str}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                type="primary",
                                use_container_width=True,
                                help="Tải báo cáo Excel 4 Sheet: Danh sách người dùng, Thống kê tần suất dùng tính năng, Báo lỗi & Góp ý, Tổng quan tối ưu sản phẩm"
                            )
                        except Exception as e:
                            st.error(f"Lỗi xuất Excel: {e}")
                            
                    all_users = get_all_registered_users()
                    
                    u_tot = len(all_users)
                    u_active = len([u for u in all_users if u.get("days_remaining", 0) > 0])
                    u_exp = len([u for u in all_users if u.get("days_remaining", 0) <= 0 and u.get("username") != "hznguyen1997"])
                    
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Tổng tài khoản đăng ký", f"{u_tot}")
                    m2.metric("Đang trong hạn 30 ngày", f"{u_active}")
                    m3.metric("Đã hết hạn dùng thử", f"{u_exp}")
                    st.markdown("---")
                    
                    for u in all_users:
                        u_name = u.get("username")
                        f_name = u.get("full_name", u_name)
                        phone = u.get("phone", "-")
                        email = u.get("email", "-")
                        comp = u.get("company", "-")
                        reg_t = u.get("registered_at", "-")
                        exp_t = u.get("trial_end", "-")
                        d_left = u.get("days_remaining", 0)
                        last_l = u.get("last_login", "-")
                        
                        is_adm_u = (u_name == "hznguyen1997")
                        badge = "<span class='pro-badge'>👑 Quản Trị Viên</span>" if is_adm_u else (
                            f"<span class='pro-badge'>🎁 Còn {d_left} ngày</span>" if d_left > 0 else "<span class='basic-badge'>Đã hết hạn</span>"
                        )
                        
                        st.markdown(
                            f"**{f_name}** (`@{u_name}`) — {badge}  \n"
                            f"• **Công ty:** `{comp}` | **SĐT/Zalo:** `{phone}` | **Email:** `{email}`  \n"
                            f"• **Ngày đăng ký (Bắt đầu):** `{reg_t}` | **Hạn kết thúc:** `{exp_t}` | **Đăng nhập gần nhất:** `{last_l}`",
                            unsafe_allow_html=True
                        )
                        
                        if not is_adm_u:
                            c_act1, c_act2 = st.columns([2.5, 1.5])
                            with c_act1:
                                if st.button(f"➕ Gia Hạn +30 Ngày Dùng Thử", key=f"ext_u_{u_name}", help="Cộng thêm 30 ngày dùng thử cho tài khoản này"):
                                    admin_extend_user_trial(u_name, extra_days=30)
                                    st.success(f"Đã cộng thêm 30 ngày dùng thử cho @{u_name}!")
                                    st.rerun()
                            with c_act2:
                                if st.button(f"🗑️ Xóa Tài Khoản", key=f"del_u_{u_name}", help=f"Xóa tài khoản @{u_name}"):
                                    ok, del_msg = admin_delete_user(u_name)
                                    if ok:
                                        st.warning(del_msg)
                                        st.rerun()
                                    else:
                                        st.error(del_msg)
                        st.markdown("<hr style='margin: 4px 0 10px 0; border: none; border-top: 1px dashed #CBD5E1;'>", unsafe_allow_html=True)
                
                # TAB 1: THỐNG KÊ GIAO DỊCH PRO DÀNH RIÊNG CHO ADMIN
                with adm_t1:
                    st.markdown("#### 💳 Thống Kê & Kiểm Soát Người Thanh Toán Gói Pro:")
                    from payment_gateway import get_all_cross_payment_transactions
                    all_txs = get_all_cross_payment_transactions()
                    
                    if not all_txs:
                        st.info("Chưa có giao dịch thanh toán nào được gửi lên hệ thống.")
                    else:
                        t_rev = sum(t.get("amount", 0) for t in all_txs if t.get("status") == "approved")
                        t_app = len([t for t in all_txs if t.get("status") == "approved"])
                        t_pen = len([t for t in all_txs if t.get("status") == "pending"])
                        
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("Tổng đơn thanh toán", f"{len(all_txs)}")
                        m2.metric("Đã kích hoạt Pro", f"{t_app}")
                        m3.metric("Chờ duyệt", f"{t_pen}")
                        m4.metric("Tổng doanh thu", f"{t_rev:,.0f} đ")
                        st.markdown("---")
                        
                        for tx in all_txs:
                            o_code = tx.get("order_code", "-")
                            u_name = tx.get("customer_name", tx.get("user_id", "Kế toán"))
                            u_phone = tx.get("contact_info", "-")
                            amt_str = f"{tx.get('amount', 99000):,.0f} đ"
                            tx_status = tx.get("status", "pending")
                            tx_syntax = tx.get("syntax", "-")
                            tx_ref = tx.get("bank_tx_ref", "-")
                            tx_time = tx.get("created_at", "-")
                            
                            status_badge = "<span class='pro-badge'>Đã kích hoạt</span>" if tx_status == "approved" else "<span class='basic-badge'>Chờ duyệt</span>"
                            
                            st.markdown(
                                f"**Đơn hàng #{o_code}** • `{amt_str}` — {status_badge}  \n"
                                f"• **Khách hàng:** `{u_name}` (SĐT/Zalo: `{u_phone}`) | **Tài khoản:** `{tx.get('user_id')}`  \n"
                                f"• **Cú pháp:** `{tx_syntax}` | **Mã GD Ngân hàng:** `{tx_ref}`  \n"
                                f"• **Thời gian:** <span style='font-size:11px; color:#64748B;'>🕒 {tx_time}</span>",
                                unsafe_allow_html=True
                            )
                            
                            if tx_status == "pending":
                                col_ap, col_re = st.columns([1.5, 1.5])
                                with col_ap:
                                    if st.button(f"✅ Duyệt & Mở Pro", key=f"appr_{o_code}"):
                                        db.approve_payment_transaction(o_code)
                                        st.success(f"Đã duyệt và mở Pro cho {u_name}!")
                                        st.rerun()
                                with col_re:
                                    if st.button(f"❌ Từ chối", key=f"rejc_{o_code}"):
                                        db.reject_payment_transaction(o_code)
                                        st.warning("Đã từ chối đơn hàng!")
                                        st.rerun()
                            st.markdown("<hr style='margin: 6px 0 12px 0; border: none; border-top: 1px dashed #CBD5E1;'>", unsafe_allow_html=True)
                
                # TAB 2: BÁO CÁO TỔNG HỢP TUẦN
                with adm_t2:
                    if st.button("📊 Tổng Hợp & Gửi Báo Cáo Tuần (hznguyen1993@gmail.com)", type="primary", use_container_width=True):
                        try:
                            from feedback_reporter import generate_weekly_report, save_weekly_report_snapshot, RECIPIENT_EMAIL
                            report_file = save_weekly_report_snapshot()
                            rep_data = generate_weekly_report(days=7)
                            st.success(f"✅ **Đã tổng hợp thành công {rep_data['total_count']} ý kiến!** Đã xuất báo cáo tuần gửi tới email **{RECIPIENT_EMAIL}** (Bản lưu: `{os.path.basename(report_file)}`).")
                            st.markdown(rep_data["markdown"])
                        except Exception as e:
                            st.error(f"Lỗi khi tổng hợp báo cáo: {e}")
                            
                # TAB 3: QUẢN LÝ BÌNH LUẬN GÓP Ý
                with adm_t3:
                    st.markdown("#### 🛠️ Bảng Điều Khiển Xử Lý Bình Luận:")
                    from feedback_reporter import get_all_cross_user_feedback, delete_cross_user_feedback, update_cross_user_feedback
                    from content_moderator import mask_profanity
                    all_fbs = get_all_cross_user_feedback(days=30)
                    
                    if not all_fbs:
                        st.info("Chưa có bình luận nào trong hệ thống.")
                    else:
                        for fb in all_fbs:
                            fb_id = fb.get("id")
                            u_id = fb.get("user_id", "Kế toán")
                            db_p = fb.get("db_path", "")
                            c_text = mask_profanity(fb.get("comment", ""))
                            c_time = fb.get("created_at", "-")
                            c_status = fb.get("status", "Chờ xử lý")
                            c_note = fb.get("admin_note", "")
                            stars = "⭐" * fb.get("rating", 5)
                            
                            st.markdown(f"**#{fb_id} [{u_id}]** {stars} • <span style='font-size:11px; color:#64748B;'>🕒 {c_time}</span> — **Trạng thái:** `{c_status}`", unsafe_allow_html=True)
                            st.markdown(f"> _{c_text}_")
                            
                            c1, c2, c3 = st.columns([1.5, 2, 1.2])
                            with c1:
                                new_status = st.selectbox(
                                    f"Trạng thái",
                                    options=["Chờ xử lý", "Đang xử lý", "Đã giải quyết"],
                                    index=["Chờ xử lý", "Đang xử lý", "Đã giải quyết"].index(c_status) if c_status in ["Chờ xử lý", "Đang xử lý", "Đã giải quyết"] else 0,
                                    key=f"sel_st_{fb_id}_{u_id}"
                                )
                            with c2:
                                new_note = st.text_input(f"Ghi chú xử lý", value=c_note, key=f"inp_nt_{fb_id}_{u_id}", placeholder="Ghi chú hướng khắc phục...")
                            with c3:
                                col_s, col_d = st.columns(2)
                                with col_s:
                                    if st.button("💾 Lưu", key=f"btn_sv_{fb_id}_{u_id}", help="Lưu trạng thái xử lý"):
                                        update_cross_user_feedback(db_p, fb_id, new_status, new_note)
                                        st.success("Đã cập nhật!")
                                        st.rerun()
                                with col_d:
                                    if st.button("🗑️", key=f"btn_dl_{fb_id}_{u_id}", help="Xóa bình luận này"):
                                        delete_cross_user_feedback(db_p, fb_id)
                                        st.warning("Đã xóa!")
                                        st.rerun()
                            st.markdown("<hr style='margin: 4px 0 10px 0; border: none; border-top: 1px dashed #CBD5E1;'>", unsafe_allow_html=True)
            elif admin_pwd:
                st.error("❌ Mật khẩu không chính xác!")
            else:
                st.caption("🛡️ Dữ liệu tổng hợp và kiểm soát thanh toán được bảo mật riêng tư cho Quản trị viên.")

