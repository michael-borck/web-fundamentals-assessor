import time
import argparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import os

class ChatGPTScraper:
    def __init__(self, headless=True):
        """
        Initialize the ChatGPT scraper.
        
        Args:
            headless: Whether to run in headless mode
        """
        self.headless = headless
        self.driver = None
    
    def setup_driver(self):
        """Set up the Chrome WebDriver with appropriate options."""
        try:
            options = Options()
            
            if self.headless:
                options.add_argument('--headless=new')
            
            # Add additional options to make headless Chrome more similar to regular Chrome
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--start-maximized')
            options.add_argument('--remote-debugging-port=9222')  # This can help with detection bypass
            
            # Add user agent
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36')
            
            # Disable automation flags
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Create the WebDriver instance
            self.driver = webdriver.Chrome(options=options)
            
            # Set window size explicitly (even in headless mode)
            self.driver.set_window_size(1920, 1080)
            
            # Execute CDP commands to prevent detection
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
            })
            
            # Execute JavaScript to prevent detection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return True
        
        except Exception as e:
            print(f"Error setting up WebDriver: {e}")
            return False
    
    def extract_conversation(self, share_url, output_file=None):
        """
        Extract the conversation from a ChatGPT share URL.
        
        Args:
            share_url: The ChatGPT share URL
            output_file: The file to save the conversation to (optional)
            
        Returns:
            The conversation as a dictionary
        """
        if not self.driver:
            if not self.setup_driver():
                return None
        
        try:
            print(f"Opening URL: {share_url}")
            self.driver.get(share_url)
            
            # Wait for page to load (adjust timeout as needed)
            time.sleep(5)
            
            # Try different selectors that might contain the conversation
            possible_selectors = [
                ".flex.flex-col.pb-9.text-sm",
                ".flex.flex-col.items-center",
                "main .flex-col.gap-2",
                ".prose"
            ]
            
            # Try each selector
            for selector in possible_selectors:
                try:
                    # Wait for the element to appear
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    print(f"Found matching element with selector: {selector}")
                    break
                except:
                    continue
            
            # Save screenshot for debugging
            self.driver.save_screenshot('page_screenshot.png')
            print(f"Saved screenshot to page_screenshot.png")
            
            # Extract conversation
            conversation = self._extract_messages()
            
            # If no messages were extracted, get the page source
            if not conversation.get('messages'):
                page_source = self.driver.page_source
                with open('page_source.html', 'w', encoding='utf-8') as f:
                    f.write(page_source)
                print(f"Saved page source to page_source.html")
                
                # Try a more general approach to find conversation
                conversation = self._extract_messages_from_source(page_source)
            
            # Save to file if specified
            if output_file and conversation.get('messages'):
                self._save_conversation(conversation, output_file)
            
            return conversation
        
        except Exception as e:
            print(f"Error extracting conversation: {e}")
            # Save page source for debugging
            try:
                page_source = self.driver.page_source
                with open('error_page_source.html', 'w', encoding='utf-8') as f:
                    f.write(page_source)
                print(f"Saved error page source to error_page_source.html")
            except:
                pass
            return None
        
        finally:
            # Close the browser
            if self.driver:
                self.driver.quit()
                self.driver = None
    
    def _extract_messages(self):
        """Extract all messages from the loaded conversation."""
        conversation = []
        
        try:
            # Try multiple selectors for message elements
            selectors = [
                ".flex.flex-col.items-start.gap-4.whitespace-pre-wrap",
                ".markdown.prose",
                ".chat-message .message-content",
                ".message"
            ]
            
            message_elements = []
            for selector in selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    message_elements = elements
                    print(f"Found {len(elements)} messages with selector: {selector}")
                    break
            
            if not message_elements:
                print("Could not find message elements with predefined selectors.")
                # Try to get all text paragraphs as a fallback
                message_elements = self.driver.find_elements(By.TAG_NAME, "p")
                print(f"Found {len(message_elements)} paragraph elements as fallback")
            
            for i, message in enumerate(message_elements):
                # Determine if this is a user or assistant message
                # This is a heuristic and might need adjustment
                role = "user" if i % 2 == 0 else "assistant"
                
                # Extract the text content
                text_content = message.text.strip()
                
                if text_content:
                    # Add to conversation
                    conversation.append({
                        "role": role,
                        "content": text_content
                    })
            
            return {
                "messages": conversation,
                "metadata": {
                    "url": self.driver.current_url,
                    "title": self.driver.title,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                }
            }
        
        except Exception as e:
            print(f"Error parsing messages: {e}")
            
            # Save the HTML source for manual inspection
            page_source = self.driver.page_source
            with open('message_extraction_error.html', 'w', encoding='utf-8') as f:
                f.write(page_source)
            print(f"Saved HTML source to message_extraction_error.html")
            
            return {
                "messages": [],
                "metadata": {
                    "url": self.driver.current_url,
                    "title": self.driver.title,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                }
            }
    
    def _extract_messages_from_source(self, page_source):
        """Try to extract messages from the page source directly."""
        # This is a fallback method that tries to find conversation patterns in the HTML
        # You might need to adjust this based on the actual structure
        
        conversation = []
        
        try:
            # Look for typical patterns that might indicate messages
            # This is very heuristic and might need adjustment
            
            # Save to file first for investigation
            with open('extracted_source.html', 'w', encoding='utf-8') as f:
                f.write(page_source)
            
            # Check if we can find user/assistant patterns
            import re
            
            # Try to find user messages
            user_messages = re.findall(r'<div[^>]*?role="user"[^>]*?>(.*?)</div>', page_source, re.DOTALL)
            assistant_messages = re.findall(r'<div[^>]*?role="assistant"[^>]*?>(.*?)</div>', page_source, re.DOTALL)
            
            # If we found structured messages
            if user_messages and assistant_messages:
                # Interleave them (assuming they alternate)
                for i in range(max(len(user_messages), len(assistant_messages))):
                    if i < len(user_messages):
                        # Clean up HTML tags
                        content = re.sub(r'<[^>]+>', ' ', user_messages[i]).strip()
                        conversation.append({
                            "role": "user",
                            "content": content
                        })
                    
                    if i < len(assistant_messages):
                        # Clean up HTML tags
                        content = re.sub(r'<[^>]+>', ' ', assistant_messages[i]).strip()
                        conversation.append({
                            "role": "assistant",
                            "content": content
                        })
        
        except Exception as e:
            print(f"Error extracting messages from source: {e}")
        
        return {
            "messages": conversation,
            "metadata": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "extraction_method": "regex from source"
            }
        }
    
    def _save_conversation(self, conversation, output_file):
        """Save the conversation to a file."""
        try:
            output_format = output_file.split('.')[-1].lower()
            
            if output_format == 'json':
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(conversation, f, ensure_ascii=False, indent=2)
            
            elif output_format == 'txt':
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(f"ChatGPT Conversation\n")
                    f.write(f"URL: {conversation['metadata']['url']}\n")
                    f.write(f"Extracted: {conversation['metadata']['timestamp']}\n\n")
                    
                    for msg in conversation.get('messages', []):
                        role = msg['role'].upper()
                        content = msg['content']
                        f.write(f"[{role}]\n{content}\n\n")
            
            else:
                # Default to txt format
                output_file = output_file if '.' in output_file else output_file + '.txt'
                self._save_conversation(conversation, output_file)
            
            print(f"Conversation saved to {output_file}")
            return True
        
        except Exception as e:
            print(f"Error saving conversation: {e}")
            return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract conversation from a ChatGPT share link')
    parser.add_argument('url', help='The ChatGPT share URL')
    parser.add_argument('--output', '-o', help='Output file (default: conversation.txt)')
    parser.add_argument('--no-headless', action='store_true', help='Run in non-headless mode (shows browser)')
    
    args = parser.parse_args()
    
    output_file = args.output or 'conversation.txt'
    headless = not args.no_headless
    
    scraper = ChatGPTScraper(headless=headless)
    conversation = scraper.extract_conversation(args.url, output_file)
    
    if not conversation or not conversation.get('messages'):
        print("Failed to extract conversation or no messages found")
        print("Try running with --no-headless flag to see what's happening")
    else:
        print(f"Successfully extracted {len(conversation.get('messages', []))} messages")


