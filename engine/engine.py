import pyautogui
import pyperclip
import yaml
import time
import os
import pygetwindow as gw
import pytesseract
from PIL import ImageGrab, ImageChops

# Point this directly to your Tesseract installation folder
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\Daer7417\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

# Security: Move mouse to 0,0 to abort
pyautogui.FAILSAFE = True

class AutomationEngine:
    def __init__(self, image_dir="."):
        self.image_dir = image_dir
        self.latency_multiplier = 1.0

    def get_path(self, filename):
        return os.path.join(self.image_dir, filename)

    def find_image(self, template, confidence=0.8):
        if not template: return None
        try:
            return pyautogui.locateCenterOnScreen(self.get_path(template), confidence=confidence)
        except:
            return None

    def find_text_on_screen(self, target_text, lang='eng'):
        print(f"Running OCR for text: '{target_text}' (Language: {lang})...")
        try:
            screenshot = ImageGrab.grab()
            # output_type=DICT is required to get bounding box coordinates
            data = pytesseract.image_to_data(screenshot, lang=lang, output_type=pytesseract.Output.DICT)
            
            for i in range(len(data['text'])):
                word = data['text'][i].strip()
                if not word: continue
                
                # Case-insensitive match
                if target_text.lower() == word.lower():
                    x = data['left'][i] + (data['width'][i] / 2)
                    y = data['top'][i] + (data['height'][i] / 2)
                    print(f"Found '{word}' at X:{x}, Y:{y}")
                    return (x, y)
                    
            print(f"OCR could not locate the text '{target_text}'.")
            return None
        except Exception as e:
            print(f"OCR Error: {e}")
            return None

    def execute_step(self, step):
        print(f"Executing Step {step['step_id']}: {step.get('description', '')}")

        # 1. Handle Window Activation & Launching
        if step['action'] == "ActivateWindow":
            title = step['window_title']
            wins = [w for w in gw.getAllWindows() if title.lower() in w.title.lower()]
            
            if not wins:
                print(f"Window '{title}' not found. Attempting to launch...")
                os.startfile('wmplayer')
                time.sleep(5) 
                wins = [w for w in gw.getAllWindows() if title.lower() in w.title.lower()]

            if wins:
                target = wins[0]
                try:
                    target.restore() 
                    target.activate()
                    target.maximize()
                    time.sleep(1)
                except Exception as e:
                    print(f"Focus error: {e}")
            else:
                raise Exception(f"Could not launch or find window with title: {title}")
            return

        # 2. Find Image Anchor (if action uses one)
        anchor = None
        if 'image_anchor' in step:
            anchor = self.find_image(step.get('image_anchor'), step.get('confidence', 0.8))
            if not anchor and step['action'] in ["Click", "Type"]:
                raise Exception(f"Image anchor {step['image_anchor']} not found.")
        
        # 3. Perform Actions
        if step['action'] == "Click":
            btn = step.get('button', 'left') 
            pyautogui.click(anchor.x + step.get('offset_x', 0), anchor.y + step.get('offset_y', 0), button=btn)

        elif step['action'] == "ClickText":
            target_text = step['text_anchor']
            # Default to English if not specified in YAML
            ocr_lang = step.get('lang', 'eng') 
            
            coords = self.find_text_on_screen(target_text, lang=ocr_lang)
            if coords:
                btn = step.get('button', 'left')
                pyautogui.click(coords[0] + step.get('offset_x', 0), coords[1] + step.get('offset_y', 0), button=btn)
            else:
                 raise Exception(f"Text anchor '{target_text}' not found on screen.")

        elif step['action'] == "Type":
            pyautogui.click(anchor.x + step.get('offset_x', 0), anchor.y + step.get('offset_y', 0))
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.press('backspace')
            pyperclip.copy(step['value'])
            pyautogui.hotkey('ctrl', 'v')
            pyautogui.press('enter')

        elif step['action'] == "KeyPress":
            pyautogui.press(step['key'], presses=step.get('repeat', 1), interval=0.2)

        elif step['action'] == "Hotkey":
            pyautogui.hotkey(*step['keys'])
        
        elif step['action'] == "ScrollAndFindText":
            target_text = step['text_anchor']
            max_attempts = step.get('max_scrolls', 10)
            # PyAutoGUI scroll: negative numbers scroll down, positive scroll up
            scroll_clicks = step.get('scroll_amount', -500) 
            ocr_lang = step.get('lang', 'eng')

            # 1. Park the mouse over the scrollable area
            pyautogui.moveTo(step.get('hover_x', 500), step.get('hover_y', 500))
            time.sleep(0.5)

            previous_screenshot = None

            for attempt in range(max_attempts):
                print(f"Scroll iteration {attempt + 1}/{max_attempts} searching for '{target_text}'...")

                # 2. Run OCR on the current view
                coords = self.find_text_on_screen(target_text, lang=ocr_lang)
                
                if coords:
                    print(f"Success! Found '{target_text}'. Executing click.")
                    btn = step.get('button', 'left')
                    pyautogui.click(coords[0], coords[1], button=btn)
                    break # Exit the loop, step is complete

                # 3. Bottom-of-Page Detection
                current_screenshot = ImageGrab.grab()
                if previous_screenshot:
                    # Compare current screen to the screen before we scrolled
                    diff = ImageChops.difference(current_screenshot, previous_screenshot)
                    if not diff.getbbox(): 
                        # If getbbox() is None, the images are 100% identical. The screen didn't move.
                        raise Exception(f"Reached bottom of list. '{target_text}' not found.")

                previous_screenshot = current_screenshot

                # 4. Scroll the UI
                pyautogui.scroll(scroll_clicks)
                
                # 5. Method C Buffer: Crucial wait for the VM to render the new list items
                time.sleep(1.5 * self.latency_multiplier) 

            else:
                # This executes if the loop hits max_attempts without breaking
                raise Exception(f"Hit scroll limit ({max_attempts}) without finding '{target_text}'.")

        # 4. Post-Action Delay
        delay = step.get('post_delay_ms', 500) * self.latency_multiplier
        time.sleep(delay / 1000.0)

    def run(self, yaml_file):
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        self.latency_multiplier = data.get('settings', {}).get('latency_multiplier', 1.0)
        
        for step in data['steps']:
            try:
                self.execute_step(step)
            except Exception as e:
                print(f"CRITICAL ERROR: {e}")
                break

if __name__ == "__main__":
    engine = AutomationEngine(image_dir=".") 
    engine.run("explorer_ocr_test.yaml")