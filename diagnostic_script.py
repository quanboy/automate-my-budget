from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
import time

service = Service("msedgedriver.exe")
options = Options()
options.add_argument("--log-level=3")

driver = webdriver.Edge(service=service, options=options)
driver.get("https://www.icloud.com/notes")

print("👉 Log in to iCloud manually in the Edge window.")
input("Press ENTER here once you see your Notes list...")

time.sleep(5)

# Find all iframes
iframes = driver.find_elements(By.TAG_NAME, "iframe")
print(f"Found {len(iframes)} iframes")

for idx, iframe in enumerate(iframes):
    driver.switch_to.default_content()
    driver.switch_to.frame(iframe)

    try:
        notes = driver.find_elements(By.CSS_SELECTOR, ".list-item")
        print(f"➡️ Iframe {idx}: Found {len(notes)} .list-item elements")
    except Exception as e:
        print(f"⚠️ Iframe {idx}: error {e}")

driver.quit()
