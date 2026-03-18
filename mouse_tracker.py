import pyautogui
import time

print("Coordinate Tracker Started.")
print("Move your mouse to find the X, Y coordinates.")
print("Press Ctrl+C in this terminal to stop.")
print("-" * 40)

try:
    while True:
        # Get current mouse X and Y
        x, y = pyautogui.position()
        # Print them dynamically on the same line
        print(f"Current Position ->  X: {x:<4} Y: {y:<4}", end='\r')
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nTracker stopped.")