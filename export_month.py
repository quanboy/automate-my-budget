from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
import re
import os

service = Service(executable_path='msedgedriver.exe')
driver = webdriver.Edge(service=service)
driver.get('https://www.icloud.com/notes')

print("Please log in to your iCloud account manually.")
input("Press Enter after you have logged in and the notes are visible.")

time.sleep(5)  # Wait for the page to load completely
notes = driver.find_elements(By.CSS_SELECTOR, ".list-item")

found = False

for i, note in enumerate(notes):
    try:
        title_preview = note.text.strip()
        if re.search(r"september", title_preview. re.IGNORECASE):
            print(f"Found note: {title_preview}")
            note.click()
            time.sleep(3)  # Wait for the note to load

            try:
                title = driver.find.element(By.CSS_SELECTOR, ".note-title").text
            except:
                title = "Untitled"
            
            try:
                body = driver.find.element(By.CSS_SELECTOR, ".note-text").text
            except:
                body = ""
            
            safe_title = re.sub(r'[\\/*?:"<>|]', "_", title)

            filename = f"{safe_title}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(title + "\n\n" + body)
            print(f"Saved note as {filename}")
            found = True
            break
    except Exception as e:
        print(f"Error processing note {i+1}: {e}")

if not found:
    print("No note with 'September' found.")

driver.quit()
