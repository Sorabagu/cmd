# cmd.pyw

import sys
import os
from PyQt5.QtWidgets import QApplication
from scripts.ui_cmd import CustomCmd

SOFTWARE_VERSION = "1.0.1"

def generate_version_file(version, file_path="bin/version.ini"):
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as version_file:
            version_file.write(f"[Version]\nsoftware_version={version}\n")
    except Exception as e:
        pass

if __name__ == "__main__":
    generate_version_file(SOFTWARE_VERSION)
    
    app = QApplication(sys.argv)
    
    window = CustomCmd()
    
    window.show()
    
    sys.exit(app.exec_())
