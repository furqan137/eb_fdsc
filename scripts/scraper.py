"""
eBay Feedback Scraper - Enhanced Multi-Seller Version
Scrapes user feedback from eBay and follows seller chains to collect comprehensive feedback data
"""

import os
import time
import logging
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re
from collections import defaultdict

def setup_logging():
    """Setup logging configuration"""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/log.txt'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def init_driver():
    """Initialize Chrome WebDriver with enhanced anti-detection settings"""
    logger = logging.getLogger(__name__)
    
    try:
        # Setup Chrome options with enhanced anti-detection
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--window-size=1920,1080')
        
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')  # Faster loading
        chrome_options.add_argument('--disable-javascript')  # Disable JS to avoid detection scripts
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--no-default-browser-check')
        chrome_options.add_argument('--disable-default-apps')
        
        # Initialize driver with webdriver-manager
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
        driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
        
        logger.info("Chrome WebDriver initialized successfully with anti-detection measures")
        return driver
        
    except Exception as e:
        logger.error(f"Failed to initialize WebDriver: {str(e)}")
        raise

def handle_captcha_manually(driver):
    """Handle captcha by allowing user to solve it manually"""
    logger = logging.getLogger(__name__)
    
    print("\n" + "="*60)
    print("🔧 MANUAL CAPTCHA SOLVING MODE")
    print("="*60)
    print("The browser window is now open for you to manually solve the captcha.")
    print("Please:")
    print("1. Switch to the Chrome browser window")
    print("2. Complete the captcha/verification")
    print("3. Navigate to the eBay feedback page if needed")
    print("4. Come back here and press Enter when done")
    print("="*60)
    
    input("Press Enter after you've solved the captcha and are on the feedback page...")
    
    # Check if we're now on a valid page
    current_url = driver.current_url
    page_title = driver.title
    
    print(f"Current URL: {current_url}")
    print(f"Page title: {page_title}")
    
    if 'captcha' in current_url.lower() or 'captcha' in page_title.lower():
        print("⚠️  Still on captcha page. Please try again.")
        return False
    
    print("✅ Captcha appears to be solved! Continuing...")
    return True

