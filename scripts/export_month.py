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
from PIL import Image
import pytesseract
from selenium.webdriver.common.keys import Keys
from difflib import SequenceMatcher

# 🧩 Strict merging: removes only *true contiguous* overlaps between OCR screenshots


def merge_ocr_blocks_fuzzy(ocr_blocks, max_overlap_lines=10, min_match_ratio=0.6, debug=False):
    """
    Merge OCR blocks while detecting fuzzy overlaps (not only exact matches).
    Keeps all unique content but trims shifted duplicates.
    """
    merged_lines = ocr_blocks[0].splitlines()

    for i in range(1, len(ocr_blocks)):
        next_lines = ocr_blocks[i].splitlines()
        best_overlap = 0
        best_ratio = 0.0

        # Check all possible alignments between the tail of merged_lines and head of next_lines
        for n in range(1, min(max_overlap_lines, len(merged_lines), len(next_lines)) + 1):
            for shift in range(0, n):  # allow shifted matching
                a_chunk = "\n".join(merged_lines[-n + shift:])
                b_chunk = "\n".join(next_lines[:n - shift])
                ratio = SequenceMatcher(None, a_chunk, b_chunk).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_overlap = n - shift

        # If fuzzy overlap found — trim the duplicate prefix
        if best_ratio >= min_match_ratio and best_overlap > 0:
            if debug:
                print(f"🧩 Fuzzy overlap ({best_overlap} lines, sim={best_ratio:.2f}) between block {i-1} and {i}")
            merged_lines.extend(next_lines[best_overlap:])
        else:
            merged_lines.extend(next_lines)

    # Remove accidental global duplicates while preserving order
    seen = set()
    final_lines = []
    for line in merged_lines:
        if line.strip().lower() not in seen:
            final_lines.append(line)
            seen.add(line.strip().lower())

    return "\n".join(final_lines)



# 🧹 Filter lines: keep only valid expense-like patterns
def filter_ocr_text(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    expense_pattern = re.compile(r"^\d+(\.\d+)?\s+\w+")
    cleaned = [lines[0]]
    
    for line in lines[1:]:
        if expense_pattern.match(line):
            cleaned.append(line)
    
    return "\n".join(cleaned)


# 🌐 Switch into iCloud Notes iframe
def switch_to_iframe_with_element(driver, by, value, timeout=20):
    driver.switch_to.default_content()
    WebDriverWait(driver, timeout).until(EC.presence_of_all_elements_located((By.TAG_NAME, "iframe")))
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    for f in iframes:
        driver.switch_to.default_content()
        driver.switch_to.frame(f)
        try:
            WebDriverWait(driver, 2).until(EC.presence_of_element_located((by, value)))
            return True
        except TimeoutException:
            continue
    raise TimeoutException("Element not found in any iframe")


# 📸 Capture & parse note text using OCR
def capture_note_image(driver, max_scrolls=3, wait_seconds=2, debug=False):
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

    ocr_blocks = []

    # Take multiple screenshots while scrolling
    for i in range(max_scrolls):
        filename = f"part_{i}.png"
        canvas.screenshot(filename)
        img = Image.open(filename)
        ocr_text = pytesseract.image_to_string(img, lang='eng')

        if ocr_blocks and ocr_text.strip() == ocr_blocks[-1].strip():
            print(f"🛑 Detected identical block {i}, stopping early.")
            break

        ocr_blocks.append(ocr_text)

        if debug:
            print(f"🖼️ Captured part {i}, {len(ocr_text.splitlines())} lines")

        # Scroll down slightly
        driver.execute_script("""
            const el = arguments[0];
            el.dispatchEvent(new WheelEvent('wheel', {deltaY: 600, bubbles: true}));
        """, canvas)
        time.sleep(1.5)  # allow redraw

    if debug:
        print("\n📜 OCR block end previews (last 3 lines each):")
        for idx, block in enumerate(ocr_blocks):
            lines = [l for l in block.splitlines() if l.strip()]
            print(f"  Block {idx} → {lines[-3:]}")
        print("-" * 50)

    # Merge screenshots with strict overlap removal
    merged_text = merge_ocr_blocks_fuzzy(ocr_blocks, debug=debug)

    # Optional cleanup (only expense-like lines)
    filtered = filter_ocr_text(merged_text)
    return filtered


# 🧠 OCR setup
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
options = Options()
options.add_argument("--log-level=3")
options.add_experimental_option('excludeSwitches', ['enable-logging'])
options.add_argument("start-maximized")

# Launch Edge (you can delete your local driver if WebDriver Manager is installed)
service = Service(executable_path='../configs/msedgedriver.exe')
driver = webdriver.Edge(service=service, options=options)

driver.get('https://www.icloud.com/notes')

print("Please log in to your iCloud account manually.")
input("Press Enter after you have logged in and the notes are visible.")

time.sleep(3)
switch_to_iframe_with_element(driver, By.CSS_SELECTOR, ".list-item")

# Locate pinned notes
all_pinned_notes = WebDriverWait(driver, 15).until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".list-item.is-pinned"))
)
pinned_notes = [note for note in all_pinned_notes if note.is_displayed()]
print(f"📋 Total visible pinned notes: {len(pinned_notes)}")

found = False

months = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december"
]

# Process each note
for i, note in enumerate(pinned_notes):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", note)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", note)
        time.sleep(3)

        note_text = capture_note_image(driver, max_scrolls=3, debug=True)
        preview = note_text.splitlines()[:5]
        print(f"📝 Preview of note {i+1}:\n" + "\n".join(preview))

        # Detect month name
        for month in months:
            if month in note_text.lower():
                filename = f"{month.upper()}.TXT"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(note_text)
                print(f"✅ Saved note with '{month.capitalize()}' → {filename}")
                found = True

    except Exception as e:
        print(f"⚠️ Error processing note {i+1}: {e}")

if not found:
    print("❌ No note containing a month name was found.")

driver.quit()
