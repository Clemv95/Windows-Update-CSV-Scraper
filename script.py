from datetime import datetime
import requests
import re
from bs4 import BeautifulSoup
import csv

def convert_json_to_csv(name,json_data):
    csv_file = '{}.csv'.format(name)
    csv_columns = json_data[0].keys()
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
        i = i + 1
    return release_list

def main():
    win10_builds = get_win_build_info("Windows 10", 'https://learn.microsoft.com/en-us/windows/release-health/release-information')
    win11_builds = get_win_build_info("Windows 11", 'https://learn.microsoft.com/en-us/windows/release-health/windows11-release-information')
    convert_json_to_csv("win10_builds",win10_builds)
    convert_json_to_csv("win11_builds",win11_builds)

if __name__ == '__main__':
    main()
