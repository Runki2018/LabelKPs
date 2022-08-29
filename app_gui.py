import sys
from collections import defaultdict
from PySide2.QtCore import QFile, QIODevice, Slot, Signal
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QFileDialog, QLabel, QMessageBox
from PySide2.QtGui import QPixmap, QIcon
from utils.my_scene import MyScene
from utils.detection import Detector
from utils.config_parser import Config
from utils.ListItem import my_kps_Item
from utils.label_parser import LabelParser
from utils.TreeWidgetItem import ParentTreeItem, ChildTreeItem
from pathlib import Path


class myGUI:
    """app类, 除了画布场景的操作, 其余控件操作在该类定义。"""
    # detect_signal = Signal(int)  
    def __init__(self):
        # 加载 ui
        # ui_file_name = "./UI/labelKPs.ui"
        ui_file_name = "./UI/labelKPs_plus.ui"   # 加入MediaPipe变检测变修改
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

        self.cfg = Config(cfg_file='./config.json')
        self.detector = Detector(self.cfg)
        # self.ui = QUiLoader().load("./UI/labelKPs.ui")
        self.ui.setWindowIcon(QIcon('hand_icon.ico'))

        # 定义控件，方便补全代码
        self.statusBar = self.ui.statusbar  # 状态条，用于显示提示信息，可设置信息时效ms
        self.statusTime = 5000  # ms
        self.statusLabel = QLabel("源码：")
        self.statusURL = QLabel("<a href=\"https://github.com/Runki2018/LabelKPs\">访问GitHub")
        self.statusURL.setOpenExternalLinks(True)
        self.statusBar.addPermanentWidget(self.statusLabel)
        self.statusBar.addPermanentWidget(self.statusURL)

        # button:
        self.loadButton = self.ui.loadButton  # 图片加载目录
        self.outputButton = self.ui.outputButton  # 生成标注文件的输出目录
        self.generateButton = self.ui.generateButton  # 生成标注文件到输出目录
        self.jsonButton = self.ui.jsonButton  # 选择json标注文件
        # self.jsonButton.setEnabled(False)  # 只有选择了图像加载路径后，才能选择标注保存路径
        self.redetectButton = self.ui.redetectButton  # 重新检测当前图片
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
        self.discardCheckBox = self.ui.discard  # 丢弃选项，勾选代表样本存在问题，后期会删除
        self.poorCheckBox = self.ui.poor  # 手部样本质量较差的选项.
        self.isShuffleCheckBox = self.ui.isShuffle_checkBox  # 是否打乱检测图片检测顺序

        # listWidget:
        self.listWidget_points = self.ui.listWidget_points  # 显示当前关键点坐标的列表框

        # TreeWidget:
        self.treeWidget_files = self.ui.treeWidget
        self.treeWidget_files.header().setVisible(False)  # 隐藏表头，不显示属性项，如名字，大小，时间等
 
        # graphicsView:
        self.graphicsView = self.ui.graphicsView  # 图片框
        # 场景，把列表控件传入，便于更新列表项，也可以用信号进制实现
        self.scene = MyScene(self.listWidget_points)
        self.graphicsView.setScene(self.scene)

        # 滚动条
        self.boneScrollBar = self.ui.bone_scollBar  # 用于调整骨架线条的粗细或透明度
        # 滚动条初始位置与场景骨架笔宽初始值一致
        self.init_scrollBar(self.boneScrollBar, 1, 20, 1, self.scene.bonePen_width)
        hand_maximum = self.cfg.mediapipe['max_num_hands']
        detection_threshold = self.cfg.mediapipe['min_detection_confidence']
        self.max_num_handsScrollBar = self.ui.max_num_hands_ScrollBar
        self.init_scrollBar(self.max_num_handsScrollBar, 1, 30, 1, int(hand_maximum))
        self.thr_detectionScrollBar = self.ui.detection_thr_ScrollBar
        self.init_scrollBar(self.thr_detectionScrollBar, 1, 10, 1,
                            int(10 * detection_threshold))
        
        #spinBox
        # 设置检测的图片数目，默认值为-1表示检测图片目录中所有图片
        self.num_detectionSpinBox = self.ui.num_spinBox   
        
        # grogressBar and timer
        self.progressBar = self.ui.progressBar

        # label:
        self.process_number = self.ui.number_label  # 显示当前已处理的图片数/总图片数
        self.example_caption = self.ui.label_caption
        self.example_picture = self.ui.label_picture
        self.example_caption.setText("手腕1个点,其余手指各4个点,共21个点。\n"
                                     "改点的两种鼠标操作方式：\n 1、左键点击后拖拽,释放左键\n"
                                     " 2、按左键点击选中,鼠标移动至合适位置后,按右键释放")
        self.example_picture.setPixmap(QPixmap("./Example.png"))
        self.label_classes = self.ui.label_classes  # 类别标签
        self.label_predict = self.ui.label_predict  # 预测标签
        self.label_num_detection = self.ui.num_label      # 生成标注文件时需要检测的图片个数

        self.hand_maximum = self.ui.hand_maximum_label   # mediapipe 检测的最大手数
        self.thr_label = self.ui.thr_label        # mediapipe 手部得分阈值
        self.hand_maximum.setText("max_num_hands".ljust(20) + str(hand_maximum).rjust(4))
        self.thr_label.setText("detection".ljust(20) + str(detection_threshold).rjust(4))


        # comboBox
        self.labelComboBox = self.ui.comboBox  # 弹出一个类别列表，用于显示和修改类别标签真值
        self.labelComboBox.addItems(self.cfg.categories_name)  # list['lable1', 'label2']
        # action
        self.override = self.ui.action_override  # 菜单栏中的可选项，勾选时保存在原文件上
        # lineEdit
        self.lineEdit = self.ui.lineEdit  # 输入框，用于输入将跳转的图片数

        # 定义事件
        self.loadButton.clicked.connect(self.get_load_dir)  # 加载图片文件夹
        self.outputButton.clicked.connect(self.get_output_dir)  # 检测并生成标注文件
        self.generateButton.clicked.connect(self.generate_annotations)  # 检测并生成标注文件
        self.redetectButton.clicked.connect(self.regenerate_annotations)
        self.jsonButton.clicked.connect(self.chooseLabelFile)  # 选择标注文件
        self.saveButton.clicked.connect(self.save_label)  # 保存标注文件
        self.preButton.clicked.connect(self.pre_img)  # 上一张图片
        self.nextButton.clicked.connect(self.next_img)  # 下一张图片
        self.goButton.clicked.connect(self.go_img)  # 下一张图片
        self.show_radioButton.clicked.connect(self.showBoneLine)  # 显示骨架
        self.hide_radioButton.clicked.connect(self.hideBoneLine)  # 隐藏骨架
        
        self.boneScrollBar.valueChanged.connect(self.BonescrollEvent)  # 调整骨架粗细
        self.num_detectionSpinBox.valueChanged.connect(self.change_num_detection)
        # 检测手数的上限
        self.max_num_handsScrollBar.valueChanged.connect(self.change_mediapipe_args)
        self.max_num_handsScrollBar.sliderReleased.connect(self.set_mediapipe_args)
        # 调整检测阈值  
        self.thr_detectionScrollBar.valueChanged.connect(self.change_mediapipe_args)
        self.thr_detectionScrollBar.sliderReleased.connect(self.set_mediapipe_args) 
        self.labelComboBox.currentIndexChanged.connect(self.reviseTrueLabel)  # 纠正类别标签
        # 更新图片检测进度条
        # self.detector.app_signal[int].connect(self.update_progressBar)
        # self.detect_signal[int].connect(self.update_progressBar)

        # 加载和保持标注信息
        self.label = None               # 标注类，用于读取标注文件。 

        # 定义实例变量
        self.save_file = ""
        self.detect_order = 'shuffle'
        self.img_number = 0  # 图片总数
        self.image_index = 0  # 已处理的图片数
        self.hand_index = 0  # 当前图片的手部id， 0~当前图片手部实例-1
        self.imgToHandNum = defaultdict(int)  # 哈希表：图片id -> 图片中有多少只手
        self.points_list = []  # 当前手的关键点列表（未经修改）

    def get_load_dir(self):
        """选择图片加载目录"""
        load_dirpath = QFileDialog.getExistingDirectory(self.ui, "选择图片加载目录", './')
        if load_dirpath != "":
            self.cfg.images_input_path = load_dirpath
            self.jsonButton.setEnabled(True)  # 只有选择了图像加载路径后，才能选择标注保持路径
            num_image_files = len(self.detector.get_image_files(False))
            self.init_spinBox(num_image_files)
            self.statusBar.showMessage("提示:" + load_dirpath, self.statusTime)
        else:
            self.statusBar.showMessage("提示：加载目录为空！", self.statusTime)
        print(f"directory of Loding images  => {load_dirpath}")


    def get_output_dir(self):
        output_dirpath = QFileDialog.getExistingDirectory(self.ui, "选择标注文件输出目录", './')
        if output_dirpath != "":
            self.cfg.annotations_output_path = output_dirpath
            self.showMessage("提示:" + output_dirpath)
        else:
            self.showMessage("提示：加载目录为空！")
        print(f"directory of saving annotations => {output_dirpath}")

    def generate_annotations(self):
        """使用MediaPipe检测关键点"""
        is_shuffle = self.isShuffleCheckBox.isChecked()
        self.cfg.annotation_file = self.detector.detect_all_images(
            self.progressBar, is_shuffle)
        self.statusBar.showMessage(f"=> {self.cfg.annotation_file}", self.statusTime)
        print(f"generate annotations file => {self.cfg.annotation_file}")

    def regenerate_annotations(self):
        img_file = self.label.get_imagePath()
        _, hand_kpts, handedness, scores, bboxes = self.detector.detect_one_image(img_file)
        print(f"=> {len(hand_kpts)=}\t{len(handedness)=}\t{len(scores)=}")
        new_annIds = self.label.regenerate_annotations(hand_kpts, handedness, scores, bboxes)
        imgItem  = self.treeWidget_files.topLevelItem(self.label.image_index)
        imgItem.takeChildren()  # 移除所有子孩子并返回
        for i, ann_id in enumerate(new_annIds):
            ann_state = self.label.annoState(ann_id)
            annItem = ChildTreeItem(i, 'hand_' + str(ann_id), ann_state)
            imgItem.addChild(annItem)
        self.update_widget()

    def chooseLabelFile(self):
        self.save_file, _ = QFileDialog.getOpenFileName(self.ui, "选择标注文件", './', 'JSON files(*.json)')
        print("save images directory!")
        print(self.save_file)
        if self.save_file != "":
            self.cfg.annotation_file = self.save_file
            self.label = LabelParser(self.cfg)
            self.img_number = self.label.image_number
            self.init_treeWidget_files()  # 初始化文件列表，只初始化一次
            self.update_widget()
            self.setButtonEnable()
            self.showMessage("提示:" + self.save_file)
        else:
            self.showMessage("提示：未选择标注文件！")

    def update_widget(self):
        """更新控件：显示当前图片数的标签、绘图框、关键点列表"""
        text = "图片数：" + str(self.label.image_index + 1) + "/" + str(self.img_number)
        self.process_number.setText(text)
        true_idx, predict_str = self.label.get_category()
        self.label_classes.setText("真值：")
        self.labelComboBox.setCurrentIndex(true_idx)
        self.label_predict.setText("预测：" + predict_str)
        self.init_listWidget_points(self.label.get_raw_keypoints())
        self.init_graphicsView()
        fileItem = self.treeWidget_files.topLevelItem(self.label.image_index)
        # fileItem.setSelected(True)  # 当前文件名高亮显示
        fileItem.setExpanded(True)  # 当前图片显示Child
        discard, poor = self.label.checkboxState()
        if discard != None:
            self.discardCheckBox.setChecked(discard)
            self.poorCheckBox.setChecked(poor)
    
    # @Slot(int)
    # def update_progressBar(self, value):
    #     """通过槽函数接收信号发送的value值"""
    #     self.progressBar.setValue(value)
    #     pass

    def init_graphicsView(self):
        """更新图像框图像和关键点，必须在更新关键点列表后执行"""
        img_path = self.label.get_imagePath()
        print(f"{img_path=}")
        # 深拷贝 -> 值传递，后面对比二者是否不同
        self.scene.init_scene(img_path, self.points_list.copy())  

    def init_listWidget_points(self, keypoints):
        self.points_list = []
        self.listWidget_points.clear()
        if len(keypoints) > 0:
            for k in range(21):
                ki = 2 * k
                keypoint = (round(keypoints[ki], 2), round(keypoints[ki + 1], 2))
                self.points_list.append(keypoint)
                item_text = str(keypoint)
                item = my_kps_Item(k, item_text)
                self.listWidget_points.addItem(item)

    def init_treeWidget_files(self):
        """初始化files框列表项"""
        self.treeWidget_files.clear()
        images = self.label.get_images()
        for i, img_info in enumerate(images):
            img_id = img_info['id']
            print(f"{self.label.imgs[img_id]=}")
            img_state = self.label.imageState(img_id)
            file_name = img_info['file_name']
            annsIds = self.label.imgIdToAnnIds[img_id]
            imgItem = ParentTreeItem(i, file_name, img_state)

            for j, ann_id in enumerate(annsIds):
                ann_state = self.label.annoState(ann_id)
                annItem = ChildTreeItem(j, 'hand_' + str(ann_id), ann_state)
                imgItem.addChild(annItem)
            self.treeWidget_files.addTopLevelItem(imgItem)

    def init_scrollBar(self, scrollBar, min_v, max_v, step, value):
        scrollBar.setMinimum(min_v)
        scrollBar.setMaximum(max_v)  # length = Max - Min + PageStep
        scrollBar.setPageStep(step)
        scrollBar.setValue(value)

    def set_CheckState(self, new_keypoints):
        """设置当前文件的检查状态,查看scene坐标与读入的初始坐标是否一致,一致则未修改,否则就修改过"""
        # 这功能便于在查看文件列表中样本的处理情况（空：未处理，实心：查看过，打勾：修改过）
        imgItem = self.treeWidget_files.topLevelItem(self.label.image_index)
        handItem = imgItem.child(self.label.hand_index)
        for i, k in enumerate(new_keypoints):
            if k != self.points_list[i]:   # (x1,y1) != (x1',y1') ?
                self.label.set_imageState("Checked")
                self.label.set_annState("Checked")
                imgItem.set_myCheckState("Checked")
                handItem.set_myCheckState("Checked")
                break
        if self.label.imageState(self.label.image_index) != "Checked":
            imgItem.set_myCheckState("PartiallyChecked")
            self.label.set_imageState("PartiallyChecked")
            if self.label.ann_id != None:
                self.label.set_annState("PartiallyChecked")
                handItem.set_myCheckState("PartiallyChecked")

    def pre_img(self):
        self.showMessage("上一页！")
        # 保持上一张图片标注信息，并将index+1, 当index合理时，才更新下一张图片
        self.set_keypoints()
        self.label.decrement
        self.update_widget()

    def next_img(self):
        # 保持上一张图片标注信息，并将index+1, 当index合理时，才更新下一张图片
        if self.label.image_index < self.img_number-1:
            self.showMessage("下一页！")
            self.set_keypoints()
            self.label.increment
            self.update_widget()
        else:
            self.showMessage("已到最后一页！")

    def save_label(self):
        self.showMessage("正在保存文件。。。")
        self.setButtonDisable()
        self.set_keypoints()  # 修改标注信息
        self.label.save_annotations(self.override.isChecked())  # 保存标注信息
        self.setButtonEnable()
        self.showMessage("")

    def set_keypoints(self):
        """获取scene中当前图片的21个关键点坐标, 并更新标注列表中的标注信息"""
        if not self.label.annIsNone:
            keypoints = []
            for kp_tuple in self.scene.keypoints:
                keypoints.extend(kp_tuple)   # [(x1,y1),(x2,y2)] -> [x1,y1,x2,y2]
            self.set_CheckState(self.scene.keypoints)
            discard, poor = self.discardCheckBox.isChecked(), self.poorCheckBox.isChecked()
            self.label.set_checkbox(discard, poor)
            self.label.update_keypoints(keypoints)

    def closeEventDialog(self):
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
        if self.lineEdit.text().isnumeric():
            index = int(self.lineEdit.text())  # 输入的范围是 1~图像数
            if 0 < index <= self.img_number:
                self.label.image_index = index - 1  # 索引是从0开始的
                self.update_widget()
                self.lineEdit.setText('')
                self.showMessage("提示：跳转到" + str(index))
                return
        self.showMessage("提示：非法跳转！")

    def showBoneLine(self):
        """骨架连线可见性改变时触发该事件,给场景更新状态"""
        self.showMessage("显示骨架！")
        self.scene.app_signal[str].emit("show")

    def hideBoneLine(self):
        """骨架连线可见性改变时触发该事件,给场景更新状态"""
        self.showMessage("隐藏骨架！")
        self.scene.app_signal[str].emit("hide")

    def BonescrollEvent(self):
        """水平滚动条，调整骨架粗细或透明度， """
        self.showMessage("调整骨架粗细...")
        self.scene.app_signal[int].emit(self.boneScrollBar.value())  # 参数为 int 型

    def change_mediapipe_args(self):
        """Mediapipe argument => num_max_hands """
        self.showMessage("调整检测器参数...")
        hand_maximum = self.max_num_handsScrollBar.value()    # 最大手数
        thr = self.thr_detectionScrollBar.value() / 10  # 检测阈值
        self.hand_maximum.setText("max_num_hands".ljust(20) + str(hand_maximum).rjust(4))
        self.thr_label.setText("detection".ljust(20) + str(thr).rjust(4))
        print(f"{hand_maximum=}\t{thr=}")
        return hand_maximum, thr

    def set_mediapipe_args(self):
        self.showMessage("已修改检测器参数")
        hand_maximum, thr = self.change_mediapipe_args()
        self.cfg.mediapipe['max_num_hands'] = hand_maximum
        self.cfg.mediapipe['min_detection_confidence'] = thr
        self.generateButton.setDisabled(True)
        self.detector.setConfig(self.cfg)
        self.generateButton.setEnabled(True)
        print(f"successfully set detector arguments")

    def change_num_detection(self):
        self.showMessage("修改待检测图片的数目")
        self.cfg.mediapipe['num_images'] = self.num_detectionSpinBox.value()


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

    def reviseTrueLabel(self):
        """纠正标签"""
        label = self.labelComboBox.currentIndex()
        self.label.update_category(label)

    def showMessage(self, text):
        self.statusBar.clearMessage()
        self.statusBar.showMessage(text, 0)
        # self.statusBar.showMessage(text, self.statusTime)
        self.statusBar.update()

    def init_spinBox(self, num):
        self.num_detectionSpinBox.setMaximum(num)
        value = min(self.cfg.mediapipe['num_images'], num)
        self.num_detectionSpinBox.setValue(value)




