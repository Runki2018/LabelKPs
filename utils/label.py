import json
import time


class label_it:
    """读取粗略的标注信息"""

    def __init__(self, annotation_file):
        self.new_annotation_file = "label_" + \
                                   time.strftime("%Y-%m-%d", time.localtime()) + ".json"
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
        # 初始化关键点遮挡状态
        self.init_occlusionState()

    def get_imagePath(self):
        return self.images_list[self.index]["file_name"]

    def get_images_number(self):
        return len(self.images_list)

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

    # def update_index(self):
    #     # if self.index < self.image_number:
    #     #     print("old index = ", self.index)
    #     #     self.index += 1 if self.index < self.image_number - 1 else 0
    #     #     print("new index = ", self.index)
    #     self.index += 1

    def save_annotations(self):
        """每次加载下一张图片时，自动调用该函数保存当前图像的修改"""
        self.json_ann["info"]["image_index"] = self.index
        self.json_ann["annotations"] = self.annotations_list
        self.json_ann["images"] = self.images_list
        json.dump(self.json_ann, open(self.new_annotation_file, "w"), indent=4)
        print(self.new_annotation_file)
        print("save!!!")

    # def save_annotations(self, keypoints):
    #     """每次加载下一张图片时，自动调用该函数保存当前图像的修改"""
    #     self.json_ann["info"]["image_index"] = self.index
    #     self.revise_annotation(keypoints)
    #     self.json_ann["annotations"] = self.annotations_list
    #     self.json_ann["images"] = self.images_list
    #     if self.index < self.image_number:
    #         print("index = ", self.index)
    #         self.index += 1 if self.index < self.image_number - 1 else 0
    #         print("index = ", self.index)
    #         json.dump(self.json_ann, open(self.new_annotation_file, "w"), indent=4)
    #         print(self.new_annotation_file)
    #         print("save!!!")

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

    def init_occlusionState(self):
        """初始化关键点被遮挡状态,0:否，1：是"""
        for index in range(self.image_number):
            if "occlusion" not in self.images_list[index].keys():
                self.images_list[index]["occlusion"] = 1  # 默认被遮挡，因为大多数情况下，部分手指被遮挡。

    def set_occlusion(self, is_occlusion=True):
        """关键点被遮挡,0:否，1：是"""
        self.images_list[self.index]["occlusion"] = int(is_occlusion)

    def is_occlusion(self):
        """获取关键点被遮挡状态,0:否，1：是"""
        return self.images_list[self.index]["occlusion"]


if __name__ == '__main__':
    path = "C:/Users/WISE & BRAVE/Desktop/data_labelKps/new_annotations.json"
    label_it(path)
    ii = 0
    ll = [x for x in range(63)]
    for i in range(21):
        ii += 2
        ll.pop(ii)
    print(ll)
