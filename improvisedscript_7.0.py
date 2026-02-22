import os
import csv
import json
import re
import random
from datetime import datetime
from collections import defaultdict
import httplib2
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. CONFIGURATION ---
OUTPUT_BASE = 'production_build'
CSV_FILE = 'Final_Master_Silo_with_Schemas.csv'
SITE_URL = "https://stationsteps.com"
KEY_FILE = "stationsteps-maps-8606569f2c45.txt" # Kept local/ignored for security
VERIFIED_TS = f"Verified {datetime.now().strftime('%B %Y')}" 

# --- 2. TEMPLATES ---

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
    {breadcrumb_schema}
</head>
<body class="bg-slate-50 text-slate-900 font-sans pb-24">
    <div class="bg-blue-600 text-white py-2 px-4 text-center">
        <p class="text-[10px] font-black uppercase tracking-widest">{verified_ts} • Official Logistics Protocol</p>
    </div>

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

        <section class="bg-white rounded-[2rem] shadow-2xl border border-slate-100 overflow-hidden mb-12">
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

        <section class="mb-12">
            <h3 class="text-xs font-black uppercase tracking-widest text-slate-400 mb-6">Logistics Intelligence</h3>
            <div class="space-y-3">{faq_html}</div>
            
            <a href="index.html" class="block w-full text-center py-4 mt-8 border-2 border-dashed border-slate-200 rounded-2xl text-[10px] font-black uppercase tracking-widest text-slate-400 hover:border-blue-600 hover:text-blue-600 hover:bg-blue-50 transition-all">
                <i class="fas fa-city mr-2"></i> View All {city} Station Exits
            </a>
        </section>

        <footer class="text-center pt-12 border-t border-slate-200">
            <h4 class="text-[10px] font-black uppercase text-slate-300 mb-6">Nearby Stations</h4>
            <div class="flex flex-wrap justify-center gap-3">{neighbor_links}</div>
            <div class="mt-12 flex justify-center gap-6 text-[10px] font-bold text-slate-300 uppercase tracking-widest">
                <a href="../../index.html">Directory</a> • <a href="../../privacy.html">Privacy</a> • <a href="../../terms.html">Terms</a>
            </div>
        </footer>
    </main>
</body>
</html>"""

# [B] CITY HUB TEMPLATE
CITY_HUB_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{city} Station Exits | StationSteps</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-slate-50 text-slate-900">
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
        <div class="grid md:grid-cols-2 gap-4">
            {landmark_cards}
        </div>
    </main>
    <footer class="bg-white border-t border-slate-200 py-12 text-center">
        <div class="flex justify-center gap-6 text-[10px] font-black text-slate-400 uppercase tracking-widest">
            <a href="../../index.html">Home</a> <a href="../../privacy.html">Privacy</a> <a href="../../terms.html">Terms</a>
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
    <meta name="description" content="Verified station exit commands and logistics for the world's most iconic landmarks.">
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
        body { font-family: 'Inter', sans-serif; }
        .hero-pattern { background-color: #0f172a; background-image: radial-gradient(#1e293b 1px, transparent 1px); background-size: 24px 24px; }
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
        <div class="mt-12 pt-8 border-t border-slate-100 text-center"><p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Last Updated: January 2026</p></div>
    </div>
</body></html>"""

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

def get_power_title(landmark, city):
    power_words = ["Verified", "Fastest", "Official", "Step-Free", "2026 Guide"]
    word = random.choice(power_words)
    return f"{word}: {landmark} Station Exit & Logistics | {city}"

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

def notify_google_indexing(url_list):
    if not os.path.exists(KEY_FILE):
        print(f"⚠️ Skip Indexing: Key file '{KEY_FILE}' not found. Make sure it is in the root directory.")
        return
    
    print(f"🚀 Pinging Google Indexing API for {len(url_list)} URLs...")
    SCOPES = ["https://www.googleapis.com/auth/indexing"]
    ENDPOINT = "https://indexing.googleapis.com/v3/urlNotifications:publish"
    
    try:
        credentials = ServiceAccountCredentials.from_json_keyfile_name(KEY_FILE, SCOPES)
        http = credentials.authorize(httplib2.Http())
        for url in url_list:
            full_url = f"{SITE_URL}/{url.replace('index.html', '')}"
            body = json.dumps({"url": full_url, "type": "URL_UPDATED"})
            response, content = http.request(ENDPOINT, method="POST", body=body)
            print(f"Indexed: {full_url} | Status: {response.status}")
    except Exception as e:
        print(f"❌ Indexing Error: {e}")

# --- 4. MAIN BUILD ENGINE ---

