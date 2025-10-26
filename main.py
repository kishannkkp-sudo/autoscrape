import os
import re
import datetime
from datetime import timedelta
import requests
import time
import random
from urllib.parse import urlparse
import logging
from flask import Flask, jsonify

# ----- CONFIG -----
INDIA_COUNTRY_FACET_ID = "c4f78be1a8f14da0ab49ce1162348a5e"  # Standard Workday facet ID for India
BACKEND_URL = os.environ.get('BACKEND_URL', "https://autopostnodejs.vercel.app/posts")  # URL of the Node.js backend

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# List of companies (same as original)
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
    {"name": "Alcoa", "url": "https://alcoa.wd5.myworkdayjobs.com/careers/1/refreshFacet/318c8bb6f553100021d223d9780d30be"},
    {"name": "American Electric Power", "url": "https://aep.wd1.myworkdayjobs.com/AEPCareerSite"},
    {"name": "Amgen", "url": "https://amgen.wd1.myworkdayjobs.com/Careers"},
    {"name": "Applied Materials", "url": "https://amat.wd1.myworkdayjobs.com/External"},
    {"name": "Arrow Electronics", "url": "https://arrow.wd1.myworkdayjobs.com/AC"},
    {"name": "Assurant", "url": "https://assurant.wd1.myworkdayjobs.com/Assurant_Careers"},
    {"name": "AT&T", "url": "https://att.wd1.myworkdayjobs.com/ATTGeneral"},
    {"name": "Avis Budget Group", "url": "https://avisbudget.wd1.myworkdayjobs.com/ABG_Careers"},
    {"name": "BlackRock", "url": "https://blackrock.wd1.myworkdayjobs.com/BlackRock_Professional"},
    {"name": "Bupa", "url": "https://bupa.wd3.myworkdayjobs.com/EXT_CAREER"},
    {"name": "Cognizant", "url": "https://collaborative.wd1.myworkdayjobs.com/AllOpenings"},
    {"name": "Workday", "url": "https://workday.wd5.myworkdayjobs.com/Workday"},
    {"name": "Fidelity", "url": "https://wd1.myworkdaysite.com/en-US/recruiting/fmr/FidelityCareers"},
    {"name": "AIG", "url": "https://aig.wd1.myworkdayjobs.com/aig"},
    {"name": "Analog Devices", "url": "https://analogdevices.wd1.myworkdayjobs.com/External"},
    {"name": "Intel", "url": "https://intel.wd1.myworkdayjobs.com/External"},
    {"name": "Mastercard", "url": "https://mastercard.wd1.myworkdayjobs.com/CorporateCareers"},
    {"name": "JLL", "url": "https://jll.wd1.myworkdayjobs.com/jllcareers"},
    {"name": "CNX", "url": "https://cnx.wd1.myworkdayjobs.com/external_global"},
    {"name": "Coca-Cola", "url": "https://coke.wd1.myworkdayjobs.com/coca-cola-careers"},
    {"name": "Dell", "url": "https://dell.wd1.myworkdayjobs.com/External"},
    {"name": "Bank of America", "url": "https://ghr.wd1.myworkdayjobs.com/Lateral-US"},
    {"name": "Accenture", "url": "https://accenture.wd103.myworkdayjobs.com/en-US/AccentureCareers/"},
    {"name": "PwC", "url": "https://pwc.wd3.myworkdayjobs.com/Global_Experienced_Careers"},
    {"name": "Huron", "url": "https://huron.wd1.myworkdayjobs.com/huroncareers"},
    {"name": "ING", "url": "https://ing.wd3.myworkdayjobs.com/ICSGBLCOR"},
    {"name": "eBay", "url": "https://ebay.wd5.myworkdayjobs.com/apply/"},
    {"name": "AstraZeneca", "url": "https://astrazeneca.wd3.myworkdayjobs.com/Careers"},
    {"name": "Nexstar", "url": "https://nexstar.wd5.myworkdayjobs.com/nexstar"},
    {"name": "Samsung", "url": "https://sec.wd3.myworkdayjobs.com/Samsung_Careers"},
    {"name": "Warner Bros", "url": "https://warnerbros.wd5.myworkdayjobs.com/global"},
    
    {"name": "Hitachi", "url": "https://hitachi.wd1.myworkdayjobs.com/hitachi"},
    {"name": "Ciena", "url": "https://ciena.wd5.myworkdayjobs.com/Careers"},
    {"name": "BDX", "url": "https://bdx.wd1.myworkdayjobs.com/EXTERNAL_CAREER_SITE_INDIA"},
    {"name": "Cengage", "url": "https://cengage.wd5.myworkdayjobs.com/CengageIndiaCareers"},
    {"name": "Pfizer", "url": "https://pfizer.wd1.myworkdayjobs.com/PfizerCareers"},
    {"name": "Availity", "url": "https://availity.wd1.myworkdayjobs.com/Availity_Careers_India"},
    {"name": "Wells Fargo", "url": "https://wd1.myworkdaysite.com/recruiting/wf/WellsFargoJobs"},
    {"name": "Motorola Solutions", "url": "https://motorolasolutions.wd5.myworkdayjobs.com/Careers"},
    {"name": "2020 Companies", "url": "https://2020companies.wd1.myworkdayjobs.com/External_Careers"},
    {"name": "Kyndryl", "url": "https://kyndryl.wd5.myworkdayjobs.com/KyndrylProfessionalCareers"},
    {"name": "IFF", "url": "https://iff.wd5.myworkdayjobs.com/en-US/iff_careers"}
]