def detect_captcha_or_verification(driver, soup):
    """Detect if eBay is showing captcha or verification page with manual solving option"""
    logger = logging.getLogger(__name__)
    
    page_text = soup.get_text().lower()
    page_source = driver.page_source.lower()
    current_url = driver.current_url.lower()
    
    # Check for common captcha/verification indicators
    captcha_indicators = [
        'captcha', 'verify', 'verification', 'robot', 'automated', 
        'suspicious activity', 'security check', 'prove you are human',
        'unusual activity', 'blocked', 'access denied', 'temporarily unavailable',
        'security measure'
    ]
    
    verification_found = (any(indicator in page_text for indicator in captcha_indicators) or 
                         'captcha' in current_url or 'security' in current_url)
    
    if verification_found:
        logger.warning("eBay verification/captcha page detected!")
        print("\n" + "="*60)
        print("⚠️  CAPTCHA/VERIFICATION DETECTED!")
        print("="*60)
        print("eBay is showing a verification page. This could be due to:")
        print("1. Too many requests from your IP")
        print("2. eBay's anti-bot protection")
        print("3. Geographic restrictions")
        print("\nOptions:")
        print("1. Try manual captcha solving (recommended)")
        print("2. Wait and retry later")
        print("3. Exit and try from different network")
        print("="*60)
        
        # Save page content for debugging
        with open('logs/captcha_page.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("Page content saved to 'logs/captcha_page.html' for debugging")
        
        choice = input("\nDo you want to try solving the captcha manually? (y/n): ").strip().lower()
        
        if choice == 'y' or choice == 'yes':
            return not handle_captcha_manually(driver)  # Return False if captcha solved successfully
        else:
            print("Exiting due to captcha. Please try again later.")
            return True
    
    return False

def scrape_feedback_page(driver, soup, source_user=""):
    """Extract feedback data from a single page with seller identification"""
    feedback_data = []
    
    try:
        if detect_captcha_or_verification(driver, soup):
            return []
        
        feedback_entries = []
        
        # Try modern eBay feedback selectors first
        modern_selectors = [
            'div[data-testid="review-card"]',
            'div.reviews__review',
            'div.ebay-review-item',
            'div.feedback-card',
            'tr.feedback-entry',
            'div.review-item-content',
            'div[class*="review"]',
            'div[class*="feedback"]',
            'tbody tr',  # Table rows for feedback
            'div.card',
            'div.feedback-list-item',  # New selector
            'div[id*="feedback"]',     # New selector
            'tr[class*="feedback"]'    # New selector
        ]
        
        for selector in modern_selectors:
            entries = soup.select(selector)
            if entries:
                feedback_entries = entries
                print(f"[DEBUG] Found {len(entries)} entries using selector: {selector}")
                break
        
        if not feedback_entries:
            print("[DEBUG] No structured feedback found, trying aggressive detection...")
            
            potential_containers = soup.find_all(['div', 'tr', 'li'], 
                string=lambda text: text and any(keyword in text.lower() for keyword in 
                ['positive', 'negative', 'neutral', 'feedback', 'buyer', 'seller', 'item', 'purchase', 'fast shipping', 'great']))
            
            if potential_containers:
                feedback_entries = potential_containers[:50]  # Limit to avoid noise
                print(f"[DEBUG] Found {len(feedback_entries)} potential feedback containers")
            else:
                print("[DEBUG] Trying more aggressive text detection...")
                all_divs = soup.find_all(['div', 'tr', 'td', 'span'])
                potential_feedback = []
                
                for div in all_divs:
                    text_content = div.get_text(strip=True)
                    if (len(text_content) > 20 and len(text_content) < 1000 and 
                        any(word in text_content.lower() for word in ['good', 'great', 'excellent', 'fast', 'quick', 'perfect', 'recommend', 'satisfied', 'item', 'shipping'])):
                        potential_feedback.append(div)
                
                if potential_feedback:
                    feedback_entries = potential_feedback[:20]
                    print(f"[DEBUG] Found {len(feedback_entries)} potential feedback via aggressive detection")
        
        print(f"[DEBUG] Total potential feedback entries to process: {len(feedback_entries)}")
        
        if not feedback_entries:
            print("[DEBUG] No feedback entries found. Analyzing page content...")
            page_text = soup.get_text()[:1000]  # First 1000 chars
            print(f"[DEBUG] Page content preview: {page_text}")
            
            # Check if this is actually a feedback page
            if 'feedback' not in page_text.lower() and 'review' not in page_text.lower():
                print("[DEBUG] This doesn't appear to be a feedback page")
                return []
        
        for i, entry in enumerate(feedback_entries):
            try:
                feedback_text = ""
                
                # Try multiple text extraction methods
                text_elements = entry.find_all(string=True)
                full_text = ' '.join([t.strip() for t in text_elements if t.strip()])
                
                # Look for feedback-like content
                feedback_indicators = ['positive', 'negative', 'neutral', 'great', 'excellent', 'good', 'bad', 'terrible', 'fast shipping', 'slow', 'recommend', 'satisfied', 'perfect', 'amazing', 'quick', 'smooth']
                
                if any(indicator in full_text.lower() for indicator in feedback_indicators) and len(full_text.strip()) > 10:
                    feedback_text = full_text[:500]  # Limit length
                    
                    rating = "Unknown"
                    rating_text = full_text.lower()
                    
                    if any(word in rating_text for word in ['positive', 'good', 'great', 'excellent', 'satisfied', 'recommend', 'perfect', 'amazing', 'quick', 'smooth']):
                        rating = "Positive"
                    elif any(word in rating_text for word in ['negative', 'bad', 'terrible', 'awful', 'disappointed', 'slow', 'poor']):
                        rating = "Negative"
                    elif 'neutral' in rating_text:
                        rating = "Neutral"
                    
                    date = ""
                    date_patterns = [
                        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
                        r'\b\w{3,9}\s+\d{1,2},?\s+\d{4}\b',
                        r'\b\d{1,2}\s+\w{3,9}\s+\d{4}\b'
                    ]
                    
                    for pattern in date_patterns:
                        match = re.search(pattern, full_text)
                        if match:
                            date = match.group()
                            break
                    
                    item = ""
                    # Look for item-like text (often in quotes or after "item:")
                    item_patterns = [
                        r'(?:item[:\s]+|")(.*?)(?:"|$)',
                        r'(?:bought|purchased|received)\s+(.*?)(?:\.|$)',
                        r'(?:product|listing)[:\s]+(.*?)(?:\.|$)'
                    ]
                    
                    for pattern in item_patterns:
                        item_match = re.search(pattern, full_text, re.IGNORECASE)
                        if item_match:
                            item = item_match.group(1)[:100]  # Limit length
                            break
                    
                    # Extract seller/buyer username
                    seller_buyer = ""
                    # Look for usernames (often alphanumeric with underscores/dashes)
                    username_patterns = [
                        r'\b[a-zA-Z0-9_-]{3,20}\b',
                        r'(?:seller|buyer|from)[:\s]+([a-zA-Z0-9_-]{3,20})',
                        r'@([a-zA-Z0-9_-]{3,20})'
                    ]
                    
                    for pattern in username_patterns:
                        username_match = re.search(pattern, full_text)
                        if username_match:
                            potential_username = username_match.group(1) if len(username_match.groups()) > 0 else username_match.group()
                            if potential_username.lower() not in ['positive', 'negative', 'neutral', 'feedback', 'great', 'good', 'excellent', 'item', 'seller', 'buyer']:
                                seller_buyer = potential_username
                                break
                    
                    if feedback_text and len(feedback_text.strip()) > 10:
                        feedback_data.append({
                            'Source User': source_user,
                            'Date': date,
                            'Feedback': feedback_text.strip(),
                            'Rating': rating,
                            'Item': item.strip(),
                            'Seller/Buyer Username': seller_buyer.strip()
                        })
                        
                        if i < 5:  # Show first 5 for debugging
                            print(f"[DEBUG] Entry {i+1}: Rating='{rating}', Seller/Buyer='{seller_buyer}', Text='{feedback_text[:50]}...'")
                    
            except Exception as e:
                logging.getLogger(__name__).warning(f"Error parsing feedback entry {i}: {str(e)}")
                continue
                
    except Exception as e:
        logging.getLogger(__name__).error(f"Error scraping feedback page: {str(e)}")
    
    return feedback_data

def extract_sellers_from_feedback(feedback_data, limit=20):
    """Extract unique seller usernames from feedback data"""
    sellers = set()
    
    for feedback in feedback_data:
        seller_buyer = feedback.get('Seller/Buyer Username', '').strip()
        if seller_buyer and len(seller_buyer) >= 3:
            sellers.add(seller_buyer)
            if len(sellers) >= limit:
                break
    
    return list(sellers)

def scrape_user_feedback(driver, username, max_feedback=10, retry_count=0):
    """Scrape feedback for a specific user with retry mechanism"""
    logger = logging.getLogger(__name__)
    feedback_data = []
    
    try:
        # Use the specific URL pattern requested by client
        feedback_url = f"https://www.ebay.com/fdbk/feedback_profile/{username}?filter=feedback_page%3ARECEIVED_AS_SELLER&sort=TIME"
        
        logger.info(f"Scraping feedback for user: {username}")
        logger.info(f"URL: {feedback_url}")
        
        import random
        delay = random.uniform(3, 8)
        print(f"[DEBUG] Waiting {delay:.1f} seconds before loading page...")
        time.sleep(delay)
        
        driver.get(feedback_url)
        
        wait_time = random.uniform(8, 15)
        time.sleep(wait_time)
        
        current_url = driver.current_url
        page_title = driver.title
        print(f"[DEBUG] Current URL: {current_url}")
        print(f"[DEBUG] Page title: {page_title}")
        
        # Check if user exists
        page_source = driver.page_source.lower()
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        if detect_captcha_or_verification(driver, soup):
            if retry_count < 2:
                print(f"Retrying in 30 seconds... (attempt {retry_count + 1}/3)")
                time.sleep(30)
                return scrape_user_feedback(driver, username, max_feedback, retry_count + 1)
            else:
                print("Max retries reached. Skipping this user.")
                return []
        
        if ("user not found" in page_source or "no longer registered" in page_source or 
            "invalid user" in page_source or "member id" in page_source):
            logger.warning(f"User '{username}' not found or invalid")
            return []
        
        count_selectors = [
            'span[class*="count"]',
            'div[class*="count"]',
            'span[class*="total"]',
            'div[class*="total"]'
        ]
        
        total_feedback = "Unknown"
        for selector in count_selectors:
            count_elements = soup.select(selector)
            for element in count_elements:
                text = element.get_text()
                count_match = re.search(r'(\d+)', text)
                if count_match and int(count_match.group(1)) > 0:
                    total_feedback = count_match.group(1)
                    break
            if total_feedback != "Unknown":
                break
        
        if total_feedback == "Unknown":
            page_text = soup.get_text()
            count_patterns = [
                r'(\d+)\s*(?:feedback|reviews?)',
                r'(?:feedback|reviews?):\s*(\d+)',
                r'total\s*(?:feedback|reviews?):\s*(\d+)'
            ]
            
            for pattern in count_patterns:
                count_match = re.search(pattern, page_text, re.IGNORECASE)
                if count_match:
                    total_feedback = count_match.group(1)
                    break
        
        logger.info(f"User {username} has {total_feedback} total feedback entries")
        
        page_count = 0
        collected_feedback = 0
        
        while collected_feedback < max_feedback:
            page_count += 1
            logger.info(f"Scraping page {page_count} for user {username}...")
            
            time.sleep(3)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            page_feedback = scrape_feedback_page(driver, soup, username)
            
            if page_feedback:
                # Limit feedback to requested amount
                remaining_needed = max_feedback - collected_feedback
                page_feedback = page_feedback[:remaining_needed]
                
                feedback_data.extend(page_feedback)
                collected_feedback += len(page_feedback)
                logger.info(f"Page {page_count}: Found {len(page_feedback)} feedback entries. Total: {collected_feedback}")
                
                if collected_feedback >= max_feedback:
                    logger.info(f"Reached feedback limit of {max_feedback} for user {username}")
                    break
            else:
                logger.warning(f"No feedback found on page {page_count} for user {username}")
                break
            
            # Try to go to next page
            try:
                next_scripts = [
                    "return document.querySelector('a[aria-label*=\"Next\"]')",
                    "return document.querySelector('a.pagination__next')",
                    "return [...document.querySelectorAll('a')].find(a => a.textContent.toLowerCase().includes('next'))"
                ]
                
                next_button = None
                for script in next_scripts:
                    try:
                        next_button = driver.execute_script(script)
                        if next_button and next_button.is_enabled() and next_button.is_displayed():
                            break
                        else:
                            next_button = None
                    except:
                        continue
                
                if not next_button:
                    logger.info(f"No more pages found for user {username}")
                    break
                
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(5)
                
            except Exception as e:
                logger.info(f"Pagination ended for user {username}: {str(e)}")
                break
            
            if page_count >= 10:  # Safety limit per user
                logger.warning(f"Reached page limit for user {username}")
                break
        
        return feedback_data
        
    except Exception as e:
        logger.error(f"Error scraping user {username}: {str(e)}")
        return feedback_data

def scrape_comprehensive_feedback(username, max_sellers=20, max_items=100):
    """Main function to scrape feedback following the client's workflow with enhanced error handling"""
    logger = logging.getLogger(__name__)
    driver = None
    all_feedback = []
    
    try:
        driver = init_driver()
        
        print("Establishing session with eBay...")
        driver.get("https://www.ebay.com")
        time.sleep(5)
        
        # Step 1: Scrape the main user's feedback (up to 10 entries)
        print(f"\n=== Step 1: Scraping feedback for main user '{username}' ===")
        main_user_feedback = scrape_user_feedback(driver, username, max_feedback=10)
        
        if not main_user_feedback:
            logger.error(f"No feedback found for main user '{username}'")
            return []
        
        all_feedback.extend(main_user_feedback)
        logger.info(f"Collected {len(main_user_feedback)} feedback entries from main user")
        
        # Step 2: Extract seller usernames from the main user's feedback
        print(f"\n=== Step 2: Extracting seller usernames ===")
        sellers = extract_sellers_from_feedback(main_user_feedback, limit=max_sellers)
        logger.info(f"Found {len(sellers)} unique sellers: {sellers[:5]}{'...' if len(sellers) > 5 else ''}")
        
        # Step 3: Scrape feedback from each seller (up to 20 sellers)
        print(f"\n=== Step 3: Scraping feedback from {len(sellers)} sellers ===")
        
        sellers_processed = 0
        for seller in sellers:
            if len(all_feedback) >= max_items:
                logger.info(f"Reached maximum items limit of {max_items}")
                break
            
            if sellers_processed >= max_sellers:
                logger.info(f"Reached maximum sellers limit of {max_sellers}")
                break
            
            try:
                remaining_items = max_items - len(all_feedback)
                feedback_per_seller = min(10, remaining_items)  # Up to 10 per seller or remaining items
                
                print(f"\nScraping seller {sellers_processed + 1}/{len(sellers)}: '{seller}' (up to {feedback_per_seller} items)")
                
                seller_feedback = scrape_user_feedback(driver, seller, max_feedback=feedback_per_seller)
                
                if seller_feedback:
                    all_feedback.extend(seller_feedback)
                    logger.info(f"Collected {len(seller_feedback)} feedback entries from seller '{seller}'. Total: {len(all_feedback)}")
                else:
                    logger.warning(f"No feedback found for seller '{seller}'")
                
                sellers_processed += 1
                
                import random
                delay = random.uniform(5, 12)
                print(f"[DEBUG] Waiting {delay:.1f} seconds before next seller...")
                time.sleep(delay)
                
            except Exception as e:
                logger.error(f"Error scraping seller '{seller}': {str(e)}")
                continue
        
        logger.info(f"Comprehensive scraping completed. Total feedback entries: {len(all_feedback)}")
        logger.info(f"Processed {sellers_processed} sellers from {len(sellers)} found sellers")
        
        return all_feedback
        
    except Exception as e:
        logger.error(f"Error during comprehensive scraping: {str(e)}")
        return all_feedback
        
    finally:
        if driver:
            time.sleep(3)
            driver.quit()

def save_to_files(data, username):
    """Save scraped data to Excel and CSV files"""
    logger = logging.getLogger(__name__)
    
    try:
        os.makedirs('data', exist_ok=True)
        
        if not data:
            logger.warning("No data to save")
            return None, None
        
        df = pd.DataFrame(data)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"data/feedback_{username}_{timestamp}.csv"
        excel_filename = f"data/feedback_{username}_{timestamp}.xlsx"
        
        df.to_csv(csv_filename, index=False, encoding='utf-8')
        logger.info(f"Data saved to CSV: {csv_filename}")
        
        df.to_excel(excel_filename, index=False, engine='openpyxl')
        logger.info(f"Data saved to Excel: {excel_filename}")
        
        return csv_filename, excel_filename
        
    except Exception as e:
        logger.error(f"Error saving files: {str(e)}")
        return None, None

def main():
    """Main execution function with enhanced workflow"""
    logger = setup_logging()
    logger.info("eBay Comprehensive Feedback Scraper started")
    
    try:
        print("=== eBay Comprehensive Feedback Scraper ===")
        print("This scraper will:")
        print("1. Scrape feedback for the main user (up to 10 entries)")
        print("2. Extract seller usernames from that feedback")
        print("3. Scrape feedback from each seller (up to 20 sellers)")
        print("4. Collect up to 100 total feedback items")
        print()
        print("⚠️  Note: If eBay shows captcha/verification, the scraper will pause")
        print("   and provide instructions on how to proceed.")
        print()
        
        username = input("Enter eBay username: ").strip()
        
        if not username:
            print("Error: Username cannot be empty")
            return
        
        max_sellers_input = input("Enter max sellers to scrape (default 20): ").strip()
        max_sellers = 20
        if max_sellers_input:
            try:
                max_sellers = int(max_sellers_input)
                if max_sellers <= 0:
                    print("Error: Number of sellers must be positive")
                    return
            except ValueError:
                print("Error: Invalid number of sellers, using default (20)")
        
        max_items_input = input("Enter max total items to collect (default 100): ").strip()
        max_items = 100
        if max_items_input:
            try:
                max_items = int(max_items_input)
                if max_items <= 0:
                    print("Error: Number of items must be positive")
                    return
            except ValueError:
                print("Error: Invalid number of items, using default (100)")
        
        print(f"\nStarting comprehensive scraping for '{username}'...")
        print(f"Max sellers: {max_sellers}, Max total items: {max_items}")
        
        feedback_data = scrape_comprehensive_feedback(username, max_sellers, max_items)
        
        if not feedback_data:
            print("No feedback data found. Please check the username and try again.")
            return
        
        print(f"\nExporting {len(feedback_data)} feedback entries...")
        csv_file, excel_file = save_to_files(feedback_data, username)
        
        if csv_file and excel_file:
            print("\n=== Export Completed ===")
            print(f"CSV file saved at: {csv_file}")
            print(f"Excel file saved at: {excel_file}")
            print(f"Total feedback entries: {len(feedback_data)}")
            
            # Show summary statistics
            df = pd.DataFrame(feedback_data)
            unique_users = df['Source User'].nunique()
            unique_sellers = df['Seller/Buyer Username'].nunique()
            
            print(f"\n=== Summary Statistics ===")
            print(f"Unique source users: {unique_users}")
            print(f"Unique sellers/buyers found: {unique_sellers}")
            print(f"Rating distribution:")
            if 'Rating' in df.columns:
                rating_counts = df['Rating'].value_counts()
                for rating, count in rating_counts.items():
                    print(f"  {rating}: {count}")
        else:
            print("Error: Failed to save files")
            
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
        logger.info("Scraping interrupted by user")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        logger.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()
