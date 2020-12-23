import math
import sys

from PySide2.QtCore import QFile, QIODevice, QSize
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QFileDialog
from utils.ListItem import my_kps_Item, my_files_Item
from utils.my_scene import MyScene
from utils.label import label_it
from PySide2.QtGui import QPixmap, QIcon


class my_UI:

    def __init__(self):
        # 加载 ui
        # ui_file_name = "./UI/labelKPs.ui"
        ui_file_name = "./UI/labelKPs_file.ui"
        ui_file = QFile(ui_file_name)
        if not ui_file.open(QIODevice.ReadOnly):
            print("Cannot open {}: {}".format(ui_file_name, ui_file.errorString()))
            sys.exit(-1)
        loader = QUiLoader()
        self.ui = loader.load(ui_file)
        ui_file.close()
        if not self.ui:
            print(loader.errorString())
            sys.exit(-1)

        # self.ui = QUiLoader().load("./UI/labelKPs.ui")
        # 定义控件，方便补全代码
        self.ui.setWindowIcon(QIcon('hand_icon.ico'))

        # button:
        self.loadButton = self.ui.loadButton  # 图片加载目录
        self.saveButton = self.ui.saveButton  # 标注保存目录
        self.saveButton.setEnabled(False)
        self.preButton = self.ui.preButton  # 上一张
        self.preButton.setEnabled(False)
        self.nextButton = self.ui.nextButton  # 下一张
        self.nextButton.setEnabled(False)
        self.goButton = self.ui.goButton  # 跳转
        self.goButton.setEnabled(False)
        # self.clearButton = self.ui.clearButton  # 清空

        # radiobutton:
        # self.bbox_radioButton = self.ui.bbox_radioButton  # 画边界框单选框
        # self.kps_radioButton = self.ui.kps_radioButton  # 画关键点单选框

        # label:
        self.process_number = self.ui.number_label  # 显示当前已处理的图片数/总图片数
        self.hintBox = self.ui.hint  # 提示框
        self.example_caption = self.ui.label_caption
        self.example_picture = self.ui.label_picture
        self.example_caption.setText("手腕1个点，其余手指各4个点，共21个点。\n"
                                     "改点的两种鼠标操作方式：\n 1、左键点击后拖拽，释放左键\n"
                                     " 2、按左键点击选中，鼠标移动至合适位置后，按右键释放")
        self.example_picture.setPixmap(QPixmap("./example.png"))

        # lineEdit
        self.lineEdit = self.ui.lineEdit  # 输入框，用于输入将跳转的图片数

        # listWidget:
        self.listWidget_points = self.ui.listWidget_points  # 显示当前关键点坐标的列表框
        self.listWidget_files = self.ui.listWidget_files  # 显示图片文件的列表框

        # graphicsView:
        self.graphicsView = self.ui.graphicsView  # 图片框
        self.scene = MyScene(self.listWidget_points)  # 场景
        self.graphicsView.setScene(self.scene)

        # 定义事件
        self.loadButton.clicked.connect(self.load_dir)  # 加载图片文件夹
        self.saveButton.clicked.connect(self.save_dir)  # 选着保存文件夹
        self.preButton.clicked.connect(self.pre_img)  # 上一张图片
        self.nextButton.clicked.connect(self.next_img)  # 下一张图片
        self.goButton.clicked.connect(self.go_img)  # 下一张图片
        # self.g = QtWidgets.QGraphicsView

        # 加载和保持标注信息
        self.label = None

        # 定义实例变量
        self.load_dirpath = ""
        self.save_file = ""
        self.img_number = 0  # 图片总数
        self.index = 0  # 已处理的图片数
        self.points_list = []  # 当前手的关键点列表（未经修改）
        # self.raw_points_list = []  # 未经修改的关键点列表

    def load_dir(self):
        self.load_dirpath = QFileDialog.getExistingDirectory(self.ui, "选择图片加载目录", './')
        if self.load_dirpath != "":
            self.saveButton.setEnabled(True)  # 只有选择了图像加载路径后，才能选择标注保持路径
            self.hintBox.setText("提示:" + self.load_dirpath)
        else:
            self.hintBox.setText("提示：加载目录为空！")
        print("load images directory!")
        print(self.load_dirpath)

    def save_dir(self):
        self.save_file, _ = QFileDialog.getOpenFileName(self.ui, "选择标注文件", './', 'JSON files(*.json)')
        print("save images directory!")
        print(self.save_file)
        if self.save_file != "":
            self.label = label_it(self.save_file)
            self.img_number = self.label.image_number
            self.update_widget()
            self.init_listWidget_files()  # 初始化文件列表，只初始化一次
            self.preButton.setEnabled(True)
            self.nextButton.setEnabled(True)
            self.goButton.setEnabled(True)
            self.hintBox.setText("提示:" + self.save_file)
        else:
            self.hintBox.setText("提示：未选择标注文件！")

    def update_widget(self):
        """更新控件：显示当前图片数的标签、绘图框、关键点列表"""
        text = "图片数：" + str(self.label.index + 1) + "/" + str(self.img_number)
        self.process_number.setText(text)
        self.init_listWidget_points(self.label.get_raw_keypoints())
        self.init_graphicsView()

    def init_listWidget_points(self, keypoints):
        self.points_list = []
        self.listWidget_points.clear()
        for k in range(21):
            ki = 2 * k
            keypoint = (round(keypoints[ki], 2), round(keypoints[ki + 1], 2))
            self.points_list.append(keypoint)
            item_text = str(keypoint)
            item = my_kps_Item(k, item_text)
            self.listWidget_points.addItem(item)

    def init_graphicsView(self):
        """更新图像框图像和关键点，必须在更新关键点列表后执行"""
        img_path = self.load_dirpath + '/' + self.label.get_imagePath()
        print(img_path)
        self.scene.init_scene(img_path, self.points_list.copy())  # 深拷贝 -> 值传递，后面对比二者是否不同

    def init_listWidget_files(self):
        """初始化files框列表项"""
        self.listWidget_files.clear()
        images_list = self.label.images_list
        for i, img_info in enumerate(images_list):
            item_text = img_info["file_name"]
            check_state = self.label.image_CheckState(i)
            item = my_files_Item(i, check_state, item_text)
            self.listWidget_files.addItem(item)

    def set_CheckState(self, new_keypoints):
        """设置当前文件的检查状态,查看scene坐标与读入的初始坐标是否一致，一致则未修改，否则就修改过"""
        file_item = self.listWidget_files.item(self.label.index)
        for i, k in enumerate(new_keypoints):
            if k != self.points_list[i]:   # (x1,y1) != (x1',y1') ?
                self.label.set_image_CheckState("Checked")
                file_item.set_myCheckState("Checked")
                break
        if self.label.image_CheckState(self.label.index) != "Checked":
            self.label.set_image_CheckState("PartiallyChecked")
            file_item.set_myCheckState("PartiallyChecked")

    def pre_img(self):
        # x = self.ui.graphicsView
        self.hintBox.setText("提示：上一页！")
        # 保持上一张图片标注信息，并将index+1, 当index合理时，才更新下一张图片
        self.label.index -= 1 if self.label.index > 0 else 0
        self.update_widget()

    def next_img(self):
        # 保持上一张图片标注信息，并将index+1, 当index合理时，才更新下一张图片
        self.hintBox.setText("提示：下一页！")
        keypoints = []
        for kp_tuple in self.scene.keypoints:
            keypoints.extend(kp_tuple)   # [(x1,y1)] -> [x1,y1]
        self.set_CheckState(self.scene.keypoints)
        self.label.save_annotations(keypoints)
        if self.label.index < self.img_number:
            self.update_widget()

    def go_img(self):
        """跳转到指定图像"""
        index = int(self.lineEdit.text())  # 输入的范围是 1~图像数
        if 0 < index <= self.img_number:
            self.label.index = index - 1  # 索引是从0开始的
            self.update_widget()
            self.hintBox.setText("提示：跳转到" + str(index))
        else:
            self.hintBox.setText("提示：非法跳转！")

    # def addItem(self, item):
    #     if not isinstance(item, my_kps_Item):
    #         raise TypeError("item must be LabelListWidgetItem")
    #     self.listWidget_points.addItem(item)



