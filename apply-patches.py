 # 
 # This file is part of the device_xiaomi_mondrian-patch distribution (https://github.com/flakeforever/device_xiaomi_mondrian-patch).
 # Copyright (c) 2024 Flakeforever.
 # 
 # This program is free software: you can redistribute it and/or modify  
 # it under the terms of the GNU General Public License as published by  
 # the Free Software Foundation, version 3.
 #
 # This program is distributed in the hope that it will be useful, but 
 # WITHOUT ANY WARRANTY; without even the implied warranty of 
 # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU 
 # General Public License for more details.
 #
 # You should have received a copy of the GNU General Public License 
 # along with this program. If not, see <http://www.gnu.org/licenses/>.
 #

import curses
import os
import subprocess

base_dir = os.path.dirname(os.path.abspath(__file__))

# Function to get all patch files in the directory and its subdirectories
def get_patch_files(directory):
    patch_files = []
    for root, _, files in os.walk(directory):
        for file_name in files:
            if file_name.endswith(".patch"):
                file_path = os.path.join(root, file_name)
                patch_files.append(file_path)
    patch_files = sorted(patch_files)
    return patch_files

def convert_to_item(file_name):
    item = {}
    item["full_path"] = file_name

    # Remove base_dir and patch file name, and extract the middle subdirectory
    relative_path = file_name.replace(base_dir, "").strip("/")
    subdirectory = os.path.dirname(relative_path)
    item["subdirectory"] = subdirectory.replace("_", "/")

    # Extract patch file name
    patch_file_name = os.path.basename(file_name)
    item["patch_file_name"] = patch_file_name

    item["enabled"] = 0
    return item

def create_menu(items):
    # Initialize curses
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)

    # Set up colors
    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)  # Selected item color
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)  # Unselected item color

    # Set up menu
    menu_win = curses.newwin(curses.LINES - 2, curses.COLS - 2, 1, 1)
    menu_win.box()
    menu_win.addstr(0, 2, "Select patches to enable (use spacebar to toggle)")
    menu_win.addstr(1, 2, "Press ENTER to execute all selected patches.")

    # Display menu items
    selected_indices = []
    for i, item in enumerate(items):
        checkbox = "[ ]"
        if item["enabled"]:
            checkbox = "[X]"
            selected_indices.append(i)
        color_pair = curses.color_pair(1) if i == 0 else curses.color_pair(2)
        menu_win.addstr(i + 3, 2, checkbox + " " + item["subdirectory"] + "/" + item["patch_file_name"], color_pair)

    def update_item(current_item, item, focus):
        color_pair = curses.color_pair(2)
        if focus:
            color_pair = curses.color_pair(1)   
        if current_item in selected_indices:
            menu_win.addstr(current_item + 3, 2, "[X]" + " " + item["subdirectory"] + "/" + item["patch_file_name"], color_pair)
        else:
            menu_win.addstr(current_item + 3, 2, "[ ]" + " " + item["subdirectory"] + "/" + item["patch_file_name"], color_pair)       

        
    # Handle menu navigation and item selection
    current_item = 0
    menu_win.keypad(True)
    while True:
        menu_win.refresh()
        key = menu_win.getch()

        if key == ord('\n'):  # Press ENTER to save and exit
            break
        elif key == ord(' '):  # Toggle item selection
            item = items[current_item]
            if current_item in selected_indices:
                selected_indices.remove(current_item)
                update_item(current_item, item, 1)
            else:
                selected_indices.append(current_item)
                update_item(current_item, item, 1)
        elif key == curses.KEY_UP:
            if current_item > 0:
                update_item(current_item, items[current_item], 0)            
                current_item -= 1
                update_item(current_item, items[current_item], 1)
        elif key == curses.KEY_DOWN:
            if current_item < len(items) - 1:
                update_item(current_item, items[current_item], 0)            
                current_item += 1
                update_item(current_item, items[current_item], 1)

    # Clean up curses
    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()

    # Update enabled field based on selected indices
    for i in range(len(items)):
        items[i]["enabled"] = 1 if i in selected_indices else 0

    return items

# Get patch files in the base directory and its subdirectories
patch_files = get_patch_files(base_dir)

items = []
# Print the patch files
print("Patch files:")
for patch_file in patch_files:
    item = convert_to_item(patch_file)
    items.append(item)

updated_items = create_menu(items)

# Print all items
print("Updated items:")
current_path = os.getcwd()
for item in updated_items:
    if item["enabled"] == 1:
        full_path = os.path.join(current_path, item["full_path"]) 
        git_command = f'git -C {item["subdirectory"]} am {full_path}'
        print("Executing:", git_command)
        result = subprocess.run(git_command, shell=True)
        if result.returncode == 0:
            print("Execute successfully")
        else:
            print("Execute failed")