def generate_auto_tags(title):
    stopwords = {'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 'to', 'was', 'were', 'will', 'with'}
    words = re.sub(r'[^\w\s]', ' ', title.lower()).split()
    tags = [word for word in words if word not in stopwords and len(word) > 3][:5]
    return tags if tags else ['job', 'india', 'hiring']

def determine_exp_level(title, description):
    text = (title + ' ' + description).lower()
    fresher_keywords = ['fresher', 'entry level', '0-1 year', 'junior', 'intern', 'graduate', 'fresh graduate']
    if any(keyword in text for keyword in fresher_keywords):
        return 'fresher'
    years_match = re.search(r'(\d+\s*-\s*\d+\s*(?:year[\u2019\']?s?)?(?:\s*of\s*experience)?|\d+\s*\+\s*(?:year[\u2019\']?s?)?(?:\s*of\s*experience)?)', text, re.I)
    if years_match:
        exp_str = years_match.group(0).replace('years', '').replace("year\u2019s", '').replace("year's", '').replace('year', '').replace('of experience', '').strip()
        exp_str = re.sub(r'\s+', '', exp_str)
        return exp_str
    exp_keywords = ['senior', 'lead', 'manager', '2+', '3+']
    if any(keyword in text for keyword in exp_keywords):
        return 'exp'
    return 'fresher'

def get_company_logo(company_name):
    domain = company_name.lower().replace(' ', '') + '.com'
    logo_url = f"https://logo.clearbit.com/{domain}"
    try:
        r = requests.head(logo_url, timeout=10)
        if r.status_code == 200:
            return logo_url
    except requests.RequestException:
        pass
    logger.warning(f"Could not find logo for {company_name}.")
    return None

def fetch_past_jobs(company_name, base_url, target_date_str):
    parsed_url = urlparse(base_url)
    host = parsed_url.netloc
    path = parsed_url.path.strip('/')
    if 'en-US/' in path:
        site = path.split('en-US/')[1]
    else:
        site = path
    tenant = host.split('.')[0]
    endpoint = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Referer': base_url,
    }

    jobs = []
    offset = 0
    limit = 20
    today = datetime.date.today()
    has_more = True
    while has_more:
        data = {
            "limit": limit,
            "offset": offset,
            "searchText": ""
        }
        try:
            data_with_facets = data.copy()
            data_with_facets["appliedFacets"] = {"locationCountry": [INDIA_COUNTRY_FACET_ID]}
            r = requests.post(endpoint, headers=headers, json=data_with_facets, timeout=10)
            if r.status_code == 400:
                logger.warning(f"Facets failed for {company_name}, trying without facets.")
                r = requests.post(endpoint, headers=headers, json=data, timeout=10)
            if r.status_code != 200:
                logger.error(f"Failed to fetch jobs for {company_name}: {r.status_code} - {r.reason}")
                return jobs
            response_data = r.json()
        except Exception as e:
            logger.warning(f"Exception in list fetch for {company_name}: {str(e)}, trying without facets.")
            try:
                r = requests.post(endpoint, headers=headers, json=data, timeout=10)
                if r.status_code != 200:
                    logger.error(f"Failed to fetch jobs for {company_name} (no facets): {r.status_code} - {r.reason}")
                    return jobs
                response_data = r.json()
            except Exception as e2:
                logger.error(f"Error fetching jobs for {company_name}: {str(e2)}")
                return jobs

        job_postings = response_data.get('jobPostings', [])
        if not job_postings:
            has_more = False
            break

        for posting in job_postings:
            title = posting.get('title', 'Unknown Title')
            external_path = posting.get('externalPath', '')
            if not external_path:
                continue
            slug = external_path.split('/')[-1]
            try:
                title_slug, job_req_id = slug.rsplit('_', 1)
            except ValueError:
                title_slug = slug
                job_req_id = slug
            apply_link = f"https://{host}/en-US/{site}/details/{slug}?q={job_req_id}"
            location = posting.get('locationsText', '')
            if INDIA_COUNTRY_FACET_ID not in data.get("appliedFacets", {}).get("locationCountry", []) and 'india' not in location.lower():
                continue
            posted_text = posting.get('postedOn', '')
            posted_delta = 0
            if 'Today' in posted_text or 'today' in posted_text.lower():
                posted_delta = 0
            elif re.search(r'(\d+) day[s]? ago', posted_text, re.I):
                match = re.search(r'(\d+) day[s]? ago', posted_text, re.I)
                if match:
                    posted_delta = int(match.group(1))
            elif re.search(r'posted (\d+) days? ago', posted_text, re.I):
                match = re.search(r'posted (\d+) days? ago', posted_text, re.I)
                if match:
                    posted_delta = int(match.group(1))
            posted_date = (today - timedelta(days=posted_delta)).isoformat()
            date_match = re.search(r'\d{4}-\d{2}-\d{2}', posted_text)
            if date_match:
                posted_date = date_match.group(0)
            if posted_date != target_date_str:
                if posted_delta > (today - datetime.date.fromisoformat(target_date_str)).days:
                    has_more = False
                continue
            detail_endpoint = f"https://{host}/wday/cxs/{tenant}/{site}{external_path}"
            try:
                detail_r = requests.get(detail_endpoint, headers=headers, timeout=10)
                if detail_r.status_code == 200:
                    detail_data = detail_r.json()
                    job_info = detail_data.get('jobPostingInfo', {})
                    original_desc = job_info.get('jobDescription', title + ' - ' + location + '. Exciting opportunity at ' + company_name + ' in India.')
                    description = re.sub(r'<[^>]+>', '', original_desc)
                    skills = re.findall(r'\b(?:[A-Za-z0-9+.#]+(?:/[A-Za-z0-9+.#]+)?|[A-Za-z]+)\b(?=\s*(?:,|\.|;|\sand\s|\sor\s|\(|\)))', description, re.I)
                    skills = list(set([skill for skill in skills if len(skill) > 2 and not re.match(r'^\d+$', skill)]))[:5]
                    experience_match = re.search(r'(\d+\s*-\s*\d+\s*(?:year[\u2019\']?s?)?(?:\s*of\s*experience)?|\d+\s*\+\s*(?:year[\u2019\']?s?)?(?:\s*of\s*experience)?)', description, re.I)
                    experience = experience_match.group(0) if experience_match else "Not specified"
                    # Extract additional metadata
                    remote_type = job_info.get('remoteType', 'Not specified')
                    time_type = job_info.get('timeType', 'Not specified')
                    time_left_to_apply = job_info.get('timeLeftToApply', 'Not specified')
                else:
                    logger.warning(f"Failed to fetch details for {title}: {detail_r.status_code}")
                    original_desc = title + ' - ' + location + '. Exciting opportunity at ' + company_name + ' in India.'
                    description = original_desc
                    skills = ['Not specified']
                    experience = 'Not specified'
                    remote_type = 'Not specified'
                    time_type = 'Not specified'
                    time_left_to_apply = 'Not specified'
            except Exception as e:
                logger.warning(f"Could not fetch details for {title}: {str(e)}")
                original_desc = title + ' - ' + location + '. Exciting opportunity at ' + company_name + ' in India.'
                description = original_desc
                skills = ['Not specified']
                experience = 'Not specified'
                remote_type = 'Not specified'
                time_type = 'Not specified'
                time_left_to_apply = 'Not specified'
            exp_level = determine_exp_level(title, description)
            jobs.append({
                'title': title,
                'description': original_desc,
                'apply_link': apply_link,
                'posted_date': posted_date,
                'posted_text': posted_text,
                'exp': exp_level,
                'company': company_name,
                'location': location,
                'skills': skills,
                'experience': experience,
                'remote_type': remote_type,
                'time_type': time_type,
                'time_left_to_apply': time_left_to_apply,
                'job_req_id': job_req_id
            })
        offset += limit
        total = response_data.get('total', 0)
        if offset >= total:
            has_more = False
    return jobs

