import os
import csv
import glob
import configparser
import tkinter as tk
from tkinter import filedialog, ttk

config_filename = 'config.ini'

def load_config():
    config = configparser.ConfigParser()
    config.read(config_filename)

    if 'Collections' in config and 'selected_collections' in config['Collections']:
        selected_collections = config['Collections']['selected_collections'].split(',')
    else:
        selected_collections = []

    if 'Settings' in config and 'logs_folder' in config['Settings']:
        logs_folder = config['Settings']['logs_folder']
    else:
        logs_folder = None

    return selected_collections, logs_folder

def save_config(selected_collections, logs_folder):
    config = configparser.ConfigParser()
    config['Collections'] = {
        'selected_collections': ','.join(selected_collections)
    }
    config['Settings'] = {
        'logs_folder': logs_folder
    }

    with open(config_filename, 'w') as configfile:
        config.write(configfile)

def read_collection_logs(collection_folders, selected_collections):
    data = []

    for folder in collection_folders:
        collection_name = os.path.basename(os.path.normpath(folder))

        if collection_name in selected_collections:
            processed_count = 0
            missing_count = 0

            log_files = glob.glob(os.path.join(folder, '*.log'))

            for log_file in log_files:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                for line in lines:
                    if "Movies Processed" in line:
                        processed_count += int(line.split("Movies Processed")[0].split()[-1])
                    elif "Movies Missing" in line:
                        missing_count += int(line.split("Movies Missing")[0].split()[-1])

            data.append((collection_name, processed_count, missing_count))

    return data

def save_to_csv(collection_data, output_file):
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['Collection', 'Processed Movies', 'Missing Movies'])
        csvwriter.writerows(collection_data)

def browse_logs_folder():
    folder = filedialog.askdirectory(title='Select the folder containing the logs')
    if folder:
        logs_folder_var.set(folder)

def proceed_to_collections():
    global logs_folder
    logs_folder = logs_folder_var.get()
    if logs_folder:
        save_config(prev_selected_collections, logs_folder)
        collection_selection_screen()

def collection_selection_screen():
    folder_selection_frame.pack_forget()
    collection_selection_frame.pack()

    collection_folders = glob.glob(os.path.join(logs_folder, '*/'))

    for folder in collection_folders:
        folder = folder.rstrip(os.path.sep)
        collection_name = os.path.basename(folder)
        collection_var = tk.BooleanVar(value=collection_name in prev_selected_collections)
        collection_vars[collection_name] = collection_var
        cb = tk.Checkbutton(scrollable_frame, text=collection_name, variable=collection_var)
        cb.pack(anchor="w")

prev_selected_collections, logs_folder = load_config()

root = tk.Tk()
root.title("Plex Meta Manager Collection Report")

def generate_report():
    selected_collections = [name for name, var in collection_vars.items() if var.get()]
    save_config(selected_collections, logs_folder)

    collection_folders = glob.glob(os.path.join(logs_folder, '*/'))
    collection_data = read_collection_logs(collection_folders, selected_collections)
    output_file = os.path.join(logs_folder, 'collection_report.csv')
    save_to_csv(collection_data, output_file)

    print("Report saved as:", output_file)


# Folder Selection Frame
folder_selection_frame = ttk.Frame(root)
folder_selection_frame.pack(padx=10, pady=10)

logs_folder_var = tk.StringVar(value=logs_folder)
logs_folder_entry = ttk.Entry(folder_selection_frame, textvariable=logs_folder_var, width=60)
logs_folder_entry.pack(side="left", padx=(0, 5))

browse_button = ttk.Button(folder_selection_frame, text="Browse", command=browse_logs_folder)
browse_button.pack(side="left")

proceed_button = ttk.Button(folder_selection_frame, text="Proceed", command=proceed_to_collections)
proceed_button.pack(side="left", padx=(5, 0))

# Collection Selection Frame
collection_selection_frame = ttk.Frame(root)

frame = ttk.Frame(collection_selection_frame)
frame.pack(padx=10, pady=10)

canvas = tk.Canvas(frame, width=500, height=500)
scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
scrollable_frame = ttk.Frame(canvas)

scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

collection_vars = {}

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

generate_button = ttk.Button(collection_selection_frame, text="Generate Report", command=generate_report)
generate_button.pack(pady=(10, 0))

root.mainloop()
