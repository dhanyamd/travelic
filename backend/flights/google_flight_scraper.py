from playwright.async_api import async_playwright 
from browser_use import Agent, Browser, BrowserConfig 
from config.models import model 
from flights.util import flight_scrape_task 
from dotenv import load_dotenv 
import os 

load_dotenv() 

class FlightSearchScrapper: 
    async def start(self, use_bright_data=True):
        self.playwright = await async_playwright().start() 

        if use_bright_data: 
            self.browser = await self.playwright.chromium.connect(
                os.getenv("BRIGHTDATA_WSS_URL")
            )
        else: 
            self.browser = await self.playwright.chromium.launch(
                headless=True
            )
        self.context = await self.browser.new_context()
        self.page = await self.browser.new_page()

    async def find_origin_input(self): 
        element = await self.page.wait_for_selector(
            'input[aria-label="Where from?"]', timeout=5000
        )
        if element:
            return element

        raise Exception("Could not find origin input field")
    
    async def fill_and_select_airport(self, input_selector, airport_name): 
        try: 
            input_element = await self.page.wait_for_selector(input_selector)
            await input_element.press("Control+a")
            await input_element.press("Delete")
            await input_element.type(airport_name, delay=50)
            await self.page.wait_for_selector(
                f'li[role="option"][aria-label*="{airport_name}"]', timeout=3000
            )
            await self.page.wait_for_timeout(500)

            # Try different selectors for the dropdown item
            dropdown_selectors = [
                f'li[role="option"][aria-label*="{airport_name}"]',
                f'li[role="option"] .zsRT0d:text-is("{airport_name}")',
                f'.zsRT0d:has-text("{airport_name}")',
            ]

            for selector in dropdown_selectors:
                try:
                    dropdown_item = await self.page.wait_for_selector(
                        selector, timeout=5000
                    )
                    if dropdown_item:
                        await dropdown_item.click()
                        await self.page.wait_for_load_state("networkidle")
                        return True
                except:
                    continue

            raise Exception(f"Could not select airport: {airport_name}")

        except Exception as e:
            print(f"Error filling airport: {str(e)}")
            await self.page.screenshot(path=f"error_{airport_name.lower()}.png")
            return False
    
    async def fill_flight_search(self, origin, destination, start_date, end_date):
        try:
            print("Navigating to Google Flights...")
            await self.page.goto("https://www.google.com/travel/flights")

            print("Filling in destination...")
            if not await self.fill_and_select_airport(
                'input[aria-label="Where to? "]', destination
            ):
                raise Exception("Failed to set destination airport")

            # Fill origin and destination using helper method
            print("Filling in origin...")
            if not await self.fill_and_select_airport(
                'input[aria-label="Where from?"]', origin
            ):
                raise Exception("Failed to set origin airport")

            print("Selecting dates...")
            # Click the departure date button

            await self.page.click('input[aria-label*="Departure"]')
            await self.page.wait_for_timeout(1000)

            # Select departure date
            departure_button = await self.page.wait_for_selector(
                f'div[aria-label*="{start_date}"]', timeout=5000
            )
            await departure_button.click()
            await self.page.wait_for_timeout(1000)

            return_button = await self.page.wait_for_selector(
                f'div[aria-label*="{end_date}"]', timeout=5000
            )
            await return_button.click()
            await self.page.wait_for_timeout(1000)

            # Click Done button if it exists
            try:
                done_button = await self.page.wait_for_selector(
                    'button[aria-label*="Done."]', timeout=5000
                )
                await done_button.click()
            except:
                print("No Done button found, continuing...")

            return self.page.url 
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return None
    
    async def close(self): 
        try: 
            await self.context.close() 
            await self.browser.close() 
            await self.playwright.stop() 
        except Exception as e: 
            print(f"Error during cleanup: {str(e)}")

async def scrape_flights(url, preferences): 
    browser = Browser(
        config=BrowserConfig(
        chrome_instance_path="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        )
    )
    initial_actions = [
        {"open_tab": {"url": url}}
    ]
    agent = Agent(
        task=flight_scrape_task(preferences, url),
        llm=model,
        initial_actions=initial_actions,
        browser=browser
    )
    history = await agent.run() 
    await browser.close() 
    result = history.final_result()
    return result 

async def get_flight_url(origin, destination, start_date, end_date): 
    try: 
        scrapper = FlightSearchScrapper() 
        await scrapper.start(use_bright_data=False) 
        url = await scrapper.fill_flight_search(
            origin=origin,
            destination=destination,
            start_date=start_date,
            end_date=end_date
        )
        return url 
    finally: 
        print("Closing connection...") 
        if "scraper" in locals():
            await scrapper.close()
