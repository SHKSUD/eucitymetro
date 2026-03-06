import os
import csv
import json
import re
import random
from datetime import datetime
from collections import defaultdict

# ============================================================
# STATIONSTEPS GENERATOR v8.0
# Changes from v7.0:
#   - Affiliate monetisation layer (LuggageHero + Booking.com)
#   - Affiliate disclosure banner (legal requirement)
#   - Scroll-triggered sticky CTA bar (mobile-first)
#   - TouristAttraction schema on landmark pages
#   - Deterministic title generation (no more random.choice)
#   - Richer meta descriptions
#   - Deterministic neighbour links (alphabetical)
#   - Airalo eSIM block on city hub pages
#   - Luggage storage section on landmark pages
#   - Stay Nearby (Booking.com) section on landmark pages
#   - Affiliate Disclosure page auto-generated
#   - Sitemap with priority scores
# ============================================================

# --- 1. CONFIGURATION ---
OUTPUT_BASE = 'production_build'
CSV_FILE = 'Final_Master_Silo_with_Schemas.csv'
SITE_URL = "https://stationsteps.com"
VERIFIED_TS = f"Verified {datetime.now().strftime('%B %Y')}"

# ============================================================
# AFFILIATE CONFIGURATION
# Replace placeholder URLs with your actual affiliate links.
#
# LuggageHero:
#   Sign up: https://luggagehero.com/affiliate
#   Programme: In-house. ~$2–5 per booking. Approval ~48h.
#   Your link format will be: https://luggagehero.com?ref=YOURCODE
#
# Booking.com:
#   Sign up: https://join.booking.com
#   Programme: In-house. 25–40% commission on Booking's cut.
#   Your link format will be: https://www.booking.com/index.html?aid=YOURAID
#   For city-specific searches: add &ss=CITYNAME to the base URL
# ============================================================

LUGGAGEHERO_URL   = "https://luggagehero.com?ref=YOUR_AFFILIATE_CODE"
LUGGAGEHERO_CITY_URL = "https://luggagehero.com/luggage-storage/{city_slug}?ref=YOUR_AFFILIATE_CODE"
# ^ This URL pattern works for LuggageHero city pages — replace {city_slug} is handled in code

BOOKING_BASE_URL  = "https://www.booking.com/searchresults.html?aid=YOUR_AID_NUMBER&ss={city_name}&label=stationsteps"
# ^ Booking.com deep links to city search. YOUR_AID_NUMBER is your affiliate ID from join.booking.com

# ============================================================


# --- 2. TEMPLATES ---

# ── SHARED SNIPPETS ──────────────────────────────────────────

# Affiliate disclosure banner — sits below the top verified bar.
# One line. Links to the generated /affiliate-disclosure.html page.
DISCLOSURE_BANNER = """
    <div class="bg-slate-100 border-b border-slate-200 py-1.5 px-4 text-center">
        <p class="text-[9px] text-slate-400 uppercase tracking-widest font-bold">
            Some links on this page are affiliate links. 
            <a href="../../affiliate-disclosure.html" class="underline hover:text-blue-600 transition">Learn more</a>
        </p>
    </div>"""

# Disclosure banner variant for city hub pages (one level up)
DISCLOSURE_BANNER_CITY = """
    <div class="bg-slate-100 border-b border-slate-200 py-1.5 px-4 text-center">
        <p class="text-[9px] text-slate-400 uppercase tracking-widest font-bold">
            Some links on this page are affiliate links. 
            <a href="../../affiliate-disclosure.html" class="underline hover:text-blue-600 transition">Learn more</a>
        </p>
    </div>"""

# Scroll-triggered sticky bar (landmark pages)
# Appears when user scrolls down 300px. Dismissible with X button.
# gtag click tracking on the primary CTA.
def get_sticky_bar(station, city, city_slug):
    lh_city_url = LUGGAGEHERO_CITY_URL.replace("{city_slug}", city_slug)
    return f"""
    <!-- STICKY BAR: appears on scroll -->
    <div id="sticky-bar" class="fixed bottom-0 left-0 right-0 z-50 transform translate-y-full transition-transform duration-300 ease-in-out">
        <div class="bg-slate-900 border-t-2 border-blue-500 px-4 py-3 shadow-2xl">
            <div class="max-w-2xl mx-auto flex items-center justify-between gap-3">
                <div class="flex-shrink-0">
                    <p class="text-[9px] font-bold text-slate-500 uppercase tracking-widest">Near {station}</p>
                    <p class="text-xs font-black text-white">Store Your Bags</p>
                </div>
                <a href="{lh_city_url}" 
                   target="_blank" rel="noopener sponsored"
                   onclick="gtag && gtag('event','affiliate_click',{{affiliate:'luggagehero',placement:'sticky_bar',city:'{city}',station:'{station}'}});"
                   class="flex-shrink-0 bg-blue-600 hover:bg-blue-500 text-white text-[11px] font-black uppercase tracking-widest px-5 py-2.5 rounded-xl transition-colors whitespace-nowrap">
                    <i class="fas fa-suitcase-rolling mr-1.5"></i> Find Storage
                </a>
                <button id="sticky-close" 
                        onclick="document.getElementById('sticky-bar').classList.add('translate-y-full'); gtag && gtag('event','sticky_bar_dismissed',{{city:'{city}'}});"
                        class="flex-shrink-0 text-slate-500 hover:text-white transition-colors p-1">
                    <i class="fas fa-times text-xs"></i>
                </button>
            </div>
        </div>
    </div>
    <script>
        (function() {{
            var bar = document.getElementById('sticky-bar');
            var dismissed = false;
            window.addEventListener('scroll', function() {{
                if (dismissed) return;
                if (window.scrollY > 300) {{
                    bar.classList.remove('translate-y-full');
                }} else {{
                    bar.classList.add('translate-y-full');
                }}
            }}, {{ passive: true }});
            document.getElementById('sticky-close').addEventListener('click', function() {{
                dismissed = true;
            }});
        }})();
    </script>"""


