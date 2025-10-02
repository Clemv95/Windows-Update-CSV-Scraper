from datetime import datetime
import requests
import re
from bs4 import BeautifulSoup
import csv

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
    convert_json_to_csv("win10_builds",win10_builds)
    convert_json_to_csv("win11_builds",win11_builds)

if __name__ == '__main__':
    main()
