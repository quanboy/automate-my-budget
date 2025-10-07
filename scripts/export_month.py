import time
import re
import os
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options
from PIL import Image, ImageChops
import pytesseract
from selenium.webdriver.common.keys import Keys

# Deduplicate OCR text by removing repeated blocks of lines
def deduplicate_ocr_text(text, window=5):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return ""

    cleaned_lines = []
    seen_blocks = set()

    i = 0
    while i < len(lines):
        block = tuple(lines[i:i+window])

        if block in seen_blocks:
            i += window
            continue
        cleaned_lines.append(lines[i])
        seen_blocks.add(block)
        i += 1
    return "\n".join(cleaned_lines)

def filter_ocr_text(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    expense_pattern = re.compile(r"^\d+(\.\d+)?\s+\w+")
    cleaned = [lines[0]]
    
    for line in lines[1:]:
        if expense_pattern.match(line):
            cleaned.append(line)
    
    return "\n".join(cleaned)

# Switch to the iframe that contains the specified element
def switch_to_iframe_with_element(driver, by, value, timeout=20):
    driver.switch_to.default_content()
    WebDriverWait(driver, timeout).until(EC.presence_of_all_elements_located((By.TAG_NAME, "iframe")))
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    for idx, f in enumerate(iframes):
        driver.switch_to.default_content()
        driver.switch_to.frame(f)
        try:
            WebDriverWait(driver, 2).until(EC.presence_of_element_located((by, value)))
            return True
        except TimeoutException:
            continue
    raise TimeoutException("Element not found in any iframe")

# Capture note image by scrolling and performing OCR
def capture_note_image(driver, max_scrolls=2, wait_seconds=2):
        # Locate visible canvas
        canvas = WebDriverWait(driver, wait_seconds).until(
            lambda d: d.execute_script("""
                const cvs = Array.from(document.querySelectorAll('canvas'));
                for (const c of cvs) {
                    const r = c.getBoundingClientRect();
                    if (r.width > 0 && r.height > 0) return c;
                }
                return null;
            """)
        )

        all_text = ""
        for i in range(max_scrolls):
            filename = f"part_{i}.png"
            canvas.screenshot(filename)
            img = Image.open(filename)
            ocr_text = pytesseract.image_to_string(img, lang='eng')
            all_text += ocr_text + "\n"

            # Scroll down with wheel event
            driver.execute_script("""
                const el = arguments[0];
                el.dispatchEvent(new WheelEvent('wheel', {deltaY: 600, bubbles: true}));
            """, canvas)
            time.sleep(1.5)  # wait for redraw

        deduped = deduplicate_ocr_text(all_text)
        filtered = filter_ocr_text(deduped)
        return filtered


pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
options = Options()

# Suppress logs
options.add_argument("--log-level=3")
options.add_experimental_option('excludeSwitches', ['enable-logging'])
options.add_argument("start-maximized")

service = Service(executable_path='configs/msedgedriver.exe')
driver = webdriver.Edge(service=service, options=options)
driver.get('https://www.icloud.com/notes')

print("Please log in to your iCloud account manually.")
input("Press Enter after you have logged in and the notes are visible.")

# Wait for the page to load completely
time.sleep(3)

switch_to_iframe_with_element(driver, By.CSS_SELECTOR, ".list-item")

all_pinned_notes = WebDriverWait(driver, 15).until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".list-item.is-pinned"))
    )
pinned_notes = [note for note in all_pinned_notes if note.is_displayed()]
print(f"Total notes found: {len(pinned_notes)}")

found = False

# Iterate through pinned notes and look for notes containing a month in header
for i, note in enumerate(pinned_notes):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", note)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", note)
        # Wait for the note to load
        time.sleep(3)

        # Try to capture the note
        note_text = capture_note_image(driver)
        preview = note_text.splitlines()[:5]
        print("Preview:\n", "\n".join(preview))

        months = ["january", "february", "march", "april", "may", "june",
          "july", "august", "september", "october", "november", "december"]
        
        for month in months:
            if month in note_text.lower():
                filename = f"{month.upper()}.TXT"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(note_text)
                print(f"Found and saved note with '{month.capitalize()}' → {filename}")
                found = True

    except Exception as e:
        try:
            # Count canvases in the current frame
            canvas_count = driver.execute_script("return document.querySelectorAll('canvas').length;")
            print(f"Error processing note {i+1}, canvases found: {canvas_count}. Error: {e}")
        except Exception:
            print(f"Error processing note {i+1}, unable to count canvases. Error: {e}")


if not found:
    print("No note containing a month was found among the pinned notes.")

driver.quit()
