from PySide2.QtWidgets import QGraphicsItem
from PySide2.QtGui import QPainter, QPainterPath, QTransform, QBrush, QColor
from PySide2.QtCore import QRectF, Qt, QPoint, QRect
from PySide2.QtWidgets import QStyleOptionGraphicsItem, QGraphicsEllipseItem


class my_item(QGraphicsItem):
    """
    为GraphicsView的场景实现一个画关键点的自定义图元, 现在没被采用。
    场景通过boundingRect()和shape()决定图元的位置和交互。
    API 参考：
    http://pyside.digitser.net/5.15/zh-CN/PySide2/QtWidgets/
    QGraphicsItem.html#PySide2.QtWidgets.PySide2.QtWidgets.QGraphicsItem.setSelected
    """
    # 设置光标类型
    CURSOR_Default = Qt.ArrowCursor
    CURSOR_DragMove = Qt.DragMoveCursor
    CURSOR_ClosedHand = Qt.ClosedHandCursor
    CURSOR_Cross = Qt.CrossCursor
    CURSOR_PointingHand = Qt.PointingHandCursor
    # 绘制模式
    MODE_Default = 0
    MODE_HoverText = 1

    # 画刷配置
    point_color = [Qt.red, Qt.cyan, QColor(170, 85, 130), QColor(222, 96, 27), Qt.blue, Qt.green]

    # 点的宽高
    wh = 10  # 取偶数，方便待会除2取整

    def __init__(self, x, y, color_i, parent=None):
        super(my_item, self).__init__()
        self.Type = QGraphicsItem.UserType + 1
        # self.setFlag(self.ItemIsMovable, True)  # 允许鼠标移动图元
        # self.setFlag(self.ItemIsSelectable, True)
        # self.setAcceptHoverEvents(True)
        # self.setAcceptDrops(True)
        print("hover flag = ", self.acceptHoverEvents())
        self.paintMode = self.MODE_Default
        self.brush = QBrush()
        self.brush.setStyle(Qt.SolidPattern)  # 实心填充模式
        self.brush.setColor(self.point_color[color_i])
        print("pos = ", self.pos())
        print("scenePos = ", self.scenePos())
        self.setParentItem(parent)
        print("-" * 20)
        print(self.parentItem())
        self.mapFromParent(0,0,224,224)
        self.setPos(x, y)
        self.x = x
        self.y = y
        print("-" * 20)

    def sceneBoundingRect(self):
        x, y = self.pos().toTuple()  # x,y 为边界框中心点坐标
        print("SB")
        return QRectF(x, y, self.wh, self.wh)

    def boundingRect(self):
        """每次paint绘图前自动调用，返回该图元的绘图面积,决定了图元的绘制区域"""
        x, y = self.pos().toTuple()  # x,y 为边界框中心点坐标
        # return QRectF(x, y, self.wh, self.wh)
        return QRectF(0, 0, 224, 224)

    def shape(self):
        """自动调用，决定了交互的边界线范围，不设置正确的shape,事件失效或不灵敏"""
        path = QPainterPath()
        x, y = self.pos().toTuple()
        if self.paintMode == self.MODE_Default:
            path.addEllipse(x, y, self.wh, self.wh)
        elif self.paintMode == self.MODE_HoverText:
            path.addRoundRect(QRect(x, y, self.wh*2, self.wh*2), 25)
        return path

    def paint(self, painter, option, widget=None):
        """该方法在创建该图元实例时自动调用并实现该图元的绘制"""
        x, y = self.pos().toTuple()
        lx, ly = x - self.wh / 2, y - self.wh / 2  # 计算左上角点坐标
        lx = lx if lx > 0 else 0
        ly = ly if ly > 0 else 0
        if self.paintMode == self.MODE_Default:
            painter.setBrush(self.brush)
            painter.drawEllipse(x, y, self.wh, self.wh)
        elif self.paintMode == self.MODE_HoverText:
            painter.setBrush(self.brush)
            painter.drawRoundRect(lx, ly, self.wh*2, self.wh*2, 25, 25)

    def type(self):
        return self.Type

    # 事件
    # def dropEvent(self, event):
    # """必须设置接收拖拽的标注为真，该事件才生效"""
    #     self.setPos(event.pos())
    #     print("drag !")

    # def hoverEnterEvent(self, event):
    #     """要想图元的悬浮事件生效，那么场景scene中不要重写mouseMoveEvent"""
    #     print("Hover In !")
    #     self.setCursor(self.CURSOR_PointingHand)
    #     self.paintMode = self.MODE_HoverText
    #     option = QStyleOptionGraphicsItem()
    #     painter = QPainter()
    #     self.paint(painter, option)
    #     self.update()
    #
    # def hoverLeaveEvent(self, event):
    #     self.setCursor(self.CURSOR_Default)
    #     self.paintMode = self.MODE_Default
    #     self.update()
    #     print("Hover Out !")
