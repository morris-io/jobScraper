import asyncio
from playwright.async_api import async_playwright
from vector_storage import add_job

async def scrape_dice_jobs(search_query, location):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        url = f"https://www.dice.com/jobs?q={search_query}&l={location}"
        await page.goto(url)
        
        await page.wait_for_selector('.card')
        
        job_cards = await page.query_selector_all('a.card-title-link')
        
        for i, card in enumerate(job_cards[:10]): 
            title = await card.inner_text()
            job_url = await card.get_attribute('href')
            
            job_page = await browser.new_page()
            await job_page.goto(job_url)
            await job_page.wait_for_selector('#jobDescription')
            
            description = await job_page.inner_text('#jobDescription')
            company = await job_page.inner_text('[data-cy="companyName"]')
            
            job_id = f"dice-{i}"
            add_job(job_id, title, company, description)
            
            await job_page.close()

        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_dice_jobs("Application Support Security+", "New Jersey"))