from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options
import time
import re
import os
from PIL import Image, ImageChops
import pytesseract
from selenium.webdriver.common.keys import Keys

def images_are_equal(img1, img2):
    return ImageChops.difference(img1, img2).getbbox() is None

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

def find_overlap(prev_img, curr_img, min_overlap=50):
    """
    Find vertical overlap between two images.
    Returns the number of pixels to trim from the top of curr_img.
    """
    prev_crop = prev_img.crop((0, prev_img.height - min_overlap, prev_img.width, prev_img.height))
    for offset in range(min_overlap, curr_img.height, 10):  # step 10px for speed
        curr_crop = curr_img.crop((0, 0, curr_img.width, offset))
        # Compare sizes
        if prev_crop.size == curr_crop.size and ImageChops.difference(prev_crop, curr_crop).getbbox() is None:
            return offset
    return 0

def capture_note_image(driver, outfile, max_scrolls=2, wait_seconds=2):
    try:
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

        screenshots = []
        prev_img = None

        for i in range(max_scrolls):
            filename = f"part_{i}.png"
            canvas.screenshot(filename)
            img = Image.open(filename)

            # Stop if image identical to previous (end of note)
            if prev_img and ImageChops.difference(prev_img, img).getbbox() is None:
                print(f"🛑 Reached end of note at part {i}")
                os.remove(filename)
                break

            screenshots.append(img)
            prev_img = img

            # Scroll down with wheel event
            driver.execute_script("""
                const el = arguments[0];
                el.dispatchEvent(new WheelEvent('wheel', {deltaY: 600, bubbles: true}));
            """, canvas)

            time.sleep(1.5)  # wait for redraw

        # Stitch screenshots with overlap trimming
        stitched_parts = []
        prev_img = None
        for img in screenshots:
            if prev_img is None:
                stitched_parts.append(img)
            else:
                overlap = find_overlap(prev_img, img)
                if overlap > 0:
                    img = img.crop((0, overlap, img.width, img.height))
                stitched_parts.append(img)
            prev_img = img

        widths, heights = zip(*(im.size for im in stitched_parts))
        stitched_height = sum(heights)
        stitched = Image.new("RGB", (max(widths), stitched_height))

        offset = 0
        for im in stitched_parts:
            stitched.paste(im, (0, offset))
            offset += im.height

        stitched.save(outfile)
        print(f"✅ Saved full stitched note to {outfile}")
        return "canvas-wheel-trimmed"

    except Exception as e:
        print(f"⚠️ Capture failed: {e}")
        body = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        body.screenshot(outfile)
        return "body"



pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
options = Options()

# Suppress logs
options.add_argument("--log-level=3")
options.add_experimental_option('excludeSwitches', ['enable-logging'])
options.add_argument("start-maximized")

service = Service(executable_path='msedgedriver.exe')
driver = webdriver.Edge(service=service, options=options)
driver.get('https://www.icloud.com/notes')

print("Please log in to your iCloud account manually.")
input("Press Enter after you have logged in and the notes are visible.")

# Wait for the page to load completely
time.sleep(3)

switch_to_iframe_with_element(driver, By.CSS_SELECTOR, ".list-item")

pinned_notes = WebDriverWait(driver, 15).until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".list-item.is-pinned"))
    )
print(f"Total notes found: {len(pinned_notes)}")

found = False

for i, note in enumerate(pinned_notes):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", note)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", note)

        # Wait for the note to load
        time.sleep(3)

        # Try to capture the note
        img_path = f"note_{i+1}.png"
        how = capture_note_image(driver, img_path)
        print(f"Captured note {i+1} using {how}")

        text = pytesseract.image_to_string(Image.open(img_path), lang='eng')
        print(f"Checked Note {i+1}: {text[:60]}...")

        if "september" in text.lower():
            with open("SEPTEMBER.TXT", "w", encoding="utf-8") as f:
                f.write(text)
            print(f"Found and saved note with 'September' to SEPTEMBER.TXT")
            found = True
            # Stop after finding the first matching note
            break

    except Exception as e:
        try:
            # Count canvases in the current frame
            canvas_count = driver.execute_script("return document.querySelectorAll('canvas').length;")
            print(f"Error processing note {i+1}, canvases found: {canvas_count}. Error: {e}")
        except Exception:
            print(f"Error processing note {i+1}, unable to count canvases. Error: {e}")


if not found:
    print("No note with 'September' found.")

driver.quit()
