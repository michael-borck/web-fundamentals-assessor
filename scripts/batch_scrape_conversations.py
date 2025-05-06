import os
import argparse
import re
import time

# Attempt to import ChatGPTScraper from scrape_chat.py
# This assumes batch_scrape_conversations.py is in the same directory as scrape_chat.py (e.g., 'scripts/')
try:
    from scrape_chat import ChatGPTScraper
except ImportError:
    print("Error: Could not import ChatGPTScraper from scrape_chat.py.")
    print("Ensure batch_scrape_conversations.py is in the same directory as scrape_chat.py (e.g., 'scripts/').")
    print("Alternatively, ensure the 'scripts' directory is in your PYTHONPATH.")
    exit(1)

def sanitize_filename_component(url):
    """
    Creates a somewhat readable and safe filename component from a URL.
    """
    try:
        # Remove http(s)://
        name = re.sub(r'^https?://', '', url)
        # Remove www.
        name = re.sub(r'^www\.', '', name)
        # Replace non-alphanumeric characters (except dots and hyphens that are not leading/trailing) with underscores
        name = re.sub(r'[^\w.-]', '_', name)
        # Remove leading/trailing underscores/dots/hyphens
        name = name.strip('_.')
        # Truncate if too long
        return name[:50]  # Limit length
    except Exception:
        return "chat" # Fallback

def batch_scrape(url_file_path, output_dir, output_format="txt", headless=True):
    """
    Reads URLs from a file, scrapes each conversation, and saves them.

    Args:
        url_file_path (str): Path to the text file containing URLs (one per line).
        output_dir (str): Directory to save the scraped conversation files.
        output_format (str): "txt" or "json" for the output file format.
        headless (bool): Whether to run the scraper in headless mode.
    """
    if not os.path.exists(url_file_path):
        print(f"Error: URL file not found at {url_file_path}")
        return

    os.makedirs(output_dir, exist_ok=True)
    failed_log_path = os.path.join(output_dir, "failed_scrapes.log")

    urls_to_scrape = []
    with open(url_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            url = line.strip()
            if url and re.match(r'^https?://', url): # Basic URL validation
                urls_to_scrape.append(url)
            elif url:
                print(f"Skipping invalid URL or non-HTTP/S URL: {url}")

    if not urls_to_scrape:
        print("No valid URLs found in the input file.")
        return

    print(f"Found {len(urls_to_scrape)} URLs to scrape.")
    successful_scrapes = 0
    failed_scrapes = 0

    for i, url in enumerate(urls_to_scrape):
        print(f"\nProcessing URL {i+1}/{len(urls_to_scrape)}: {url}")
        
        # Generate a somewhat unique filename based on URL or index
        # filename_base = sanitize_filename_component(url)
        # Using index to ensure uniqueness and order if URLs are very similar
        filename_base = f"scraped_conversation_{i+1}"
        output_filename = os.path.join(output_dir, f"{filename_base}.{output_format}")

        try:
            scraper = ChatGPTScraper(headless=headless)
            # The extract_conversation method in the provided scrape_chat.py
            # already handles saving the file if output_file is given.
            # It also quits the driver internally.
            conversation_data = scraper.extract_conversation(url, output_filename)

            if conversation_data and conversation_data.get('messages'):
                print(f"Successfully scraped and saved to {output_filename}")
                successful_scrapes += 1
            elif conversation_data: # Data extracted but no messages
                print(f"Extracted data from {url} but no messages found. Saved structure to {output_filename}.")
                # Consider this a partial success or failure based on requirements.
                # For now, let's count it as a success if a file was written.
                if os.path.exists(output_filename):
                     successful_scrapes += 1
                else:
                    print(f"Failed to save data for {url} even though some data was extracted.")
                    failed_scrapes += 1
                    with open(failed_log_path, 'a', encoding='utf-8') as flog:
                        flog.write(f"{url} (Extraction partially succeeded but no messages or save failed)\n")
            else:
                print(f"Failed to extract conversation from {url}.")
                failed_scrapes += 1
                with open(failed_log_path, 'a', encoding='utf-8') as flog:
                    flog.write(f"{url}\n")
        except Exception as e:
            print(f"An error occurred while processing {url}: {e}")
            failed_scrapes += 1
            with open(failed_log_path, 'a', encoding='utf-8') as flog:
                flog.write(f"{url} (Error: {e})\n")
        
        # Optional: Add a small delay between requests if scraping many URLs
        if i < len(urls_to_scrape) - 1:
            time.sleep(2) # 2-second delay

    print("\n--- Batch Scraping Summary ---")
    print(f"Total URLs processed: {len(urls_to_scrape)}")
    print(f"Successfully scraped: {successful_scrapes}")
    print(f"Failed to scrape: {failed_scrapes}")
    if failed_scrapes > 0:
        print(f"Details of failed URLs logged in: {failed_log_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch scrape AI conversations from a list of URLs.")
    parser.add_argument("url_file", help="Path to a text file containing share URLs (one URL per line).")
    parser.add_argument("output_dir", help="Directory to save the scraped conversation files.")
    parser.add_argument("--format", choices=["txt", "json"], default="txt",
                        help="Output format for scraped conversations (default: txt).")
    parser.add_argument("--no-headless", action="store_false", dest="headless",
                        help="Run the browser in non-headless mode (visible) for debugging.")
    
    args = parser.parse_args()

    batch_scrape(args.url_file, args.output_dir, args.format, args.headless)