# Luggage storage section — placed after the exit command card, before FAQ.
def get_luggage_section(station, city, city_slug):
    lh_city_url = LUGGAGEHERO_CITY_URL.replace("{city_slug}", city_slug)
    return f"""
        <!-- LUGGAGE STORAGE: LuggageHero affiliate -->
        <section class="mb-10">
            <div class="bg-slate-900 rounded-[1.5rem] overflow-hidden border border-slate-800">
                <div class="p-6">
                    <div class="flex items-start justify-between gap-4">
                        <div class="flex-grow">
                            <div class="flex items-center gap-2 mb-2">
                                <i class="fas fa-suitcase-rolling text-blue-400 text-sm"></i>
                                <span class="text-[10px] font-black uppercase tracking-widest text-slate-400">Logistics: Bag Storage</span>
                            </div>
                            <h3 class="text-white font-black text-lg leading-tight mb-1">Store bags near {station}</h3>
                            <p class="text-slate-400 text-xs leading-relaxed">Verified storage locations within walking distance. From ~€5/day. Book ahead for guaranteed space.</p>
                        </div>
                        <div class="flex-shrink-0 bg-blue-600/20 border border-blue-500/30 rounded-xl p-3 text-center">
                            <span class="block text-blue-400 font-black text-lg">~€5</span>
                            <span class="text-[9px] text-slate-500 uppercase font-bold">/day</span>
                        </div>
                    </div>
                    <a href="{lh_city_url}" 
                       target="_blank" rel="noopener sponsored"
                       onclick="gtag && gtag('event','affiliate_click',{{affiliate:'luggagehero',placement:'luggage_section',city:'{city}',station:'{station}'}});"
                       class="mt-4 flex items-center justify-between w-full bg-blue-600 hover:bg-blue-500 text-white font-black text-xs uppercase tracking-widest px-5 py-3 rounded-xl transition-colors">
                        <span><i class="fas fa-map-marker-alt mr-2"></i>Find Storage in {city}</span>
                        <i class="fas fa-arrow-right text-blue-200"></i>
                    </a>
                </div>
                <div class="border-t border-slate-800 px-6 py-2.5 flex items-center gap-2">
                    <i class="fas fa-shield-alt text-green-500 text-[10px]"></i>
                    <span class="text-[9px] text-slate-500 uppercase tracking-widest font-bold">Insured storage • Verified by StationSteps</span>
                </div>
            </div>
        </section>"""


# Stay Nearby section — placed after FAQ, before footer.
def get_hotels_section(city, city_slug):
    booking_url = BOOKING_BASE_URL.replace("{city_name}", city).replace("{city_slug}", city_slug)
    return f"""
        <!-- STAY NEARBY: Booking.com affiliate -->
        <section class="mb-12">
            <div class="bg-white rounded-[1.5rem] border border-slate-200 overflow-hidden shadow-sm">
                <div class="bg-slate-50 border-b border-slate-200 px-6 py-4 flex items-center justify-between">
                    <div>
                        <span class="text-[10px] font-black uppercase tracking-widest text-slate-400">Logistics: Accommodation</span>
                        <h3 class="font-black text-slate-900 text-base mt-0.5">Stay Near {city} Stations</h3>
                    </div>
                    <i class="fas fa-moon text-blue-600 text-lg"></i>
                </div>
                <div class="p-6">
                    <p class="text-xs text-slate-500 mb-5 leading-relaxed">Hotels within direct transit access of the landmarks in this guide. Prices and availability via Booking.com.</p>
                    <a href="{booking_url}" 
                       target="_blank" rel="noopener sponsored"
                       onclick="gtag && gtag('event','affiliate_click',{{affiliate:'booking_com',placement:'stay_nearby',city:'{city}'}});"
                       class="flex items-center justify-between w-full bg-slate-900 hover:bg-slate-800 text-white font-black text-xs uppercase tracking-widest px-5 py-3.5 rounded-xl transition-colors">
                        <span><i class="fas fa-search mr-2 text-blue-400"></i>Search Hotels in {city}</span>
                        <i class="fas fa-external-link-alt text-slate-400 text-[10px]"></i>
                    </a>
                    <p class="text-[9px] text-slate-300 text-center mt-3 uppercase tracking-widest">Via Booking.com · Affiliate link</p>
                </div>
            </div>
        </section>"""


