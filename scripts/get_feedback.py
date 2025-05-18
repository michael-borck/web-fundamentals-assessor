#!/usr/bin/env python3
import os
import sys
import argparse
from openai import OpenAI

DEFAULT_SYSTEM_PROMPT = (
    "You are an experienced web-development assessor. "
    "The student has submitted a vanilla HTML/CSS/JavaScript website and saved "
    "all files (including their AI interaction log) in a single text blob, "
    "delimited by “--- Filename: … ---” markers. AI tools were permitted, "
    "and your job is to evaluate the student’s own understanding and refinement "
    "of any AI suggestions."
)

def main():
    parser = argparse.ArgumentParser(
        description="Send prompt+content to OpenAI as a web-dev assessor."
    )
    parser.add_argument(
        "prompt_file",
        help="Path to the text file containing your user prompt (e.g. prompt.txt)"
    )
    parser.add_argument(
        "content_file",
        help="Path to the text file containing the attached project files (e.g. contents.txt)"
    )
    parser.add_argument(
        "--system-file",
        help="Optional path to a file containing your system prompt; "
             "if omitted, uses the built-in assessor prompt."
    )
    parser.add_argument(
        "--model",
        default="gpt-4.1-mini-2025-04-14",
        help="Which OpenAI model to use (default: %(default)s)"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=1,
        help="Sampling temperature (default: %(default)s)"
    )
    args = parser.parse_args()

    # Load API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set in environment", file=sys.stderr)
        sys.exit(1)

    # Determine system prompt
    if args.system_file:
        try:
            with open(args.system_file, "r", encoding="utf-8") as f:
                system_prompt = f.read().strip()
        except IOError as e:
            print(f"ERROR reading --system-file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        system_prompt = DEFAULT_SYSTEM_PROMPT

    # Read user prompt and content
    try:
        with open(args.prompt_file, "r", encoding="utf-8") as f:
            user_prompt = f.read().strip()
        with open(args.content_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
    except IOError as e:
        print(f"ERROR reading input files: {e}", file=sys.stderr)
        sys.exit(1)

    # Build messages payload
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": f"{user_prompt}\n\n--- Attached content below ---\n{content}"
        }
    ]

    # Call the new v1 client
    client = OpenAI(api_key=api_key)
    try:
        resp = client.chat.completions.create(
            model=args.model,
            messages=messages,
            temperature=args.temperature
        )
    except Exception as e:
        print(f"API error: {e}", file=sys.stderr)
        sys.exit(1)

    # Print the assistant’s reply
    print(resp.choices[0].message.content.strip())


if __name__ == "__main__":
    main()


