import asyncio
import random
import urllib.parse
from playwright.async_api import async_playwright
from vector_storage import add_job

# --- 1. MULTI-KEYWORD LINKEDIN SCRAPER (PAST WEEK FILTER APPLIED) ---
async def scrape_linkedin_keywords(keywords=None):
    if keywords is None:

        keywords = [
            "Application Support", 
            "DevOps", 
            "Dev Operations", 
            "Program Analyst", 
            "Software Analyst"
        ]
    
    # BASE URL WITH "PAST WEEK" FILTER (f_TPR=r604800)
    # location=Berlin, NJ (GeoId: 107096287)
    # distance=50 miles
    # f_WT=1,3 (On-site & Hybrid)
    base_url_template = (
        "https://www.linkedin.com/jobs/search?"
        "keywords={}"                 # Keyword placeholder
        "&location=Berlin&geoId=107096287"
        "&distance=50"
        "&f_TPR=r604800"              # PAST WEEK FILTER
        "&f_WT=1%2C3"                 # On-site (1) and Hybrid (3)
        "&f_E=2%2C3"                  # Entry level (2) and Associate/Mid (3)
        "&position=1"
        "&pageNum=0"
    )

    print(f"--- 🕵️ STARTED LINKEDIN MULTI-SCRAPE: {len(keywords)} Keywords (Past Week) ---", flush=True)

    async with async_playwright() as p:
        # HEADFUL MODE IS REQUIRED FOR LINKEDIN
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        
        total_scraped = 0
        
        for keyword in keywords:
            page = await context.new_page()
            
            # Construct URL for this specific keyword
            encoded_kw = urllib.parse.quote(keyword)
            search_url = base_url_template.format(encoded_kw)
            
            print(f"   🔍 Searching: '{keyword}'...", flush=True)
            
            try:
                await page.goto(search_url, timeout=60000)
                await page.wait_for_timeout(random.randint(3000, 5000))
                
                # Scroll to load more jobs (LinkedIn infinite scroll)
                for _ in range(5):
                    await page.keyboard.press("End")
                    await page.wait_for_timeout(2000)
                
                # Extract Job Links
                # LinkedIn job cards usually have class 'base-card' or 'job-search-card'
                job_links = page.locator('a.base-card__full-link')
                count = await job_links.count()
                
                print(f"      Found {count} jobs for '{keyword}'. Processing top 15...", flush=True)
                
                # Limit to top 15 per keyword to avoid getting blocked
                for i in range(min(count, 15)):
                    try:
                        link = job_links.nth(i)
                        url = await link.get_attribute('href')
                        
                        if url:
                            # Clean URL (remove tracking params)
                            if "?" in url:
                                url = url.split("?")[0]
                            
                            # Open in new tab to preserve search results
                            job_page = await context.new_page()
                            data = await scrape_single_job_logic(job_page, url)
                            await job_page.close()
                            
                            if data and "error" not in data:
                                # Save to Vector DB
                                unique_id = f"li-{keyword[:3]}-{random.randint(1000,9999)}"
                                add_job(unique_id, data['title'], data['company'], data['description'], url)
                                total_scraped += 1
                                print(f"         ✅ Saved: {data['title'][:30]}...", flush=True)
                                
                            await asyncio.sleep(random.uniform(1.0, 3.0)) # Random pause
                            
                    except Exception as e:
                        print(f"         ⚠️ Skipped link: {e}", flush=True)
                        
            except Exception as e:
                print(f"   ❌ Error searching '{keyword}': {e}", flush=True)
            
            await page.close()
            await asyncio.sleep(5) # Pause between keywords
            
        await browser.close()
        print(f"--- SCRAPE COMPLETE: {total_scraped} Jobs Saved ---", flush=True)

