
import sys
from PySide2.QtWidgets import QApplication, QMainWindow
from app import myGUI


def main():
    app = QApplication(sys.argv)
    GUI = myGUI()  # 一定要创建类的实例，才能调用实例方法
    GUI.ui.show()
    sys.exit(app.exec_())


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

