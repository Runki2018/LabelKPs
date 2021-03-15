import json
import time
import os


class label_it:
    """读取粗略的标注信息"""
    classes = ["0-其他 ", "1-OK", "2-手掌", " 3-向上", "4-向下", "5-向右", "6-向左", "7-比心", "8-嘘"]

    def __init__(self, annotation_file):
        save_dir = "./annotation/"
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)
        self.new_annotation_file = save_dir + time.strftime("%Y-%m-%d", time.localtime()) + ".json"
        self.json_ann = json.load(open(annotation_file, "r"))
        self.annotations_list = self.json_ann["annotations"]
        self.images_list = self.json_ann["images"]
        # print(time.strftime("%Y/%m/%d", time.localtime()))
        self.json_ann["info"]["date_created"] = time.strftime("%Y/%m/%d", time.localtime())  # 更改标注文件的修改日期
        self.json_ann["info"]["year"] = time.strftime("%Y", time.localtime())
        # 读取已处理的图像数
        if "image_index" in self.json_ann["info"].keys():
            self.index = self.json_ann["info"]["image_index"]  # 已处理的图像数
        else:
            self.json_ann["info"]["image_index"] = 0
            self.index = 0  # 已处理的图像数
        self.image_number = len(self.images_list)  # 图像总数
        # 初始化关键点遮挡和模糊状态
        self.init_occlusion_blur()

    def get_imagePath(self):
        return self.images_list[self.index]["file_name"]

    def get_images_number(self):
        return len(self.images_list)

    def get_classes(self):
        """返还手势类别ID: 0~8
        0-其他； 1-OK； 2-手掌； 3-向上； 4-向下； 5-向右； 6-向左； 7-比心； 8-嘘
        """
        class_id = self.images_list[self.index]["label"]
        return self.classes[class_id]

    def get_raw_keypoints(self):
        """获取粗略的关键点坐标"""
        keypoints = self.annotations_list[self.index]["keypoints"].copy()  # 深拷贝，不然pop后就修改了原标注信息
        pop_i = 0  # 去除每个关键点的置信度
        for k in range(21):
            pop_i += 2
            keypoints.pop(pop_i)
        return keypoints

    def update_keypoints(self, keypoints):
        """修改某一个图像的关键点标注,并给修改后的每个关键点增加置信度为 1"""
        insert_i = -1
        for i in range(21):
            insert_i += 3
            keypoints.insert(insert_i, 1)
        self.annotations_list[self.index]["keypoints"] = keypoints

    def save_annotations(self):
        """每次加载下一张图片时，自动调用该函数保存当前图像的修改"""
        self.json_ann["info"]["image_index"] = self.index
        self.json_ann["annotations"] = self.annotations_list
        self.json_ann["images"] = self.images_list
        json.dump(self.json_ann, open(self.new_annotation_file, "w"), indent=4)
        print(self.new_annotation_file)
        print("save!!!")

    def image_CheckState(self, index):
        """判断该图像是否已经检查处理过，返回检查状态，用于初始化listWidget_files"""
        if "CheckState" in self.images_list[index].keys():
            check_state = self.images_list[index]["CheckState"]  # return PartiallyChecked or Checked
        else:
            check_state = "Unchecked"
            self.images_list[index]["CheckState"] = check_state
        return check_state

    def set_image_CheckState(self, check_state):
        """三种状态：未检查、已检查未修改、已检查且修改"""
        self.images_list[self.index]["CheckState"] = check_state

    def init_occlusion_blur(self):
        """初始化关键点被遮挡和模糊状态,0:否，1：是"""
        for index in range(self.image_number):
            keys = self.images_list[index].keys()
            label = self.images_list[index]["label"]
            if "occlusion" not in keys:
                if label == 1 or label == 2:
                    self.images_list[index]["occlusion"] = 0  # 无遮挡，因为大多数情况下，OK和手掌类是无遮挡的。
                else:
                    self.images_list[index]["occlusion"] = 1  # 被遮挡，因为大多数情况下，部分手指被遮挡。
            if "blur" not in keys:
                self.images_list[index]["blur"] = 0  # 默认图片手部是清晰的

    def set_occlusion_blur(self, is_occlusion=True, blur=False):
        """关键点被遮挡/模糊,0:否，1：是"""
        self.images_list[self.index]["occlusion"] = int(is_occlusion)
        self.images_list[self.index]["blur"] = int(blur)

    def is_occlusion_blur(self):
        """获取关键点被遮挡状态, 0:否，1：是
          图片是否模糊， 0:否，1：是
        """
        occlusion = self.images_list[self.index]["occlusion"]
        blur = self.images_list[self.index]["blur"]
        return occlusion, blur