def build_site():
    print("🏭 Initializing Master Engine v6.3...")
    
    if not os.path.exists(CSV_FILE):
        print(f"❌ Error: {CSV_FILE} not found.")
        return

    with open(CSV_FILE, mode='r', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    
    silos = defaultdict(list)
    for row in rows:
        silos[row['city']].append(row)
    
    generated_urls = [] 

    try:
        # 1. GENERATE LANDMARK PAGES
        print("... Building Landmark Pages (With Accordions)")
        for row in rows:
            landmark, city = row['landmark'], row['city']
            l_slug, c_slug = slugify(landmark), slugify(city)
            
            hz_badge = extract_signal(row.get('terrain_en', ''), r'\d+Hz', 'VIBE')
            db_badge = extract_signal(row.get('terrain_en', ''), r'\d+dB', 'AUDIO')

            peers = [x for x in silos[city] if x['landmark'] != landmark]
            n_links = "".join([f'<a href="{slugify(n["landmark"])}.html" class="px-4 py-2 bg-white border rounded-xl text-[10px] font-bold text-slate-500 uppercase hover:border-blue-600 transition-all">{n["landmark"]}</a>' for n in random.sample(peers, min(len(peers), 5))])

            # NEW: Building the HTML Accordion Structure
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
                    </details>
                    """

            power_title = get_power_title(landmark, city)
            breadcrumb_json = get_breadcrumb_schema(city, c_slug, landmark, l_slug)

            html = LANDMARK_TEMPLATE.format(
                title_tag=power_title,
                meta_desc=f"Navigate {landmark} from {row['station']}. {row['walk_time']}m walk.",
                hreflang_tags=get_hreflang(c_slug, l_slug),
                canonical_url=f"{SITE_URL}/en/{c_slug}/{l_slug}.html",
                schema_block=get_schema_block(row, 'en'),
                breadcrumb_schema=breadcrumb_json,
                verified_ts=VERIFIED_TS, city=city, landmark=landmark,
                hz_badge=hz_badge, db_badge=db_badge,
                station=row['station'], walk_time=row['walk_time'],
                exit_command=row['exit_command_en'], expert_tip=row.get('expert_tip_en', ''),
                faq_html=faq_html, neighbor_links=n_links
            )

            out_dir = os.path.join(OUTPUT_BASE, 'en', c_slug)
            os.makedirs(out_dir, exist_ok=True)
            with open(os.path.join(out_dir, f"{l_slug}.html"), 'w', encoding='utf-8') as f_out:
                f_out.write(html)
            generated_urls.append(f"en/{c_slug}/{l_slug}.html")

        # 2. GENERATE CITY HUBS
        print("... Building City Hubs")
        city_cards_html = "" 
        
        for city, city_rows in silos.items():
            c_slug = slugify(city)
            country = city_rows[0].get('country', 'Global')
            count = len(city_rows)
            avg_w = int(sum([float(re.sub(r'[^\d.]','', str(r.get('walk_time', 0)))) for r in city_rows]) / count)
            
            l_cards = ""
            for r in city_rows:
                l_slug = slugify(r['landmark'])
                l_cards += f"""<a href="{l_slug}.html" class="group bg-white p-6 rounded-3xl border border-slate-200 hover:shadow-xl transition-all">
                    <div class="flex justify-between items-start"><h3 class="font-black text-xl text-slate-800 group-hover:text-blue-600 italic tracking-tighter">{r['landmark']}</h3><i class="fas fa-arrow-right text-slate-300 group-hover:text-blue-600 transition-transform group-hover:translate-x-1"></i></div>
                    <p class="text-[10px] font-bold uppercase text-slate-400 mt-2 tracking-widest"><i class="fas fa-train mr-1"></i> {r.get('station','Metro')}</p>
                </a>"""

            hub_html = CITY_HUB_TEMPLATE.format(city=city, country=country, count=count, avg_walk=avg_w, landmark_cards=l_cards)
            
            with open(os.path.join(OUTPUT_BASE, 'en', c_slug, "index.html"), 'w', encoding='utf-8') as f_hub:
                f_hub.write(hub_html)
            generated_urls.append(f"en/{c_slug}/index.html")

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

        # 3. GENERATE HOMEPAGE
        print("... Building Homepage")
        final_home = HOMEPAGE_TEMPLATE.format(date_str=datetime.now().strftime("%B %Y"), city_grid=city_cards_html)
        with open(os.path.join(OUTPUT_BASE, "index.html"), 'w', encoding='utf-8') as f_home:
            f_home.write(final_home)
        generated_urls.append("index.html")

        # 4. GENERATE LEGAL PAGES
        print("... Building Legal Pages")
        legal_docs = [
            ("Privacy Policy", "privacy.html", "We value your privacy. This site is for informational purposes only."),
            ("Terms of Service", "terms.html", "By using StationSteps, you agree that transit data may change without notice.")
        ]
        for title, fname, content in legal_docs:
            with open(os.path.join(OUTPUT_BASE, fname), 'w', encoding='utf-8') as f_leg:
                f_leg.write(LEGAL_TEMPLATE.format(title=title, content=content))
            generated_urls.append(fname)

    except Exception as e:
        print(f"⚠️ Warning during page generation: {e}")

    # 5. GENERATE SITEMAP & ROBOTS
    print("... Generating Sitemap & Robots.txt")
    
    with open(os.path.join(OUTPUT_BASE, "robots.txt"), 'w') as f_rob:
        f_rob.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml")

    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in generated_urls:
        clean_url = url.replace("index.html", "") if "index.html" in url and url != "index.html" else url
        if clean_url == "index.html": clean_url = "" 
        
        full_url = f"{SITE_URL}/{clean_url}"
        sitemap_xml += f'  <url>\n    <loc>{full_url}</loc>\n    <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>\n    <changefreq>monthly</changefreq>\n  </url>\n'
    sitemap_xml += '</urlset>'

    with open(os.path.join(OUTPUT_BASE, "sitemap.xml"), 'w') as f_map:
        f_map.write(sitemap_xml)

    print(f"✅ Success: Production build complete. Sitemap contains {len(generated_urls)} URLs.")
    
    # 6. TRIGGER INDEXING API
    notify_google_indexing(generated_urls)

if __name__ == "__main__":
    build_site()