# Airalo eSIM block — used on city hub index pages
def get_airalo_block_city(city, country):
    # Airalo: sign up at https://www.airalo.com/affiliate-program (via Impact Radius)
    # ~$3-6 per eSIM sale. Replace URL below with your Impact Radius tracking link.
    airalo_url = "https://www.airalo.com?ref=YOUR_AIRALO_REFERRAL_CODE"
    return f"""
        <!-- AIRALO eSIM: affiliate block for city hub pages -->
        <!-- Sign up: https://www.airalo.com/affiliate-program (via Impact Radius) -->
        <div class="bg-slate-900 rounded-[1.5rem] border border-slate-800 p-6 mb-8">
            <div class="flex items-center gap-4">
                <div class="flex-shrink-0 w-12 h-12 bg-blue-600/20 border border-blue-500/30 rounded-xl flex items-center justify-center">
                    <i class="fas fa-signal text-blue-400 text-lg"></i>
                </div>
                <div class="flex-grow">
                    <span class="text-[9px] font-black uppercase tracking-widest text-slate-500">Travelling to {country}?</span>
                    <h4 class="text-white font-black text-sm leading-tight">Get a local eSIM before you land</h4>
                    <p class="text-slate-400 text-[11px] mt-0.5">Stay connected from the moment you exit. {country} eSIMs from ~$5.</p>
                </div>
            </div>
            <a href="{airalo_url}" 
               target="_blank" rel="noopener sponsored"
               onclick="gtag && gtag('event','affiliate_click',{{affiliate:'airalo',placement:'city_hub',city:'{city}',country:'{country}'}});"
               class="mt-4 block w-full text-center bg-blue-600 hover:bg-blue-500 text-white font-black text-xs uppercase tracking-widest px-5 py-3 rounded-xl transition-colors">
                <i class="fas fa-sim-card mr-2"></i>Browse {country} eSIMs on Airalo
            </a>
        </div>"""


# TouristAttraction schema block — injected alongside existing FAQPage schema
def get_tourist_attraction_schema(row):
    landmark = row.get('landmark', '')
    city = row.get('city', '')
    country = row.get('country', '')
    station = row.get('station', '')
    schema = {
        "@context": "https://schema.org",
        "@type": "TouristAttraction",
        "name": landmark,
        "description": f"Verified station exit directions and logistics guide for {landmark}, {city}. Nearest station: {station}.",
        "address": {
            "@type": "PostalAddress",
            "addressLocality": city,
            "addressCountry": country
        },
        "touristType": "Transit logistics, accessibility, last-mile navigation"
    }
    return f'<script type="application/ld+json">\n{json.dumps(schema, indent=2)}\n</script>'


# --- DETERMINISTIC TITLE LOGIC ---
# Replaces random.choice() from v7.0.
# Rules: step-free terrain → "Step-Free Guide", short walk (≤3min) → "Fastest Exit",
#        long walk (>10min) → "Full Logistics Guide", default → "Verified Guide"
def get_deterministic_title(landmark, city, row):
    terrain = row.get('terrain_en', '').lower()
    try:
        walk = float(re.sub(r'[^\d.]', '', str(row.get('walk_time', '5'))))
    except:
        walk = 5.0
    if '0hz' in terrain or 'step-free' in terrain or 'level' in terrain:
        prefix = "Step-Free Guide"
    elif walk <= 3:
        prefix = "Fastest Exit"
    elif walk >= 10:
        prefix = "Full Logistics Guide"
    else:
        prefix = "Verified Exit Guide"
    return f"{landmark} {prefix} from {city} Station | StationSteps"


# --- RICHER META DESCRIPTION ---
def get_meta_desc(row):
    landmark = row.get('landmark', '')
    station = row.get('station', '')
    walk = row.get('walk_time', '')
    tip = row.get('expert_tip_en', '')
    # Use first 100 chars of expert tip if available, else fallback
    tip_snippet = tip[:90].rstrip(',. ') + '.' if tip else ''
    base = f"Exit {station} station and reach {landmark} in {walk} minutes."
    if tip_snippet:
        return f"{base} {tip_snippet}"
    return f"{base} Verified exit commands, step-free routes & bag storage for {landmark}."


# [A] LANDMARK TEMPLATE
LANDMARK_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title_tag}</title>
    <meta name="description" content="{meta_desc}">
    <meta property="og:title" content="{title_tag}">
    <meta property="og:description" content="{meta_desc}">
    <meta name="twitter:card" content="summary_large_image">
    {hreflang_tags}
    <link rel="canonical" href="{canonical_url}">
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    {schema_block}
    {tourist_attraction_schema}
    {breadcrumb_schema}
