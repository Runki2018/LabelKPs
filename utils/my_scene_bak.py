import math
from PySide2.QtCore import (QCoreApplication, QDate, QDateTime, QMetaObject,
                            QObject, QPoint, QRect, QSize, QTime, QUrl, Qt)
from PySide2.QtGui import (QBrush, QColor, QConicalGradient, QCursor, QFont,
                           QFontDatabase, QIcon, QKeySequence, QLinearGradient, QPalette, QPainter,
                           QPixmap, QTransform, QRadialGradient, QPen, QPainterPath)
from PySide2.QtWidgets import *


class MyScene(QGraphicsScene):
    """
        自定义的场景，层次用法： QGraphicsView -> QGraphicsScene -> QGraphicsItem
        该场景定义了显示图像、标注关键点和边界框、图像缩放等功能。
    """
    # 6种颜色，分别是手腕1，拇指4，食指4，中指4，无名指4，小指4的关键点颜色
    pen_color = [Qt.red, Qt.cyan, QColor(170, 85, 130), QColor(222, 96, 27), Qt.blue, Qt.green]  # 预设笔的颜色
    pen_width = 5  # 预设笔的宽度
    wh = 5  # 关键点的大小
    scaleRatio = 1  # 图像缩放的比例

    def __init__(self, listWidget):  # 初始函数
        super(MyScene, self).__init__()  # 实例化QGraphicsScene
        self.listWidget = listWidget  # 列表控件，用于显示21个关键点坐标
        self.wheel_degree = 0  # 滚轮滚动的角度，范围-150~150，每次滚动15
        self.pen = QPen()  # 实例QPen
        self.pen.setWidth(self.pen_width)  # 设置宽度

        self.points_list = []
        self.current_point = ""
        self.image = None   # 单独存储原始图像，用于后面的缩放保持质量，每次缩放基于原图。
        self.my_pixmap_item = None
        self.w = self.h = 0  # 图片的原始宽高
        self.coordinate = (0, 0)  # 鼠标所在的场景坐标
        self.group = None

    def init_scene(self, img_path, keypoints):
        # 先清空当前所有的图元Item
        if self.points_list:
            self.points_list = []
            self.current_point = ""
            for item in self.items():
                self.removeItem(item)
            self.destroyItemGroup(self.group)
        # 读入图片，并将图片的大小设置为scene的大小
        self.image = QPixmap(img_path)  # 单独存储原始图像，用于后面的缩放保持质量，每次缩放基于原图。
        self.my_pixmap_item = self.addPixmap(self.image)
        self.w, self.h = self.image.size().toTuple()  # 场景的大小 = Pixmap图元的大小
        w, h = self.image.size().toTuple()  # 场景的大小 = Pixmap图元的大小
        self.setSceneRect(QRect(0, 0, w, h))  # 设置场景起始及大小，默认场景是中心为起始，不方便后面的代码
        # 添加关键点图元
        for i, (x, y) in enumerate(keypoints):
            self.addPoint(i, x, y)
        # print(self.items(order=Qt.AscendingOrder))
        pixmap_points = self.items(order=Qt.AscendingOrder)  # 获取当前所有的图元，包含图片和关键点
        self.group = self.createItemGroup(pixmap_points)  # 将图片和关键点划分为一个组，使他们同时发生映射变化

    def addPoint(self, index, x, y):
        if index == 0:
            self.pen.setColor(self.pen_color[0])  # 设置颜色
        else:
            i = (index - 1) // 4 + 1
            self.pen.setColor(self.pen_color[i])  # 设置颜色
        self.current_point = self.addEllipse(x, y, self.wh, self.wh, self.pen)
        self.current_point.setAcceptHoverEvents(True)  # 给每个点设置鼠标悬浮事件，用于提示该点信息
        self.points_list.append(self.current_point)

    def mousePressEvent(self, event):  # 重载鼠标事件
        pos = event.scenePos()  # 当前鼠标事件发生的场景坐标QPointF(x,y)
        x, y = pos.toTuple()
        old_point = self.current_point
        if event.button() == Qt.LeftButton:  # 仅左键事件触发
            transform = QTransform(1, 0, 0, 0, 1, 0, 0, 0, 1)  # 仿射变换矩阵，这里是不变
            self.current_point = self.itemAt(pos, transform)
            print("选中的图元：", self.current_point)
            if isinstance(self.current_point, QGraphicsEllipseItem):
                self.current_point.setRect(x, y, self.wh*2, self.wh*2)  # 放大选中的点
                self.select_listItem()
            else:
                self.current_point = old_point  # 防止选中了点后，没按右键释放，而是选中了图片图元

        if event.button() == Qt.RightButton:  # 仅右键事件触发
            # 如果当前选中的Item是关键点，则将该关键点移动到当前光标所在位置
            if isinstance(self.current_point, QGraphicsEllipseItem):
                self.current_point.setRect(QRect(x, y, self.wh, self.wh))
                print("释放的点：", self.current_point.rect())
                # print(self.current_point.acceptHoverEvents())
                self.current_point.setRect(x, y, self.wh, self.wh)  # 释放点时，其大小恢复正常
                self.update_listItem(x, y)  # 更新列表框中的关键点坐标数值
                self.update()

    def select_listItem(self):
        """使选中的列表项高亮显示"""
        index = self.points_list.index(self.current_point)
        item = self.listWidget.item(index)
        item.setSelected(True)
        return index, item

    def update_listItem(self, x, y):
        index, item = self.select_listItem()
        text = str(index + 1) + ": " + str((x, y))  # 更改item的坐标
        item.setText(text)

    def zoomRequest(self, delta):
        """处理滚轮事件中的场景的缩放请求"""
        # 场景缩放
        if delta > 0:  # 滚轮向前滑动，delta= 120 >0 ，反之为 -120
            scene_width_new = math.ceil(self.width() * 1.1)
            scene_height_new = math.ceil(self.height() * 1.1)
            self.scaleRatio = 1.1
        else:
            scene_width_new = math.floor(self.width() * 0.9)
            scene_height_new = math.floor(self.height() * 0.9)
            self.scaleRatio = 0.9
            # 已知bug，当缩放的过小，如消失后，图像不能再放大。这个可以最小缩放值来限制。
            if scene_width_new / self.w < 0.5:
                scene_width_new = self.width()
                scene_height_new = self.height()
                self.scaleRatio = 1
        # print(scene_width_new, scene_height_new)
        self.setSceneRect(QRect(0, 0, scene_width_new, scene_height_new))
        self.my_pixmap_item.setPixmap(self.image.scaled(
            QSize(scene_width_new, scene_height_new),
            Qt.IgnoreAspectRatio,
            Qt.SmoothTransformation))
        self.update()
        self.update_points_pos()

    # def update_points_pos(self):
    #     """缩放场景和PixmapItem后，需要更新图中关键点Item的位置"""
    #     for point in self.points_list:
    #         x, y, _, _ = point.rect().getRect()  # x,y,w,h
    #         x *= self.scaleRatio
    #         y *= self.scaleRatio
    #         # 取整，调整精度，否则关键点再多次缩放后会发生点的偏移
    #         if self.scaleRatio > 1:
    #             x, y = math.ceil(x), math.ceil(y)
    #         else:
    #             x, y = math.floor(x), math.floor(y)
    #         w, h = self.wh, self.wh
    #         point.setRect(QRect(x, y, w, h))
    #         self.current_point = point
    #         self.update_listItem(x, y)
    #         self.update()
    def update_points_pos(self):
        """缩放场景和PixmapItem后，需要更新图中关键点Item的位置"""
        sr = self.width() / self.w
        print("sr = ", sr)
        for i, point in enumerate(self.points_list):
            x, y = self.keypoints[i]
            x *= sr
            y *= sr
            lx, ly = self.center2LeftTop(x, y)
            # # 取整，调整精度，否则关键点再多次缩放后会发生点的偏移
            # if self.scaleRatio > 1:
            #     lx, ly = math.ceil(lx), math.ceil(ly)
            # else:
            #     lx, ly = math.floor(lx), math.floor(ly)
            w, h = self.wh, self.wh
            point.setRect(QRect(lx, ly, w, h))
            self.update_listItem(x, y)
            self.update()

    def wheelEvent(self, event):
        if event.modifiers() == Qt.CTRL:
            # Most mouse types work in steps of 15 degrees, in which case the delta value is
            # a multiple of 120 (== 15 * 8).
            self.zoomRequest(event.delta())

    def mouseMoveEvent(self, event):  # 重载鼠标移动事件
        if self.acceptMove:
            print("move !!!!!!")
            x, y = event.scenePos().toTuple()
            lx, ly = self.center2LeftTop(x, y)
            self.current_point.setRect(QRect(lx, ly, self.wh, self.wh))
            self.move = True

    def mouseReleaseEvent(self, event):  # 重载鼠标松开事件
        if event.button() == Qt.LeftButton and self.move:  # 判断鼠标发生过拖拽移动且左键松开
            x, y = event.scenePos().toTuple()
            self.move = False
            self.acceptMove = False
            self.wh = self.wh_const   # 释放后缩小关键点
            lx, ly = self.center2LeftTop(x, y)
            self.current_point.setRect(QRect(lx, ly, self.wh, self.wh))
            self.changeKeyPoints(x, y)