import os
import argparse
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.common.by import By
    from selenium.common.exceptions import WebDriverException
except ImportError:
    print("Error: Selenium is not installed. Please install it with: pip install selenium")
    exit(1)


class HtmlScreenshotter:
    def __init__(self, output_dir="screenshots", device_sizes=None, browser_type="chrome"):
        """
        Initialize the HTML screenshot tool.
        
        Args:
            output_dir: Directory to save screenshots
            device_sizes: Dictionary mapping device names to (width, height) tuples
            browser_type: Type of browser to use ('chrome' or 'firefox')
        """
        self.output_dir = output_dir
        
        # Default device sizes if none provided
        self.device_sizes = device_sizes or {
            "desktop": (1366, 768),
            "mobile": (375, 812)  # iPhone X dimensions
        }
        
        self.visited_urls = set()
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize browsers for each device size
        self.browsers = {}
        
        try:
            for device_name, size in self.device_sizes.items():
                print(f"Initializing {device_name} browser ({size[0]}x{size[1]})...")
                
                if browser_type.lower() == "firefox":
                    # Firefox options
                    options = FirefoxOptions()
                    options.add_argument("--headless")
                    options.add_argument(f"--width={size[0]}")
                    options.add_argument(f"--height={size[1]}")
                    
                    browser = webdriver.Firefox(options=options)
                    
                else:  # Default to Chrome
                    # Chrome options
                    options = ChromeOptions()
                    options.add_argument("--headless=new")  # Updated headless syntax
                    options.add_argument("--disable-gpu")
                    options.add_argument(f"--window-size={size[0]},{size[1]}")
                    options.add_argument("--hide-scrollbars")
                    
                    # For mobile emulation
                    if device_name == "mobile":
                        mobile_emulation = {
                            "deviceMetrics": {
                                "width": size[0],
                                "height": size[1],
                                "pixelRatio": 3.0
                            },
                            "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
                        }
                        options.add_experimental_option("mobileEmulation", mobile_emulation)
                    
                    try:
                        browser = webdriver.Chrome(options=options)
                    except Exception as e:
                        print(f"Warning: {e}")
                        print("Trying to specify Chrome paths explicitly...")
                        
                        # Try to locate Chrome binary
                        chrome_binary = None
                        possible_chrome_paths = [
                            "/usr/bin/google-chrome",
                            "/usr/bin/google-chrome-stable",
                            "/usr/bin/chromium-browser",
                            "/usr/bin/chromium"
                        ]
                        
                        for path in possible_chrome_paths:
                            if os.path.exists(path):
                                chrome_binary = path
                                break
                        
                        if chrome_binary:
                            print(f"Found Chrome at: {chrome_binary}")
                            options.binary_location = chrome_binary
                            browser = webdriver.Chrome(options=options)
                        else:
                            raise Exception("Could not find Chrome or Chromium.")
                
                browser.set_window_size(*size)
                self.browsers[device_name] = browser
                print(f"Successfully initialized {browser_type} browser for {device_name}")
                
        except Exception as e:
            print(f"Error initializing browsers: {e}")
            self.cleanup()
            raise
    
    def cleanup(self):
        """Clean up all browser resources."""
        for device_name, browser in self.browsers.items():
            try:
                print(f"Closing {device_name} browser...")
                browser.quit()
            except:
                pass
    
    def __del__(self):
        """Destructor to clean up resources when object is destroyed."""
        self.cleanup()
    
    def take_screenshots(self, url, output_base_filename=None):
        """
        Take screenshots of the given URL with all device sizes and save them to files.
        
        Args:
            url: URL of the page to screenshot
            output_base_filename: Optional base filename for the screenshots
        
        Returns:
            Dictionary mapping device names to screenshot file paths
        """
        if url in self.visited_urls:
            print(f"Already visited {url}, skipping")
            return None
        
        self.visited_urls.add(url)
        
        # Generate output base filename if not provided
        if not output_base_filename:
            parsed_url = urlparse(url)
            path_parts = parsed_url.path.strip('/').split('/')
            if path_parts and path_parts[-1]:
                filename = path_parts[-1]
            else:
                filename = "index.html"
            
            if '.' not in filename:
                filename += ".html"
            
            # Create subdirectories based on URL path
            subdirs = '/'.join(path_parts[:-1])
            if subdirs:
                save_dir = os.path.join(self.output_dir, subdirs)
                os.makedirs(save_dir, exist_ok=True)
                output_base_filename = os.path.join(save_dir, os.path.splitext(filename)[0])
            else:
                output_base_filename = os.path.join(self.output_dir, os.path.splitext(filename)[0])
        
        screenshots = {}
        print(f"Taking screenshots of {url}")
        
        for device_name, browser in self.browsers.items():
            try:
                output_filename = f"{output_base_filename}.{device_name}.png"
                print(f"  - {device_name} -> {output_filename}")
                
                browser.get(url)
                
                # Wait for page to load fully
                time.sleep(1.5)  # Simple wait, increase for slower connections
                
                # Get the full height of the page for desktop screenshots
                if device_name == "desktop":
                    # Scroll to get the full page height
                    scroll_height = browser.execute_script("return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);")
                    
                    # Check if we should take a full-page screenshot
                    if scroll_height > self.device_sizes[device_name][1]:
                        # Option 1: Set window size to match page height (works for most pages)
                        original_size = browser.get_window_size()
                        browser.set_window_size(self.device_sizes[device_name][0], scroll_height)
                        time.sleep(0.5)  # Wait for resize
                        browser.save_screenshot(output_filename)
                        browser.set_window_size(original_size['width'], original_size['height'])
                        
                        # If that didn't work, we could also try:
                        # Option 2: Use JavaScript to take a full-page screenshot
                        # But this requires more complex logic and libraries
                    else:
                        browser.save_screenshot(output_filename)
                else:
                    # For mobile, just take the viewport screenshot
                    browser.save_screenshot(output_filename)
                
                screenshots[device_name] = output_filename
            except WebDriverException as e:
                print(f"Error capturing {url} on {device_name}: {e}")
        
        return screenshots if screenshots else None
    
    def extract_links(self, base_url, device_name="desktop"):
        """
        Extract all links from the current page.
        
        Args:
            base_url: Base URL to resolve relative links
            device_name: Device browser to use for extracting links
        
        Returns:
            List of absolute URLs found on the page
        """
        links = []
        try:
            browser = self.browsers[device_name]
            elements = browser.find_elements(By.TAG_NAME, "a")
            for element in elements:
                href = element.get_attribute("href")
                if href and not href.startswith(("javascript:", "mailto:", "tel:", "#")):
                    absolute_url = urljoin(base_url, href)
                    
                    # Filter out URLs outside the base domain
                    if urlparse(absolute_url).netloc == urlparse(base_url).netloc:
                        links.append(absolute_url)
        except Exception as e:
            print(f"Error extracting links: {e}")
        
        return links
    
    def crawl_and_screenshot(self, start_url, max_pages=None):
        """
        Crawl a website starting from a URL and take screenshots of each page.
        
        Args:
            start_url: Starting URL for crawling
            max_pages: Maximum number of pages to process
        
        Returns:
            Dictionary mapping URLs to screenshot file paths by device
        """
        to_visit = [start_url]
        screenshots = {}
        
        while to_visit and (max_pages is None or len(screenshots) < max_pages):
            url = to_visit.pop(0)
            
            if url in self.visited_urls:
                continue
            
            # Take screenshots
            screenshot_paths = self.take_screenshots(url)
            if screenshot_paths:
                screenshots[url] = screenshot_paths
                
                # Extract links from the page and queue them
                links = self.extract_links(url)
                for link in links:
                    if link not in self.visited_urls and link not in to_visit:
                        to_visit.append(link)
        
        return screenshots
    
    def process_directory(self, directory, server_url=None):
        """
        Find all HTML files in a directory and take screenshots.
        
        Args:
            directory: Directory containing HTML files
            server_url: Optional base URL if files are served via a web server
        
        Returns:
            Dictionary mapping file paths to screenshot paths by device
        """
        html_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(('.html', '.htm')):
                    html_files.append(os.path.join(root, file))
        
        screenshots = {}
        for html_file in html_files:
            if server_url:
                # Get relative path from the base directory
                rel_path = os.path.relpath(html_file, directory)
                url = urljoin(server_url, rel_path)
                
                # Take screenshots using the URL
                output_filename = os.path.splitext(rel_path)[0]
                output_path = os.path.join(self.output_dir, output_filename)
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                screenshot_paths = self.take_screenshots(url, output_path)
                if screenshot_paths:
                    screenshots[html_file] = screenshot_paths
            else:
                # Use file:// protocol to open local files
                url = f"file://{os.path.abspath(html_file)}"
                
                # Generate output path that maintains directory structure
                rel_path = os.path.relpath(html_file, directory)
                output_filename = os.path.splitext(rel_path)[0]
                output_path = os.path.join(self.output_dir, output_filename)
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                screenshot_paths = self.take_screenshots(url, output_path)
                if screenshot_paths:
                    screenshots[html_file] = screenshot_paths
        
        return screenshots


