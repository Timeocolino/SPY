#!/usr/bin/env python3
"""Search for a username across many sites and output results to a PDF.

Usage:
    python username_search.py <username> [--output results.pdf]

The script loads a list of site URL templates where "{username}" will be replaced.
Only sites that return a non-404 response are included in the output PDF.
"""

import argparse
import random
import requests
import string
import sys
from urllib.parse import unquote, urlparse
from fpdf import FPDF

# default list of sites (used if an external file isn't provided or can't be read)
# users can supply a file with one template per line. Lines starting with '#' or blank
# lines are ignored. Each template must include the literal "{username}".
DEFAULT_SITE_TEMPLATES = [
    "https://github.com/{username}",
    "https://twitter.com/{username}",
    "https://www.instagram.com/{username}",
    "https://www.reddit.com/user/{username}",
    "https://www.facebook.com/{username}",
]

NOT_FOUND_MARKERS = [
    "not found",
    "page not found",
    "user not found",
    "profile not found",
    "account doesn't exist",
    "doesn't exist",
    "n'existe pas",
    "introuvable",
    "404",
]


def check_username(username: str, template: str, timeout: float = 5.0) -> bool:
    url = template.format(username=username)
    try:
        resp = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (SPY username checker)"},
        )

        # Keep only successful pages. This avoids false positives on 403/429/500.
        if resp.status_code != 200:
            return False

        username_l = username.lower()
        final_url = unquote(resp.url).lower()

        # Redirected to generic/login pages -> usually not a real profile hit.
        redirect_failure_markers = [
            "/login",
            "/signin",
            "/sign-in",
            "/signup",
            "/sign-up",
            "/register",
            "/join",
            "/auth",
            "/account/login",
            "/accounts/login",
            "/users/sign_in",
            "/explore",
            "/search",
        ]
        if any(marker in final_url for marker in redirect_failure_markers):
            return False

        # Some sites return HTTP 200 with a "user not found" page.
        if any(token in final_url for token in ["/404", "not-found", "not_found", "missing"]):
            return False

        # If the final URL no longer contains the requested username, reject.
        # This catches many silent redirects to home pages.
        if username_l not in final_url:
            return False

        body = resp.text[:30000].lower()
        if any(marker in body for marker in NOT_FOUND_MARKERS):
            return False

        # Site-specific anti false-positive rules.
        host = urlparse(template).netloc.lower()
        if "hackerrank.com" in host:
            # Valid public profiles are on /profile/<username>.
            if "/profile/" not in final_url:
                return False
            # Generic landing pages often use this title/description while still returning 200.
            if "programming problems and competitions :: hackerrank" in body:
                return False
            if "join over 28 million developers in solving code challenges" in body:
                return False

        # Extra strictness: page content should reference the username.
        if username_l not in body and f"@{username_l}" not in body:
            return False

        return True
    except requests.RequestException:
        return False


def make_control_username(length: int = 24) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


def load_templates(path: str) -> list:
    """Read URL templates from a file.

    Returns a list of non-empty, non-comment lines. If the file cannot be
    opened, falls back to ``DEFAULT_SITE_TEMPLATES`` and prints a warning.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = []
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "{username}" not in line:
                    print(f"warning: skipping invalid template (no {{username}}): {line}")
                    continue
                lines.append(line)
            if lines:
                return lines
            else:
                print(f"warning: {path} contained no valid templates, using defaults")
    except FileNotFoundError:
        print(f"warning: sites file {path} not found; using default list")
    except Exception as e:
        print(f"warning: failed to read {path}: {e}; using default list")
    return DEFAULT_SITE_TEMPLATES.copy()


def generate_pdf(results: list, output_path: str) -> None:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Search results", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", size=12)
    for _, url in results:
        pdf.multi_cell(0, 10, url)
        pdf.ln(1)
    pdf.output(output_path)


def main():
    parser = argparse.ArgumentParser(description="Search username across many sites")
    parser.add_argument("username", help="the username to search for")
    parser.add_argument("--output", "-o", default="results.pdf", help="PDF output file")
    parser.add_argument(
        "--sites-file",
        "-s",
        default="site.txt",
        help="path to a file containing URL templates (one per line).",
    )
    args = parser.parse_args()
    username = args.username.strip()
    if not username:
        print("Please provide a non-empty username.")
        sys.exit(1)

    # load templates from file
    site_file = args.sites_file
    templates = load_templates(site_file)
    control_username = make_control_username()

    results = []
    for template in templates:
        # If a random username is "found" too, this template is unreliable.
        if check_username(control_username, template):
            print(f"Skipping unreliable template: {template}")
            continue

        if check_username(username, template):
            results.append((template, template.format(username=username)))
            print(f"Found on: {template.format(username=username)}")
        else:
            print(f"Not found on: {template.format(username=username)}")
    if results:
        generate_pdf(results, args.output)
        print(f"Results written to {args.output}")
    else:
        print("No results to write.")


if __name__ == "__main__":
    main()
