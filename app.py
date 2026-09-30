import os
import re
import time
import pickle
import requests
import streamlit as st
from typing import Optional

# =============================
# CONFIG
# =============================
API_BASE    = "https://movie-rec-466x.onrender.com"
TMDB_IMG    = "https://image.tmdb.org/t/p/w500"
TMDB_BACKDROP = "https://image.tmdb.org/t/p/original"

PLACEHOLDER_POSTER   = "https://placehold.co/500x750/0a0e1a/1a2032.png?text=No+Poster"
PLACEHOLDER_BACKDROP = "https://placehold.co/1920x1080/0a0e1a/0a0e1a.png"

st.set_page_config(page_title="NetMirror", page_icon="🎬", layout="wide", initial_sidebar_state="collapsed")

# =============================
# CSS
# =============================
st.markdown("""
<style>
/* ── Base ───────────────────────────────────── */
html, body {
    overflow-x: hidden !important;
    scroll-behavior: smooth !important;
    -webkit-tap-highlight-color: transparent !important;
}
*, *::before, *::after {
    box-sizing: border-box !important;
}
[data-testid="stAppViewContainer"] {
    background-color: #0a0e1a;
    color: #E4E7EF;
    overflow-x: hidden !important;
}
[data-testid="block-container"] {
    max-width: 100% !important;
    padding: 5.6rem 0rem 2rem !important;
}
header[data-testid="stHeader"] { display: none !important; }

/* ── Subpages (Details, Watchlist, Active Search): Reduced Top Gap ── */
[data-testid="block-container"]:has(.nm-det-nav-marker),
[data-testid="block-container"]:has(.nm-wl-nav-marker),
[data-testid="block-container"]:has(.nm-search-active-marker) {
    padding-top: 4.1rem !important;
    padding-left: 2.4rem !important;
    padding-right: 2.4rem !important;
}

/* Zero-height markers for subpages */
.nm-det-nav-marker,
.nm-wl-nav-marker,
.nm-search-active-marker,
.nm-det-btn-row-marker,
.nm-wl-btn-row-marker {
    display: none !important;
    position: absolute !important;
    width: 0 !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    pointer-events: none !important;
}
.element-container:has(.nm-det-nav-marker),
.element-container:has(.nm-wl-nav-marker),
.element-container:has(.nm-search-active-marker),
.element-container:has(.nm-det-btn-row-marker),
.element-container:has(.nm-wl-btn-row-marker),
[data-testid*="lementContainer"]:has(.nm-det-nav-marker),
[data-testid*="lementContainer"]:has(.nm-wl-nav-marker),
[data-testid*="lementContainer"]:has(.nm-search-active-marker),
[data-testid*="lementContainer"]:has(.nm-det-btn-row-marker),
[data-testid*="lementContainer"]:has(.nm-wl-btn-row-marker) {
    display: none !important;
    margin: 0 !important;
    padding: 0 !important;
    height: 0 !important;
    min-height: 0 !important;
    line-height: 0 !important;
}

/* Collapse details backdrop container so it consumes 0 flow height */
.element-container:has(.det-bg),
[data-testid*="lementContainer"]:has(.det-bg) {
    margin: 0 !important;
    padding: 0 !important;
    height: 0 !important;
    min-height: 0 !important;
    overflow: visible !important;
}

/* Subpage Back & Action row */
div[data-testid*="orizontalBlock"]:has(.nm-det-btn-row-marker),
div[data-testid*="orizontalBlock"]:has(.nm-wl-btn-row-marker) {
    margin-top: 0 !important;
    margin-bottom: 0.5rem !important;
    align-items: center !important;
}

div[data-testid*="orizontalBlock"]:has(.nm-det-btn-row-marker) .stButton > button,
div[data-testid*="orizontalBlock"]:has(.nm-wl-btn-row-marker) .stButton > button {
    background: rgba(255, 255, 255, 0.07) !important;
    border: 1px solid rgba(255, 255, 255, 0.16) !important;
    border-radius: 20px !important;
    color: rgba(255, 255, 255, 0.85) !important;
    font-size: 0.82rem !important;
    font-weight: 700 !important;
    padding: 6px 16px !important;
    min-height: 34px !important;
    height: 34px !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: all 0.2s ease !important;
    width: auto !important;
}

div[data-testid*="orizontalBlock"]:has(.nm-det-btn-row-marker) .stButton > button:hover,
div[data-testid*="orizontalBlock"]:has(.nm-wl-btn-row-marker) .stButton > button:hover {
    background: rgba(255, 255, 255, 0.15) !important;
    border-color: rgba(255, 255, 255, 0.35) !important;
    color: #fff !important;
    transform: translateY(-1px) !important;
}

div[data-testid*="orizontalBlock"]:has(.nm-det-btn-row-marker) > div[data-testid*="olumn"]:last-child {
    display: flex !important;
    justify-content: flex-end !important;
}

div[data-testid*="orizontalBlock"]:has(.meta-chips) {
    margin-top: 0 !important;
}

/* ── Sticky Nav (single row: logo + browse + search + watchlist + home) ── */
div[data-testid="stHorizontalBlock"]:has(.nm-logo) {
    position: fixed !important;
    top: 0 !important; left: 0 !important; right: 0 !important;
    width: 100% !important;
    max-width: 100vw !important;
    box-sizing: border-box !important;
    background: #0d1220 !important;
    z-index: 99999 !important;
    padding: 0.8rem 2.4rem !important;
    margin: 0 !important;
    border-bottom: 1px solid rgba(255,255,255,0.06) !important;
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    gap: 8px !important;
}
div[data-baseweb="popover"] { z-index: 999999 !important; }

/* ── Logo ───────────────────────────────────── */
a.nm-logo, .nm-logo {
    font-size: 1.5rem;
    font-weight: 900;
    color: #E50914 !important;
    letter-spacing: -0.03em;
    line-height: 1;
    white-space: nowrap;
    text-decoration: none !important;
    cursor: pointer !important;
    transition: opacity 0.2s ease, transform 0.2s ease !important;
    display: inline-block !important;
}
a.nm-logo:hover {
    color: #ff2a36 !important;
    opacity: 0.92;
    text-decoration: none !important;
    transform: scale(1.03);
}

/* ── Nav buttons ────────────────────────────── */
.stButton > button[kind="secondary"] {
    background: transparent !important;
    border: none !important;
    color: rgba(255,255,255,0.5) !important;
    font-size: 0.8rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.04em;
    padding: 6px 0 !important;
    min-height: 36px !important;
    box-shadow: none !important;
    transition: color 0.2s !important;
    border-radius: 0 !important;
    width: 100%;
    text-transform: uppercase;
    white-space: nowrap;
}
.stButton > button[kind="secondary"]:hover { color: #fff !important; }

/* Nav-row buttons: don't stretch full width, keep tight */
div[data-testid="stHorizontalBlock"]:has(.nm-logo) .stButton > button {
    width: auto !important;
    padding: 6px 10px !important;
}
/* Push right-side nav items toward the right edge */
div[data-testid="stHorizontalBlock"]:has(.nm-logo) > div[data-testid*="olumn"]:has(.nm-nav-spacer) {
    flex: 1 1 auto !important;
    min-width: 10px !important;
}

div[data-testid="stHorizontalBlock"]:has(.nm-logo) > div[data-testid*="olumn"]:has(.nm-nav-browse) {
    flex: 0 0 auto !important;
    width: auto !important;
    min-width: 120px !important;
    display: flex !important;
    justify-content: flex-end !important;
}

div[data-testid="stHorizontalBlock"]:has(.nm-logo) > div[data-testid*="olumn"]:has(.nm-nav-search) {
    flex: 0 1 300px !important;
    width: 100% !important;
    max-width: 300px !important;
    display: flex !important;
    justify-content: flex-end !important;
}

/* Watchlist and Home: keep tightly grouped next to each other */
div[data-testid="stHorizontalBlock"]:has(.nm-logo) > div[data-testid*="olumn"]:has(.nm-nav-wl),
div[data-testid="stHorizontalBlock"]:has(.nm-logo) > div[data-testid*="olumn"]:has(.nm-nav-home) {
    width: auto !important;
    min-width: 0 !important;
    flex: 0 0 auto !important;
    display: flex !important;
    justify-content: flex-end !important;
    margin: 0 !important;
    padding: 0 !important;
}

div[data-testid="stHorizontalBlock"]:has(.nm-logo) > div[data-testid*="olumn"]:has(.nm-nav-wl) .stButton,
div[data-testid="stHorizontalBlock"]:has(.nm-logo) > div[data-testid*="olumn"]:has(.nm-nav-home) .stButton {
    width: auto !important;
    margin: 0 !important;
}

div[data-testid="stHorizontalBlock"]:has(.nm-logo) > div[data-testid*="olumn"]:has(.nm-nav-wl) .stButton > button,
div[data-testid="stHorizontalBlock"]:has(.nm-logo) > div[data-testid*="olumn"]:has(.nm-nav-home) .stButton > button {
    width: auto !important;
    padding: 6px 10px !important;
    white-space: nowrap !important;
}

/* Search input inside the nav row */
div[data-testid="stHorizontalBlock"]:has(.nm-logo) .stTextInput {
    margin: 0 !important;
    max-width: 320px !important;
    width: 100% !important;
}
div[data-testid="stHorizontalBlock"]:has(.nm-logo) .stTextInput > div {
    max-width: 320px !important;
}
div[data-testid="stHorizontalBlock"]:has(.nm-logo) .stTextInput > div > div > input {
    min-height: 38px !important;
    max-width: 320px !important;
    padding: 0.45rem 0.9rem !important;
    font-size: 0.85rem !important;
}

/* Nav markers (zero height, invisible) */
.nm-nav-browse, .nm-nav-search, .nm-nav-spacer, .nm-nav-wl, .nm-nav-home {
    display: none !important;
    position: absolute !important;
    width: 0 !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    pointer-events: none !important;
}
.element-container:has(.nm-nav-browse),
.element-container:has(.nm-nav-search),
.element-container:has(.nm-nav-spacer),
.element-container:has(.nm-nav-wl),
.element-container:has(.nm-nav-home),
[data-testid*="lementContainer"]:has(.nm-nav-browse),
[data-testid*="lementContainer"]:has(.nm-nav-search),
[data-testid*="lementContainer"]:has(.nm-nav-spacer),
[data-testid*="lementContainer"]:has(.nm-nav-wl),
[data-testid*="lementContainer"]:has(.nm-nav-home) {
    display: none !important;
    margin: 0 !important;
    padding: 0 !important;
    height: 0 !important;
    min-height: 0 !important;
}

/* Primary CTA (View Details) */
.stButton > button[kind="primary"] {
    background: #E50914 !important;
    border: none !important;
    color: #fff !important;
    font-weight: 800 !important;
    letter-spacing: 0.03em;
    border-radius: 24px !important;
    padding: 0 1.8rem !important;
    height: 46px !important;
    line-height: 46px !important;
    font-size: 0.82rem !important;
    text-transform: uppercase;
    box-shadow: 0 6px 18px rgba(229,9,20,0.35) !important;
    transition: background 0.2s !important;
}
.stButton > button[kind="primary"]:hover { background: #b8060d !important; }

/* Hero column buttons: stacked vertically (View Details on top, Watchlist below).
   Uses substring attribute selectors ([data-testid*="..."]) instead of exact matches
   because Streamlit has renamed these testids across versions (e.g. "column" -> "stColumn"). */
div[data-testid*="orizontalBlock"]:has(.nm-hero-marker) {
    align-items: flex-start !important;
    position: relative !important;
    z-index: 5 !important;
    margin-top: -110px !important;
    padding: 0 2.4rem !important;
}
div[data-testid*="olumn"]:has(.nm-hero-marker) {
    row-gap: 14px !important;
    gap: 14px !important;
    display: flex !important;
    flex-direction: column !important;
}
.element-container:has(.nm-hero-marker),
[data-testid*="lementContainer"]:has(.nm-hero-marker),
[data-testid*="arkdownContainer"]:has(.nm-hero-marker),
div[class*="stMarkdown"]:has(.nm-hero-marker) {
    margin: 0 !important;
    padding: 0 !important;
    min-height: 0 !important;
    height: 0 !important;
}
.nm-hero-marker {
    position: absolute !important;
    display: block !important;
    height: 0 !important;
    width: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    line-height: 0 !important;
    overflow: hidden !important;
    pointer-events: none !important;
}
div[data-testid*="olumn"]:has(.nm-hero-marker) .stButton > button[kind="primary"],
div[data-testid*="olumn"]:has(.nm-hero-marker) .stButton > button[kind="secondary"] {
    height: 46px !important;
    line-height: 46px !important;
    padding: 0 1.8rem !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    box-sizing: border-box !important;
    white-space: nowrap !important;
    width: 100% !important;
}
div[data-testid*="olumn"]:has(.nm-hero-marker) .stButton > button[kind="secondary"] {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.22) !important;
    color: #fff !important;
    font-weight: 800 !important;
    letter-spacing: 0.03em;
    border-radius: 24px !important;
    font-size: 0.82rem !important;
    text-transform: uppercase;
    transition: background 0.2s, border-color 0.2s !important;
}
div[data-testid*="olumn"]:has(.nm-hero-marker) .stButton > button[kind="secondary"]:hover {
    background: rgba(255,255,255,0.15) !important;
    border-color: rgba(255,255,255,0.35) !important;
    color: #fff !important;
}

/* ── Search bar ─────────────────────────────── */
.stTextInput > div > div > input {
    background: #131a2b !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 10px !important;
    color: #fff !important;
    font-size: 0.88rem !important;
    padding: 0.7rem 1.1rem !important;
    transition: all 0.3s ease !important;
    min-height: 44px !important;
    box-shadow: none !important;
}
.stTextInput > div > div > input:focus {
    border-color: rgba(229,9,20,0.5) !important;
    background: #161d31 !important;
}
.stTextInput > div > div > input::placeholder { color: rgba(255,255,255,0.35) !important; }

/* ── Selectbox (browse) ─────────────────────── */
.stSelectbox > div > div {
    background: transparent !important;
    border: none !important;
    color: rgba(255,255,255,0.8) !important;
    font-size: 0.8rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.04em;
    min-height: 36px !important;
    box-shadow: none !important;
    text-transform: uppercase;
}
div[data-testid="stHorizontalBlock"]:has(.nm-logo) div[data-baseweb="select"] > div {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.16) !important;
    border-radius: 8px !important;
    cursor: pointer !important;
    padding-left: 4px !important;
    transition: background 0.2s, border-color 0.2s !important;
}
div[data-testid="stHorizontalBlock"]:has(.nm-logo) div[data-baseweb="select"] > div:hover {
    background: rgba(255,255,255,0.12) !important;
    border-color: rgba(229,9,20,0.5) !important;
}
div[data-testid="stHorizontalBlock"]:has(.nm-logo) div[data-baseweb="select"] svg {
    fill: rgba(255,255,255,0.6) !important;
}

/* ── Section title ──────────────────────────── */
.section-title {
    font-size: 1.05rem; font-weight: 800; color: #fff;
    margin-bottom: 1rem; padding-left: 10px;
    border-left: 3px solid #E50914; line-height: 1;
    display: flex; align-items: center; justify-content: space-between;
    text-transform: uppercase; letter-spacing: 0.03em;
}
.section-title .see-all {
    font-size: 0.75rem; color: #E50914; font-weight: 600;
    cursor: pointer; padding-left: 8px;
}

/* ── Movie cards ────────────────────────────── */
@keyframes fadeIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
.movie-card-wrap {
    position: relative; border-radius: 8px; overflow: hidden;
    background: #10162a; box-shadow: 0 8px 16px rgba(0,0,0,0.4);
    transition: transform 0.25s cubic-bezier(0.25,0.8,0.25,1), box-shadow 0.25s;
    cursor: pointer; animation: fadeIn 0.4s ease backwards;
}
.movie-card-wrap:hover {
    transform: scale(1.05) translateY(-4px);
    box-shadow: 0 16px 32px rgba(0,0,0,0.7), 0 0 0 2px rgba(229,9,20,0.6);
    z-index: 10;
}
.movie-card-img {
    width: 100%; aspect-ratio: 2/3; object-fit: cover; display: block;
}
.movie-card-overlay {
    position: absolute; inset: 0;
    background: linear-gradient(to top, rgba(0,0,0,0.92) 0%, rgba(0,0,0,0.3) 40%, transparent 100%);
    opacity: 0; transition: opacity 0.25s; display: flex;
    flex-direction: column; justify-content: flex-end; padding: 12px;
}
.movie-card-wrap:hover .movie-card-overlay { opacity: 1; }
.card-title-hover { font-size: 0.8rem; font-weight: 700; color: #fff; line-height: 1.3; margin-bottom: 5px; }
.rating-badge {
    display: inline-flex; align-items: center; gap: 3px;
    background: rgba(229,9,20,0.15); border: 0.5px solid rgba(229,9,20,0.35);
    color: #FF5C5C; border-radius: 6px; padding: 2px 7px;
    font-size: 0.72rem; font-weight: 700; width: fit-content;
}
.movie-card-title {
    font-size: 0.78rem; font-weight: 500; color: rgba(255,255,255,0.6);
    margin-top: 6px; padding: 0 3px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.watchlist-badge {
    position: absolute; top: 7px; right: 7px;
    background: rgba(229,9,20,0.9); border-radius: 50%;
    width: 24px; height: 24px; display: flex;
    align-items: center; justify-content: center;
    font-size: 0.6rem; color: #fff; font-weight: 700;
}

/* ── Genre pills ────────────────────────────── */
.genre-pills {
    display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 1.2rem;
}
.genre-pill {
    font-size: 0.75rem; font-weight: 600;
    padding: 4px 12px; border-radius: 20px; cursor: pointer;
    border: 0.5px solid rgba(255,255,255,0.1);
    color: rgba(255,255,255,0.55); background: transparent;
    transition: all 0.2s; display: inline-block;
}
.genre-pill.active { background: #E50914; border-color: #E50914; color: #fff; }

/* ── Hero ───────────────────────────────────── */
.nm-hero-wrap { position: relative; width: 100%; margin-top: -1rem; height: 600px; }
.cinematic-hero-bg {
    position: absolute; top: 0; left: 0; right: 0; height: 100%;
    background-color: #0a0e1a;
    background-size: cover; background-position: center 25%;
    z-index: 1;
}
.nm-hero-shade-h {
    position: absolute; top: 0; left: 0; height: 100%; width: 65%;
    background: linear-gradient(to right, #0a0e1a 15%, rgba(10,14,26,0.85) 45%, rgba(10,14,26,0.15) 90%, transparent 100%);
    z-index: 2;
}
.nm-hero-shade-v {
    position: absolute; bottom: 0; left: 0; right: 0; height: 45%;
    background: linear-gradient(to top, #0a0e1a 0%, transparent 100%);
    z-index: 2;
}
.nm-hero-content { position: relative; z-index: 3; padding: 5.5rem 2.4rem 3rem; }

.nm-badge-row { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.nm-badge-pill {
    background: #E50914; color: #fff; font-size: 0.72rem; font-weight: 800;
    letter-spacing: 0.05em; text-transform: uppercase;
    padding: 5px 12px; border-radius: 5px;
}
.nm-badge-meta {
    color: rgba(255,255,255,0.55); font-size: 0.78rem; font-weight: 700;
    letter-spacing: 0.05em; text-transform: uppercase;
}
.nm-hero-title {
    font-size: 4.6rem; font-weight: 900; color: #fff; line-height: 0.95;
    letter-spacing: -0.02em; margin-bottom: 18px; text-transform: uppercase;
    font-style: italic; max-width: 780px;
}
.nm-hero-desc {
    color: rgba(255,255,255,0.7); font-size: 1.02rem; line-height: 1.6;
    max-width: 560px; margin-bottom: 26px; font-weight: 400;
}

/* ── Thumbnail rail (right of hero) ──────────── */
.nm-rail {
    position: absolute; top: 0; right: 0; height: 100%; width: 130px;
    z-index: 3; display: flex; flex-direction: column; gap: 10px;
    padding: 1.4rem 1.6rem; overflow: hidden;
}
.nm-rail-item {
    border-radius: 8px; overflow: hidden; flex-shrink: 0;
    border: 2px solid transparent; opacity: 0.55; transition: all 0.2s;
    aspect-ratio: 2/3; width: 100%;
}
.nm-rail-item.active { border-color: #E50914; opacity: 1; box-shadow: 0 0 0 1px #E50914, 0 8px 20px rgba(0,0,0,0.6); }
.nm-rail-item img { width: 100%; height: 100%; object-fit: cover; display: block; }

/* ── Meta chips ─────────────────────────────── */
.meta-chips { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 1.2rem; }
.meta-chip {
    background: rgba(255,255,255,0.03); border: 0.5px solid rgba(255,255,255,0.08);
    border-radius: 10px; padding: 8px 16px; backdrop-filter: blur(4px);
}
.meta-chip-label { font-size: 0.65rem; font-weight: 700; color: rgba(255,255,255,0.35); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 3px; }
.meta-chip-value { font-size: 0.9rem; font-weight: 700; color: #fff; }

/* ── Cast card ──────────────────────────────── */
.cast-card {
    text-align: center; width: 80px;
    display: inline-block; vertical-align: top;
    margin-right: 12px;
}
.cast-avatar {
    width: 60px; height: 60px; border-radius: 50%;
    object-fit: cover; border: 1.5px solid rgba(255,255,255,0.1);
    margin: 0 auto 5px; display: block;
}
.cast-avatar-initials {
    width: 60px; height: 60px; border-radius: 50%;
    background: linear-gradient(135deg, #172038, #0a0e1a);
    border: 0.5px solid rgba(255,255,255,0.1);
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto 5px; font-size: 0.8rem; font-weight: 700;
    color: rgba(255,255,255,0.5);
}
.cast-name { font-size: 0.7rem; font-weight: 600; color: rgba(255,255,255,0.75); line-height: 1.3; }
.cast-role { font-size: 0.62rem; color: rgba(255,255,255,0.35); margin-top: 2px; }

/* ── Watchlist sidebar items ────────────────── */
.wl-item {
    display: flex; align-items: center; gap: 10px;
    padding: 8px 0; border-bottom: 0.5px solid rgba(255,255,255,0.06);
}
.wl-poster { width: 36px; height: 54px; border-radius: 5px; object-fit: cover; flex-shrink: 0; }
.wl-info { flex: 1; min-width: 0; }
.wl-title { font-size: 0.78rem; font-weight: 600; color: #fff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.wl-rating { font-size: 0.68rem; color: #FF5C5C; margin-top: 2px; }

/* ── Skeleton loading ───────────────────────── */
@keyframes shimmer {
    0% { background-position: -600px 0; }
    100% { background-position: 600px 0; }
}
.skeleton-card {
    aspect-ratio: 2/3; border-radius: 8px;
    background: linear-gradient(90deg, #10162a 25%, #1a2238 37%, #10162a 63%);
    background-size: 1200px 100%;
    animation: shimmer 1.5s ease-in-out infinite;
}

/* ── Divider ────────────────────────────────── */
.nm-divider { border: none; border-top: 0.5px solid rgba(255,255,255,0.07); margin: 2rem 0; }

/* ── Empty state ────────────────────────────── */
.empty-state {
    text-align: center; padding: 3rem 1rem; color: rgba(255,255,255,0.3);
    font-size: 0.9rem; background: rgba(255,255,255,0.02);
    border-radius: 12px; border: 0.5px dashed rgba(255,255,255,0.08);
}

/* ── Load more ──────────────────────────────── */
.load-more-wrap { display: flex; justify-content: center; margin-top: 1.5rem; }

/* ── Pagination row (numbered page switcher) ─── */
div[data-testid*="orizontalBlock"]:has(.nm-pg-marker) {
    justify-content: center !important;
    align-items: center !important;
    gap: 6px !important;
}
div[data-testid*="orizontalBlock"]:has(.nm-pg-marker) > div[data-testid*="olumn"] {
    width: auto !important;
    min-width: 0 !important;
    flex: 0 0 auto !important;
}
.element-container:has(.nm-pg-marker),
[data-testid*="lementContainer"]:has(.nm-pg-marker),
[data-testid*="arkdownContainer"]:has(.nm-pg-marker),
div[class*="stMarkdown"]:has(.nm-pg-marker) {
    margin: 0 !important;
    padding: 0 !important;
    min-height: 0 !important;
    height: 0 !important;
}
.nm-pg-marker {
    position: absolute !important;
    display: block !important;
    height: 0 !important; width: 0 !important;
    margin: 0 !important; padding: 0 !important;
    line-height: 0 !important;
    overflow: hidden !important; pointer-events: none !important;
}
div[data-testid*="orizontalBlock"]:has(.nm-pg-marker) .stButton > button {
    min-width: 40px !important;
    width: 40px !important;
    height: 40px !important;
    padding: 0 !important;
    border-radius: 8px !important;
    font-size: 0.85rem !important;
    font-weight: 700 !important;
    text-transform: none !important;
    letter-spacing: normal !important;
}
div[data-testid*="orizontalBlock"]:has(.nm-pg-marker) .stButton > button[kind="secondary"] {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: rgba(255,255,255,0.6) !important;
}
div[data-testid*="orizontalBlock"]:has(.nm-pg-marker) .stButton > button[kind="secondary"]:hover:not(:disabled) {
    background: rgba(255,255,255,0.12) !important;
    border-color: rgba(255,255,255,0.2) !important;
    color: #fff !important;
}
div[data-testid*="orizontalBlock"]:has(.nm-pg-marker) .stButton > button[kind="primary"] {
    box-shadow: none !important;
}
div[data-testid*="orizontalBlock"]:has(.nm-pg-marker) .stButton > button:disabled {
    opacity: 0.35 !important;
    cursor: not-allowed !important;
}
.nm-pg-ellipsis {
    color: rgba(255,255,255,0.3); font-size: 0.85rem;
    padding-top: 10px; text-align: center; min-width: 20px;
}
.nm-pg-wrap { display: flex; justify-content: center; margin-top: 1.5rem; }

/* ── Page content padding (below hero) ───────── */
.nm-page-pad { padding: 0 2.4rem; }

/* ── Details Page Typography & Spacing ───────── */
.det-title {
    font-size: 2.6rem;
    font-weight: 900;
    color: #fff;
    line-height: 1.1;
    margin-bottom: 6px;
    letter-spacing: -0.02em;
}
.det-tagline {
    font-size: 0.95rem;
    color: #E50914;
    font-style: italic;
    margin-bottom: 16px;
}
.det-overview {
    font-size: 1rem;
    color: rgba(255,255,255,0.68);
    line-height: 1.7;
}

/* ── Card Grid Base (Desktop > 1200px) ───────── */
@media (min-width: 1201px) {
    div[data-testid*="orizontalBlock"]:has(.movie-card-wrap),
    div[data-testid*="orizontalBlock"]:has(.skeleton-card) {
        display: flex !important;
        flex-direction: row !important;
        gap: 12px !important;
        margin-bottom: 12px !important;
    }
}

/* ── Responsive Breakpoint: Tablet & Small Laptops (769px - 1200px) ── */
@media (max-width: 1200px) {
    [data-testid="block-container"] {
        padding: 5.2rem 0rem 1.8rem !important;
    }
    [data-testid="block-container"]:has(.nm-det-nav-marker),
    [data-testid="block-container"]:has(.nm-wl-nav-marker),
    [data-testid="block-container"]:has(.nm-search-active-marker) {
        padding-top: 3.9rem !important;
        padding-left: 1.4rem !important;
        padding-right: 1.4rem !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.nm-logo) {
        padding: 0.7rem 1.4rem !important;
        gap: 6px !important;
    }
    .nm-logo {
        font-size: 1.3rem !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.nm-logo) .stTextInput {
        max-width: 240px !important;
    }
    .nm-page-pad {
        padding: 0 1.4rem !important;
    }
    .nm-hero-wrap {
        height: 520px !important;
    }
    .nm-hero-content {
        padding: 4.5rem 1.4rem 2rem !important;
    }
    .nm-hero-title {
        font-size: 3.2rem !important;
        line-height: 1.05 !important;
        max-width: 600px !important;
    }
    .nm-rail {
        width: 110px !important;
    }
    div[data-testid*="orizontalBlock"]:has(.nm-hero-marker) {
        margin-top: -95px !important;
        padding: 0 1.4rem !important;
    }
    div[data-testid*="orizontalBlock"]:has(.nm-hero-marker) > div[data-testid*="olumn"]:first-child {
        width: 220px !important;
    }

    /* 4 cards per row on tablets & medium displays */
    div[data-testid*="orizontalBlock"]:has(.movie-card-wrap),
    div[data-testid*="orizontalBlock"]:has(.skeleton-card) {
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 12px !important;
        margin-bottom: 12px !important;
    }
    div[data-testid*="orizontalBlock"]:has(.movie-card-wrap) > div[data-testid*="olumn"],
    div[data-testid*="orizontalBlock"]:has(.skeleton-card) > div[data-testid*="olumn"] {
        flex: 0 0 calc(25% - 9px) !important;
        min-width: calc(25% - 9px) !important;
        max-width: calc(25% - 9px) !important;
    }
    div[data-testid*="orizontalBlock"]:has(.movie-card-wrap) > div[data-testid*="olumn"]:not(:has(.movie-card-wrap)),
    div[data-testid*="orizontalBlock"]:has(.skeleton-card) > div[data-testid*="olumn"]:not(:has(.skeleton-card)) {
        display: none !important;
    }
}

/* ── Responsive Breakpoint: Tablets Portrait & Large Mobiles (481px - 768px) ── */
@media (max-width: 768px) {
    [data-testid="block-container"] {
        padding: 6.8rem 0rem 1.2rem !important;
    }
    [data-testid="block-container"]:has(.nm-det-nav-marker),
    [data-testid="block-container"]:has(.nm-wl-nav-marker),
    [data-testid="block-container"]:has(.nm-search-active-marker) {
        padding-top: 5.7rem !important;
        padding-left: 0.85rem !important;
        padding-right: 0.85rem !important;
    }
    div[data-testid*="orizontalBlock"]:has(.nm-det-btn-row-marker),
    div[data-testid*="orizontalBlock"]:has(.nm-wl-btn-row-marker) {
        display: flex !important;
        flex-direction: row !important;
        justify-content: space-between !important;
        align-items: center !important;
        margin-bottom: 0.4rem !important;
    }
    div[data-testid*="orizontalBlock"]:has(.nm-det-btn-row-marker) > div[data-testid*="olumn"]:nth-child(2) {
        display: none !important;
    }
    div[data-testid*="orizontalBlock"]:has(.nm-det-btn-row-marker) > div[data-testid*="olumn"],
    div[data-testid*="orizontalBlock"]:has(.nm-wl-btn-row-marker) > div[data-testid*="olumn"] {
        width: auto !important;
        min-width: 0 !important;
        flex: 0 0 auto !important;
    }
    /* Fixed 2-Row Header on Mobile/Tablet Portrait */
    div[data-testid="stHorizontalBlock"]:has(.nm-logo) {
        padding: 0.5rem 0.85rem !important;
        row-gap: 6px !important;
        column-gap: 6px !important;
        flex-wrap: wrap !important;
        justify-content: space-between !important;
        background: #0d1220 !important;
        border-bottom: 1px solid rgba(255,255,255,0.08) !important;
    }

    /* Reset Streamlit's default column width overrides */
    div[data-testid="stHorizontalBlock"]:has(.nm-logo) > div[data-testid*="olumn"] {
        min-width: 0 !important;
        width: auto !important;
        flex: 0 0 auto !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Hide the spacer column on mobile */
    div[data-testid="stHorizontalBlock"]:has(.nm-logo) > div[data-testid*="olumn"]:has(.nm-nav-spacer) {
        display: none !important;
    }

    /* ROW 1: Logo on the left, Watchlist and Home on the right */
    div[data-testid="stHorizontalBlock"]:has(.nm-logo) > div[data-testid*="olumn"]:has(.nm-logo) {
        order: 1 !important;
        flex: 0 0 auto !important;
        display: flex !important;
        align-items: center !important;
    }
    .nm-logo {
        font-size: 1.3rem !important;
        line-height: 1 !important;
    }

    div[data-testid="stHorizontalBlock"]:has(.nm-logo) > div[data-testid*="olumn"]:has(.nm-nav-wl) {
        order: 2 !important;
        flex: 0 0 auto !important;
        margin-left: auto !important;
    }

    div[data-testid="stHorizontalBlock"]:has(.nm-logo) > div[data-testid*="olumn"]:has(.nm-nav-home) {
        order: 3 !important;
        flex: 0 0 auto !important;
    }

    /* ROW 2: Browse on the left, Search on the right */
    div[data-testid="stHorizontalBlock"]:has(.nm-logo) > div[data-testid*="olumn"]:has(.nm-nav-browse) {
        order: 4 !important;
        flex: 0 0 35% !important;
        min-width: 110px !important;
        max-width: 140px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.nm-logo) div[data-baseweb="select"] > div {
        min-height: 34px !important;
        height: 34px !important;
        font-size: 0.76rem !important;
        border-radius: 8px !important;
        padding-left: 6px !important;
        background: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
    }

    div[data-testid="stHorizontalBlock"]:has(.nm-logo) > div[data-testid*="olumn"]:has(.nm-nav-search) {
        order: 5 !important;
        flex: 1 1 auto !important;
        min-width: 140px !important;
        max-width: none !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.nm-logo) .stTextInput {
        max-width: 100% !important;
        width: 100% !important;
        margin: 0 !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.nm-logo) .stTextInput > div {
        max-width: 100% !important;
        width: 100% !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.nm-logo) .stTextInput > div > div > input {
        min-height: 34px !important;
        height: 34px !important;
        max-width: 100% !important;
        width: 100% !important;
        padding: 0.35rem 0.75rem !important;
        font-size: 0.78rem !important;
        border-radius: 8px !important;
        background: #141c2e !important;
        border: 1px solid rgba(255,255,255,0.14) !important;
    }

    /* Buttons in header */
    div[data-testid="stHorizontalBlock"]:has(.nm-logo) .stButton {
        margin: 0 !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.nm-logo) .stButton > button {
        padding: 4px 10px !important;
        font-size: 0.75rem !important;
        font-weight: 700 !important;
        min-height: 32px !important;
        height: 32px !important;
        border-radius: 6px !important;
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.14) !important;
        color: #fff !important;
    }
    .nm-page-pad {
        padding: 0 0.85rem !important;
    }
    .section-title {
        font-size: 0.95rem !important;
        margin-bottom: 0.8rem !important;
    }

    /* Hero section */
    .nm-hero-wrap {
        height: 440px !important;
    }
    .nm-hero-content {
        padding: 3.4rem 0.85rem 1.2rem !important;
    }
    .nm-hero-shade-h {
        width: 100% !important;
        background: linear-gradient(to right, rgba(10,14,26,0.92) 0%, rgba(10,14,26,0.72) 100%) !important;
    }
    .nm-hero-shade-v {
        height: 55% !important;
    }
    .nm-hero-title {
        font-size: 2.2rem !important;
        line-height: 1.1 !important;
        margin-bottom: 10px !important;
        max-width: 100% !important;
    }
    .nm-hero-desc {
        font-size: 0.85rem !important;
        line-height: 1.45 !important;
        max-width: 100% !important;
        margin-bottom: 12px !important;
    }
    .nm-rail {
        display: none !important;
    }
    div[data-testid*="orizontalBlock"]:has(.nm-hero-marker) {
        margin-top: -85px !important;
        padding: 0 0.85rem !important;
    }
    div[data-testid*="orizontalBlock"]:has(.nm-hero-marker) > div[data-testid*="olumn"]:first-child {
        width: 210px !important;
        max-width: 100% !important;
    }
    div[data-testid*="olumn"]:has(.nm-hero-marker) .stButton > button[kind="primary"],
    div[data-testid*="olumn"]:has(.nm-hero-marker) .stButton > button[kind="secondary"] {
        height: 40px !important;
        line-height: 40px !important;
        font-size: 0.78rem !important;
        padding: 0 1.2rem !important;
    }

    /* 3 cards per row on small tablets & larger phones */
    div[data-testid*="orizontalBlock"]:has(.movie-card-wrap),
    div[data-testid*="orizontalBlock"]:has(.skeleton-card) {
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 10px !important;
        margin-bottom: 10px !important;
    }
    div[data-testid*="orizontalBlock"]:has(.movie-card-wrap) > div[data-testid*="olumn"],
    div[data-testid*="orizontalBlock"]:has(.skeleton-card) > div[data-testid*="olumn"] {
        flex: 0 0 calc(33.333% - 7px) !important;
        min-width: calc(33.333% - 7px) !important;
        max-width: calc(33.333% - 7px) !important;
    }
    div[data-testid*="orizontalBlock"]:has(.movie-card-wrap) > div[data-testid*="olumn"]:not(:has(.movie-card-wrap)),
    div[data-testid*="orizontalBlock"]:has(.skeleton-card) > div[data-testid*="olumn"]:not(:has(.skeleton-card)) {
        display: none !important;
    }

    /* Touch screen friendly movie card overlay */
    .movie-card-overlay {
        opacity: 1 !important;
        background: linear-gradient(to top, rgba(0,0,0,0.7) 0%, transparent 45%) !important;
        padding: 6px !important;
    }
    .card-title-hover {
        display: none !important;
    }
    .rating-badge {
        font-size: 0.68rem !important;
        padding: 1px 5px !important;
    }
    .movie-card-title {
        font-size: 0.74rem !important;
    }

    /* Genre pills */
    .genre-pills {
        gap: 5px !important;
        margin-bottom: 0.9rem !important;
    }
    .genre-pill {
        font-size: 0.7rem !important;
        padding: 3px 9px !important;
    }

    /* Details Page Responsive Layout */
    div[data-testid*="orizontalBlock"]:has(.meta-chips) {
        flex-direction: column !important;
        align-items: center !important;
    }
    div[data-testid*="orizontalBlock"]:has(.meta-chips) > div[data-testid*="olumn"]:first-child {
        width: 100% !important;
        max-width: 220px !important;
        margin: 0 auto 1rem auto !important;
    }
    div[data-testid*="orizontalBlock"]:has(.meta-chips) > div[data-testid*="olumn"]:last-child {
        width: 100% !important;
        text-align: center !important;
    }
    .det-title {
        font-size: 1.7rem !important;
        text-align: center !important;
    }
    .det-tagline {
        text-align: center !important;
        font-size: 0.88rem !important;
    }
    .meta-chips {
        justify-content: center !important;
        gap: 6px !important;
    }
    .meta-chip {
        padding: 6px 10px !important;
    }
    .meta-chip-label {
        font-size: 0.6rem !important;
    }
    .meta-chip-value {
        font-size: 0.8rem !important;
    }
    .det-overview {
        font-size: 0.88rem !important;
        line-height: 1.55 !important;
        text-align: left !important;
    }

    /* Pagination buttons on mobile */
    div[data-testid*="orizontalBlock"]:has(.nm-pg-marker) {
        gap: 3px !important;
        flex-wrap: wrap !important;
    }
    div[data-testid*="orizontalBlock"]:has(.nm-pg-marker) .stButton > button {
        padding: 2px 7px !important;
        min-width: 28px !important;
        height: 30px !important;
        font-size: 0.74rem !important;
    }
}

/* ── Responsive Breakpoint: Standard Mobile (<= 480px) ── */
@media (max-width: 480px) {
    [data-testid="block-container"] {
        padding: 6.5rem 0rem 1rem !important;
    }
    [data-testid="block-container"]:has(.nm-det-nav-marker),
    [data-testid="block-container"]:has(.nm-wl-nav-marker),
    [data-testid="block-container"]:has(.nm-search-active-marker) {
        padding-top: 5.3rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.nm-logo) {
        padding: 0.4rem 0.6rem !important;
        row-gap: 5px !important;
        column-gap: 5px !important;
    }
    .nm-logo {
        font-size: 1.2rem !important;
        letter-spacing: -0.03em !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.nm-logo) > div[data-testid*="olumn"]:has(.nm-nav-browse) {
        flex: 0 0 35% !important;
        min-width: 95px !important;
        max-width: 120px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.nm-logo) div[data-baseweb="select"] > div {
        min-height: 32px !important;
        height: 32px !important;
        font-size: 0.72rem !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.nm-logo) .stTextInput > div > div > input {
        min-height: 32px !important;
        height: 32px !important;
        font-size: 0.74rem !important;
        padding: 0.25rem 0.55rem !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.nm-logo) .stButton > button {
        padding: 3px 7px !important;
        font-size: 0.7rem !important;
        min-height: 30px !important;
        height: 30px !important;
    }
    .nm-page-pad {
        padding: 0 0.5rem !important;
    }

    /* Hero section on small screens */
    .nm-hero-wrap {
        height: 390px !important;
    }
    .nm-hero-content {
        padding: 2.8rem 0.5rem 0.9rem !important;
    }
    .nm-hero-title {
        font-size: 1.75rem !important;
    }
    .nm-badge-pill {
        font-size: 0.64rem !important;
        padding: 3px 8px !important;
    }
    .nm-badge-meta {
        font-size: 0.68rem !important;
    }
    div[data-testid*="orizontalBlock"]:has(.nm-hero-marker) {
        margin-top: -72px !important;
        padding: 0 0.5rem !important;
    }
    div[data-testid*="orizontalBlock"]:has(.nm-hero-marker) > div[data-testid*="olumn"]:first-child {
        width: 100% !important;
        max-width: 195px !important;
    }
    div[data-testid*="olumn"]:has(.nm-hero-marker) .stButton > button[kind="primary"],
    div[data-testid*="olumn"]:has(.nm-hero-marker) .stButton > button[kind="secondary"] {
        height: 36px !important;
        line-height: 36px !important;
        font-size: 0.72rem !important;
        padding: 0 1rem !important;
    }

    /* 2 cards per row on mobile screens (Standard streaming layout) */
    div[data-testid*="orizontalBlock"]:has(.movie-card-wrap),
    div[data-testid*="orizontalBlock"]:has(.skeleton-card) {
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 8px !important;
        margin-bottom: 8px !important;
    }
    div[data-testid*="orizontalBlock"]:has(.movie-card-wrap) > div[data-testid*="olumn"],
    div[data-testid*="orizontalBlock"]:has(.skeleton-card) > div[data-testid*="olumn"] {
        flex: 0 0 calc(50% - 4px) !important;
        min-width: calc(50% - 4px) !important;
        max-width: calc(50% - 4px) !important;
    }
    div[data-testid*="orizontalBlock"]:has(.movie-card-wrap) > div[data-testid*="olumn"]:not(:has(.movie-card-wrap)),
    div[data-testid*="orizontalBlock"]:has(.skeleton-card) > div[data-testid*="olumn"]:not(:has(.skeleton-card)) {
        display: none !important;
    }

    .det-title {
        font-size: 1.45rem !important;
    }
    .cast-card {
        width: 70px !important;
        margin-right: 8px !important;
    }
    .cast-avatar, .cast-avatar-initials {
        width: 50px !important;
        height: 50px !important;
    }
    .cast-name {
        font-size: 0.65rem !important;
    }
}
</style>
""", unsafe_allow_html=True)