</head>
<body class="bg-slate-50 text-slate-900 font-sans pb-28">

    <!-- VERIFIED BAR -->
    <div class="bg-blue-600 text-white py-2 px-4 text-center">
        <p class="text-[10px] font-black uppercase tracking-widest">{verified_ts} • Official Logistics Protocol</p>
    </div>

    <!-- AFFILIATE DISCLOSURE BANNER -->
{disclosure_banner}

    <!-- NAVIGATION -->
    <nav class="bg-white border-b border-slate-200 px-4 py-4 sticky top-0 z-50 shadow-sm">
        <div class="max-w-2xl mx-auto flex justify-between items-center text-[10px] font-bold uppercase tracking-widest text-slate-400">
            <div class="flex items-center gap-2">
                <a href="../../index.html" class="hover:text-blue-600 transition">STATIONSTEPS</a> 
                <span>/</span> 
                <a href="index.html" class="hover:text-blue-600 transition">{city}</a>
            </div>
            <span class="text-blue-600">LIVE FEED</span>
        </div>
    </nav>

    <main class="max-w-2xl mx-auto px-4 py-10">

        <!-- HERO HEADER -->
        <header class="mb-10 text-center">
            <h1 class="text-5xl font-black tracking-tighter italic mb-4 text-slate-900 leading-[0.9]">
                {landmark}<br><span class="text-blue-600 uppercase text-3xl not-italic tracking-normal">Logistics Guide</span>
            </h1>
            <div class="flex justify-center gap-2 mt-6">
                {hz_badge}
                {db_badge}
                <div class="bg-green-50 text-green-700 px-3 py-1 rounded-md border border-green-100 font-bold text-[10px] flex items-center gap-2">
                    <i class="fas fa-check-circle"></i> VERIFIED
                </div>
            </div>
        </header>

        <!-- EXIT COMMAND CARD -->
        <section class="bg-white rounded-[2rem] shadow-2xl border border-slate-100 overflow-hidden mb-8">
            <div class="bg-slate-900 p-8 text-white relative">
                <div class="flex items-center justify-between relative z-10">
                    <div class="text-center">
                        <p class="text-[10px] font-bold text-slate-500 uppercase mb-2">Platform</p>
                        <span class="text-sm font-black">{station}</span>
                    </div>
                    <div class="flex-grow flex flex-col items-center px-4">
                        <span class="text-[10px] font-mono text-blue-400 mb-1">{walk_time} MIN</span>
                        <div class="w-full h-px bg-slate-700 relative">
                            <div class="absolute top-1/2 left-1/2 -translate-y-1/2 -translate-x-1/2 w-2 h-2 bg-blue-500 rounded-full shadow-[0_0_10px_#3b82f6]"></div>
                        </div>
                    </div>
                    <div class="text-center">
                        <p class="text-[10px] font-bold text-slate-500 uppercase mb-2">Exit Goal</p>
                        <span class="text-sm font-black">{landmark}</span>
                    </div>
                </div>
            </div>
            <div class="p-8 text-center border-b border-slate-100">
                <h2 class="text-[10px] font-black uppercase text-slate-400 tracking-[0.3em] mb-4">Immediate Exit Command</h2>
                <p class="text-3xl font-black italic text-slate-800 leading-tight">"{exit_command}"</p>
            </div>
            <div class="p-8 bg-slate-50 italic text-slate-600 text-sm leading-relaxed">
                <i class="fas fa-lightbulb text-amber-500 mr-2"></i> "{expert_tip}"
            </div>
        </section>

        <!-- LUGGAGE STORAGE (LUGGAGEHERO AFFILIATE) -->
{luggage_section}

        <!-- FAQ / LOGISTICS INTELLIGENCE -->
        <section class="mb-8">
            <h3 class="text-xs font-black uppercase tracking-widest text-slate-400 mb-6">Logistics Intelligence</h3>
            <div class="space-y-3">{faq_html}</div>
            
            <a href="index.html" class="block w-full text-center py-4 mt-8 border-2 border-dashed border-slate-200 rounded-2xl text-[10px] font-black uppercase tracking-widest text-slate-400 hover:border-blue-600 hover:text-blue-600 hover:bg-blue-50 transition-all">
                <i class="fas fa-city mr-2"></i> View All {city} Station Exits
            </a>
        </section>

        <!-- STAY NEARBY (BOOKING.COM AFFILIATE) -->
{hotels_section}

        <!-- FOOTER -->
        <footer class="text-center pt-12 border-t border-slate-200">
            <h4 class="text-[10px] font-black uppercase text-slate-300 mb-6">Nearby Stations</h4>
            <div class="flex flex-wrap justify-center gap-3">{neighbor_links}</div>
            <div class="mt-12 flex justify-center gap-6 text-[10px] font-bold text-slate-300 uppercase tracking-widest">
                <a href="../../index.html">Directory</a> • <a href="../../privacy.html">Privacy</a> • <a href="../../terms.html">Terms</a> • <a href="../../affiliate-disclosure.html">Affiliates</a>
            </div>
        </footer>
    </main>

    <!-- SCROLL-TRIGGERED STICKY BAR -->
{sticky_bar}