def check_existing_post(title, apply_link, max_results=100):
    try:
        response = requests.get(BACKEND_URL)
        if response.status_code == 200:
            posts = response.json()
            for post in posts:
                if title.lower() in post.get('title', '').lower() or apply_link in post.get('description', ''):
                    return True
        return False
    except Exception as e:
        logger.error(f"Error checking existing posts: {str(e)}")
        return False

def generate_post_title(job):
    base_title = re.sub(r'\s+-\s+.*', '', job['title']).strip()
    exp_str = job['exp']
    if exp_str == 'fresher':
        return f"{base_title} - fresher"
    elif exp_str == 'exp':
        return f"{base_title} - (experienced)"
    else:
        return f"{base_title} - ({exp_str})"

def create_post(title, content_html, logo_url=None, company_name=None, max_retries=3, retry_delay=60):
    for attempt in range(max_retries):
        try:
            payload = {
                "title": title,
                "description": content_html,
                "company_logo": logo_url,
                "company_name": company_name
            }
            response = requests.post(BACKEND_URL, json=payload, timeout=10)
            if response.status_code == 201:
                logger.info(f"Posted! {title}")
                return response.json()
            else:
                logger.warning(f"Failed to post {title}: {response.status_code} - {response.text}")
                time.sleep(retry_delay)
        except Exception as e:
            logger.warning(f"Error posting {title}: {str(e)}. Retrying after {retry_delay} seconds ({attempt+1}/{max_retries})...")
            time.sleep(retry_delay)
    logger.error(f"Failed to post {title} after {max_retries} attempts.")
    return None