# =============================
# SESSION STATE
# =============================
defaults = {
    "view": "home",
    "selected_tmdb_id": None,
    "home_category": "trending",
    "home_page": 1,
    "watchlist": {},          # {tmdb_id: {title, poster_url, vote_average}}
    "active_genre_id": None,
    "active_genre_name": "All",
    "hero_index": 0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Query param sync
qp_view = st.query_params.get("view")
qp_id   = st.query_params.get("id")
if qp_view in ("home", "details", "watchlist"):
    st.session_state.view = qp_view
if qp_view == "home" and not qp_id and st.session_state.get("prev_qp_view") not in (None, "home"):
    st.session_state.selected_tmdb_id = None
    st.session_state.active_genre_id = None
    st.session_state.active_genre_name = "All"
    st.session_state.pop("top_search", None)
st.session_state.prev_qp_view = qp_view
if qp_id:
    try:
        st.session_state.selected_tmdb_id = int(qp_id)
        st.session_state.view = "details"
    except (ValueError, TypeError):
        pass

# =============================
# NAVIGATION HELPERS
# =============================
def goto_home():
    st.session_state.view = "home"
    st.session_state.home_page = 1
    st.session_state.pop("top_search", None)  # clear stale search text
    st.query_params["view"] = "home"
    st.query_params.pop("id", None)
    st.rerun()

def goto_details(tmdb_id: int):
    st.session_state.view = "details"
    st.session_state.selected_tmdb_id = int(tmdb_id)
    st.query_params["view"] = "details"
    st.query_params["id"] = str(int(tmdb_id))
    st.rerun()

def goto_watchlist():
    st.session_state.view = "watchlist"
    st.query_params["view"] = "watchlist"
    st.query_params.pop("id", None)
    st.rerun()

# =============================
# TEXT HELPERS
# =============================
def capitalize_sentences(text: str) -> str:
    if not isinstance(text, str) or not text:
        return text
    text = re.sub(r'^([^a-zA-Z]*)([a-zA-Z])', lambda m: m.group(1) + m.group(2).upper(), text)
    text = re.sub(r'([.?!]\s*[^a-zA-Z]*)([a-zA-Z])', lambda m: m.group(1) + m.group(2).upper(), text)
    return text

_ROMAN = {"ii","iii","iv","v","vi","vii","viii","ix","x","xi","xii","xiii","xiv","xv","xvi","xvii","xviii","xix","xx"}
_WORD_RE = re.compile(r"\b\w+\b")

def capitalize_title(title: str) -> str:
    if not isinstance(title, str) or not title:
        return title
    titled = title.title()
    titled = re.sub(r"'([A-Z])\b", lambda m: "'" + m.group(1).lower(), titled)
    titled = _WORD_RE.sub(lambda m: m.group(0).upper() if m.group(0).lower() in _ROMAN else m.group(0), titled)
    return titled

def format_rating(rating) -> str:
    try:
        if rating is not None:
            r = float(rating)
            if r > 0:
                return f"{round(r, 1)}"
            if r == 0:
                return "NR"
    except (ValueError, TypeError):
        pass
    return ""

def format_runtime(runtime) -> str:
    try:
        if runtime is not None:
            r = int(runtime)
            if r > 0:
                h, m = divmod(r, 60)
                if h > 0 and m > 0:
                    return f"{h}h {m}m"
                if h > 0:
                    return f"{h}h"
                return f"{m}m"
    except (ValueError, TypeError):
        pass
    return ""

def get_img_url(url, is_backdrop=False) -> str:
    if not url or not isinstance(url, str):
        return ""
    lower = url.lower()
    if "null" in lower or "none" in lower:
        return ""
    if url.startswith("/"):
        base = TMDB_BACKDROP if is_backdrop else TMDB_IMG
        return f"{base}{url}"
    return url

def initials(name: str) -> str:
    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return name[:2].upper() if name else "?"

# =============================
# API HELPERS
# =============================
@st.cache_data(ttl=60, show_spinner=False)
def api_get(path: str, params: Optional[dict] = None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=25)
        if r.status_code >= 400:
            return None, f"HTTP {r.status_code}: {r.text[:300]}"
        return r.json(), None
    except Exception as e:
        return None, f"Request failed: {e}"

@st.cache_data(ttl=3600, show_spinner=False)
def api_get_cached(path: str, params: Optional[dict] = None):
    return api_get.__wrapped__(path, params)

# =============================
# LOCAL METADATA & ENRICHMENT
# =============================
LANGUAGE_NAMES = {
    "en": "English", "es": "Spanish", "fr": "French", "de": "German",
    "it": "Italian", "ja": "Japanese", "ko": "Korean", "zh": "Chinese",
    "cn": "Chinese", "hi": "Hindi", "ru": "Russian", "pt": "Portuguese",
    "ta": "Tamil", "te": "Telugu", "ml": "Malayalam", "kn": "Kannada",
    "mr": "Marathi", "bn": "Bengali", "pa": "Punjabi", "ar": "Arabic",
    "tr": "Turkish", "nl": "Dutch", "sv": "Swedish", "da": "Danish",
    "no": "Norwegian", "fi": "Finnish", "pl": "Polish", "id": "Indonesian",
    "th": "Thai", "vi": "Vietnamese", "el": "Greek", "he": "Hebrew",
    "fa": "Persian", "cs": "Czech", "hu": "Hungarian", "ro": "Romanian",
}

def format_language(lang_raw) -> str:
    if not lang_raw or str(lang_raw).strip().lower() in ("", "none", "null", "n/a"):
        return "English"
    code = str(lang_raw).lower().strip()
    return LANGUAGE_NAMES.get(code, code.upper())

def _norm_title(t: str) -> str:
    return re.sub(r'[^a-z0-9]', '', str(t).lower())

@st.cache_resource
def load_local_movie_metadata() -> dict:
    meta_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "local_movie_meta.pkl")
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "rb") as f:
                return pickle.load(f)
        except Exception:
            pass
    return {}

