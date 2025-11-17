# main.py - FirstJobly Workday Scraper v3.5 (November 17, 2025)
import os
import re
import datetime
from datetime import timedelta
import requests
import time
import random
import html
import logging
from urllib.parse import urlparse
from flask import Flask, jsonify
import threading

# ==================== CONFIG ====================
INDIA_COUNTRY_FACET_ID = "c4f78be1a8f14da0ab49ce1162348a5e"
BACKEND_URL = os.environ.get('BACKEND_URL', "https://autopostnodejs.vercel.app/posts")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# In-memory deduplication
POSTED_JOBS = set()

# ==================== FULL COMPANY LIST (50+ MNCs) ====================
COMPANIES = [
    {"name": "Boeing", "url": "https://boeing.wd1.myworkdayjobs.com/EXTERNAL_CAREERS"},
    {"name": "3M", "url": "https://3m.wd1.myworkdayjobs.com/search"},
    {"name": "Adobe", "url": "https://adobe.wd5.myworkdayjobs.com/external_experienced"},
    {"name": "NVIDIA", "url": "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite"},
    {"name": "Salesforce", "url": "https://salesforce.wd12.myworkdayjobs.com/External_Career_Site"},
    {"name": "Target", "url": "https://target.wd5.myworkdayjobs.com/targetcareers"},
    {"name": "Walmart", "url": "https://walmart.wd5.myworkdayjobs.com/WalmartExternal"},
    {"name": "Chevron", "url": "https://chevron.wd5.myworkdayjobs.com/jobs"},
    {"name": "Deloitte", "url": "https://deloitteie.wd3.myworkdayjobs.com/Early_Careers"},
    {"name": "Puma", "url": "https://puma.wd3.myworkdayjobs.com/Jobs_at_Puma"},
    {"name": "Sanofi", "url": "https://sanofi.wd3.myworkdayjobs.com/SanofiCareers"},
    {"name": "Comcast", "url": "https://comcast.wd5.myworkdayjobs.com/Comcast_Careers"},
    {"name": "Abbott", "url": "https://abbott.wd5.myworkdayjobs.com/abbottcareers"},
    {"name": "Alcoa", "url": "https://alcoa.wd5.myworkdayjobs.com/careers"},
    {"name": "American Electric Power", "url": "https://aep.wd1.myworkdayjobs.com/AEPCareerSite"},
    {"name": "Amgen", "url": "https://amgen.wd1.myworkdayjobs.com/Careers"},
    {"name": "Applied Materials", "url": "https://amat.wd1.myworkdayjobs.com/External"},
    {"name": "Arrow Electronics", "url": "https://arrow.wd1.myworkdayjobs.com/AC"},
    {"name": "AT&T", "url": "https://att.wd1.myworkdayjobs.com/ATTGeneral"},
    {"name": "BlackRock", "url": "https://blackrock.wd1.myworkdayjobs.com/BlackRock_Professional"},
    {"name": "Cognizant", "url": "https://collaborative.wd1.myworkdayjobs.com/AllOpenings"},
    {"name": "Workday", "url": "https://workday.wd5.myworkdayjobs.com/Workday"},
    {"name": "Intel", "url": "https://intel.wd1.myworkdayjobs.com/External"},
    {"name": "Mastercard", "url": "https://mastercard.wd1.myworkdayjobs.com/CorporateCareers"},
    {"name": "Coca-Cola", "url": "https://coke.wd1.myworkdayjobs.com/coca-cola-careers"},
    {"name": "Dell", "url": "https://dell.wd1.myworkdayjobs.com/External"},
    {"name": "Accenture", "url": "https://accenture.wd103.myworkdayjobs.com/en-US/AccentureCareers/"},
    {"name": "PwC", "url": "https://pwc.wd3.myworkdayjobs.com/Global_Experienced_Careers"},
    {"name": "eBay", "url": "https://ebay.wd5.myworkdayjobs.com/apply/"},
    {"name": "AstraZeneca", "url": "https://astrazeneca.wd3.myworkdayjobs.com/Careers"},
    {"name": "Samsung", "url": "https://sec.wd3.myworkdayjobs.com/Samsung_Careers"},
    {"name": "Pfizer", "url": "https://pfizer.wd1.myworkdayjobs.com/PfizerCareers"},
    {"name": "Wells Fargo", "url": "https://wd1.myworkdaysite.com/recruiting/wf/WellsFargoJobs"},
    {"name": "Kyndryl", "url": "https://kyndryl.wd5.myworkdayjobs.com/KyndrylProfessionalCareers"},
    {"name": "IFF", "url": "https://iff.wd5.myworkdayjobs.com/en-US/iff_careers"}
]