</body>
</html>"""


# [B] CITY HUB TEMPLATE
CITY_HUB_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{city} Station Exits & Transit Guide | StationSteps</title>
    <meta name="description" content="Verified exit commands and last-mile logistics for {count} landmarks in {city}. Step-free routes, bag storage & hotel recommendations.">
    <link rel="canonical" href="{site_url}/en/{city_slug}/index.html">
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-slate-50 text-slate-900">

    <!-- VERIFIED BAR -->
    <div class="bg-blue-600 text-white py-2 px-4 text-center">
        <p class="text-[10px] font-black uppercase tracking-widest">{verified_ts} • Official Logistics Protocol</p>
    </div>

    <!-- AFFILIATE DISCLOSURE -->
    <div class="bg-slate-100 border-b border-slate-200 py-1.5 px-4 text-center">
        <p class="text-[9px] text-slate-400 uppercase tracking-widest font-bold">
            Some links on this page are affiliate links. 
            <a href="../../affiliate-disclosure.html" class="underline hover:text-blue-600 transition">Learn more</a>
        </p>
    </div>

    <nav class="bg-white border-b border-slate-200 px-6 py-4 sticky top-0 z-50">
        <div class="max-w-4xl mx-auto flex justify-between items-center">
            <a href="../../index.html" class="font-black text-xl tracking-tighter text-slate-900 uppercase italic">STATION<span class="text-blue-600">STEPS</span></a>
            <span class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">{country}</span>
        </div>
    </nav>

    <header class="bg-slate-900 text-white py-16 px-6 relative overflow-hidden">
        <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 via-cyan-400 to-blue-500"></div>
        <div class="max-w-4xl mx-auto relative z-10">
            <h1 class="text-5xl md:text-7xl font-black italic tracking-tighter mb-4">{city}</h1>
            <div class="flex gap-8">
                <div><span class="block text-2xl font-black text-blue-400">{count}</span><span class="text-[10px] font-bold uppercase text-slate-500">Landmarks</span></div>
                <div><span class="block text-2xl font-black text-blue-400">~{avg_walk}m</span><span class="text-[10px] font-bold uppercase text-slate-500">Avg Walk</span></div>
            </div>
        </div>
    </header>

    <main class="max-w-4xl mx-auto px-6 py-12">

        <!-- AIRALO eSIM BLOCK -->
        <!-- NOTE: Airalo not yet activated in this build. To activate: -->
        <!-- 1. Sign up at https://www.airalo.com/affiliate-program (via Impact Radius) -->
        <!-- 2. Replace YOUR_AIRALO_REFERRAL_CODE in the CONFIGURATION section above -->
        <!-- 3. Uncomment the airalo_block placeholder below by switching to True in build_site() -->
{airalo_block}

        <!-- LANDMARK GRID -->
        <div class="grid md:grid-cols-2 gap-4">
            {landmark_cards}
        </div>

    </main>

    <footer class="bg-white border-t border-slate-200 py-12 text-center">
        <div class="flex justify-center gap-6 text-[10px] font-black text-slate-400 uppercase tracking-widest">
            <a href="../../index.html">Home</a> • <a href="../../privacy.html">Privacy</a> • <a href="../../terms.html">Terms</a> • <a href="../../affiliate-disclosure.html">Affiliates</a>
        </div>
    </footer>
</body>
</html>"""