def run_scrape():
    target_date = datetime.date.today().isoformat()
    logger.info(f"Fetching jobs posted today ({target_date})...")
    random.shuffle(COMPANIES)
    posted_count = 0

    for company in COMPANIES:
        logger.info(f"Processing {company['name']}...")
        jobs = fetch_past_jobs(company['name'], company['url'], target_date)
        for job in jobs:
            post_title = generate_post_title(job)
            if check_existing_post(post_title, job['apply_link']):
                logger.info(f"Skipping {post_title} as it already exists.")
                continue
            logo_url = get_company_logo(company['name'])
            content_html = f"{job['title']}<br>\n"
            content_html += f"Apply: <a href='{job['apply_link']}'>Apply Link</a><br>\n"
            content_html += f"Locations: {job['location']}<br>\n"
            content_html += f"Time Type: {job['time_type']}<br>\n"
            content_html += f"Posted On: {job['posted_text']}<br>\n"
            content_html += f"Time Left to Apply: {job['time_left_to_apply']}<br>\n"
            content_html += f"Job Requisition ID: {job['job_req_id']}<br>\n"
            content_html += f"<br>\n{job['description']}<br>\n"
            content_html += f"Skills: {', '.join(job['skills'])}<br>\n"
            content_html += f"Experience: {job['experience']}<br>\n"
            logger.info(f"Creating post for: {post_title}")
            try:
                post = create_post(post_title, content_html, logo_url, company['name'])
                if post:
                    logger.info(f"Posted! {post_title}")
                    posted_count += 1
            except Exception as e:
                logger.error(f"Failed to post {post_title}: {str(e)}")

    logger.info(f"Finished cycle! {posted_count} posts created.")
    return {"status": "success", "posted_count": posted_count}

@app.route('/scrape', methods=['GET'])
def scrape_jobs():
    try:
        result = run_scrape()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in scrape endpoint: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))