"""Module providing a widget with Restart and Exit buttons for the application.

This widget allows the user to save data and exit the application or restart it.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QApplication
from PyQt5.QtCore import Qt, QSize

try:
    from libs import eventManager
except:
    from . import eventManager


class TabViewRestartExit(QWidget):
    """Widget containing Restart and Exit buttons for application control."""
    def __init__(self, camAdapater):
        super().__init__()
        self.camAdapater = camAdapater
        self.initUI()

    def initUI(self):
        """Initialize the user interface with Restart and Exit buttons."""
        # Create main layout
        mainLayout = QHBoxLayout()

        # Exit Button
        self.exit_button = QPushButton('Save and Exit')
        self.exit_button.setFixedSize(QSize(500, 80))
        eventManager.registerEvent("exitButtonClicked", self.exit_button.clicked)        
        exit_layout = QVBoxLayout()
        exit_layout.addWidget(self.exit_button)
        exit_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Restart Button
        self.restart_button = QPushButton('Restart')
        self.restart_button.setFixedSize(QSize(500, 80))       
        eventManager.registerEvent("restartButtonClicked", self.restart_button.clicked)
        restart_layout = QVBoxLayout()
        restart_layout.addWidget(self.restart_button)
        restart_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Add buttons to main layout
        mainLayout.addLayout(exit_layout)
        mainLayout.addLayout(restart_layout)

        self.setLayout(mainLayout)
