from PySide2.QtWidgets import QListWidgetItem,QListWidget,QListView
from PySide2.QtCore import Qt
from PySide2 import QtGui, QtWidgets, QtCore
from PySide2.QtWidgets import QStyle
from PySide2.QtGui import QPalette, QColor, QBrush, QFont


class my_kps_Item(QtWidgets.QListWidgetItem):
    """
        给关键点列表添加实现自己的关键点项
    """
    type_list = ["\t手腕", "\t拇指", "\t食指", "\t中指", "\t无名指", "\t小指"]
    color = [Qt.red, QColor(64, 224, 208), Qt.magenta, QColor(222, 96, 27), Qt.blue, Qt.green]

    def __init__(self, index=0, text=None):
        super(my_kps_Item, self).__init__()
        self.set_myText(index, text)
        self.set_myTextColor(index)
        # self.set_myBackgroundColor(index)

    def set_myText(self, index=0, text=""):
        """给列表项添加自定义项，包括图标和底色"""
        self.setTextAlignment(Qt.AlignBottom)
        font = QFont()
        font.setBold(True)
        self.setFont(font)  # 字体加粗
        text = str(index + 1) + "\t" + text
        if index == 0:
            finger = self.type_list[0]
        else:
            index = (index - 1) // 4 + 1
            finger = self.type_list[index]
        text = text + finger
        self.setText(text)

    def set_myBackgroundColor(self, index):
        if index == 0:
            self.setBackgroundColor(self.color[0])
        else:
            index = (index - 1) // 4 + 1
            self.setBackgroundColor(self.color[index])

    def set_myTextColor(self, index):
        if index == 0:
            self.setTextColor(self.color[0])
        else:
            index = (index - 1) // 4 + 1
            self.setTextColor(self.color[index])


# class HTMLDelegate(QtWidgets.QStyledItemDelegate):
#     """  用HTML语言实现list里有颜色和可选框显示的listItem
#         http://pyside.digitser.net/5.15/zh-CN/PySide2/QtWidgets/QStyledItemDelegate.html
#         https://stackoverflow.com/a/2039745/4158863
#     """
#     def __init__(self, parent=None):
#         super(HTMLDelegate, self).__init__()
#         self.doc = QtGui.QTextDocument(self)
#
#     def paint(self, painter, option, index):
#         painter.save()
#         options = QtWidgets.QStyleOptionViewItem(option)
#
#         self.initStyleOption(options, index)
#         self.doc.setHtml(options.text)
#         options.text = ""
#
#         style = (
#             QtWidgets.QApplication.style()
#             if options.widget is None
#             else options.widget.style()
#         )
#         style.drawControl(QStyle.CE_ItemViewItem, options, painter)
#
#         ctx = QtGui.QAbstractTextDocumentLayout.PaintContext()
#
#         if option.state & QStyle.State_Selected:
#             ctx.palette.setColor(
#                 QPalette.Text,
#                 option.palette.color(
#                     QPalette.Active, QPalette.HighlightedText
#                 ),
#             )
#         else:
#             ctx.palette.setColor(
#                 QPalette.Text,
#                 option.palette.color(QPalette.Active, QPalette.Text),
#             )
#
#         textRect = style.subElementRect(QStyle.SE_ItemViewItemText, options)
#
#         if index.column() != 0:
#             textRect.adjust(5, 0, 0, 0)
#
#         thefuckyourshitup_constant = 4  # 哈哈，看来原作者在这里发飙了。
#         margin = (option.rect.height() - options.fontMetrics.height()) // 2
#         margin = margin - thefuckyourshitup_constant
#         textRect.setTop(textRect.top() + margin)
#
#         painter.translate(textRect.topLeft())
#         painter.setClipRect(textRect.translated(-textRect.topLeft()))
#         self.doc.documentLayout().draw(painter, ctx)
#
#         painter.restore()
#
#     def sizeHint(self, option, index):
#         thefuckyourshitup_constant = 4
#         return QtCore.QSize(
#             self.doc.idealWidth(),
#             self.doc.size().height() - thefuckyourshitup_constant,
#         )