# --- 2. REMOTE HELP DESK SCRAPER (US-Wide) ---
async def scrape_linkedin_remote_helpdesk(keywords=None):
    if keywords is None:
        keywords = [
            "Help Desk",
            "IT Support Specialist",
            "Technical Support Specialist",
            "Desktop Support",
            "Service Desk",
        ]

    # Remote filter: f_WT=2, US-wide (no geoId), Past Week filter
    base_url_template = (
        "https://www.linkedin.com/jobs/search?"
        "keywords={}"
        "&location=United+States"
        "&f_TPR=r604800"              # PAST WEEK FILTER
        "&f_WT=2"                     # Remote only
        "&f_E=2%2C3"                  # Entry level (2) and Associate/Mid (3)
        "&position=1"
        "&pageNum=0"
    )

    print(f"--- 🌐 STARTED REMOTE HELP DESK SCRAPE: {len(keywords)} Keywords (Past Week, US Remote) ---", flush=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )

        total_scraped = 0

        for keyword in keywords:
            page = await context.new_page()
            encoded_kw = urllib.parse.quote(keyword)
            search_url = base_url_template.format(encoded_kw)

            print(f"   🔍 Searching Remote: '{keyword}'...", flush=True)

            try:
                await page.goto(search_url, timeout=60000)
                await page.wait_for_timeout(random.randint(3000, 5000))

                for _ in range(5):
                    await page.keyboard.press("End")
                    await page.wait_for_timeout(2000)

                job_links = page.locator('a.base-card__full-link')
                count = await job_links.count()

                print(f"      Found {count} jobs for '{keyword}'. Processing top 15...", flush=True)

                for i in range(min(count, 15)):
                    try:
                        link = job_links.nth(i)
                        url = await link.get_attribute('href')

                        if url:
                            if "?" in url:
                                url = url.split("?")[0]

                            job_page = await context.new_page()
                            data = await scrape_single_job_logic(job_page, url)
                            await job_page.close()

                            if data and "error" not in data:
                                unique_id = f"li-hd-{keyword[:3]}-{random.randint(1000,9999)}"
                                add_job(unique_id, data['title'], data['company'], data['description'], url)
                                total_scraped += 1
                                print(f"         ✅ Saved: {data['title'][:30]}...", flush=True)

                            await asyncio.sleep(random.uniform(1.0, 3.0))

                    except Exception as e:
                        print(f"         ⚠️ Skipped link: {e}", flush=True)

            except Exception as e:
                print(f"   ❌ Error searching '{keyword}': {e}", flush=True)

            await page.close()
            await asyncio.sleep(5)

        await browser.close()
        print(f"--- REMOTE SCRAPE COMPLETE: {total_scraped} Jobs Saved ---", flush=True)


# --- 3. SINGLE LINK SCRAPER (Shared Logic) ---
async def scrape_single_url(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        data = await scrape_single_job_logic(page, url)
        await browser.close()
        return data

async def scrape_single_job_logic(page, url):
    try:
        await page.goto(url, timeout=45000)
        await page.wait_for_timeout(2000)
        
        # Check for login wall
        content = await page.content()
        if "auth_wall" in content or "Sign in" in await page.title():
            return {"error": "Login Wall"}

        # Extract Details (LinkedIn Public View)
        # Try "Show More" button
        try:
            if await page.locator('button[data-tracking-control-name="public_jobs_show-more-html-btn"]').is_visible():
                await page.locator('button[data-tracking-control-name="public_jobs_show-more-html-btn"]').click()
        except:
            pass

        try:
            title = await page.locator('h1.top-card-layout__title').inner_text()
        except:
            title = "Unknown Role"
            
        try:
            company = await page.locator('a.top-card-layout__company-url').inner_text()
        except:
            company = "Unknown Company"
            
        try:
            description = await page.locator('div.show-more-less-html__markup').inner_text()
        except:
            description = ""

        if not description:
            return {"error": "Empty Description"}

        return {
            "title": title.strip(),
            "company": company.strip(),
            "description": description[:8000],
            "url": url
        }

    except Exception as e:
        return {"error": f"Error: {e}"}
