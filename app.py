"""程序入口。"""

import sys
from PySide6.QtWidgets import QApplication

from tft_analysis.application import configure_application
from tft_analysis.ui import MainWindow


def main():
    application = QApplication(sys.argv)
    configure_application(application)
    window = MainWindow()
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
