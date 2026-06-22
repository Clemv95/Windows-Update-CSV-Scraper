from datetime import datetime
import requests
import re
from bs4 import BeautifulSoup
import csv

SOURCES = [
    {
        "url": "https://support.microsoft.com/en-us/topic/release-notes-for-hotpatch-on-windows-11-enterprise-version-25h2-0bbaa1c7-5070-41ca-a7c9-4ead79602dbf",
        "os":  "Windows 11",
        "ver": "25H2",
    },
    {
        "url": "https://support.microsoft.com/en-us/topic/release-notes-for-hotpatch-on-windows-11-enterprise-version-24h2-c0906ee6-5e62-498f-bd5a-8f4966349f3c",
        "os":  "Windows 11",
        "ver": "24H2",
    },

]


MONTH_ABBR = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}

def parse_date(text: str):
    """Return (iso, 'Month YYYY') from 'May 12, 2026' / 'May 2026'."""
    text = text.strip()
    for fmt in ("%B %d, %Y", "%B %Y"):
        try:
            dt = datetime.strptime(text, fmt)
            return dt.strftime("%Y-%m-%d"), dt.strftime("%B %Y")
        except ValueError:
            pass
    return text, ""


def detect_update_type(title: str) -> str:
    low = title.lower()
    if "out-of-band" in low or "out of band" in low:
        return "OOB"
    if "hotpatch" in low:
        return "Hotpatch"
    if "baseline" in low:
        return "Baseline"
    return "Other"


def parse_link_title(title: str, base_url: str):
    """
    Parse one sidebar link title into structured fields.

    Examples:
      'May 12, 2026—Hotpatch KB5089466 (OS Builds 26200.8390 and 26100.8390)'
      'April 14, 2026—Baseline'
      'January 13, 2026—Baseline'
      'March 10, 2026—Hotpatch KB5079420 (OS Builds 26200.7979 and 26100.7979)'
      'December 9, 2025—Hotpatch KB5072014 (OS Builds 26200.7392 and 26100.7392)'
      'September 9, 2025—Hotpatch KB5065474 (OS Build 26100.6508)'   ← single build
      'March 16, 2026—Hotpatch KB5084897 ... Out-of-band'
    """
    # Split on em-dash or regular dash variants
    parts = re.split(r'[—–-]{1,2}', title, maxsplit=1)
    if len(parts) < 2:
        return None

    raw_date = parts[0].strip()
    rest     = parts[1].strip()

    iso_date, month_year = parse_date(raw_date)
    if not iso_date or iso_date == raw_date:
        return None   # couldn't parse date → skip

    update_type = detect_update_type(title)

    # KB number
    kb_match = re.search(r"(KB\d{6,})", rest, re.IGNORECASE)
    kb = kb_match.group(1) if kb_match else ""

    # Build numbers — one or two
    builds_match = re.search(
        r"OS Builds?\s+([\d.]+)(?:\s+and\s+([\d.]+))?",
        rest, re.IGNORECASE
    )
    build_a = ""
    build_b = ""
    if builds_match:
        build_a = builds_match.group(1).strip()  # e.g. 26200.8390 or 26100.8390
        build_b = (builds_match.group(2) or "").strip()

    # Single canonical build_number (first one, or only one)
    build_number = f"10.0.{build_a}" if build_a else ""

    # Map to 25H2 / 24H2 buckets by base build prefix
    build_25h2 = ""
    build_24h2 = ""
    for b in (build_a, build_b):
        if not b:
            continue
        prefix = b.split(".")[0]
        if prefix == "26200":
            build_25h2 = f"10.0.{b}"
        elif prefix == "26100":
            build_24h2 = f"10.0.{b}"
        elif prefix == "20348":  # WS 2022
            build_24h2 = f"10.0.{b}"

    return {
        "release_date":        iso_date,
        "release_date_format": month_year,
        "update_type":         update_type,
        "kb":                  kb,
        "build_number":        build_number,
        "build_25h2":          build_25h2,
        "build_24h2":          build_24h2,
    }


# ---------------------------------------------------------------------------
# Fetcher
# ---------------------------------------------------------------------------

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )
}