# ==================== RICH CONTENT TEMPLATES ====================
INTRO_TEMPLATES = [
    "Looking for a rewarding career with a global leader? {company} is actively hiring for <strong>{title}</strong> roles across India.",
    "Great news! {company} is expanding in India and hiring talented professionals for <strong>{title}</strong> positions.",
    "Your next career move starts here! {company} is hiring <strong>{title}</strong> with excellent growth opportunities."
]

HOW_TO_APPLY = """
<h3>How to Apply (Step-by-Step)</h3>
<ol>
    <li>Click the <strong>"Apply Now"</strong> button below</li>
    <li>You will be redirected to the official {company} Workday portal</li>
    <li>Complete your profile and upload your resume</li>
    <li>Submit your application</li>
</ol>
<p><strong>Apply early — applications are reviewed on a rolling basis!</strong></p>
"""

def generate_rich_content(job, company_name):
    title = html.escape(job['title'])
    location = html.escape(job.get('location', 'India'))
    clean_loc = location.split(',')[0]
    skills = job['skills'][:6] if job['skills'] else ["Communication", "Teamwork"]
    exp = job.get('experience', 'Not specified')
    remote = job.get('remote_type', 'Office').replace('Remote', 'Work from Home')
    job_id = job['job_req_id']

    content = f"<h1>{title} at {company_name}</h1>"
    content += f"<p><strong>Location:</strong> {location} | <strong>Experience:</strong> {exp} | <strong>Mode:</strong> {remote}</p>"
    content += f"<p><strong>Job ID:</strong> {job_id}</p><hr>"

    content += f"<p>{random.choice(INTRO_TEMPLATES).format(company=company_name, title=title)}</p>"
    content += "<p>Join a world-class team and work on cutting-edge projects with global impact.</p>"

    content += "<h2>Key Requirements</h2><ul>"
    content += f"<li>Experience: {exp}</li>"
    for s in skills:
        content += f"<li>{s}</li>"
    content += "</ul>"

    content += HOW_TO_APPLY.format(company=company_name)

    content += f"<div style='text-align:center;margin:40px 0;'>"
    content += f"<a href='{job['apply_link']}' target='_blank' style='background:#0066cc;color:white;padding:18px 50px;font-size:20px;border-radius:12px;text-decoration:none;font-weight:bold;'>APPLY NOW - OFFICIAL LINK</a>"
    content += "</div>"

    content += f"<p><small>Posted: {job['posted_text']} | Source: {company_name} Careers | Updated: November 17, 2025</small></p>"
    return content

# ==================== DEDUPLICATION & POSTING ====================
def is_duplicate(job_req_id, company_name):
    key = f"{company_name.lower()}|{job_req_id}"
    if key in POSTED_JOBS:
        return True
    try:
        r = requests.get(BACKEND_URL, timeout=10)
        if r.ok:
            for post in r.json():
                if post.get('job_req_id') == job_req_id and post.get('company_name') == company_name:
                    return True
    except:
        pass
    return False

def mark_as_posted(job_req_id, company_name):
    POSTED_JOBS.add(f"{company_name.lower()}|{job_req_id}")

def post_to_backend(job, company_name, logo_url):
    payload = {
        "title": f"{job['title']} at {company_name} - {job['location'].split(',')[0] if job['location'] else 'India'}",
        "description": generate_rich_content(job, company_name),
        "company_name": company_name,
        "company_logo": logo_url or "",
        "job_req_id": job['job_req_id'],
        "apply_link": job['apply_link'],
        "location": job['location'],
        "experience": job.get('experience'),
        "skills": job['skills'],
        "remote_type": job.get('remote_type'),
        "time_type": job.get('time_type', 'Full-Time'),
        "posted_date": job['posted_date']
    }
    try:
        r = requests.post(BACKEND_URL, json=payload, timeout=15)
        if r.status_code == 201:
            logger.info(f"POSTED: {payload['title']}")
            return True
    except Exception as e:
        logger.error(f"Post failed: {e}")
    return False