# [C] HOMEPAGE TEMPLATE
HOMEPAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StationSteps | The Global Last-Mile Transit Guide</title>
    <meta name="description" content="Verified station exit commands and logistics for the world's most iconic landmarks. Step-free routes, bag storage and hotel guides.">
    <link rel="canonical" href="https://stationsteps.com/">
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
        body {{ font-family: 'Inter', sans-serif; }}
        .hero-pattern {{ background-color: #0f172a; background-image: radial-gradient(#1e293b 1px, transparent 1px); background-size: 24px 24px; }}
    </style>
</head>
<body class="bg-slate-50 text-slate-900 selection:bg-blue-200">
    <nav class="fixed top-0 w-full bg-slate-900/90 backdrop-blur-md border-b border-slate-800 z-50">
        <div class="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
            <a href="#" class="text-xl font-black italic tracking-tighter text-white">
                STATION<span class="text-blue-500">STEPS</span>
            </a>
            <div class="hidden md:flex gap-6 text-xs font-bold uppercase tracking-widest text-slate-400">
                <a href="#cities" class="hover:text-white transition-colors">Cities</a>
                <a href="#" class="text-blue-500">2026 Edition</a>
            </div>
        </div>
    </nav>

    <header class="hero-pattern text-white pt-40 pb-32 px-6 relative overflow-hidden">
        <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-600 via-cyan-400 to-blue-600"></div>
        <div class="max-w-4xl mx-auto text-center relative z-10">
            <div class="inline-flex items-center gap-2 bg-slate-800/50 border border-slate-700 rounded-full px-3 py-1 mb-8">
                <span class="flex h-2 w-2 relative">
                    <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                    <span class="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                </span>
                <span class="text-[10px] font-bold uppercase tracking-widest text-blue-200">System Verified • {date_str}</span>
            </div>
            <h1 class="text-6xl md:text-8xl font-black italic tracking-tighter mb-6 leading-[0.9]">
                MASTER THE <br><span class="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-300">LAST MILE.</span>
            </h1>
            <p class="text-slate-400 text-lg md:text-xl font-medium max-w-2xl mx-auto mb-10 leading-relaxed">
                Verified exit commands, step-free routes, and luggage logistics for the world's most complex transit hubs.
            </p>
        </div>
    </header>

    <section id="cities" class="py-24 px-6 bg-slate-50">
        <div class="max-w-6xl mx-auto">
            <div class="flex items-end justify-between mb-12 border-b border-slate-200 pb-6">
                <div>
                    <h2 class="text-4xl font-black text-slate-900 tracking-tighter mb-2">Global Hubs</h2>
                    <p class="text-sm font-bold text-slate-400 uppercase tracking-widest">Select your destination</p>
                </div>
            </div>
            <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {city_grid}
            </div>
        </div>
    </section>

    <footer class="bg-white border-t border-slate-200 py-12 text-center">
        <p class="text-xs font-bold uppercase tracking-widest text-slate-300 mb-4">© 2026 StationSteps Logistics</p>
        <div class="flex justify-center gap-6 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
            <a href="privacy.html" class="hover:text-blue-600">Privacy Policy</a>
            <a href="terms.html" class="hover:text-blue-600">Terms of Service</a>
            <a href="affiliate-disclosure.html" class="hover:text-blue-600">Affiliate Disclosure</a>
            <a href="sitemap.xml" class="hover:text-blue-600">Sitemap</a>
        </div>
    </footer>
</body>
</html>"""


# [D] LEGAL TEMPLATE
LEGAL_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><title>{title} | StationSteps</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-50 p-8 text-slate-800 font-sans">
    <div class="max-w-3xl mx-auto bg-white p-10 rounded-3xl shadow-sm border border-slate-200">
        <nav class="mb-10"><a href="index.html" class="font-black italic text-slate-400 hover:text-blue-600 tracking-tighter uppercase">← Home</a></nav>
        <h1 class="text-4xl font-black italic uppercase text-slate-900 mb-8 tracking-tighter">{title}</h1>
        <div class="prose prose-slate leading-relaxed text-slate-600">{content}</div>
        <div class="mt-12 pt-8 border-t border-slate-100 text-center"><p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Last Updated: {current_date}</p></div>
    </div>
</body></html>"""


# [E] AFFILIATE DISCLOSURE PAGE CONTENT
AFFILIATE_DISCLOSURE_CONTENT = """
<h2 class="text-xl font-black text-slate-800 mb-4 mt-6">What is an affiliate link?</h2>
<p class="mb-4">Some links on StationSteps are affiliate links. This means if you click a link and make a purchase or booking, StationSteps may earn a small commission — at no extra cost to you. Prices are exactly the same whether you use our link or go directly to the provider.</p>

<h2 class="text-xl font-black text-slate-800 mb-4 mt-6">Which programmes do we participate in?</h2>
<p class="mb-4">StationSteps currently uses affiliate programmes from the following providers:</p>
<ul class="list-disc pl-6 mb-4 space-y-2">
    <li><strong>LuggageHero</strong> — luggage storage booking platform. We link to storage locations near transit stations.</li>
    <li><strong>Booking.com</strong> — hotel search and booking. We link to city hotel search results via the Booking.com Affiliate Partner Programme.</li>
</ul>
<p class="mb-4">We only link to services that are directly relevant to transit travellers using StationSteps. We do not accept payment to feature or promote any specific provider over another.</p>

<h2 class="text-xl font-black text-slate-800 mb-4 mt-6">Does this affect our editorial content?</h2>
<p class="mb-4">No. Our exit commands, terrain data, walk times, and logistics intelligence are independently verified and are not influenced by affiliate relationships. We would link to these services regardless of whether an affiliate programme existed.</p>

<h2 class="text-xl font-black text-slate-800 mb-4 mt-6">Legal basis</h2>
<p class="mb-4">This disclosure is made in accordance with the FTC's guidelines on endorsements and testimonials (USA), the ASA/CAP Code (UK), and the EU Directive on Unfair Commercial Practices. Affiliate links are labelled with <code>rel="sponsored"</code> in the page HTML.</p>

<h2 class="text-xl font-black text-slate-800 mb-4 mt-6">Questions?</h2>
<p>If you have any questions about our affiliate relationships, contact us via the StationSteps privacy page.</p>
"""


# --- 3. HELPER FUNCTIONS ---

def slugify(text):
    if not text: return ""
    return re.sub(r'[^a-z0-9]+', '-', str(text).lower()).strip('-')

def extract_signal(text, pattern, unit):
    match = re.search(pattern, str(text), re.IGNORECASE)
    if match:
        val = match.group(0)
        return f'<div class="bg-slate-900 text-white px-3 py-1 rounded-md border border-slate-700 font-mono text-[10px] flex items-center gap-2"><span>{unit}</span><span class="text-blue-400 font-black">{val}</span></div>'
    return ""

def get_schema_block(row, lang_suffix):
    col_name = f'schema_{lang_suffix}'
    csv_schema = row.get(col_name, "").strip()
    if csv_schema and len(csv_schema) > 20:
        if "<script" not in csv_schema:
            return f'<script type="application/ld+json">\n{csv_schema}\n</script>'
        return csv_schema
    return ""

def get_hreflang(c_slug, l_slug):
    en_url = f"{SITE_URL}/en/{c_slug}/{l_slug}.html"
    return f'<link rel="alternate" hreflang="en" href="{en_url}" />\n    <link rel="alternate" hreflang="x-default" href="{en_url}" />'

def get_breadcrumb_schema(city, city_slug, landmark, landmark_slug):
    schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE_URL}/index.html"},
            {"@type": "ListItem", "position": 2, "name": city, "item": f"{SITE_URL}/en/{city_slug}/index.html"},
            {"@type": "ListItem", "position": 3, "name": landmark, "item": f"{SITE_URL}/en/{city_slug}/{landmark_slug}.html"}
        ]
    }
    return f'<script type="application/ld+json">\n{json.dumps(schema, indent=2)}\n</script>'