def create_index_html(screenshots, output_dir):
    """
    Create an HTML index page with screenshots.
    
    Args:
        screenshots: Dictionary mapping URLs/file paths to screenshot paths by device
        output_dir: Output directory for the index file
    """
    index_path = os.path.join(output_dir, "screenshot_index.html")
    
    with open(index_path, 'w') as f:
        f.write('<!DOCTYPE html>\n')
        f.write('<html>\n<head>\n')
        f.write('<title>Website Screenshots</title>\n')
        f.write('<meta name="viewport" content="width=device-width, initial-scale=1.0">\n')
        f.write('<style>\n')
        f.write('body { font-family: Arial, sans-serif; margin: 20px; }\n')
        f.write('.screenshot { margin-bottom: 40px; border-bottom: 1px solid #ccc; padding-bottom: 20px; }\n')
        f.write('.device-views { display: flex; flex-wrap: wrap; gap: 20px; margin-top: 10px; }\n')
        f.write('.device-view { flex: 1; min-width: 300px; }\n')
        f.write('.device-view img { max-width: 100%; border: 1px solid #ddd; }\n')
        f.write('.device-label { font-weight: bold; margin-bottom: 5px; }\n')
        f.write('h1, h2 { color: #333; }\n')
        f.write('h2 { word-break: break-all; }\n')
        f.write('</style>\n</head>\n<body>\n')
        f.write('<h1>Website Screenshots</h1>\n')
        
        for url, devices in screenshots.items():
            f.write(f'<div class="screenshot">\n')
            f.write(f'  <h2>{url}</h2>\n')
            f.write(f'  <div class="device-views">\n')
            
            for device, screenshot_path in devices.items():
                rel_path = os.path.relpath(screenshot_path, output_dir)
                f.write(f'    <div class="device-view">\n')
                f.write(f'      <div class="device-label">{device.capitalize()}</div>\n')
                f.write(f'      <a href="{rel_path}" target="_blank">\n')
                f.write(f'        <img src="{rel_path}" alt="{url} - {device}" loading="lazy">\n')
                f.write(f'      </a>\n')
                f.write(f'    </div>\n')
            
            f.write(f'  </div>\n')
            f.write(f'</div>\n')
        
        f.write('</body>\n</html>')
    
    print(f"Created screenshot index at {index_path}")
    
    return index_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Take screenshots of HTML pages on different devices')
    parser.add_argument('--directory', '-d', help='Directory containing HTML files')
    parser.add_argument('--url', '-u', help='Starting URL for crawling')
    parser.add_argument('--server', '-s', help='Base server URL for directory mode (e.g., http://localhost:8000/)')
    parser.add_argument('--output', '-o', default='screenshots', help='Output directory for screenshots')
    parser.add_argument('--max-pages', '-m', type=int, help='Maximum number of pages to process')
    parser.add_argument('--browser', '-b', default='chrome', choices=['chrome', 'firefox'],
                        help='Browser to use for capturing screenshots (chrome or firefox)')
    parser.add_argument('--desktop-width', type=int, default=1366, help='Desktop viewport width (default: 1366)')
    parser.add_argument('--desktop-height', type=int, default=768, help='Desktop viewport height (default: 768)')
    parser.add_argument('--mobile-width', type=int, default=375, help='Mobile viewport width (default: 375 - iPhone X)')
    parser.add_argument('--mobile-height', type=int, default=812, help='Mobile viewport height (default: 812 - iPhone X)')
    parser.add_argument('--tablet', action='store_true', help='Also capture tablet screenshots')
    parser.add_argument('--tablet-width', type=int, default=768, help='Tablet viewport width (default: 768 - iPad)')
    parser.add_argument('--tablet-height', type=int, default=1024, help='Tablet viewport height (default: 1024 - iPad)')
    
    args = parser.parse_args()
    
    if not args.directory and not args.url:
        parser.error("Either --directory or --url must be specified")
    
    # Setup device sizes
    device_sizes = {
        "desktop": (args.desktop_width, args.desktop_height),
        "mobile": (args.mobile_width, args.mobile_height)
    }
    
    if args.tablet:
        device_sizes["tablet"] = (args.tablet_width, args.tablet_height)
    
    try:
        # Create the screenshotter
        screenshotter = HtmlScreenshotter(args.output, device_sizes, args.browser)
        
        if args.url:
            # Crawl mode
            print(f"Crawling and taking screenshots starting from {args.url}")
            screenshots = screenshotter.crawl_and_screenshot(args.url, args.max_pages)
            print(f"Took screenshots of {len(screenshots)} pages")
        elif args.directory:
            # Directory mode
            print(f"Processing HTML files in {args.directory}")
            screenshots = screenshotter.process_directory(args.directory, args.server)
            print(f"Took screenshots of {len(screenshots)} HTML files")
        
        # Create an index HTML file of all screenshots
        index_path = create_index_html(screenshots, args.output)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Make sure browsers are closed
        if 'screenshotter' in locals():
            screenshotter.cleanup()
