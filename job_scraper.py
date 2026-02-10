import asyncio
from playwright.async_api import async_playwright
from vector_storage import add_job

async def scrape_dice_jobs(search_query, location):
    print(f"Starting scraper for '{search_query}' in '{location}'...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = f"https://www.dice.com/jobs?q={search_query}&l={location}"
        print(f"Navigating to {url}")
        await page.goto(url)
        
        try:
            await page.wait_for_selector('.card', timeout=10000)
        except:
            print("No jobs found or page took too long to load.")
            await browser.close()
            return

        job_cards = await page.query_selector_all('a.card-title-link')
        print(f"Found {len(job_cards)} job cards. Processing top 10...")
        
        for i, card in enumerate(job_cards[:10]): 
            try:
                title = await card.inner_text()
                job_url = await card.get_attribute('href')
                
                print(f"[{i+1}/10] Scraping: {title}...")
                
                job_page = await browser.new_page()
                await job_page.goto(job_url)
                
                try:
                    await job_page.wait_for_selector('#jobDescription', timeout=5000)
                    description = await job_page.inner_text('#jobDescription')
                    
                    try:
                        company = await job_page.inner_text('[data-cy="companyName"]')
                    except:
                        company = "Unknown Company"

                    job_id = f"dice-{i}"
                    add_job(job_id, title, company, description)
                    
                except Exception as e:
                    print(f"Failed to extract details for {title}: {e}")
                
                await job_page.close()
                
            except Exception as card_error:
                print(f"Error processing card {i}: {card_error}")

        await browser.close()
        print("Scrape session finished.")

if __name__ == "__main__":
    asyncio.run(scrape_dice_jobs("Application Support Security+", "New Jersey"))