from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re


service = Service(executable_path='msedgedriver.exe')
driver = webdriver.Edge(service=service)
driver.get('https://www.icloud.com/notes')

print("Please log in to your iCloud account manually.")
input("Press Enter after you have logged in and the notes are visible.")

time.sleep(5)  # Wait for the page to load completely

iframes = driver.find_elements(By.TAG_NAME, "iframe")
driver.switch_to.frame(iframes[1])  # Switch to the correct iframe

#wait = WebDriverWait(driver, 20)
#notes = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".list-item")))
pinned_notes = driver.find_elements(By.CSS_SELECTOR, ".list-item.is-pinned")
print(f"Total notes found: {len(pinned_notes)}")

found = False

for i, note in enumerate(pinned_notes):
    try:
        driver.execute_script("arguments[0].scrollIntoView(true);", note)
        time.sleep(1)  # Allow time for scrolling animation
        driver.execute_script("arguments[0].click();", note)
        time.sleep(3)  # Wait for the note to load
        
        try:
            title = driver.find_element(By.CSS_SELECTOR, ".note-title").text
        except:
            title = "Untitled"
        
        try:
            body = driver.find_element(By.CSS_SELECTOR, ".note-text").text
        except:
            body = ""
        
        print(f"Checked Note {i+1}: {title[:40]}...")

        if re.search(r"september", title, re.IGNORECASE) or re.search(r"september", body, re.IGNORECASE):
            with open("SEPTEMBER.TXT", "w", encoding="utf-8") as f:
                f.write(f"Title: {title}\n\n{body}")
            print(f"Found and saved note with 'September': {title}")
            found = True
            break  # Stop after finding the first matching note

    except Exception as e:
        print(f"Error processing note {i+1}: {e}")

if not found:
    print("No note with 'September' found.")

driver.quit()



# [32116:28332:0923/205501.768:ERROR:components\device_event_log\device_event_log_impl.cc:244] [20:55:01.768] USB: usb_service_win.cc:105 SetupDiGetDeviceProperty({{A45C254E-DF1C-4EFD-8020-67D146A850E0}, 6}) failed: Element not found. (0x490)
# Checking Note 2: Untitled...
# No note with September found.
# i want to search only pinned notes