from PySide2.QtCore import Qt
from PySide2.QtWidgets import QTreeWidgetItem, QStyle
from PySide2.QtGui import  QColor, QFont, QIcon, QPixmap
from pathlib import Path


class ParentTreeItem(QTreeWidgetItem):
    """树形控件中的父项,用于表示图片， 子项为该图片所有的手部实例
    http://pyside.digitser.net/1.2.1/zh-CN/PySide/QtGui/QTreeWidgetItem.html#PySide.QtGui.PySide.QtGui.QTreeWidgetItem.type
    https://blog.csdn.net/u012219045/article/details/123106611
    """

    def __init__(self, index, text, state, type=0):
        """

        Args:
            text (str): 图片名, 如 a.jpg
            state (str): 图片的检测状态 'Unchecked' | 'PartiallyChecked' | 'Checked'
            type (int, optional): Item的类型, 这里我随便设置为0. Defaults to 0.
        """
        super().__init__(type)
        self.setFlags(Qt.ItemFlag.ItemIsUserCheckable)  # 可选框属性
        self.setCheckState(0, Qt.Unchecked)  # 一般文件有多个数据项，我们只用到第一列 0
        # self.setIcon(0, QStyle.standardIcon(QStyle.SP_FileIcon))
        icon = QIcon(QPixmap('UI\icon\img.ico'))
        self.setIcon(0, icon)
        self._set_myText(index, text)
        self.set_myCheckState(state)

    def _set_myText(self, index=0, text=""):
        """给列表项添加自定义项，包括图标和底色"""
        self.setTextAlignment(0, Qt.AlignBottom)
        font = QFont()
        font.setBold(True)
        self.setFont(0, font)  # 字体加粗
        text = str(index + 1) + ": " + text
        self.setText(0, text)

    def set_myCheckState(self, check_state):
        """设置该列表项的检查状态"""
        self.setFlags(Qt.ItemFlag.ItemIsUserCheckable)  # 可选框属性
        if check_state == "Unchecked":
            self.setCheckState(0, Qt.Unchecked)
        elif check_state == "PartiallyChecked":
            self.setCheckState(0, Qt.PartiallyChecked)
        elif check_state == "Checked":
            self.setCheckState(0, Qt.Checked)
        else:
            print(" set_myCheckState() Error !")


class ChildTreeItem(ParentTreeItem):
    """Item of annotation"""
    def __init__(self, index, text, state, type=1):
        super().__init__(index, text, state, type)
        # self.setIcon(0, QStyle.standardIcon(QStyle.SP_FileLinkIcon))
        icon = QIcon(QPixmap('UI\icon\obj.ico'))
        self.setIcon(0, icon)
        