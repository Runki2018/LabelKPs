
import sys
from PySide2.QtWidgets import QApplication, QMainWindow
from app import my_UI


def main():
    app = QApplication(sys.argv)
    window = my_UI()  # 一定要创建类的实例，才能调用实例方法
    window.ui.show()
    sys.exit(app.exec_())


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

