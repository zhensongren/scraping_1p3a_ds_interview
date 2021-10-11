from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re
import pandas as pd
import csv
import os 

#chrome_options = set_chrome_options()
#driver = webdriver.Chrome(options=chrome_options)
driver = webdriver.Chrome()
START_URL = "https://www.1point3acres.com/bbs/forum.php?mod=forumdisplay&fid=259&orderby=dateline&sortid=311&filter=author&orderby=dateline&sortid=311&page="

# Helper function to set up the headless option of chrome in linux
def set_chrome_options() -> None:
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
    while i<=max_page_num and get_next_page:
        url = START_URL + str(i)
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, 'lxml')
        posts = soup.find_all('tbody', id=re.compile("normalthread_")) 
#         print(f'{len(posts)} posts to be scraped')
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
#             print(post_dict)
#             print('--'*20)
            refers.append(post_dict)
        # set the next page
        i+=1
    return refers
    
    
# # Insert the new data to the front of the csv file.
# def init_csv_file(file_path, field_names):
#     with open(file_path, 'w', newline='', encoding='utf8') as csv_file:
#         writer = csv.DictWriter(csv_file, fieldnames=field_names)
#         writer.writeheader()
        
# def write_to_csv(file_path, field_names, data):
#     with open(file_path, 'a', newline='', encoding='utf8') as csv_file:
#         writer = csv.DictWriter(csv_file, fieldnames=field_names)
#         writer.writerows(data)

# field_names = ['Date', 'Poster', 'Replies', 'Views', 'post_id', 'post_title', 'company']

# #initialize the file for the 1st scrpae
# init_csv_file('./referral_US.csv', field_names=field_names)
# #Add new data to existing file
# write_to_csv('./referral_US.csv', field_names=field_names, data=refers)

# Lower level of handling saving new data.
def insert_into_csv(file_path, data):
    with open(file_path, 'r', newline='', encoding='utf8') as csv_file:
        text = csv_file.readlines()
        new_data = []
        for row_num in range(len(refers)):
            row = ','.join([str(value) for value in data[row_num].values()])+'\n'
            new_data.append(row)
        # Use slice assignment to insert a list to the first row.
        text[0:0] = new_data
        print(text[0])
        
    with open(file_path, 'w', newline='', encoding='utf8') as csv_file:
        csv_file.writelines(text)

# insert_into_csv('./referral_US.csv', data=refers)

# Always save the new data just below the header row.
def insert_data(file_path, data):
    fieldnames = []
    if len(data)>0:
        fieldnames = list(data[0].keys())
    else: print('no data scraped')
    # Save the old data and headers
    if os.path.exists(file_path):
        with open(file_path, 'r', newline='', encoding='utf8') as csv_file:
            reader = csv.DictReader(csv_file)
            if reader.fieldnames is None:
                reader.fieldnames = fieldnames
                
            old_data = []
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
    old_df = pd.read_csv('interview_DS_US.csv', nrows=1)
    latest_id_from_CSV = old_df['post_id'][0]
    latest_date_from_CSV = pd.to_datetime(old_df['Date'][0])
else:   
    latest_id_from_CSV = 0
    latest_date_from_CSV = pd.to_datetime('1900-01-01')

refers = get_referrals(driver, START_URL, max_page_num=2, 
                       latest_id_from_CSV=latest_id_from_CSV, latest_date_from_CSV=latest_date_from_CSV)

insert_data('./interview_DS_US.csv', data=refers)

df = pd.read_csv('interview_DS_US.csv')

print(df.head())

print(df.shape)

print(df.dtypes)