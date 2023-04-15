import sys
import os
import csv
import json
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QCheckBox, QScrollArea, QFrame
from PyQt5.QtCore import Qt

class PlexMetaManagerGUI(QWidget):
    def __init__(self):
        super().__init__()

        self.config_file = 'config.json'
        self.load_config()

        self.init_ui()

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as file:
                config = json.load(file)
                self.collections_folder_path = config.get('collections_folder', '')
                self.csv_save_location_path = config.get('csv_save_location', '')
        else:
            self.collections_folder_path = ''
            self.csv_save_location_path = ''

    def save_config(self):
        config = {
            'collections_folder': self.collections_folder.text(),
            'csv_save_location': self.csv_save_location.text()
        }
        with open(self.config_file, 'w') as file:
            json.dump(config, file)

    def init_ui(self):
        self.setWindowTitle('Plex Meta Manager Collections Report')
        self.resize(1280,720)

        vbox = QVBoxLayout()

        hbox1 = QHBoxLayout()
        hbox1.addWidget(QLabel('Collections Folder:'))
        self.collections_folder = QLineEdit(self.collections_folder_path)
        hbox1.addWidget(self.collections_folder)
        browse_collections_btn = QPushButton('Browse')
        browse_collections_btn.clicked.connect(self.browse_collections)
        hbox1.addWidget(browse_collections_btn)
        vbox.addLayout(hbox1)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(QLabel('Save CSV to:'))
        self.csv_save_location = QLineEdit(self.csv_save_location_path)
        hbox2.addWidget(self.csv_save_location)
        browse_csv_btn = QPushButton('Browse')
        browse_csv_btn.clicked.connect(self.browse_csv)
        hbox2.addWidget(browse_csv_btn)
        vbox.addLayout(hbox2)

        update_collections_btn = QPushButton('Update Collection List')
        update_collections_btn.clicked.connect(self.update_collections)
        vbox.addWidget(update_collections_btn)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        vbox.addWidget(self.scroll_area)

        generate_report_btn = QPushButton('Generate Reports')
        generate_report_btn.clicked.connect(self.generate_reports)
        vbox.addWidget(generate_report_btn)

        self.setLayout(vbox)

    def browse_collections(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Collections Folder')
        if folder:
            self.collections_folder.setText(folder)

    def browse_csv(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select CSV Save Location')
        if folder:
            self.csv_save_location.setText(folder)

    def update_collections(self):
        collections_path = self.collections_folder.text()
        if not os.path.isdir(collections_path):
            return

        collections = [folder for folder in os.listdir(collections_path) if os.path.isdir(os.path.join(collections_path, folder))]
        collections.sort()

        grid_layout = QGridLayout()
        self.checkboxes = []

        columns = 3  # Set the number of columns you want
        index = 0

        for collection in collections:
            collection_folder = os.path.join(collections_path, collection)
            log_files = [f for f in os.listdir(collection_folder) if os.path.isfile(os.path.join(collection_folder, f)) and f.endswith('.log')]

            include_collection = False

            for log_file in log_files:
                with open(os.path.join(collection_folder, log_file), 'r', encoding='utf-8') as file:
                    log_content = file.read()

                    movies_processed_line = next((line for line in log_content.split('\n') if 'Movies Processed' in line), None)
                    movies_missing_line = next((line for line in log_content.split('\n') if 'Movies Missing' in line), None)

                    if movies_processed_line or movies_missing_line:
                        include_collection = True
                        break

            if include_collection:
                row = index // columns
                col = index % columns
                checkbox = QCheckBox(collection)
                grid_layout.addWidget(checkbox, row, col)
                self.checkboxes.append(checkbox)
                index += 1

        frame = QFrame()
        frame.setLayout(grid_layout)
        self.scroll_area.setWidget(frame)



    def generate_reports(self):
        collections_path = self.collections_folder.text()
        save_path = self.csv_save_location.text()

        if not os.path.isdir(collections_path) or not os.path.isdir(save_path):
            return

        report_data = [['Collection Name', 'Movies in Collection', 'Movies Missing']]

        for checkbox in self.checkboxes:
            if checkbox.isChecked():
                collection_name = checkbox.text()
                collection_folder = os.path.join(collections_path, collection_name)
                log_files = [f for f in os.listdir(collection_folder) if os.path.isfile(os.path.join(collection_folder, f)) and f.endswith('.log')]

                num_movies = 0
                num_missing = 0

                for log_file in log_files:
                    with open(os.path.join(collection_folder, log_file), 'r', encoding='utf-8') as file:
                        log_content = file.read()

                        movies_processed_line = next((line for line in log_content.split('\n') if 'Movies Processed' in line), None)
                        if movies_processed_line:
                            num_movies += int(movies_processed_line.split("Movies Processed")[0].split()[-1])

                        movies_missing_line = next((line for line in log_content.split('\n') if 'Movies Missing' in line), None)
                        if movies_missing_line:
                            num_missing += int(movies_missing_line.split("Movies Missing")[0].split()[-1])

                report_data.append([collection_name, num_movies, num_missing])

        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        csv_filename = os.path.join(save_path, f'collections_report_{timestamp}.csv')

        with open(csv_filename, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerows(report_data)

        print(f'Report saved to {csv_filename}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PlexMetaManagerGUI()
    window.show()
    sys.exit(app.exec_())
