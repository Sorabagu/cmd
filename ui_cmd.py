# ui_cmd.py

import sys
import os
import json
import subprocess
import threading
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QLineEdit, QTextEdit, QWidget,
    QMenuBar, QAction, QMessageBox, QFileDialog, QLabel
)
from PyQt5.QtGui import QIcon, QPixmap, QTextCursor, QTextCharFormat, QColor
from PyQt5.QtCore import Qt, pyqtSignal, QObject


class CommandRunner(QObject):
    command_output = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.console_encoding = self.get_console_encoding()

    def get_console_encoding(self):
        try:
            result = subprocess.run(
                "chcp",
                shell=True,
                capture_output=True,
                text=True,
                encoding="cp850"
            )
            if result.stdout:
                return "cp" + result.stdout.strip().split(":")[-1].strip()
        except Exception:
            pass
        return "cp850"

    def run_command(self, command):
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                encoding=self.console_encoding,
                errors='replace'
            )
            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                output += f"Error:\n{result.stderr}"
            self.command_output.emit(output)
        except Exception as e:
            self.command_output.emit(f"Error: {str(e)}")


class CustomCmd(QMainWindow):
    def __init__(self):
        super().__init__()
        self.styles = self.load_styles()
        self.init_ui()
        self.command_runner = CommandRunner()
        self.command_runner.command_output.connect(self.update_output)

    def load_styles(self):
        styles_file = "bin/style.json"
        try:
            with open(styles_file, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            return {"styles": {}, "background": "bin/1/default1.jpg"}

    def save_styles(self):
        styles_file = "bin/style.json"
        try:
            with open(styles_file, "w", encoding="utf-8") as file:
                json.dump(self.styles, file, indent=4)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not save styles: {str(e)}")

    def init_ui(self):
        self.setWindowTitle("Custom CMD")
        self.setWindowIcon(QIcon("icon.ico"))
        self.setGeometry(100, 100, 1200, 720)

        self.bg_label = QLabel(self)
        self.bg_label.setScaledContents(True)
        self.bg_label.setGeometry(self.rect())

        self.output_area = QTextEdit(self)
        self.output_area.setReadOnly(True)
        self.output_area.setStyleSheet("background-color: rgba(30, 30, 30, 0.85); color: #dcdcdc;")

        self.input_line = QLineEdit(self)
        self.input_line.setPlaceholderText("Enter your command here...")
        self.input_line.returnPressed.connect(self.run_command)
        self.input_line.setStyleSheet("background-color: #1e1e1e; color: #dcdcdc; padding: 5px;")

        layout = QVBoxLayout()
        layout.addWidget(self.output_area)
        layout.addWidget(self.input_line)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.current_bg = self.styles.get("background", "bin/1/default1.jpg")
        self.set_background(self.current_bg)

        self.init_menu_bar()

    def init_menu_bar(self):
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)

        file_menu = menu_bar.addMenu("File")
        change_bg_action = QAction("Change Background", self)
        change_bg_action.triggered.connect(self.change_background)
        file_menu.addAction(change_bg_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        help_menu = menu_bar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def set_background(self, bg_path):
        if os.path.exists(bg_path):
            pixmap = QPixmap(bg_path)
            self.bg_label.setPixmap(pixmap)
            self.styles["background"] = bg_path
            self.save_styles()
        else:
            QMessageBox.warning(self, "Error", f"The background '{bg_path}' was not found.")

    def change_background(self):
        bg_path, _ = QFileDialog.getOpenFileName(self, "Choose a background", "bin/1", "Images (*.jpg *.png)")
        if bg_path:
            self.set_background(bg_path)

    def resizeEvent(self, event):
        self.bg_label.setGeometry(self.rect())
        super().resizeEvent(event)

    def append_text(self, text, color, is_bold=False, add_newline=True):
        cursor = self.output_area.textCursor()
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if is_bold:
            fmt.setFontWeight(75)
        cursor.setCharFormat(fmt)
        cursor.insertText(text)
        if add_newline:
            cursor.insertText("\n")
        self.output_area.setTextCursor(cursor)
        self.output_area.ensureCursorVisible()

    def run_command(self):
        command = self.input_line.text().strip()

        separator_color = self.styles.get("styles", {}).get("separator", {}).get("color", "orange")
        self.append_text("---", separator_color)

        if command.startswith("cmd "):
            command_name = command[4:].strip()
            self.display_enhanced_command(command_name)
        elif command == "list cmd":
            self.display_command_list()
        elif command:
            self.display_standard_command(command)

    def display_standard_command(self, command):
        prompt_color = self.styles.get("styles", {}).get("user_input", {}).get("prompt", {}).get("color", "red")
        input_color = self.styles.get("styles", {}).get("user_input", {}).get("input", {}).get("color", "blue")
        self.append_text(">", prompt_color, is_bold=True, add_newline=False)
        self.append_text(f" {command}", input_color)
        self.input_line.clear()
        thread = threading.Thread(target=self.command_runner.run_command, args=(command,))
        thread.start()

    def display_command_list(self):
        commands_file = "bin/commands.json"
        try:
            with open(commands_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                commands = data.get("commands", [])
                self.append_text("List of commands:", "yellow", is_bold=True)
                for cmd in commands:
                    self.append_text(f"{cmd['name']} - {cmd['description']}", "white")
        except Exception as e:
            self.append_text(f"Error loading commands: {str(e)}", "red")

    def display_enhanced_command(self, command_name):
        prompt_color = self.styles.get("styles", {}).get("user_input", {}).get("prompt", {}).get("color", "red")
        input_color = self.styles.get("styles", {}).get("user_input", {}).get("input", {}).get("color", "blue")
        self.append_text("> cmd", prompt_color, is_bold=True, add_newline=False)
        self.append_text(f" {command_name}", input_color)

        details_file = "bin/command_details.json"
        try:
            with open(details_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                for cmd in data.get("commands", []):
                    if cmd["name"].lower() == command_name.lower():
                        self.append_text(f"Command: {cmd['name']}", "cyan")
                        self.append_text(f"Description: {cmd['description']}", "white")
                        self.append_text("Examples:", "yellow")
                        for example in cmd["examples"]:
                            self.append_text(f"  - {example}", "lightgreen")
                        return
                self.append_text(f"Unknown command: {command_name}", "red")
        except Exception as e:
            self.append_text(f"Error loading details: {str(e)}", "red")

    def update_output(self, output):
        self.append_text(output.strip(), "white")

    def show_about(self):
        version = self.get_version_from_file()
        QMessageBox.information(
            self,
            "About",
            f"Custom CMD\nVersion {version}\nDesigned by SoraDev."
        )

    def get_version_from_file(self, file_path="bin/version.ini"):
        try:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as version_file:
                    for line in version_file:
                        if line.startswith("software_version"):
                            return line.split("=")[-1].strip()
        except Exception:
            pass
        return "Unknown"


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CustomCmd()
    window.show()
    sys.exit(app.exec_())
