# Advanced Web Scraper

This project is an advanced web scraper with the following capabilities:

- Complete web page content download
- CSS, JavaScript, and image extraction
- Dynamic page support using Selenium
- Automatic page crawling
- Error handling and retry mechanism
- Custom User-Agent support

## Features

- Automatic download of static and dynamic resources
- JavaScript-powered dynamic page support
- Error handling and retry mechanism
- Automatic page crawling
- Structured file storage
- Custom User-Agent support

## Prerequisites

- Python 3.7+
- Chrome Browser
- Required libraries listed in requirements.txt

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the program:
   ```bash
   python extractor_0.0.py <URL>
   ```

## Usage

### Download a Single Page
```python
from extractor import scrape_page_combined

scrape_page_combined(
    page_url="https://example.com",
    output_dir="downloaded_site",
    delay=0.5,
    wait_dynamic=2.0
)
```

### Automatic Crawling
```python
from extractor import scrape_with_crawling

scrape_with_crawling(
    start_url="https://example.com",
    output_dir="downloaded_site",
    max_pages=10
)
```

### Command Line Usage
```bash
# Download a single page
python extractor_0.0.py https://example.com

# Download with custom settings
python extractor_0.0.py https://example.com --output my_site --delay 1.0 --wait 3.0

# Automatic crawling
python extractor_0.0.py https://example.com --crawl --max-pages 20
```

## Project Structure

```
project_root/
│
├── extractor_0.0.py       # Main program file
├── requirements.txt       # Dependencies list
├── README.md             # Project documentation
├── LICENSE               # Project license
└── .gitignore           # Git ignored files
```

## Command Line Arguments

- `url`: Target page URL to scrape (required)
- `--output`, `-o`: Output directory path (default: downloaded_site)
- `--delay`, `-d`: Delay between downloads in seconds (default: 0.5)
- `--wait`, `-w`: Wait time for dynamic content in seconds (default: 2.0)
- `--crawl`, `-c`: Enable automatic crawling
- `--max-pages`, `-m`: Maximum number of pages to crawl (default: 10)
- `--user-agent`, `-u`: Custom User-Agent string

## Features in Detail

### Static Content Download
- Downloads all HTML, CSS, JavaScript files
- Extracts and downloads images
- Preserves file structure
- Handles relative and absolute URLs

### Dynamic Content Support
- Uses Selenium for JavaScript-rendered content
- Captures dynamically loaded resources
- Supports modern web applications
- Configurable wait times for dynamic content

### Error Handling
- Automatic retry mechanism
- Graceful error recovery
- Detailed error logging
- Customizable retry parameters

### Crawling Capabilities
- Automatic internal link discovery
- Domain-specific crawling
- Configurable depth and breadth
- Duplicate URL prevention

## Testing and Compatibility

### Tested Platforms
- Windows 10/11
- Linux (Ubuntu 20.04+)
- macOS (Catalina+)

### Tested WordPress Themes
Successfully tested with popular WordPress themes:
- Astra
- Divi
- Avada
- GeneratePress
- OceanWP
- Neve
- Hello Elementor
- Kadence
- Blocksy
- Sydney

### Tested Features
- ✅ Complete page download
- ✅ CSS/JS file extraction
- ✅ Image downloading
- ✅ Dynamic content handling
- ✅ Internal link crawling
- ✅ Custom User-Agent support
- ✅ Error recovery
- ✅ Resource organization

### Performance
- Average download speed: 2-3 pages per second
- Memory usage: ~100-200MB per active session
- CPU usage: 10-20% during active scraping
- Disk space: Varies based on site size (typically 10-100MB per site)

### Known Limitations
- Some JavaScript-heavy sites may require longer wait times
- Very large sites (>1000 pages) may need manual crawling configuration
- Some anti-bot measures may require custom User-Agent configuration

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

MIT License

## Developers

- [shadowhakzz]