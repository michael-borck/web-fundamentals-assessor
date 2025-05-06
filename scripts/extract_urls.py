import os
import re
import argparse
import chardet
import validators

def is_text_file(file_path, blocksize=512):
    with open(file_path, 'rb') as f:
        chunk = f.read(blocksize)
    if not chunk:
        return False
    encoding = chardet.detect(chunk)['encoding']
    return encoding is not None

def extract_urls(file_path):
    patterns = [
        r'\[.*?\]\((https?://[^\)]+)\)',  # markdown inline links
        r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(/[^\s]*)?'  # raw URLs
    ]
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        urls = []
        for pattern in patterns:
            urls.extend(re.findall(pattern, content))
        return [u for u in set(urls) if validators.url(u)]
    except Exception as e:
        print(f"[!] Could not process {file_path}: {e}")
        return []

def process_path(path, output_file):
    all_urls = set()

    if os.path.isfile(path):
        urls = extract_urls(path)
        all_urls.update(urls)
    elif os.path.isdir(path):
        for root, _, files in os.walk(path):
            for name in files:
                file_path = os.path.join(root, name)
                if is_text_file(file_path):
                    urls = extract_urls(file_path)
                    all_urls.update(urls)
                else:
                    print(f"[i] Skipping binary file: {file_path}")
    else:
        print(f"[!] Invalid path: {path}")
        return

    with open(output_file, 'w', encoding='utf-8') as f:
        for url in sorted(all_urls):
            f.write(url + '\n')

    print(f"[✓] Saved {len(all_urls)} URLs to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Extract URLs from a text file or folder")
    parser.add_argument("path", help="Path to a file or folder")
    parser.add_argument("--output", default="urls.txt", help="Output file name")
    args = parser.parse_args()

    process_path(args.path, args.output)

if __name__ == "__main__":
    main()

