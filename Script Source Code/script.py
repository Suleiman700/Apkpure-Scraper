from bs4 import BeautifulSoup
import time
from selenium import webdriver

import json
from tqdm import tqdm


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

def chrome():
    chrome_options = Options()
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--start-maximized")

    # Replace this path with the updated ChromeDriver path
    driver_path = r"chromedriver.exe"  # 🔴 Update this path

    service = Service(driver_path)
    browser = webdriver.Chrome(service=service, options=chrome_options)

    browser.implicitly_wait(5)
    return browser

browser = chrome()
browser.minimize_window()

# a particular category
url = str(input("Enter the URL to a Particular category of apps: "))

# Set this to load more apps pages (each page has 20 apps)
load_more_times = int(input("\nEnter number of pages upto you wanna extract the data (each page has 20 apps): "))
browser.get(url)

src = browser.page_source
soup = BeautifulSoup(src, 'lxml')
data = []
apps_count = 0


for load_more in tqdm(range(load_more_times), desc= "Overall Progress"):
    # if apps_count >= 2: continue

    category_template = soup.find('div', {'class': 'apk-grid-item no-grid', 'data-dt-module-name': 'latest_update'})
    load_button_link = soup.find('a', {'class' : 'show-more'})['href']
    all_apps = category_template.find_all('li')

    for app in tqdm(all_apps, desc= "Per Page Progress"):
        try:
            app_page_link = app.find('a')['href']
            # app_page_link = 'https://apkpure.com'+app_page_link
            browser.get(app_page_link)
            browser.implicitly_wait(1)
            appInfo_src = browser.page_source
            app_page = BeautifulSoup(appInfo_src, 'lxml')

            app_data = {
                'pkg_name': '',         # com.roblox.client
                'name': '',             # Roblox
                'publisher_name': '',   # Roblox Corporation
                'icon_url': '',         # https://image.winudf.com/v2/image1/Y29tLnJvYmxveC5jbGllbnRfaWNvbl8xNjYyMDU2MTYyXzAyMQ/icon.webp?w=140&fakeurl=1&type=.webp
                'categories': [],
                'os': {
                    'android_os': '', # Android 6.0+
                },
                'media': {
                    'videos': [],
                    'pictures': [],
                },
                'versions': [
                ],
                'tags': [], # [Adventure, Single Player', ...etc]
            }

            app_pkg_name = app_page.find('main', {'class': 'dt-details-new-box page-q detail_container'})['data-pkg'] # com.roblox.client
            app_data['pkg_name'] = app_pkg_name

            info_box = app_page.find('div', {'class': 'details container'})

            # Get Android os
            android_os_section = info_box.find('li', {'data-vars-desc': 'AndroidOS'})
            android_os_data = android_os_section.find('div', {'class': 'head'}).get_text().strip() # Android 6.0+
            app_data['os']['android_os'] = android_os_data

            # Get tags
            tags_section = info_box.find('div', {'class': 'tag-box'})
            tags = []

            if tags_section:
                for tag_span in tags_section.find_all('span', {'class': 'tag-item'}):
                    tag_link = tag_span.find('a')
                    try:
                        if tag_link:
                            tag_name = tag_link.text.strip()  # Adventure
                            tags.append(tag_name)
                            # tag_url = tag_link['href']  # Extract tag URL
                            # tags.append({'name': tag_name, 'url': tag_url})
                    except:
                        continue
            app_data['tags'] = tags


            # -------------------------------Section 1-----------------------------------
            # to get category
            category_tag = info_box.find('div', {'class': 'default_ellipsis_1 bread_crumbs'})
            all_categories = category_tag.find_all('a')
            category = ''
            for categ in all_categories:
                cat = categ.get_text().strip()
                if cat != '':
                    app_data['categories'].append(cat)
                    # category += cat
                    # category += ' ->'

            # -------------------------------Section 2-----------------------------------
            # to get icon url of app
            icon_section = info_box.find('div', {'class': 'apk_info_content'})
            icon_url = icon_section.find('img')['src']
            app_data['icon_url'] = icon_url

            # to get name of app
            name_link_section = info_box.find('div', {'class': 'info'})
            name = name_link_section.find('div', {'class': 'title_link'}).find('h1').get_text().strip() # Roblox
            publisher_name = name_link_section.find('span', {'class': 'developer'}).find('a').get_text().strip() # Roblox Corporation
            app_data['name'] = name
            app_data['publisher_name'] = publisher_name

            # Description of the App
            description_section = info_box.find('div', {'class': 'content'})
            text_description = description_section.find('div', {'class': 'translate-content'}).get_text().strip()

            # Video and Pictures
            pictures_section = info_box.find('div', {'class': 'screen'})
            links_tag = pictures_section.find_all('a')
            for link_tag in links_tag:
                try:
                    video = link_tag['data-src']
                    app_data['media']['videos'].append(video)
                except:
                    picture = link_tag['href']
                    app_data['media']['pictures'].append(picture)



            # ------------------------------- Versions ----------------------------------
            current_url = browser.current_url # https://apkpure.com/roblox-android/com.roblox.client
            browser.get(current_url + '/versions') # https://apkpure.com/roblox-android/com.roblox.client/versions
            appInfo_src = browser.page_source
            app_page = BeautifulSoup(appInfo_src, 'lxml')

            versions_list = app_page.find('ul', {'class': 'ver-wrap'})
            versions = []
            max_versions_to_get = 5
            grabbed_versions = 0
            for version in versions_list.find_all('li'):
                if grabbed_versions >= max_versions_to_get:
                    break  # Stop the loop once we have enough versions
                try:
                            version_data = {
                                'number': '',
                                'description': '',
                                'download_link': '',
                                'file_size': '',
                                'file_date': '',
                            }

                            version_number = version.find('a', {'class': 'ver_download_link'})['data-dt-version'] # 2.662.537
                            version_file_size = version.find('span', {'class': 'ver-item-s'}).get_text().strip() # 232.2 MB
                            version_file_date = version.find('span', {'class': 'update-on'}).get_text().strip() # Feb 28, 2025
                            version_data['number'] = version_number
                            version_data['file_size'] = version_file_size
                            version_data['file_date'] = version_file_date

                            version_link = version.find('a', {'class': 'ver_download_link'})['href'] # https://apkpure.com/roblox-android/com.roblox.client/download/2.662.537
                            browser.get(version_link)
                            appInfo_src = browser.page_source
                            app_page = BeautifulSoup(appInfo_src, 'lxml')

                            version_description = app_page.find('div', {'class': 'show-more-content'}).get_text().strip()
                            version_data['description'] = version_description

                            version_download_link = app_page.find('a', {'id': 'download_link'})['href']
                            version_data['download_link'] = version_download_link

                            versions.append(version_data)
                except:
                    continue
                finally:
                    grabbed_versions+=1

            app_data['versions'] = versions

            # # to get download link of the app
            # download_link_section = name_link_section.find('div', {'class': 'ny-down'})
            # downloadLink_box = download_link_section.find('div', {'class': 'div-box'})
            # downloadLink = downloadLink_box.find('a')['href']
            # downloadLink = 'https://apkpure.com'+downloadLink
            #
            # # go to the download page and download the app
            # browser.get(downloadLink)
            # browser.implicitly_wait(1)
            # download_pageSrc = browser.page_source
            # download_page = BeautifulSoup(download_pageSrc, 'lxml')
            # download_link_tag = download_page.find('p', {'class': 'down-click'})
            # download_link = download_link_tag.find('a')['href']
            # # print(download_link)



            # application_description = {
            # 'SubCategory' : category,
            # 'IconUrl' : icon_url,
            # 'AppName' : name,
            # 'PublisherName' : publisher_name,
            # 'DownloadLink' : download_link,
            # 'VideoAndImagesURL' : video_pic_links,
            # 'TextDescription' : text_description,
            # }
            data.append(app_data)
            apps_count+=1
        except:
            continue

    outputs = []
    outputs.append(data)
    # load_button_link = 'https://apkpure.com' + load_button_link
    # browser.get(load_button_link)
    # time.sleep(2)
    # src = browser.page_source
    # soup = BeautifulSoup(src, 'lxml')

print(f'{apps_count} apps has been scraped.')
with open("output.json", "w") as outfile:
    json.dump(outputs, outfile,  indent = 6)
browser.quit()
