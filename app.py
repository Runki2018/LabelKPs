import math
import sys

from PySide2.QtCore import QFile, QIODevice, Qt, Signal, Slot
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QFileDialog, QLabel, QMessageBox
from utils.ListItem import my_kps_Item, my_files_Item
from utils.my_scene import MyScene
from utils.label import label_it
from PySide2.QtGui import QPixmap, QIcon, QCloseEvent


class myGUI:
    """app类，除了画布场景的操作，其余控件操作在该类定义。"""

    def __init__(self):
        # 加载 ui
        ui_file_name = "./UI/labelKPs.ui"
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
        self.ui.setWindowIcon(QIcon('hand_icon.ico'))

        # 定义控件，方便补全代码
        self.statusBar = self.ui.statusbar  # 状态条，用于显示提示信息，可设置信息时效ms
        self.statusLabel = QLabel("源码：")
        self.statusURL = QLabel("<a href=\"https://github.com/Runki2018/LabelKPs\">访问GitHub")
        self.statusURL.setOpenExternalLinks(True)
        self.statusBar.addPermanentWidget(self.statusLabel)
        self.statusBar.addPermanentWidget(self.statusURL)

        # button:
        self.loadButton = self.ui.loadButton  # 图片加载目录
        self.jsonButton = self.ui.jsonButton  # 选择json标注文件
        self.jsonButton.setEnabled(False)  # 只有选择了图像加载路径后，才能选择标注保持路径
        self.saveButton = self.ui.saveButton  # 保存标注——当图片数量大的时候，保存时间较慢，有几秒。
        self.preButton = self.ui.preButton  # 上一张
        self.nextButton = self.ui.nextButton  # 下一张
        self.goButton = self.ui.goButton  # 跳转
        self.buttonEnable = True  # 在点击加载目录前，其他切换图片状态的button处于禁用状态。
        # self.reverseButtonEnable()  # 控件状态取反
        self.setButtonDisable()

        # radiobutton:
        # self.bbox_radioButton = self.ui.bbox_radioButton  # 画边界框单选框
        # self.kps_radioButton = self.ui.kps_radioButton  # 画关键点单选框
        self.show_radioButton = self.ui.radioButton_show  # 显示骨架
        self.hide_radioButton = self.ui.radioButton_hide  # 隐藏骨架

        # checkBox
        self.is_occlusion = self.ui.is_occlusion  # 存在部分关键点被遮挡，默认为真

        # listWidget:
        self.listWidget_points = self.ui.listWidget_points  # 显示当前关键点坐标的列表框
        self.listWidget_files = self.ui.listWidget_files  # 显示图片文件的列表框

        # graphicsView:
        self.graphicsView = self.ui.graphicsView  # 图片框
        self.scene = MyScene(self.listWidget_points)  # 场景，把列表控件传入，便于更新列表项，也可以用信号进制实现
        self.graphicsView.setScene(self.scene)

        # 滚动条
        self.scrollBar = self.ui.horizontalScrollBar  # 用于调整骨架线条的粗细或透明度
        self.scrollBar.setMaximum(20)  # length = Max - Min + PageStep
        self.scrollBar.setMinimum(1)
        self.scrollBar.setPageStep(1)
        self.scrollBar.setValue(self.scene.bonePen_width)  # 设滚动条初始位置 与 场景骨架笔宽初始值一致

        # label:
        self.process_number = self.ui.number_label  # 显示当前已处理的图片数/总图片数
        self.example_caption = self.ui.label_caption
        self.example_picture = self.ui.label_picture
        self.example_caption.setText("手腕1个点，其余手指各4个点，共21个点。\n"
                                     "改点的两种鼠标操作方式：\n 1、左键点击后拖拽，释放左键\n"
                                     " 2、按左键点击选中，鼠标移动至合适位置后，按右键释放")
        self.example_picture.setPixmap(QPixmap("./Example.png"))

        # lineEdit
        self.lineEdit = self.ui.lineEdit  # 输入框，用于输入将跳转的图片数

        # 定义事件
        self.loadButton.clicked.connect(self.load_dir)  # 加载图片文件夹
        self.jsonButton.clicked.connect(self.chooseLabelFile)  # 选择标注文件
        self.saveButton.clicked.connect(self.save_label)  # 保存标注文件
        self.preButton.clicked.connect(self.pre_img)  # 上一张图片
        self.nextButton.clicked.connect(self.next_img)  # 下一张图片
        self.goButton.clicked.connect(self.go_img)  # 下一张图片
        self.show_radioButton.clicked.connect(self.showBoneLine)  # 显示骨架
        self.hide_radioButton.clicked.connect(self.hideBoneLine)  # 隐藏骨架
        self.scrollBar.valueChanged.connect(self.scrollEvent)  # 调整骨架粗细

        # 加载和保持标注信息
        self.label = None

        # 定义实例变量
        self.load_dirpath = ""
        self.save_file = ""
        self.img_number = 0  # 图片总数
        self.index = 0  # 已处理的图片数
        self.points_list = []  # 当前手的关键点列表（未经修改）

    def load_dir(self):
        self.load_dirpath = QFileDialog.getExistingDirectory(self.ui, "选择图片加载目录", './')
        if self.load_dirpath != "":
            self.jsonButton.setEnabled(True)  # 只有选择了图像加载路径后，才能选择标注保持路径
            self.setButtonDisable()
            self.statusBar.showMessage("提示:" + self.load_dirpath, 3000)
            self.statusBar.update()
        else:
            self.statusBar.showMessage("提示：加载目录为空！", 3000)
            self.statusBar.update()
        print("load images directory!")
        print(self.load_dirpath)

    def chooseLabelFile(self):
        self.save_file, _ = QFileDialog.getOpenFileName(self.ui, "选择标注文件", './', 'JSON files(*.json)')
        print("save images directory!")
        print(self.save_file)
        if self.save_file != "":
            self.label = label_it(self.save_file)
            self.img_number = self.label.image_number
            self.init_listWidget_files()  # 初始化文件列表，只初始化一次
            self.update_widget()
            self.setButtonEnable()
            self.statusBar.showMessage("提示:" + self.save_file, 3000)
            self.statusBar.update()
        else:
            self.statusBar.showMessage("提示：未选择标注文件！", 3000)
            self.statusBar.update()

    def update_widget(self):
        """更新控件：显示当前图片数的标签、绘图框、关键点列表"""
        text = "图片数：" + str(self.label.index + 1) + "/" + str(self.img_number)
        self.process_number.setText(text)
        self.init_listWidget_points(self.label.get_raw_keypoints())
        self.init_graphicsView()
        file_item = self.listWidget_files.item(self.label.index)
        file_item.setSelected(True)  # 当前文件名高亮显示
        # state = True if self.label.is_occlusion() else False  # 设置”部分遮挡“ 的状态
        self.is_occlusion.setChecked(self.label.is_occlusion())

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
        # 这功能便于在查看文件列表中样本的处理情况（空：未处理，实心：查看过，打勾：修改过）
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
        self.statusBar.showMessage("上一页！", 3000)
        self.statusBar.update()
        # 保持上一张图片标注信息，并将index+1, 当index合理时，才更新下一张图片
        self.set_keypoints()
        self.label.index -= 1 if self.label.index > 0 else 0
        self.update_widget()

    def next_img(self):
        # 保持上一张图片标注信息，并将index+1, 当index合理时，才更新下一张图片
        if self.label.index < self.img_number-1:
            self.statusBar.showMessage("下一页！", 3000)
            self.statusBar.update()
            self.set_keypoints()
            self.label.index += 1 if self.label.index < self.img_number - 1 else 0
            self.update_widget()
        else:
            self.statusBar.showMessage("已到最后一页！", 3000)
            self.statusBar.update()

    def save_label(self):
        self.statusBar.showMessage("正在保存文件。。。", 2000)
        self.statusBar.update()
        self.setButtonDisable()
        self.set_keypoints()  # 修改标注信息
        self.label.save_annotations()  # 保存标注信息
        self.setButtonEnable()
        # self.statusBar.showMessage("", 1000)
        # self.statusBar.update()

    def set_keypoints(self):
        """获取scene中当前图片的21个关键点坐标，并更新标注列表中的标注信息"""
        keypoints = []
        for kp_tuple in self.scene.keypoints:
            keypoints.extend(kp_tuple)   # [(x1,y1),(x2,y2)] -> [x1,y1,x2,y2]
        self.set_CheckState(self.scene.keypoints)
        self.label.set_occlusion(self.is_occlusion.isChecked())
        self.label.update_keypoints(keypoints)

    def closeEventDialog(self, state):
        """在关闭窗口时弹出对话框"""
        # TODO: 还没实现该方法
        option = QMessageBox.Question(self,
                                      "LabelKPs", "是否要退出程序？",
                                      QMessageBox.Yes,
                                      QMessageBox.No)
        if option == QMessageBox.Yes:
            if self.label is not None:
                self.save_label()
            # event.accept()
            print("YES", '-' * 50)
        else:
            # event.ignore()
            print("NO", '-'*50)

    def go_img(self):
        """跳转到指定图像"""
        index = int(self.lineEdit.text())  # 输入的范围是 1~图像数
        if 0 < index <= self.img_number:
            self.label.index = index - 1  # 索引是从0开始的
            self.update_widget()
            message = "提示：跳转到" + str(index)
            self.statusBar.showMessage(message, 3000)
        else:
            self.statusBar.showMessage("提示：非法跳转！", 3000)

    def showBoneLine(self):
        """骨架连线可见性改变时触发该事件,给场景更新状态"""
        self.statusBar.showMessage("显示骨架！", 2000)
        self.statusBar.update()
        self.scene.app_signal[str].emit("show")

    def hideBoneLine(self):
        """骨架连线可见性改变时触发该事件,给场景更新状态"""
        self.statusBar.showMessage("隐藏骨架！", 2000)
        self.statusBar.update()
        self.scene.app_signal[str].emit("hide")

    def scrollEvent(self):
        """水平滚动条，调整骨架粗细或透明度， """
        self.statusBar.showMessage("调整骨架粗细...", 1000)
        self.statusBar.update()
        self.scene.app_signal[int].emit(self.scrollBar.value())  # 参数为 int 型

    def setButtonEnable(self):
        self.saveButton.setEnabled(True)
        self.preButton.setEnabled(True)
        self.nextButton.setEnabled(True)
        self.goButton.setEnabled(True)
        self.buttonRepaint()

    def setButtonDisable(self):
        self.saveButton.setDisabled(True)
        self.preButton.setDisabled(True)
        self.nextButton.setDisabled(True)
        self.goButton.setDisabled(True)
        self.buttonRepaint()

    def buttonRepaint(self):
        self.saveButton.repaint()
        self.preButton.repaint()
        self.nextButton.repaint()
        self.goButton.repaint()