def enrich_movie_details(data: dict, tmdb_id: int) -> dict:
    if not isinstance(data, dict):
        return data

    tid = int(tmdb_id) if tmdb_id else None

    # 1. Check in-memory session meta store
    meta_store = st.session_state.get("movie_meta_store", {})
    if tid and tid in meta_store:
        s_meta = meta_store[tid]
        for key in ("vote_average", "original_language", "runtime", "release_date", "tagline", "budget", "revenue"):
            if data.get(key) is None and s_meta.get(key) is not None:
                data[key] = s_meta[key]

    # 2. Check local metadata dataset (has 45,433 classic/popular movies)
    if tid:
        local_all = load_local_movie_metadata()
        local_entry = local_all.get(tid)
        if local_entry:
            for key in ("vote_average", "original_language", "runtime", "tagline", "budget", "revenue"):
                if data.get(key) is None and local_entry.get(key) is not None:
                    data[key] = local_entry[key]

    # 3. If vote_average or original_language is still missing, query /tmdb/search via backend
    need_rating = data.get("vote_average") is None
    need_lang = not data.get("original_language") or str(data.get("original_language")).strip().lower() in ("", "none", "null", "n/a")

    if (need_rating or need_lang) and data.get("title"):
        title_q = data["title"]
        search_res, _ = api_get_cached("/tmdb/search", {"query": title_q})
        if search_res:
            raw_list = search_res.get("results") if isinstance(search_res, dict) else search_res
            matched = None
            if isinstance(raw_list, list):
                if tid:
                    for item in raw_list:
                        if item.get("id") == tid:
                            matched = item
                            break
                if not matched:
                    norm_q = _norm_title(title_q)
                    for item in raw_list:
                        if _norm_title(item.get("title", "")) == norm_q:
                            matched = item
                            break
                if not matched and raw_list:
                    matched = raw_list[0]

            if matched:
                if need_rating and matched.get("vote_average") is not None:
                    data["vote_average"] = matched.get("vote_average")
                if need_lang and matched.get("original_language"):
                    data["original_language"] = matched.get("original_language")
                if not data.get("release_date") and matched.get("release_date"):
                    data["release_date"] = matched.get("release_date")
                if not data.get("vote_count") and matched.get("vote_count"):
                    data["vote_count"] = matched.get("vote_count")

    # Final guarantee for language
    if not data.get("original_language") or str(data.get("original_language")).strip().lower() in ("", "none", "null", "n/a"):
        data["original_language"] = "en"

    return data