def fetch(url: str) -> str:
    s = requests.Session()
    r = s.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def parse_release_page(html: str, os_name: str, version: str, page_url: str) -> list[dict]:
    """
    The release-notes index pages contain a sidebar (or main content)
    with an <ul> of links like:
      <li><a href="...">May 12, 2026—Hotpatch KB5089466 (OS Builds …)</a></li>

    We collect every link whose text matches the date—description pattern.
    """
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    seen = set()

    for a in soup.find_all("a", href=True):
        text = a.get_text(" ", strip=True)
        # Must start with a month name
        first_word = text.split()[0].lower() if text.split() else ""
        if first_word not in MONTH_ABBR and "kb" not in first_word:
            continue
        # Must contain a dash separator
        if "—" not in text and "–" not in text:
            continue

        parsed = parse_link_title(text, a["href"])
        if not parsed:
            continue

        key = (os_name, version, parsed["release_date"], parsed["kb"])
        if key in seen:
            continue
        seen.add(key)

        href = a["href"]
        if href.startswith("/"):
            href = "https://support.microsoft.com" + href

        if parsed["update_type"] != "Baseline" and not (version == "24H2" and parsed["build_24h2"] == '') and not (version == "25H2" and parsed["build_25h2"] == ''):
            rows.append({
                "os_major_version":                  os_name,
                "feature_release_version":             version,
                "release_full_name":   f"Version {version} (OS build {parsed["build_24h2"].split("10.0.")[1].split(".")[0] if version == "24H2" else parsed["build_25h2"].split("10.0.")[1].split(".")[0]})",
                "release_date":        parsed["release_date"],
                "release_date_format": parsed["release_date_format"],
                "build_number":        parsed["build_24h2"] if version == "24H2" else parsed["build_25h2"],
                "full_version":         f"{os_name} - Version {version} (OS build {parsed["build_24h2"].split("10.0.")[1].split(".")[0] if version == "24H2" else parsed["build_25h2"].split("10.0.")[1].split(".")[0]} - {parsed["update_type"]})",
                "kb":                  parsed["kb"],
            })
            

    return rows

def convert_json_to_csv(name,json_data):
    csv_file = '{}.csv'.format(name)
    csv_columns = ["os_major_version","feature_release_version","release_full_name","release_date","release_date_format","build_number","full_version","kb"]
    with open(csv_file, 'w', newline='',encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_columns,delimiter=",")
        writer.writeheader()
        for data in json_data:
            writer.writerow(data)

def get_win_build_info(os_version, url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    release_names = []
    for version in soup.find_all('strong'):
        if "Version" in version.contents[0] and version.contents[0] not in release_names:
            release_names.append(version.contents[0])
    i = 0
    release_list = []
    tables = soup.find_all("table",id=lambda x: x and x.startswith('historyTable'))
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            row_dict = {
                'os_major_version' : os_version,
                'feature_release_version': release_names[i].split(' ')[1],
                'release_full_name': release_names[i]
            }
            cols = row.find_all('td')
            for data in cols:
                if re.match('\d+-\d+-\d+', data.text):
                    row_dict['release_date'] = data.text
                    row_dict['release_date_format'] = datetime.strptime(data.text, "%Y-%m-%d").strftime("%B %Y").capitalize()
                elif re.match('\d+\.\d+', data.text):
                    row_dict['build_number'] = "10.0.{}".format(data.text)
                elif re.match('KB\d+', data.text):
                    row_dict['kb'] = data.text
            if 'release_date' in row_dict:
                release_list.append(row_dict)
            row_dict["full_version"] = "{} - {}".format(row_dict["os_major_version"],row_dict["release_full_name"])
        i = i + 1
    tables = soup.find_all("table",id=lambda x: x and x.startswith('HotpatchCalendar'))
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            row_dict = {
                'os_major_version' : os_version,
                'feature_release_version': release_names[-1].split(' ')[1],
                'release_full_name': release_names[-1]
            }
            cols = row.find_all('td')
            process = True
            for element in cols:
                if "Baseline" in element:
                    process = False
            if process:
                for data in cols:
                    if re.match('\d+-\d+-\d+', data.text):
                        row_dict['release_date'] = data.text
                        row_dict['release_date_format'] = datetime.strptime(data.text, "%Y-%m-%d").strftime("%B %Y").capitalize()
                    elif re.match('\d+\.\d+', data.text):
                        row_dict['build_number'] = "10.0.{}".format(data.text)
                    elif re.match('KB\d+', data.text):
                        row_dict['kb'] = data.text
                if 'release_date' in row_dict:
                    release_list.append(row_dict)
                row_dict["full_version"] = "{} - {}".format(row_dict["os_major_version"],row_dict["release_full_name"])
    
    return release_list




def main():
    win10_builds = get_win_build_info("Windows 10", 'https://learn.microsoft.com/en-us/windows/release-health/release-information')
    win11_builds = get_win_build_info("Windows 11", 'https://learn.microsoft.com/en-us/windows/release-health/windows11-release-information')
    for src in SOURCES:
        print(f"Fetching {src['os']} {src['ver']} …  {src['url']}")
        try:
            html = fetch(src["url"])
            rows = parse_release_page(html, src["os"], src["ver"], src["url"])
            print(f"  → {len(rows)} entries found")
            win11_builds.extend(rows)
        except requests.HTTPError as e:
            print(f"  ⚠️  HTTP {e.response.status_code} — skipping")
        except Exception as e:
            print(f"  ⚠️  Error: {e} — skipping")

    convert_json_to_csv("win10_builds",win10_builds)
    convert_json_to_csv("win11_builds",win11_builds)

if __name__ == '__main__':
    main()
