from playwright.sync_api import sync_playwright
import time
import os
import sqlite3

conn = sqlite3.connect('downloaded_files.db')
cursor = conn.cursor()
try:
    cursor.execute('CREATE TABLE files_tbl (f_name TEXT)')
except sqlite3.OperationalError:
    print('Table already exists.')

BASE_URL = "https://shop.pfdfoods.com.au"

data = open("config.txt", "r")
for x in data:
    if 'download_path' in x:
        download_path = x.replace('download_path = ', '').replace('\n', '')
    if 'email' in x:
        email = x.replace('email = ', '').replace('\n', '')
    if 'password' in x:
        password = x.replace('password = ', '').replace('\n', '')
    if 'last_file_name' in x:
        last_file_name = x.replace('last_file_name = ', '').replace('\n', '')


def login(page, context):
    time.sleep(2)
    if page.url == BASE_URL + "/login":
        print('Logging in ...')
        page.get_by_label("User name").fill(email)
        page.get_by_label("Password").fill(password)
        page.get_by_role("button", name="LOG IN").click()
        print('Password entered')
        context.storage_state(path="auth.json")
        page.goto(BASE_URL + "/invoices?InvoicesFilter=twelveMth")
        time.sleep(5)
    else:
        print('Already logged in')


def rename_files(pdf_id):
    files = os.listdir(download_path)
    print("Total Files: ", len(files))
    for file in files:
        if file.endswith(".pdf"):
            continue
        old_name = os.path.join(download_path, file)
        new_name = download_path + "\\" + str(pdf_id) + ".pdf"
        os.rename(old_name, new_name)


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=False, downloads_path=download_path)
    context = browser.new_context(storage_state="auth.json")
    page = context.new_page()

    page.goto(BASE_URL + "/invoices?InvoicesFilter=twelveMth", timeout=90000)

    login(page, context)

    # page.get_by_role("link", name="My Account").click()
    # page.get_by_role("link", name="Invoices").click()
    # page.get_by_text("Last 12 months").click()

    try:
        page.get_by_text("View All").click()
        time.sleep(5)
        links = page.query_selector_all("a")
        print("Total Links: ", len(links))
        for link in links:
            href = link.get_attribute("href")
            if href is not None and href.endswith("download"):
                pdf_id = href.split("/")[-2]

                cursor.execute("SELECT * FROM files_tbl WHERE f_name = ?", (pdf_id,))
                existing_record = cursor.fetchone()

                if existing_record:
                    # the record exists
                    print(f"The file {pdf_id}.pdf already exists")
                    continue

                url = BASE_URL + href
                print(url)
                page1 = context.new_page()
                try:
                    page1.goto(url, timeout=90000)
                except:
                    print('File Downloaded')
                    time.sleep(4)
                    rename_files(pdf_id)
                    cursor.execute("INSERT INTO files_tbl (f_name) VALUES (?)", (pdf_id,))
                    conn.commit()
                    page1.close()
    except Exception as e:
        print(e)
        print('No more files to download')
        conn.commit()
        conn.close()
print('Completed')
conn.commit()
conn.close()
