import pyautogui
import pyperclip
import yaml
import time
import os
import pygetwindow as gw

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

        # 2. Find Anchor 
        anchor = self.find_image(step.get('image_anchor'), step.get('confidence', 0.8))
        
        # 3. Perform Actions
        if step['action'] == "Click":
            if anchor:
                btn = step.get('button', 'left') # Extract right-click if defined
                pyautogui.click(anchor.x + step.get('offset_x', 0), anchor.y + step.get('offset_y', 0), button=btn)
            else:
                raise Exception(f"Anchor {step['image_anchor']} not found.")

        elif step['action'] == "Type":
            if anchor:
                pyautogui.click(anchor.x + step.get('offset_x', 0), anchor.y + step.get('offset_y', 0))
                pyautogui.hotkey('ctrl', 'a')
                pyautogui.press('backspace')
                pyperclip.copy(step['value'])
                pyautogui.hotkey('ctrl', 'v')
                pyautogui.press('enter')
            else:
                raise Exception(f"Anchor {step['image_anchor']} not found.")

        elif step['action'] == "KeyPress":
            pyautogui.press(step['key'], presses=step.get('repeat', 1), interval=0.2)

        elif step['action'] == "Hotkey":
            pyautogui.hotkey(*step['keys'])

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
    engine.run("media_player_path_סיבת.yaml")