# Windows Release Info Scraper

This repository contains a Python script to extract version and update information for Windows 10 and Windows 11 from Microsoft's official documentation.

## Features

- Scraping of build numbers, release dates, and associated KBs.
- Generation of CSV files (`win10_builds.csv` and `win11_builds.csv`).
- Automatic daily execution via GitHub Actions.
- Automatic commit of updated CSV files.

  
## Structure
```
.
├── script.py              # Main script
├── requirements.txt       # Python dependencies
├── win10_builds.csv       # Windows 10 scraping output
├── win11_builds.csv       # Windows 11 scraping output
└── .github/
    └── workflows/
        └── schedule.yml   # GitHub Actions workflow
```

## Manual Execution

You can also trigger the workflow manually from the **Actions** tab on GitHub.

## Dependencies

- `requests`
- `beautifulsoup4`

Install them locally if you want to test on your machine:
```bash
pip install -r requirements.txt
```
## License
Free to use.