# --- 4. MAIN BUILD ENGINE ---

def build_site():
    print("🏭 Initialising StationSteps Generator v8.0...")

    if not os.path.exists(CSV_FILE):
        print(f"❌ Error: {CSV_FILE} not found.")
        return

    with open(CSV_FILE, mode='r', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))

    silos = defaultdict(list)
    for row in rows:
        silos[row['city']].append(row)

    generated_urls = []
    current_date = datetime.now().strftime("%B %Y")

    try:
        # ── 1. LANDMARK PAGES ────────────────────────────────────
        print("... Building Landmark Pages")
        for row in rows:
            landmark, city = row['landmark'], row['city']
            l_slug, c_slug = slugify(landmark), slugify(city)
            country = row.get('country', '')

            hz_badge = extract_signal(row.get('terrain_en', ''), r'\d+Hz', 'VIBE')
            db_badge = extract_signal(row.get('terrain_en', ''), r'\d+dB', 'AUDIO')

            # DETERMINISTIC neighbour links (sorted alphabetically, max 5)
            peers = sorted(
                [x for x in silos[city] if x['landmark'] != landmark],
                key=lambda x: x['landmark']
            )
            n_links = "".join([
                f'<a href="{slugify(n["landmark"])}.html" class="px-4 py-2 bg-white border rounded-xl text-[10px] font-bold text-slate-500 uppercase hover:border-blue-600 transition-all">{n["landmark"]}</a>'
                for n in peers[:5]
            ])

            # FAQ accordions
            faq_html = ""
            for i in range(1, 7):
                q, a = row.get(f'q{i}_en'), row.get(f'a{i}_en')
                if q and a:
                    faq_html += f"""
                    <details class="group bg-white rounded-2xl border border-slate-200 overflow-hidden [&_summary::-webkit-details-marker]:hidden">
                        <summary class="flex items-center justify-between p-5 font-bold text-xs cursor-pointer text-slate-800 focus:outline-none focus:bg-slate-50 transition-colors">
                            <span>{q}</span>
                            <span class="transition duration-300 group-open:-rotate-180 text-blue-500">
                                <i class="fas fa-chevron-down"></i>
                            </span>
                        </summary>
                        <div class="px-5 pb-5 text-xs text-slate-500 leading-relaxed border-t border-slate-100 pt-4 bg-slate-50">
                            {a}
                        </div>
                    </details>"""

            html = LANDMARK_TEMPLATE.format(
                title_tag=get_deterministic_title(landmark, city, row),
                meta_desc=get_meta_desc(row),
                hreflang_tags=get_hreflang(c_slug, l_slug),
                canonical_url=f"{SITE_URL}/en/{c_slug}/{l_slug}.html",
                schema_block=get_schema_block(row, 'en'),
                tourist_attraction_schema=get_tourist_attraction_schema(row),
                breadcrumb_schema=get_breadcrumb_schema(city, c_slug, landmark, l_slug),
                verified_ts=VERIFIED_TS,
                city=city, landmark=landmark,
                hz_badge=hz_badge, db_badge=db_badge,
                station=row['station'], walk_time=row['walk_time'],
                exit_command=row['exit_command_en'],
                expert_tip=row.get('expert_tip_en', ''),
                faq_html=faq_html,
                neighbor_links=n_links,
                disclosure_banner=DISCLOSURE_BANNER,
                luggage_section=get_luggage_section(row['station'], city, c_slug),
                hotels_section=get_hotels_section(city, c_slug),
                sticky_bar=get_sticky_bar(row['station'], city, c_slug),
            )

            out_dir = os.path.join(OUTPUT_BASE, 'en', c_slug)
            os.makedirs(out_dir, exist_ok=True)
            with open(os.path.join(out_dir, f"{l_slug}.html"), 'w', encoding='utf-8') as f_out:
                f_out.write(html)
            generated_urls.append((f"en/{c_slug}/{l_slug}.html", "0.8"))

        # ── 2. CITY HUB PAGES ────────────────────────────────────
        print("... Building City Hub Pages")
        city_cards_html = ""

        for city, city_rows in silos.items():
            c_slug = slugify(city)
            country = city_rows[0].get('country', 'Global')
            count = len(city_rows)
            avg_w = int(sum([float(re.sub(r'[^\d.]', '', str(r.get('walk_time', 0)))) for r in city_rows]) / count)

            # Landmark cards sorted alphabetically
            l_cards = ""
            for r in sorted(city_rows, key=lambda x: x['landmark']):
                l_slug = slugify(r['landmark'])
                l_cards += f"""<a href="{l_slug}.html" class="group bg-white p-6 rounded-3xl border border-slate-200 hover:shadow-xl transition-all">
                    <div class="flex justify-between items-start"><h3 class="font-black text-xl text-slate-800 group-hover:text-blue-600 italic tracking-tighter">{r['landmark']}</h3><i class="fas fa-arrow-right text-slate-300 group-hover:text-blue-600 transition-transform group-hover:translate-x-1"></i></div>
                    <p class="text-[10px] font-bold uppercase text-slate-400 mt-2 tracking-widest"><i class="fas fa-train mr-1"></i> {r.get('station', 'Metro')} · {r.get('walk_time', '?')} min walk</p>
                </a>"""

            # Airalo block — rendered as empty string until you activate it.
            # To activate: replace the empty string with get_airalo_block_city(city, country)
            airalo_block = ""  # ← change to: get_airalo_block_city(city, country)

            hub_html = CITY_HUB_TEMPLATE.format(
                city=city, country=country, count=count, avg_walk=avg_w,
                city_slug=c_slug, site_url=SITE_URL, verified_ts=VERIFIED_TS,
                landmark_cards=l_cards,
                airalo_block=airalo_block,
            )

            with open(os.path.join(OUTPUT_BASE, 'en', c_slug, "index.html"), 'w', encoding='utf-8') as f_hub:
                f_hub.write(hub_html)
            generated_urls.append((f"en/{c_slug}/index.html", "0.9"))

            city_cards_html += f"""
            <a href="en/{c_slug}/index.html" class="group relative bg-white rounded-3xl p-8 border border-slate-200 shadow-sm hover:shadow-2xl transition-all duration-300 overflow-hidden">
                <div class="absolute top-0 right-0 p-6 opacity-10 group-hover:opacity-20 transition-opacity"><i class="fas fa-city text-8xl text-slate-800 transform rotate-12"></i></div>
                <div class="relative z-10">
                    <p class="text-[10px] font-bold uppercase tracking-[0.2em] text-blue-600 mb-2">{country}</p>
                    <h3 class="text-3xl font-black italic text-slate-900 mb-4 group-hover:text-blue-600 transition-colors">{city}</h3>
                    <div class="flex items-center gap-4 text-xs font-bold text-slate-500">
                        <span class="bg-slate-100 px-3 py-1 rounded-full">{count} Landmarks</span>
                        <span>~{avg_w}m Walk</span>
                    </div>
                </div>
            </a>"""

        # ── 3. HOMEPAGE ───────────────────────────────────────────
        print("... Building Homepage")
        final_home = HOMEPAGE_TEMPLATE.format(
            date_str=datetime.now().strftime("%B %Y"),
            city_grid=city_cards_html
        )
        with open(os.path.join(OUTPUT_BASE, "index.html"), 'w', encoding='utf-8') as f_home:
            f_home.write(final_home)
        generated_urls.append(("index.html", "1.0"))

        # ── 4. LEGAL PAGES ────────────────────────────────────────
        print("... Building Legal Pages")
        legal_docs = [
            ("Privacy Policy", "privacy.html",
             "We value your privacy. This site is for informational purposes only. We use cookies for analytics only. We do not sell personal data."),
            ("Terms of Service", "terms.html",
             "By using StationSteps, you agree that transit data may change without notice. Exit commands are provided as guidance only. Always follow on-site signage."),
            ("Affiliate Disclosure", "affiliate-disclosure.html",
             AFFILIATE_DISCLOSURE_CONTENT),
        ]
        for title, fname, content in legal_docs:
            with open(os.path.join(OUTPUT_BASE, fname), 'w', encoding='utf-8') as f_leg:
                f_leg.write(LEGAL_TEMPLATE.format(
                    title=title, content=content, current_date=current_date
                ))
            generated_urls.append((fname, "0.3"))

    except Exception as e:
        import traceback
        print(f"⚠️  Warning during page generation: {e}")
        traceback.print_exc()

    # ── 5. SITEMAP & ROBOTS ───────────────────────────────────────
    print("... Generating Sitemap & Robots.txt")

    with open(os.path.join(OUTPUT_BASE, "robots.txt"), 'w') as f_rob:
        f_rob.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml")

    today = datetime.now().strftime("%Y-%m-%d")
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url, priority in generated_urls:
        clean_url = url.replace("index.html", "") if "index.html" in url and url != "index.html" else url
        if clean_url == "index.html": clean_url = ""
        full_url = f"{SITE_URL}/{clean_url}"
        sitemap_xml += (
            f'  <url>\n'
            f'    <loc>{full_url}</loc>\n'
            f'    <lastmod>{today}</lastmod>\n'
            f'    <changefreq>monthly</changefreq>\n'
            f'    <priority>{priority}</priority>\n'
            f'  </url>\n'
        )
    sitemap_xml += '</urlset>'

    with open(os.path.join(OUTPUT_BASE, "sitemap.xml"), 'w') as f_map:
        f_map.write(sitemap_xml)

    print(f"✅ Build complete. {len(generated_urls)} URLs generated.")
    print(f"   Landmark pages : {sum(1 for _, p in generated_urls if p == '0.8')}")
    print(f"   City hub pages : {sum(1 for _, p in generated_urls if p == '0.9')}")
    print(f"   Legal pages    : {sum(1 for _, p in generated_urls if p == '0.3')}")
    print(f"   Homepage       : 1")


if __name__ == "__main__":
    build_site()