# ==================== SCRAPER CORE ====================
def fetch_today_jobs(company_name, base_url):
    parsed = urlparse(base_url)
    host = parsed.netloc
    tenant = host.split('.')[0]
    site = parsed.path.strip('/').split('/')[-1]
    endpoint = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": base_url
    }

    jobs = []
    offset = 0
    limit = 20

    while True:
        payload = {"limit": limit, "offset": offset, "searchText": ""}
        try:
            payload_with_facet = payload.copy()
            payload_with_facet["appliedFacets"] = {"locationCountry": [INDIA_COUNTRY_FACET_ID]}
            r = requests.post(endpoint, headers=headers, json=payload_with_facet, timeout=12)
            if r.status_code == 400:
                r = requests.post(endpoint, headers=headers, json=payload, timeout=12)
            data = r.json()
        except:
            break

        postings = data.get("jobPostings", [])
        if not postings:
            break

        for p in postings:
            title = p.get("title", "")
            path = p.get("externalPath", "")
            if not path: continue
            slug = path.split("/")[-1]
            job_id = slug.split("_")[-1]
            apply_link = f"https://{host}/en-US/{site}/job/{slug}"

            posted_text = p.get("postedOn", "Just posted")
            if "day" in posted_text.lower() and "just" not in posted_text.lower():
                continue  # Skip older than today

            detail_url = f"https://{host}/wday/cxs/{tenant}/{site}{path}"
            try:
                detail = requests.get(detail_url, headers=headers, timeout=10).json()
                info = detail.get("jobPostingInfo", {})
                desc_html = info.get("jobDescription", "")
                desc_text = re.sub(r'<[^>]+>', '', desc_html)
                skills = re.findall(r'\b[A-Za-z#+.]{3,20}\b', desc_text)[:6]
            except:
                desc_text = ""
                skills = []

            jobs.append({
                "title": title,
                "location": p.get("locationsText", "India"),
                "apply_link": apply_link,
                "posted_date": datetime.date.today().isoformat(),
                "posted_text": posted_text,
                "job_req_id": job_id,
                "experience": info.get("experienceLevel", "Not specified"),
                "skills": list(set([s.capitalize() for s in skills if len(s) > 2])),
                "remote_type": info.get("remoteType", "Office"),
                "time_type": info.get("timeType", "Full Time")
            })

        offset += limit
        if offset >= data.get("total", 0):
            break
        time.sleep(1)

    return jobs

# ==================== MAIN SCRAPER (6 AM - 6 PM IST) ====================
def run_scrape_once():
    now_ist = datetime.datetime.now()
    hour = now_ist.hour

    if not (6 <= hour < 18):
        logger.info(f"Outside 6 AM - 6 PM IST. Current: {hour}:00 IST")
        return {"status": "sleeping", "time": now_ist.strftime("%H:%M IST")}

    logger.info(f"SCRAPING STARTED at {now_ist.strftime('%H:%M IST')}")

    new_posts = 0
    random.shuffle(COMPANIES)

    for comp in COMPANIES:
        name = comp["name"]
        url = comp["url"]
        try:
            jobs = fetch_today_jobs(name, url)
            for job in jobs:
                if is_duplicate(job['job_req_id'], name):
                    continue
                logo = f"https://logo.clearbit.com/{name.lower().replace(' ', '')}.com"
                logo = logo if requests.head(logo, timeout=5).status_code == 200 else ""
                if post_to_backend(job, name, logo):
                    mark_as_posted(job['job_req_id'], name)
                    new_posts += 1
                    time.sleep(3)
        except Exception as e:
            logger.error(f"Error {name}: {e}")
        time.sleep(5)

    logger.info(f"Scrape complete. {new_posts} new jobs posted.")
    return {"status": "success", "new_posts": new_posts, "time": now_ist.strftime("%H:%M IST")}

# Background loop
def background_task():
    while True:
        run_scrape_once()
        time.sleep(300)  # Every 5 minutes

# ==================== FLASK ROUTES ====================
@app.route('/scrape', methods=['GET'])
def trigger():
    return jsonify(run_scrape_once())

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "service": "FirstJobly Scraper v3.5",
        "status": "Running 24/7",
        "schedule": "Every 5 mins (6 AM - 6 PM IST)",
        "companies": len(COMPANIES),
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S IST"),
        "url": "https://www.firstjobly.in"
    })

if __name__ == "__main__":
    threading.Thread(target=background_task, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)