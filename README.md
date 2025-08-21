# eBay Feedback Scraper

An advanced Python project that scrapes eBay user feedback with intelligent multi-seller discovery, captcha handling, and comprehensive data export capabilities.

## 🚀 Features

### Core Functionality
- **Multi-Seller Discovery**: Scrapes initial user feedback, then discovers and scrapes related sellers automatically
- **Intelligent Pagination**: Automatically navigates through all feedback pages with smart detection
- **Captcha Handling**: Detects eBay security measures and provides manual solving workflow
- **Anti-Detection**: Advanced stealth measures including user agent rotation and human-like delays

### Data Collection
- **Comprehensive Data**: Extracts feedback text, ratings, dates, items, buyer/seller usernames
- **Cross-Reference Analysis**: Tracks relationships between users and sellers
- **Scalable Collection**: Collects up to 100 items across multiple sellers (configurable)
- **Smart Filtering**: Removes duplicates and validates data quality

### Export & Analysis
- **Multiple Formats**: Saves to Excel (.xlsx) and CSV (.csv) with timestamps
- **Structured Data**: Organized columns with source tracking and metadata
- **Progress Tracking**: Real-time feedback on scraping progress and statistics
- **Error Logging**: Comprehensive logging for debugging and monitoring

## 📋 Requirements

- **Python**: 3.9 or above
- **Chrome Browser**: Latest version (for Selenium WebDriver)
- **Internet Connection**: Stable connection for eBay access

## 🛠️ Installation

1. **Clone the repository:**
\`\`\`bash
git clone <repository-url>
cd ebay-feedback-scraper
\`\`\`

2. **Install dependencies:**
\`\`\`bash
pip install -r requirements.txt
\`\`\`

## 🎯 Usage

### Basic Usage
\`\`\`bash
python scraper.py
\`\`\`

### Interactive Workflow
1. **Enter Target Username**: Provide the eBay username to start scraping
2. **Set Limits**: Choose number of pages and sellers to scrape
3. **Handle Captchas**: If eBay shows verification, follow on-screen instructions
4. **Monitor Progress**: Watch real-time updates as data is collected
5. **Review Results**: Check exported files in the `data/` folder

### Advanced Configuration
The scraper automatically:
- Discovers up to 20 related sellers from initial feedback
- Scrapes up to 10 feedback entries per seller
- Implements smart delays (2-5 seconds between requests)
- Retries failed requests with exponential backoff

## 📊 Output Structure

### File Naming
- **CSV**: `feedback_{username}_{timestamp}.csv`
- **Excel**: `feedback_{username}_{timestamp}.xlsx`

### Data Columns
| Column | Description |
|--------|-------------|
| **Date** | When the feedback was left |
| **Feedback** | The complete feedback text/comment |
| **Rating** | Positive, Neutral, or Negative |
| **Item** | Product/service that was purchased |
| **Buyer Username** | Username of the feedback author |
| **Seller Username** | Username of the seller being reviewed |
| **Source User** | Original user that led to this seller discovery |

## 🏗️ Project Structure

\`\`\`
ebay-feedback-scraper/
│
├── scripts/
│   ├── scraper.py           # Main scraping engine
│   └── requirements.txt     # Python dependencies
├── data/                    # Exported data files (auto-created)
│   ├── feedback_*.csv
│   └── feedback_*.xlsx
├── logs/                    # Application logs (auto-created)
│   └── scraper.log
├── .gitignore              # Git ignore rules
└── README.md               # This documentation
\`\`\`

## 🛡️ Security & Anti-Detection

### Built-in Protections
- **Realistic User Agents**: Rotates between common browser signatures
- **Human-like Timing**: Random delays between 2-5 seconds
- **Session Management**: Maintains cookies and session state
- **Stealth Mode**: Disables automation detection features

### Captcha Handling
When eBay shows security verification:
1. **Automatic Detection**: Recognizes captcha/verification pages
2. **Manual Solving**: Pauses execution for user intervention
3. **Guided Process**: Provides clear instructions for resolution
4. **Retry Logic**: Continues scraping after successful verification

## ⚠️ Error Handling

### Robust Recovery
- **Network Issues**: Automatic retry with exponential backoff
- **Invalid Users**: Graceful handling of non-existent usernames
- **HTML Changes**: Multiple fallback selectors for element detection
- **Rate Limiting**: Respects eBay's request limits with smart delays

### Comprehensive Logging
All activities logged to `logs/scraper.log`:
- Successful page loads and data extraction
- Error conditions and recovery attempts
- Captcha encounters and resolution
- Performance metrics and timing data

## 📈 Example Output

\`\`\`
=== eBay Advanced Feedback Scraper ===
Enter eBay username: tech_store_123
Enter number of pages to scrape (default: all): 5
Enter max sellers to discover (default: 20): 10

🔍 Scraping feedback for 'tech_store_123'...
✅ Page 1: Found 25 feedback entries
✅ Page 2: Found 23 feedback entries
🔗 Discovered seller: electronics_pro_2024
🔗 Discovered seller: gadget_world_store

🔍 Scraping seller: electronics_pro_2024...
✅ Found 18 feedback entries

⚠️  Captcha detected! Please solve the verification in the browser window.
Press Enter after solving the captcha...

✅ Captcha resolved! Continuing...

📊 Final Statistics:
- Total feedback entries: 127
- Unique sellers discovered: 8
- Data quality: 98.4%

💾 Export completed:
- CSV: data/feedback_tech_store_123_20241221_143022.csv
- Excel: data/feedback_tech_store_123_20241221_143022.xlsx
\`\`\`

## ⚖️ Legal & Ethical Usage

### Important Guidelines
- **Educational Purpose**: This tool is for research and educational use only
- **Respect Terms of Service**: Ensure compliance with eBay's Terms of Service
- **Rate Limiting**: Built-in delays respect eBay's servers and bandwidth
- **Data Privacy**: Handle scraped data responsibly and ethically

### Best Practices
- Use reasonable limits (don't scrape thousands of pages)
- Implement additional delays if needed for your use case
- Respect robots.txt and website policies
- Consider reaching out to eBay for official API access for commercial use

## 🔧 Troubleshooting

### Common Issues
1. **Chrome Driver Issues**: Ensure Chrome browser is updated
2. **Captcha Loops**: Try different IP address or wait before retrying
3. **No Data Found**: Check if username exists and has public feedback
4. **Slow Performance**: Increase delays in the configuration

### Getting Help
- Check `logs/scraper.log` for detailed error information
- Ensure all dependencies are properly installed
- Verify Chrome browser compatibility
- Test with a known working eBay username first

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request with clear description

## 📄 License

This project is for educational purposes. Please ensure compliance with eBay's Terms of Service and applicable laws in your jurisdiction.
