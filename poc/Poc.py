import pyautogui
import pyperclip
import time
import os
import sys

# Safety mechanisms
pyautogui.FAILSAFE = True # Move mouse to any corner to instantly abort
pyautogui.PAUSE = 1.0     # 1-second delay after every PyAutoGUI action

import pyautogui
import pygetwindow as gw
import time
import os

def launch_and_maximize_wmp():
    print("Checking if Windows Media Player is running...")
    
    # 1. Search for an existing WMP window
    wmp_windows = gw.getWindowsWithTitle('Windows Media Player')
    
    if not wmp_windows:
        print("WMP not found. Launching it now...")
        try:
            os.startfile('wmplayer')
            # Wait for it to open before trying to grab the window
            time.sleep(5) 
            wmp_windows = gw.getWindowsWithTitle('Windows Media Player')
        except Exception as e:
            print(f"Failed to open WMP directly: {e}")
            return False

    # 2. If we found the window (either already open or newly launched)
    if wmp_windows:
        target_window = wmp_windows[0]
        
        print("Bringing window to the foreground...")
        try:
            # Force the window to be active so it receives our clicks
            target_window.activate()
            time.sleep(1)
            
            print("Maximizing window...")
            target_window.maximize()
            time.sleep(1)
            return True
            
        except Exception as e:
            print(f"Error manipulating the window: {e}")
            # Fallback if Windows blocks the activate command
            pyautogui.hotkey('alt', 'tab') 
            return False
    else:
        print("Error: Could not locate the WMP window even after launching.")
        return False

def click_ui_element(image_filename, description, confidence_level=0.8):
    """Searches the screen for an image and clicks its center."""
    print(f"Searching for {description}...")
    try:
        element_location = pyautogui.locateCenterOnScreen(image_filename, confidence=confidence_level)
        
        if element_location is not None:
            pyautogui.click(element_location)
            print(f"Success: Clicked {description}.")
            return True
        else:
            print(f"Error: Could not find '{image_filename}' on the screen.")
            return False
            
    except pyautogui.ImageNotFoundException:
         print(f"Error: PyAutoGUI could not locate '{image_filename}'.")
         return False
    except Exception as e:
         print(f"Unexpected error with {description}: {e}")
         return False

def search_and_add_to_burn_list(search_term):
    print("Searching for the stable anchor (Burn button)...")
    
    anchor_location = pyautogui.locateCenterOnScreen('search_anchor.png', confidence=0.8)

    if not anchor_location:
        print("Error: Could not find 'burn_anchor.png'.")
        return False

    anchor_x, anchor_y = anchor_location
    
    # 1. Calculate Search Bar offset and click it
    search_bar_x = anchor_x - 130  # Adjust these numbers based on your tracker math
    search_bar_y = anchor_y   
    pyautogui.click(search_bar_x, search_bar_y)
    time.sleep(0.5)
    
    # 2. Clear old text and search
    pyautogui.hotkey('ctrl', 'a') # This clears the search bar
    pyautogui.press('backspace')
    pyperclip.copy(search_term)
    pyautogui.hotkey('ctrl', 'v')
    pyautogui.press('enter')
    
    print("Waiting for search results to load...")
    time.sleep(2) # Crucial: Wait for WMP to actually find and display the songs

    # ---------------------------------------------------------
    # THE SELECT ALL OPERATION HAPPENS HERE
    # ---------------------------------------------------------
    
    # 3. Shift focus to the results pane
    # Moving the mouse 150 pixels straight down from the search bar 
    # places it directly into the list of songs.
    results_pane_x = search_bar_x - 600
    results_pane_y = search_bar_y + 74 
    
    print("Clicking results pane to gain focus...")
    # pyautogui.click(results_pane_x, results_pane_y)
    # time.sleep(0.5)

    # 4. SELECT ALL
    print("Selecting all songs...")
    pyautogui.hotkey('ctrl', 'a')
    # time.sleep(0.5)

    # ---------------------------------------------------------

    # 5. Right-click the highlighted songs
    print("Opening context menu...")
    pyautogui.click(results_pane_x, results_pane_y, button='right')
    # time.sleep(0.5)
    
    # 6. Navigate context menu via keyboard (Adjust arrow presses as needed)
    print("Adding to burn list...")
    pyautogui.press('down', presses=4, interval=0.2) # Down to 'Add to'
    pyautogui.press('right')                         # Open submenu
    # time.sleep(0.3)
    pyautogui.press('down', presses=1, interval=0.2) # Down to 'Burn list'
    pyautogui.press('enter')                         # Execute

    return True
def main():
    print("--- Starting WMP Automation PoC ---")
    
    # Step 1: Launch and prepare the environment
    if not launch_and_maximize_wmp():
        sys.exit(1)

    # Step 2: Navigate the UI
    # Note: If WMP opens directly to the Music library, you might only need the Music.png check.
    # Uncomment the others if your specific workflow requires clicking them sequentially.
    
    # if not click_ui_element('library_btn.png', "Library Button"): sys.exit(1)
    
    if not click_ui_element('Music.png', "Music Category"): 
        sys.exit(1)
        
    # if not click_ui_element('all_music_btn.png', "All Music Category"): sys.exit(1)

    # Step 3: Perform the anchored search
    target_artist = "ישי ריבו"
    if not search_and_add_to_burn_list(target_artist):
        sys.exit(1)
    
    print("--- PoC Execution Completed Successfully ---")

if __name__ == "__main__":
    main()