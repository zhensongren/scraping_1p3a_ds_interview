from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re
import pandas as pd
import csv
import os 

# Helper function to set up the headless option of chrome in linux
def set_chrome_options():
    """Sets chrome options for Selenium.
    Chrome options for headless browser is enabled.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_prefs = {}
    chrome_options.experimental_options["prefs"] = chrome_prefs
    chrome_prefs["profile.default_content_settings"] = {"images": 2}
    return chrome_options
    
def get_date(p):
    try:
        date_span = p.find('td', class_='by').find('em').find('span')
        if date_span.find('span'):
            date = date_span.find('span')['title']
        else: 
            date = date_span.text
    except:
          date = 'NA'
    else:
        date = pd.to_datetime(date)
    return date
        
def get_poster(p):
    try:
        poster = p.find('td', class_='by').find('cite').find('a').text
    except:
        poster = "NA"
    return poster

def get_reply_num(p):
    try:
        reply = int(p.find('a', class_='xi2').text)
    except: 
        reply = -1
    return reply

def get_view_num(p):
    try:
        view = int(p.find('a', class_='xi2').parent.find('em').text)
    except:
        view = -1
    return view

def get_post_id(p):
    try:
        post_id = int(p['id'].split('_')[1])
    except:
        post_id = -1
    return post_id

def get_post_title(p):
    try:
        post_title = p.find('a', class_="s xst").text
    except:
        post_title = 'NA'
        
    return post_title
def get_company(p):
    try:
        company = p.find('font', {"color": "#FF6600"}).text
    except:
        company = 'NA'
    return company

def get_referrals(driver, START_URL, max_page_num=10, latest_id_from_CSV=None, latest_date_from_CSV=None):   
    refers = []
    get_next_page = True
    # scrape the data from the page 1 to 50
    i = 1
    print(f'scraping page {i}')
    while i<=max_page_num and get_next_page:
        url = START_URL + str(i)
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, 'lxml')
        posts = soup.find_all('tbody', id=re.compile("normalthread_")) 
        # get list of referral data for each page
        for p in posts:
            # Date
            date = get_date(p)
            # Poster. 有匿名用户。
            poster = get_poster(p)
            # 回复
            reply = get_reply_num(p)
            # 查看
            view = get_view_num(p)
            # post id
            post_id = get_post_id(p)
            # Check if the post already saved.   
            if  post_id==latest_id_from_CSV:
                get_next_page = False
                break   
            # post_title
            post_title = get_post_title(p)
            # company
            company = get_company(p)
            post_dict = {'Date': date, 'Poster': poster, 'Replies': reply, 'Views': view, 'post_id':post_id, 'post_title':post_title, 'company':company}
            # print(post_dict)
            # print('--'*20)
            refers.append(post_dict)
        # set the next page
        i+=1
    return refers

# Always save the new data just below the header row.
def save_data_to_existing_file(file_path, data):
    fieldnames = []
    if len(data)>0:
        fieldnames = list(data[0].keys())
    else: 
        print('no new data was found and scraped')
        return
    old_data = []
    # Save the old data and headers
    if os.path.exists(file_path):
        with open(file_path, 'r', newline='', encoding='utf8') as csv_file:
            reader = csv.DictReader(csv_file)
            if reader.fieldnames is None:
                reader.fieldnames = fieldnames
            for row in reader:
                old_data.append(row)
                
    # Write the header and the new data                        
    with open(file_path, 'w', newline='', encoding='utf8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
        
    # Append the old data 
    with open(file_path, 'a', newline='', encoding='utf8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writerows(old_data)
        
# read the 1st row to the previous most recent id and date
if os.path.exists('./interview_DS_US.csv'):
    try:
        old_df = pd.read_csv('interview_DS_US.csv', nrows=1)
        latest_id_from_CSV = old_df['post_id'][0]
        latest_date_from_CSV = pd.to_datetime(old_df['Date'][0])
    except:   
        latest_id_from_CSV = 0
        latest_date_from_CSV = pd.to_datetime('1900-01-01')

# scrape without chorme UI(the headless option)
chrome_options = set_chrome_options()
driver = webdriver.Chrome(options=chrome_options)

# scrape with chorme UI
# driver = webdriver.Chrome() 
START_URL = "https://www.1point3acres.com/bbs/forum.php?mod=forumdisplay&fid=259&orderby=dateline&sortid=311&filter=author&orderby=dateline&sortid=311&page="

refers = get_referrals(driver, START_URL, max_page_num=50, 
                       latest_id_from_CSV=latest_id_from_CSV, latest_date_from_CSV=latest_date_from_CSV)

save_data_to_existing_file('./interview_DS_US.csv', data=refers)

df = pd.read_csv('interview_DS_US.csv')
print('---'*50)
print(df.head())
print('---'*50)
print(df.shape)
print(df.dtypes)