# =============================
# WATCHLIST HELPERS
# =============================
def toggle_watchlist(tmdb_id: int, title: str, poster_url: str, vote_average):
    tid = int(tmdb_id)
    if tid in st.session_state.watchlist:
        del st.session_state.watchlist[tid]
    else:
        st.session_state.watchlist[tid] = {
            "title": title,
            "poster_url": poster_url,
            "vote_average": vote_average,
        }

def in_watchlist(tmdb_id: int) -> bool:
    return int(tmdb_id) in st.session_state.watchlist

# =============================
# CARD DATA HELPERS
# =============================
def to_card(m: dict) -> dict:
    """Normalize any movie dict to a standard card dict."""
    tid = m.get("tmdb_id") or m.get("id")
    if tid:
        try:
            itid = int(tid)
            store = st.session_state.setdefault("movie_meta_store", {})
            entry = store.setdefault(itid, {})
            for k in ("vote_average", "original_language", "runtime", "release_date", "title"):
                v = m.get(k)
                if v is not None and v != "":
                    entry[k] = v
        except Exception:
            pass
    return {
        "tmdb_id": tid,
        "title": capitalize_title((m.get("title") or "").strip()),
        "poster_url": get_img_url(m.get("poster_url") or m.get("poster_path")),
        "vote_average": m.get("vote_average"),
        "release_date": m.get("release_date", ""),
    }

