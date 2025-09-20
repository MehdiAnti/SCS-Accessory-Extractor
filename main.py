import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import zipfile
from datetime import datetime
import logging
import threading
import shutil
import sys
import re
import time

# Needed stuff
APP_PATH = os.path.join("data", "converter_pix.exe")
SCS_FILES_PATH = os.path.join("data", "scs_files.txt")

# Initialize empty lists for files
ATS_FILES = []
ETS2_FILES = []
NEEDED_ACCS = []

LOG_FILENAME = 'log.txt'

# Delete the old log file if it exists
if os.path.exists(LOG_FILENAME):
    os.remove(LOG_FILENAME)

# Set up logging
logging.basicConfig(level=logging.INFO, filename=LOG_FILENAME,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Log application start
logging.info("Application started. Hi, here you can see application logs.")

# Check for necessary files at startup
if not os.path.exists(APP_PATH):
    logging.error("PIX 'converter_pix.exe' not found. Application will exit.")
    messagebox.showerror("Error", "PIX 'converter_pix.exe' not found. Application will exit.")
    sys.exit(1)

if not os.path.exists(SCS_FILES_PATH):
    logging.error("SCS files configuration 'scs_files.txt' not found. Application will exit.")
    messagebox.showerror("Error", "SCS files configuration 'scs_files.txt' not found. Application will exit.")
    sys.exit(1)

def load_scs_files():
    global ATS_FILES, ETS2_FILES, NEEDED_ACCS
    try:
        with open(SCS_FILES_PATH, 'r') as file:
            content = file.read()

        sections = content.split('}')
        for section in sections:
            if 'ets2_entries:' in section:
                ets2_part = section.split('{')
                if len(ets2_part) > 1:
                    ets2_entries = ets2_part[1].strip().splitlines()
                    ETS2_FILES = [line.strip() for line in ets2_entries if line.strip()]

            elif 'ats_entries:' in section:
                ats_part = section.split('{')
                if len(ats_part) > 1:
                    ats_entries = ats_part[1].strip().splitlines()
                    ATS_FILES = [line.strip() for line in ats_entries if line.strip()]

            elif 'needed_accs:' in section:
                needed_part = section.split('{')
                if len(needed_part) > 1:
                    needed_entries = needed_part[1].strip().splitlines()
                    NEEDED_ACCS = [line.strip() for line in needed_entries if line.strip()]

    except Exception as e:
        logging.error(f"Failed to load SCS files: {str(e)}")

# Call the function to load the SCS files at the start
load_scs_files()

def backup_files(kept_files, backup_dir):
    """Backup files from the folders to keep."""
    os.makedirs(backup_dir, exist_ok=True)
    
    for folder_path, files in kept_files.items():
        for file in files:
            original_file_path = os.path.join(folder_path, file)
            backup_file_path = os.path.join(backup_dir, os.path.relpath(original_file_path, start=os.path.dirname(folder_path)))
            os.makedirs(os.path.dirname(backup_file_path), exist_ok=True)
            try:
                shutil.copy2(original_file_path, backup_file_path)
                #logging.debug(f"Backed up file: {original_file_path} to {backup_file_path}")
            except (PermissionError, FileNotFoundError) as e:
                print(f"Error backing up file {original_file_path}: {e}")


def find_folders_to_keep(base_path, folders_to_keep):
    found_folders = {}
    for folder in folders_to_keep:
        found_folders[folder] = []  # Initialize a list for each folder
        for root, dirs, _ in os.walk(base_path):
            if folder in dirs:
                found_folders[folder].append(os.path.join(root, folder))  # Append all found paths
    return {k: v for k, v in found_folders.items() if v}


def clean_directory(path, temp_cleanup_folder):
    found_folders = find_folders_to_keep(path, NEEDED_ACCS)
    #logging.debug(f"Found folders to keep: {found_folders}")

    # Create a temporary directory in the system's temp folder
    os.makedirs(temp_cleanup_folder, exist_ok=True)

    # Move the specified folders to the temporary directory, maintaining their relative structure
    original_paths = []  # To keep the original paths for restoration

    for folder_name, folder_paths in found_folders.items():
        for folder_path in folder_paths:
            # Create the same relative structure in temp_dir
            relative_path = os.path.relpath(folder_path, start=path)
            temp_folder_path = os.path.join(temp_cleanup_folder, relative_path)
            os.makedirs(os.path.dirname(temp_folder_path), exist_ok=True)  # Create directories in temp
            shutil.move(folder_path, temp_folder_path)  # Move folder to temp
            original_paths.append((folder_name, folder_path))  # Store original path
            #logging.info(f"Moved {folder_path} to temporary location: {temp_folder_path}")

    # Clean the original directory
    for root, dirs, files in os.walk(path, topdown=False):
        # Remove all files
        for file_name in files:
            file_path = os.path.join(root, file_name)
            os.remove(file_path)
            #logging.info(f"Removed file: {file_path}")

        # Remove all subdirectories except those that we want to keep
        for dir_name in list(dirs):  # Use a copy of dirs for safe iteration
            dir_to_remove = os.path.join(root, dir_name)
            if not any(dir_to_remove == found_path for folder_paths in found_folders.values() for found_path in folder_paths):
                shutil.rmtree(dir_to_remove)
                #logging.info(f"Removed directory: {dir_to_remove}")

    # Move the specified folders back to their original locations
    for folder_name, original_path in original_paths:
        temp_folder = os.path.join(temp_cleanup_folder, os.path.relpath(original_path, start=path))
        if os.path.exists(temp_folder):
            # Move back to the exact original path
            shutil.move(temp_folder, original_path)
            print(f"Moved {temp_folder} back to {original_path}.")
        else:
            print(f"{temp_folder} does not exist and cannot be restored.")

def zip_temp_folder(folder_path, temp_folder, game_version):
    game_type = "ets2" if "Euro Truck Simulator 2" in folder_path else "ats" if "American Truck Simulator" in folder_path else ""
    version_suffix = f"{game_version}" if game_version else ""
    timestamp = datetime.now().strftime("%m%d_%H%M%S")

    zip_file_path = os.path.join(folder_path, f'{game_type}_{version_suffix}_packed_{timestamp}.zip')
    zip_file_path = zip_file_path.replace('\\', '/')

    try:
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for dirpath, _, filenames in os.walk(temp_folder):
                for file in filenames:
                    file_path = os.path.join(dirpath, file)
                    zip_file.write(file_path, os.path.relpath(file_path, temp_folder))

        logging.info(f"Temporary folder zipped to: {zip_file_path}")
    except Exception as e:
        logging.error(f"Failed to zip temporary folder: {str(e)}")

def process_file(file_path, temp_folder):
    file_name = os.path.basename(file_path)

    try:
        if file_name == "def.scs":
            arguments = [
                '/def/desktop/',
                '/def/vehicle/truck/',
                '/def/vehicle/trailer_owned/',
                '/def/vehicle/addon_hookups/'
            ]
        else:
            arguments = [
                '/def/vehicle/truck/',
                '/def/vehicle/trailer_owned/'
            ]

        for arg in arguments:
            if arg:
                command = [APP_PATH, '-b', file_path, '-extract_d', arg, '-e', temp_folder]
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                process.communicate()

                if process.returncode != 0:
                    logging.error(f"Error processing {file_name}")
                else:
                    logging.info(f"{file_name} processed successfully.")

    except Exception as e:
        logging.error(f"Exception processing {file_name}: {str(e)}")
        return False

    return True

def extract_game_version(folder_path, temp_folder):
    version_file_path = os.path.join(folder_path, "version.scs")

    if os.path.isfile(version_file_path):
        command = [APP_PATH, "-b", version_file_path, "-extract_d", "/", "-e", temp_folder]
        try:
            subprocess.run(command, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            sui_file_path = os.path.join(temp_folder, "version.sii")
            if os.path.isfile(sui_file_path):
                with open(sui_file_path, 'r', encoding='utf-8', errors='ignore') as file:
                    content = file.read()
                    match = re.search(r'version:\s*"([^"]*)"', content)
                    if match:
                        return match.group(1)
        except subprocess.CalledProcessError:
            logging.error(f"Error extracting version from {version_file_path}")

    return None


def get_temp_cleanup_folder():
    temp_folder = os.path.join(os.getenv('TEMP'), 'scs_cleanup_temp')
    os.makedirs(temp_folder, exist_ok=True)
    return temp_folder

def process_scs_files(folder_path, progress_var, progress_bar, file_list):
    if not os.path.exists(folder_path):
        messagebox.showerror("Error", "The specified folder does not exist.")
        return

    total_files = len(file_list)
    if total_files == 0:
        logging.error("No .scs files found for processing.")
        messagebox.showerror("Error", "No .scs files found for processing.")
        return

    all_successful = True
    start_time = datetime.now()

    temp_processing_folder = os.path.join(folder_path, "temp_proc")
    os.makedirs(temp_processing_folder, exist_ok=True)

    temp_cleanup_folder = get_temp_cleanup_folder()

    processed_files = []  # Track processed files

    # Show the progress bar
    progress_bar.pack(fill=tk.X)

    for i, file in enumerate(file_list):
        file_path = os.path.join(folder_path, file)
        if os.path.exists(file_path):
            if process_file(file_path, temp_processing_folder):
                processed_files.append(file)
            else:
                all_successful = False
        else:
            logging.warning(f"File not found, skipping: {file}")

        #progress_var.set(progress_var.get() + (100 / total_files))
        #progress_bar.update_idletasks()
        progress_var.set((i + 1) / total_files * 50)
        progress_bar.update_idletasks()

    
    game_version = extract_game_version(folder_path, temp_processing_folder)

    found_folders = find_folders_to_keep(temp_processing_folder, NEEDED_ACCS)

    total_cleanup_steps = len(found_folders) + 1
    progress_inc = 15 / total_cleanup_steps
        
    # Move unwanted files to the cleanup folder
    clean_directory(temp_processing_folder, temp_cleanup_folder)

    progress_var.set(50 + progress_inc * 1)
    progress_bar.update_idletasks()

    if all_successful:
        try:
            # Now zip the processed files from the processing folder
            zip_temp_folder(folder_path, temp_processing_folder, game_version)
            progress_var.set(65)
            progress_bar.update_idletasks()
        except Exception as e:
            logging.error(f"Cleanup or zipping failed: {str(e)}")

        # Clean up the processing temp folder after zipping
        try:
            shutil.rmtree(temp_processing_folder)  # Clean up the processing temp folder
            shutil.rmtree(temp_cleanup_folder)      # Clean up the cleanup temp folder
        except Exception as e:
            logging.error(f"Failed to delete temp folders: {str(e)}")

        for i in range(15):
            progress_var.set(85 + i)
            progress_bar.update_idletasks()
            time.sleep(0.02)

    end_time = datetime.now()
    duration = end_time - start_time
    logging.info(f"Processing completed in: {duration}")

    if processed_files:
        messagebox.showinfo("Info", "Processing completed!")
    else:
        messagebox.showinfo("Info", "No files were successfully processed.")

    # Reset and hide the progress bar after the message box is acknowledged
    progress_var.set(0)
    progress_bar.pack_forget()


def threaded_process(folder_path, file_list):
    process_scs_files(folder_path, progress_var, progress_bar, file_list)

def select_folder():
    folder_path = filedialog.askdirectory(title="Select the folder containing .scs files")
    if folder_path:
        logging.info(f"Folder selected: {folder_path}")
        progress_var.set(0)

        # Check for SCS files in the selected folder
        files_in_folder = [f for f in os.listdir(folder_path) if f.endswith('.scs')]
        if not files_in_folder:
            logging.error("No .scs files found in the selected path.")
            messagebox.showerror("Error", "No .scs files found in the selected path. Please select another path.")
            return

        # Determine the appropriate file list based on folder name
        if "Euro Truck Simulator 2" in folder_path:
            file_list = ETS2_FILES
        elif "American Truck Simulator" in folder_path:
            file_list = ATS_FILES
        else:
            messagebox.showerror("Error", "The selected folder does not contain valid SCS files.")
            return

        if not file_list:
            logging.error("No valid .scs files found for processing.")
            messagebox.showerror("Error", "No valid .scs files found for processing.")
            return

        threading.Thread(target=threaded_process, args=(folder_path, file_list)).start()

def on_closing():
    logging.info("Exit.")
    root.destroy()

def center_window(window):
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")

# GUI setup
root = tk.Tk()
root.title("SCS File Processor")
root.geometry("300x100")
root.resizable(False, False)

progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)

select_button = tk.Button(root, text="Select Folder", command=select_folder)
select_button.pack(pady=20)

root.protocol("WM_DELETE_WINDOW", on_closing)

center_window(root)
root.mainloop()
