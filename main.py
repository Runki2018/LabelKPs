import sys
from PySide2.QtWidgets import QApplication
# from app import myGUI
from app_gui import myGUI


def main():
    app = QApplication(sys.argv)
    GUI = myGUI()  
    GUI.ui.show()
    sys.exit(app.exec_())

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()


 