def tfidf_to_cards(items: list) -> list:
    cards = []
    for x in (items or []):
        tmdb = x.get("tmdb") or {}
        if tmdb.get("tmdb_id"):
            cards.append(to_card(tmdb))
    return cards

def parse_search_results(data: dict, keyword: str, limit: int = 24):
    raw = data.get("results") or [] if isinstance(data, dict) else data
    cards, suggestions = [], []
    for m in raw:
        c = to_card(m)
        if c["tmdb_id"] and c["poster_url"]:
            cards.append(c)
            year = (c.get("release_date") or "")[:4]
            label = f"{c['title']} ({year})" if year else c["title"]
            if len(suggestions) < 10:
                suggestions.append((label, c["tmdb_id"]))
    return suggestions, cards[:limit]

# =============================
# POSTER GRID
# =============================
STAR_SVG = '<svg style="width:11px;height:11px;fill:#FF5C5C;stroke:#FF5C5C;stroke-width:2;vertical-align:middle;margin-right:2px;margin-bottom:1px;" viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>'
PLAY_SVG  = '<svg style="width:13px;height:13px;fill:#fff;vertical-align:middle;margin-right:4px;" viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>'

def render_skeleton_grid(cols=7, rows=2):
    for _ in range(rows):
        colset = st.columns(cols, gap="small")
        for c in range(cols):
            with colset[c]:
                st.markdown('<div class="skeleton-card"></div>', unsafe_allow_html=True)

def poster_grid(cards: list, cols: int = 7, key_prefix: str = "grid"):
    valid = [c for c in (cards or []) if get_img_url(c.get("poster_url"))]
    if not valid:
        st.markdown('<div class="empty-state">Nothing to show here yet.</div>', unsafe_allow_html=True)
        return

    rows = (len(valid) + cols - 1) // cols
    idx = 0
    for _ in range(rows):
        colset = st.columns(cols, gap="small")
        for c in range(cols):
            if idx >= len(valid):
                break
            m = valid[idx]
            idx += 1
            tmdb_id   = m.get("tmdb_id")
            title     = capitalize_title(m.get("title", "Untitled"))
            poster    = get_img_url(m.get("poster_url"))
            rating    = format_rating(m.get("vote_average"))
            safe_t    = title.replace('"', '&quot;')
            trunc     = safe_t[:36] + "…" if len(safe_t) > 36 else safe_t
            rating_html = f'<div class="rating-badge">{STAR_SVG}{rating}</div>' if rating else ""
            wl_badge  = '<div class="watchlist-badge">✓</div>' if tmdb_id and in_watchlist(tmdb_id) else ""

            card_html = (
                f'<div class="movie-card-wrap" style="animation-delay:{idx*0.04}s">'
                f'{wl_badge}'
                f'<img class="movie-card-img" src="{poster}" alt="{safe_t}" loading="lazy" '
                f'onerror="this.onerror=null;this.src=\'{PLACEHOLDER_POSTER}\';">'
                f'<div class="movie-card-overlay">'
                f'<div class="card-title-hover">{trunc}</div>'
                f'{rating_html}'
                f'</div></div>'
                f'<div class="movie-card-title">{safe_t[:24] + "…" if len(safe_t) > 24 else safe_t}</div>'
            )

            with colset[c]:
                if tmdb_id:
                    st.markdown(
                        f'<a href="?view=details&id={tmdb_id}" target="_self" style="text-decoration:none;color:inherit;">{card_html}</a>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(card_html, unsafe_allow_html=True)

# =============================
# ROTATING HERO
# =============================
@st.fragment(run_every=6)
def render_hero(home_cards: list):
    valid = [c for c in home_cards if get_img_url(c.get("poster_url"))]
    if not valid:
        return

    rail_pool = valid[:8]
    st.session_state.hero_index = int(time.time() // 6) % min(len(valid), 12)
    feat = valid[st.session_state.hero_index]

    tmdb_id = feat.get("tmdb_id") or feat.get("id")
    poster  = get_img_url(feat.get("poster_url") or feat.get("poster_path"))
    backdrop = get_img_url(feat.get("backdrop_url") or feat.get("backdrop_path"), is_backdrop=True)
    overview = capitalize_sentences(feat.get("overview", ""))
    title    = capitalize_title(feat.get("title", "Featured"))
    release  = feat.get("release_date") or ""
    rating   = format_rating(feat.get("vote_average"))
    genres_list = []

    # Try fetching details if missing overview or backdrop
    if (not overview or not backdrop) and tmdb_id:
        det, _ = api_get_cached(f"/movie/id/{tmdb_id}")
        if det:
            overview = overview or capitalize_sentences(det.get("overview", ""))
            backdrop = backdrop or get_img_url(det.get("backdrop_url") or det.get("backdrop_path"), is_backdrop=True)
            release  = release or det.get("release_date", "")
            genres_list = [g["name"].upper() for g in (det.get("genres") or [])[:3]]

    if not backdrop:
        backdrop = poster or PLACEHOLDER_BACKDROP
    if not poster:
        poster = PLACEHOLDER_POSTER

    badge_label = genres_list[0] if genres_list else "FEATURED"
    year = release[:4] if release else ""
    meta_text = f"MOVIE" + (f" • {year}" if year else "")

    # Right-side thumbnail rail
    rail_html = '<div class="nm-rail">'
    for i, rm in enumerate(rail_pool):
        rposter = get_img_url(rm.get("poster_url") or rm.get("poster_path")) or PLACEHOLDER_POSTER
        active = " active" if i == st.session_state.hero_index else ""
        rail_html += f'<div class="nm-rail-item{active}"><img src="{rposter}" loading="lazy"></div>'
    rail_html += '</div>'

    desc = overview[:170] + "…" if overview and len(overview) > 170 else (overview or "No overview available.")

    hero_html = (
        f'<div class="nm-hero-wrap">'
        f'<div class="cinematic-hero-bg" style="background-image:url(\'{backdrop}\');"></div>'
        f'<div class="nm-hero-shade-h"></div>'
        f'<div class="nm-hero-shade-v"></div>'
        f'{rail_html}'
        f'<div class="nm-hero-content">'
        f'<div class="nm-badge-row">'
        f'<span class="nm-badge-pill">{badge_label}</span>'
        f'<span class="nm-badge-meta">{meta_text}</span>'
        f'</div>'
        f'<div class="nm-hero-title">{title}</div>'
        f'<div class="nm-hero-desc">{desc}</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(hero_html, unsafe_allow_html=True)

    # ── Buttons stacked vertically: View Details on top, Watchlist directly below ──
    st.markdown('<div class="nm-page-pad">', unsafe_allow_html=True)
    btn_col, spacer_col = st.columns([1.3, 4.7], gap="small")
    with btn_col:
        st.markdown('<span class="nm-hero-marker"></span>', unsafe_allow_html=True)
        if tmdb_id and st.button("▶  View Details", key=f"hero_btn_{tmdb_id}", type="primary", use_container_width=True):
            goto_details(tmdb_id)
        if tmdb_id and st.button(
            "✓  In Watchlist" if in_watchlist(tmdb_id) else "+  Watchlist",
            key=f"hero_wl_{tmdb_id}",
            use_container_width=True,
        ):
            toggle_watchlist(tmdb_id, title, poster, feat.get("vote_average"))
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

# =============================
# CAST SECTION
# =============================
def render_cast(tmdb_id: int):
    cast_data, err = api_get_cached(f"/movie/id/{tmdb_id}/cast", {"limit": 10})
    if err or not cast_data:
        return

    # Defensive: API may return a raw list or a dict wrapper like {"cast": [...]}
    if isinstance(cast_data, dict):
        cast_data = cast_data.get("cast") or cast_data.get("results") or []
    if not cast_data:
        return

    st.markdown('<hr class="nm-divider">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Cast</div>', unsafe_allow_html=True)

    html = '<div style="display:flex;flex-wrap:nowrap;overflow-x:auto;gap:0;padding-bottom:8px;scrollbar-width:none;">'
    for member in cast_data:
        if not isinstance(member, dict):
            continue
        profile = get_img_url(member.get("profile_url") or member.get("profile_path"))
        name    = member.get("name", "")
        role    = member.get("character", "")
        ini     = initials(name)

        avatar_html = (
            f'<img class="cast-avatar" src="{profile}" alt="{name}" '
            f'onerror="this.outerHTML=\'<div class=cast-avatar-initials>{ini}</div>\'">'
            if profile else
            f'<div class="cast-avatar-initials">{ini}</div>'
        )
        safe_name = name[:16] + "…" if len(name) > 16 else name
        safe_role = role[:16] + "…" if len(role) > 16 else role
        html += (
            f'<div class="cast-card">'
            f'{avatar_html}'
            f'<div class="cast-name">{safe_name}</div>'
            f'<div class="cast-role">{safe_role}</div>'
            f'</div>'
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

# =============================
# GENRE FILTER BAR
# =============================
def render_genre_filters():
    genres, err = api_get_cached("/genres")
    if err or not genres:
        return

    # Defensive: API may return a raw list or a dict wrapper like {"genres": [...]}
    if isinstance(genres, dict):
        genres = genres.get("genres") or genres.get("results") or []
    genres = [g for g in genres if isinstance(g, dict) and g.get("id") is not None and g.get("name")]
    if not genres:
        return

    all_genres = [{"id": None, "name": "All"}] + genres
    pills = ""
    for g in all_genres:
        is_active = (g["id"] == st.session_state.active_genre_id)
        cls = "genre-pill active" if is_active else "genre-pill"
        gid = g["id"] if g["id"] is not None else "all"
        pills += f'<span class="{cls}" onclick="void(0)">{g["name"]}</span> '

    st.markdown(f'<div class="genre-pills">{pills}</div>', unsafe_allow_html=True)

    # Streamlit selectbox version (functional)
    genre_names = ["All"] + [g["name"] for g in genres]
    genre_ids   = [None]  + [g["id"]   for g in genres]
    current_name = st.session_state.active_genre_name or "All"
    try:
        cur_idx = genre_names.index(current_name)
    except ValueError:
        cur_idx = 0

    selected = st.selectbox(
        "Filter by genre",
        genre_names,
        index=cur_idx,
        label_visibility="collapsed",
        key="genre_select",
    )
    sel_idx = genre_names.index(selected)
    new_id  = genre_ids[sel_idx]
    if new_id != st.session_state.active_genre_id:
        st.session_state.active_genre_id   = new_id
        st.session_state.active_genre_name = selected
        st.session_state.home_page = 1
        st.rerun()

# =============================
# PAGINATION (numbered page switcher)
# =============================
def render_pagination(cur_page: int, total_pages: int, key_prefix: str = "pg"):
    if total_pages <= 1:
        return

    # Build a windowed list of page numbers: first, last, and a window around current
    window = 1
    pages = {1, total_pages}
    for p in range(cur_page - window, cur_page + window + 1):
        if 1 <= p <= total_pages:
            pages.add(p)
    sorted_pages = sorted(pages)

    display = []
    prev_p = None
    for p in sorted_pages:
        if prev_p is not None and p - prev_p > 1:
            display.append("…")
        display.append(p)
        prev_p = p

    total_slots = len(display) + 2  # « prev + numbers + next »
    cols = st.columns(total_slots, gap="small")

    with cols[0]:
        st.markdown('<span class="nm-pg-marker"></span>', unsafe_allow_html=True)
        if st.button("‹", key=f"{key_prefix}_prev", disabled=(cur_page <= 1)):
            st.session_state.home_page = cur_page - 1
            st.rerun()

    for i, item in enumerate(display):
        with cols[i + 1]:
            if item == "…":
                st.markdown('<div class="nm-pg-ellipsis">…</div>', unsafe_allow_html=True)
            else:
                is_active = (item == cur_page)
                if st.button(
                    str(item),
                    key=f"{key_prefix}_p{item}",
                    type="primary" if is_active else "secondary",
                    disabled=is_active,
                ):
                    st.session_state.home_page = item
                    st.rerun()

    with cols[-1]:
        if st.button("›", key=f"{key_prefix}_next", disabled=(cur_page >= total_pages)):
            st.session_state.home_page = cur_page + 1
            st.rerun()

# =============================
# NAVIGATION (single fixed row: logo | home | browse | search | watchlist)
# =============================
GRID_COLS = 7

nc_logo, nc_spacer, nc_browse, nc_search, nc_wl, nc_home = st.columns(
    [1.2, 4.0, 1.2, 2.5, 0.7, 0.5], gap="small"
)

with nc_logo:
    st.markdown('<a href="?view=home" target="_self" class="nm-logo">NetMovie</a>', unsafe_allow_html=True)

with nc_spacer:
    st.markdown('<span class="nm-nav-spacer"></span>', unsafe_allow_html=True)

with nc_browse:
    st.markdown('<span class="nm-nav-browse"></span>', unsafe_allow_html=True)
    browse_cat = st.selectbox(
        "Browse",
        ["trending", "popular", "top_rated", "now_playing", "upcoming"],
        format_func=lambda x: x.replace("_", " ").title(),
        index=["trending","popular","top_rated","now_playing","upcoming"].index(
            st.session_state.home_category
        ),
        label_visibility="collapsed",
        key="browse_select",
    )
    if browse_cat != st.session_state.home_category:
        st.session_state.home_category = browse_cat
        st.session_state.home_page = 1
        st.session_state.active_genre_id = None
        st.session_state.active_genre_name = "All"
        if st.session_state.view != "home":
            goto_home()
        else:
            st.rerun()

with nc_search:
    st.markdown('<span class="nm-nav-search"></span>', unsafe_allow_html=True)
    typed = st.text_input(
        "Search",
        placeholder="🔍  Search movies, shows, titles…",
        label_visibility="collapsed",
        key="top_search",
    )
    if typed and typed.strip() and st.session_state.view != "home":
        st.session_state.view = "home"
        st.session_state.selected_tmdb_id = None
        st.query_params["view"] = "home"
        st.query_params.pop("id", None)
        st.rerun()

with nc_wl:
    st.markdown('<span class="nm-nav-wl"></span>', unsafe_allow_html=True)
    wl_count = len(st.session_state.watchlist)
    wl_label = f"🔖 Watchlist ({wl_count})" if wl_count else "🔖 Watchlist"
    if st.button(wl_label, key="nav_wl"):
        goto_watchlist()

with nc_home:
    st.markdown('<span class="nm-nav-home"></span>', unsafe_allow_html=True)
    if st.button("Home", key="nav_home"):
        st.session_state.active_genre_id = None
        st.session_state.active_genre_name = "All"
        goto_home()

# ==============================
# VIEW: HOME
# ==============================
if st.session_state.view == "home":

    # ── SEARCH ──────────────────────────────────
    if typed and typed.strip():
        st.markdown('<span class="nm-search-active-marker"></span>', unsafe_allow_html=True)
        q = typed.strip()
        st.markdown('<div class="nm-page-pad">', unsafe_allow_html=True)
        if len(q) < 2:
            st.caption("Type at least 2 characters to search.")
        else:
            with st.spinner(f'Searching for "{q}"…'):
                data, err = api_get("/tmdb/search", {"query": q})
            if err or data is None:
                st.error("Search failed. Please try again.")
            else:
                suggestions, cards = parse_search_results(data, q, limit=28)
                if suggestions:
                    labels   = ["— Select a title —"] + [s[0] for s in suggestions]
                    picked   = st.selectbox("Suggestions", labels, index=0, label_visibility="collapsed")
                    if picked != "— Select a title —":
                        lmap = {s[0]: s[1] for s in suggestions}
                        goto_details(lmap[picked])

                if cards:
                    st.markdown(f'<div class="section-title">Results for "{q.title()}"</div>', unsafe_allow_html=True)
                    poster_grid(cards, cols=GRID_COLS, key_prefix="search")
                else:
                    st.markdown('<div class="empty-state">No results found. Try a different keyword.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

    # ── HERO + MAIN FEED ────────────────────────
    hero_ph    = st.empty()
    filter_ph  = st.empty()
    title_ph   = st.empty()
    grid_ph    = st.empty()
    more_ph    = st.empty()

    with grid_ph.container():
        st.markdown('<div class="nm-page-pad">', unsafe_allow_html=True)
        render_skeleton_grid(cols=GRID_COLS, rows=2)
        st.markdown('</div>', unsafe_allow_html=True)

    # Fetch movies (genre filter takes precedence)
    if st.session_state.active_genre_id is not None:
        home_data, err = api_get(
            "/home/genre",
            {
                "genre_id": st.session_state.active_genre_id,
                "page": st.session_state.home_page,
                "limit": 28,
            },
        )
    else:
        home_data, err = api_get(
            "/home",
            {
                "category": st.session_state.home_category,
                "page": st.session_state.home_page,
                "limit": 28,
            },
        )

    grid_ph.empty()

    if err or not home_data:
        st.markdown('<div class="nm-page-pad">', unsafe_allow_html=True)
        st.error("Couldn't load the home feed. Please refresh.")
        with st.expander("Technical details"):
            st.code(err or "Unknown error")
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

    # Support both old (List) and new (HomePageResponse dict) format
    if isinstance(home_data, list):
        movies = home_data
        total_pages = 1
        cur_page    = 1
    else:
        movies      = home_data.get("movies") or []
        total_pages = home_data.get("total_pages", 1)
        cur_page    = home_data.get("current_page", 1)

    # Hero (only page 1 + no genre filter)
    if st.session_state.home_page == 1 and st.session_state.active_genre_id is None:
        with hero_ph.container():
            render_hero(movies)
    else:
        hero_ph.empty()

    # Genre filter bar
    with filter_ph.container():
        st.markdown('<div class="nm-page-pad">', unsafe_allow_html=True)
        render_genre_filters()
        st.markdown('</div>', unsafe_allow_html=True)

    # Section title
    cat_display = st.session_state.active_genre_name if st.session_state.active_genre_id else \
                  st.session_state.home_category.replace("_", " ").title()
    title_ph.markdown(f'<div class="nm-page-pad"><div class="section-title">{cat_display} Movies</div></div>', unsafe_allow_html=True)

    # Grid
    with grid_ph.container():
        st.markdown('<div class="nm-page-pad">', unsafe_allow_html=True)
        poster_grid(movies, cols=GRID_COLS, key_prefix="home_feed")
        st.markdown('</div>', unsafe_allow_html=True)

    # Pagination (numbered page switcher: « 1 2 3 … »)
    with more_ph.container():
        st.markdown('<div class="nm-page-pad">', unsafe_allow_html=True)
        if total_pages > 1:
            st.markdown('<div class="nm-pg-wrap">', unsafe_allow_html=True)
            pg_key = f"home_{st.session_state.active_genre_id}_{st.session_state.home_category}"
            render_pagination(cur_page, total_pages, key_prefix=pg_key)
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# VIEW: DETAILS
# ==============================
elif st.session_state.view == "details":
    st.markdown('<span class="nm-det-nav-marker"></span>', unsafe_allow_html=True)
    tmdb_id = st.session_state.selected_tmdb_id
    if not tmdb_id:
        goto_home()
        st.stop()

    with st.spinner("Loading…"):
        data, err = api_get_cached(f"/movie/id/{tmdb_id}")
    if err or not data:
        st.error("Couldn't load this title's details.")
        with st.expander("Technical details"):
            st.code(err or "Unknown error")
        if st.button("← Back to Home"):
            goto_home()
        st.stop()

    # Enrich missing fields (vote_average, original_language, runtime, etc.)
    data = enrich_movie_details(data, tmdb_id)

    # ── BACKDROP ────────────────────────────────
    backdrop = get_img_url(data.get("backdrop_url") or data.get("backdrop_path"), is_backdrop=True)
    if not backdrop:
        backdrop = PLACEHOLDER_BACKDROP

    st.markdown(
        f'<style>.det-bg{{position:fixed;top:0;left:0;width:100%;height:100vh;'
        f'background-image:url(\'{backdrop}\');background-size:cover;background-position:center 20%;'
        f'opacity:0.10;z-index:-10;pointer-events:none;}}</style>'
        f'<div class="det-bg"></div>',
        unsafe_allow_html=True,
    )

    # ── BACK + WATCHLIST ────────────────────────
    bc1, bc2, bc3 = st.columns([1.5, 3.5, 1.5], gap="small")
    with bc1:
        st.markdown('<span class="nm-det-btn-row-marker"></span>', unsafe_allow_html=True)
        if st.button("← Back", key="back_btn"):
            goto_home()
    with bc3:
        title_raw = capitalize_title(data.get("title", ""))
        poster_url = get_img_url(data.get("poster_url") or data.get("poster_path"))
        wl_text = "✓ In List" if in_watchlist(tmdb_id) else "+ My List"
        if st.button(wl_text, key="det_wl_btn"):
            toggle_watchlist(tmdb_id, title_raw, poster_url, data.get("vote_average"))
            st.rerun()

    # ── POSTER + INFO ───────────────────────────
    left, right = st.columns([1, 2.8], gap="large")

    with left:
        if poster_url:
            st.markdown(
                f'<img src="{poster_url}" style="width:100%;border-radius:12px;'
                f'box-shadow:0 15px 40px rgba(0,0,0,0.7);border:0.5px solid rgba(255,255,255,0.06);" '
                f'onerror="this.onerror=null;this.src=\'{PLACEHOLDER_POSTER}\';">',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(f'<img src="{PLACEHOLDER_POSTER}" style="width:100%;border-radius:12px;">', unsafe_allow_html=True)

    with right:
        tagline  = capitalize_sentences(data.get("tagline") or "")
        overview = capitalize_sentences(data.get("overview") or "No overview available.")
        genres_data = data.get("genres") or []
        genres = [g["name"] for g in genres_data if isinstance(g, dict)]
        release  = data.get("release_date") or "N/A"
        runtime  = format_runtime(data.get("runtime"))
        rating   = format_rating(data.get("vote_average"))
        lang     = format_language(data.get("original_language"))
        budget   = data.get("budget")
        revenue  = data.get("revenue")

        rating_html = (
            f'<span style="color:#FF5C5C;">'
            f'<svg style="width:14px;height:14px;fill:#FF5C5C;vertical-align:middle;margin-bottom:2px;" viewBox="0 0 24 24">'
            f'<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>'
            f' {rating}</span>'
            if rating and rating != "NR" else ("Not Rated" if rating == "NR" else "Not Rated")
        )

        st.markdown(f'<div class="det-title">{title_raw}</div>', unsafe_allow_html=True)
        if tagline:
            st.markdown(f'<div class="det-tagline">"{tagline}"</div>', unsafe_allow_html=True)

        # Meta chips
        chips_html = '<div class="meta-chips">'
        chips_html += f'<div class="meta-chip"><div class="meta-chip-label">Release</div><div class="meta-chip-value">{release}</div></div>'
        chips_html += f'<div class="meta-chip"><div class="meta-chip-label">Rating</div><div class="meta-chip-value">{rating_html}</div></div>'
        chips_html += f'<div class="meta-chip"><div class="meta-chip-label">Language</div><div class="meta-chip-value">{lang}</div></div>'
        if runtime:
            chips_html += f'<div class="meta-chip"><div class="meta-chip-label">Runtime</div><div class="meta-chip-value">{runtime}</div></div>'
        if budget and budget > 0:
            chips_html += f'<div class="meta-chip"><div class="meta-chip-label">Budget</div><div class="meta-chip-value">${budget:,}</div></div>'
        if revenue and revenue > 0:
            chips_html += f'<div class="meta-chip"><div class="meta-chip-label">Revenue</div><div class="meta-chip-value">${revenue:,}</div></div>'
        chips_html += "</div>"
        st.markdown(chips_html, unsafe_allow_html=True)

        # Genre pills
        if genres:
            pills = "".join(
                f'<span style="display:inline-block;background:rgba(255,255,255,0.05);'
                f'border:0.5px solid rgba(255,255,255,0.1);border-radius:20px;'
                f'padding:3px 12px;font-size:0.78rem;font-weight:600;color:rgba(255,255,255,0.7);margin:0 5px 5px 0;">{g}</span>'
                for g in genres
            )
            st.markdown(f'<div style="margin:4px 0 16px;">{pills}</div>', unsafe_allow_html=True)

        st.markdown(f'<div class="det-overview">{overview}</div>', unsafe_allow_html=True)

        st.write("")

    # ── CAST ────────────────────────────────────
    render_cast(tmdb_id)

    # ── RECOMMENDATIONS ─────────────────────────
    st.markdown('<hr class="nm-divider">', unsafe_allow_html=True)

    rec_ph = st.empty()
    with rec_ph.container():
        st.markdown('<div class="section-title">Similar Movies</div>', unsafe_allow_html=True)
        render_skeleton_grid(cols=GRID_COLS, rows=1)

    # Use new /recommend/similar/{id} endpoint first, fall back to /movie/search
    bundle, err2 = api_get(
        f"/recommend/similar/{tmdb_id}",
        {"tfidf_top_n": 14, "genre_limit": 14},
    )

    # Fallback to /movie/search if the new endpoint isn't deployed yet
    if err2 or not bundle:
        bundle, err2 = api_get(
            "/movie/search",
            {"query": data.get("title", ""), "tfidf_top_n": 14, "genre_limit": 14},
        )

    rec_ph.empty()

    if not err2 and bundle:
        tfidf_cards = tfidf_to_cards(bundle.get("tfidf_recommendations") or [])
        genre_cards = [to_card(c) for c in (bundle.get("genre_recommendations") or [])]

        if tfidf_cards:
            st.markdown('<div class="section-title">Similar Movies</div>', unsafe_allow_html=True)
            poster_grid(tfidf_cards, cols=GRID_COLS, key_prefix="det_tfidf")

        if genre_cards:
            st.markdown('<hr class="nm-divider"><div class="section-title">More Like This</div>', unsafe_allow_html=True)
            poster_grid(genre_cards, cols=GRID_COLS, key_prefix="det_genre")

    else:
        # Last resort: genre-only fallback
        genre_only, _ = api_get("/recommend/genre", {"tmdb_id": tmdb_id, "limit": 21})
        if genre_only:
            st.markdown('<div class="section-title">More Like This</div>', unsafe_allow_html=True)
            poster_grid([to_card(c) for c in genre_only], cols=GRID_COLS, key_prefix="det_genre_fb")
        else:
            st.markdown('<div class="empty-state">No recommendations available right now.</div>', unsafe_allow_html=True)

# ==============================
# VIEW: WATCHLIST (full screen)
# ==============================
elif st.session_state.view == "watchlist":
    st.markdown('<span class="nm-wl-nav-marker"></span>', unsafe_allow_html=True)

    bc1, bc2 = st.columns([1, 8], gap="small")
    with bc1:
        st.markdown('<span class="nm-wl-btn-row-marker"></span>', unsafe_allow_html=True)
        if st.button("← Back", key="wl_back_btn"):
            goto_home()

    st.markdown(
        f'<div class="section-title">My Watchlist ({len(st.session_state.watchlist)})</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.watchlist:
        st.markdown(
            '<div class="empty-state">'
            '<div style="font-size:2.2rem;margin-bottom:10px;">🔖</div>'
            '<div style="font-size:1rem;font-weight:700;color:rgba(255,255,255,0.55);margin-bottom:6px;">Your watchlist is empty</div>'
            '<div style="font-size:0.85rem;color:rgba(255,255,255,0.3);">Tap <b>+ Watchlist</b> on any movie to save it here.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        wl_cards = [
            {
                "tmdb_id": tid,
                "title": info.get("title", ""),
                "poster_url": info.get("poster_url", ""),
                "vote_average": info.get("vote_average"),
            }
            for tid, info in st.session_state.watchlist.items()
        ]
        poster_grid(wl_cards, cols=GRID_COLS, key_prefix="wl_full")

else:
    st.session_state.view = "home"
    st.rerun()