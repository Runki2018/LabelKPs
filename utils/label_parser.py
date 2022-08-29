import json
import time
from pathlib import Path
from copy import copy, deepcopy

from attr import s
from .myCOCOtools import COCOtools

def _timestamp():
    return time.strftime("%Y_%m_%d", time.localtime())


class LabelParser(COCOtools):
    """Parse the label file of COCO format 
    """
    def __init__(self, cfg):
        super().__init__(cfg.annotation_file)
        save_dir = Path("./annotations/")
        if not save_dir.exists():
            save_dir.mkdir(mode=0o777, parents=True, exist_ok=True)

        self.cfg = cfg
        # 初始化路径
        self.timestamp = _timestamp()
        self.ann_file = Path(cfg.annotation_file)
        self.new_ann_file = save_dir.joinpath(self.timestamp + '.json')
        self.image_dir = Path(self.cfg.images_input_path)

        # 读入标注文件
        self.imageNum = len(self.imgIds)   # 图像总数

        # 确定开始处理的图片id
        dataset_info = self.dataset.get('info', None)
        if dataset_info is None:
            self.image_index = 0       # 图片序列中已经处理的数目。
        else:
            self.image_index =  dataset_info['index_of_images_processed']

        self.hand_index = 0  # 每张图片预测的第几只手 0 ~ n-1
        self.annIds_count = len(self.anns)  # 最初的annIds总数
        # 初始化'discard'和 'poor'状态
        self.init_checkbox()  

    def get_imagePath(self):
        image_info = self.imgs[self.img_id]
        imagePath = self.image_dir.joinpath(image_info['file_name'])
        return str(imagePath)

    @property
    def img_id(self):
        return self.imgIds[self.image_index]
    @property
    def annIsNone(self):
        """判断当前图片的检测结果是否为空"""
        return False if len(self.imgIdToAnnIds[self.img_id]) > 0 else True
    @property
    def ann_id(self):
        if self.annIsNone: return None
        return self.imgIdToAnnIds[self.img_id][self.hand_index]
    @property
    def increment(self):
        print(f"increament{self.hand_index=}\t{self.image_index=}")
        num_hand = len(self.imgIdToAnnIds[self.img_id])
        if self.hand_index < num_hand - 1:
            self.hand_index += 1
        elif self.image_index < self.image_number - 1:
            self.hand_index =0
            self.image_index += 1
        print(f"increament => {self.hand_index=}\t{self.image_index=}")
    @property
    def decrement(self):
        print(f"decreamt {self.hand_index=}\t{self.image_index=}")
        if 0 < self.hand_index:
            self.hand_index -= 1
        elif 0 < self.image_index:
            self.image_index -= 1
            num_hand = len(self.imgIdToAnnIds[self.img_id])
            self.hand_index = num_hand - 1
        print(f"decreamt =>{self.hand_index=}\t{self.image_index=}")

    def imageState(self, img_id):
        """判断该图像是否已经检查处理过, 返回检查状态, 用于初始化listWidget_files"""
        state = self.imgs[img_id].get('state', None)
        if state is None:
            state = "Unchecked"
            self.imgs[img_id]['state'] = state
        return state

    def set_imageState(self, state):
        """三种状态：未检查、已检查未修改、已检查且修改"""
        self.imgs[self.img_id]['state'] = state

    def annoState(self, ann_id):
        """判断所有手部是否已经检查处理过, 返回检查状态, 用于初始化listWidget_files"""
        state = self.anns[ann_id].get('state', None)
        if state is None:
            state = "Unchecked"
            self.anns[ann_id]['state'] = state
        return state

    def set_annState(self, state):
        self.anns[self.ann_id]['state'] = state

    def init_checkbox(self):
        """初始化关键点标注的丢弃和模糊状态,0:否,1:是"""
        for index in range(self.imageNum):
            anns = self.imgToAnns[self.imgIds[index]]
            for ann_info in anns:
                if 'discard' not in ann_info.keys():
                    ann_info['discard'] = 0
                if 'poor' not in ann_info.keys():
                    ann_info['poor'] = 0

    def set_checkbox(self, discard=False, poor=False):
        """set_occlusion_poor"""
        ann = self.imgToAnns[self.img_id]  # list
        ann[self.hand_index]['discard'] = int(discard)  
        ann[self.hand_index]['poor'] = int(poor)  

    def checkboxState(self):
        """is_occlusion_poor"""
        if self.annIsNone:
            return None, None
        ann_info =  self.anns[self.ann_id]
        return ann_info['discard'], ann_info['poor']

    def get_category(self):
        """return category_id, 用于显示当前真值类别标签和预测类别标签"""
        if self.annIsNone:  # 如果检测结果为空，返回背景类
            return 0, self.cfg.categories_name[0]
        ann_info =  self.imgToAnns[self.img_id][self.hand_index]
        category_id = ann_info['category_id']
        prediction_id = ann_info.get('prediction_id', None)
        prediction_id = prediction_id if  prediction_id != None else category_id
        return category_id, self.cfg.categories_name[prediction_id]
       

    def update_category(self, category_id):
        self.anns[self.ann_id]['category_id'] = category_id

    def get_raw_keypoints(self):
        """ get raw keypoints from annotation file"""
        if self.annIsNone:
            return []
        # kpts = self.imgToAnns[self.img_id][self.hand_index]['keypoints']
        kpts = self.anns[self.ann_id]['keypoints']
        kpts_without_vis = []
        for i in range(21):
            kpts_without_vis += [kpts[i*3], kpts[i*3+1]]
        return kpts_without_vis

    def update_keypoints(self, kpts_without_vis):
        """修改某一个图像的关键点标注,并给修改后的每个关键点增加置信度为 1,
        """
        kpts = []
        for i in range(21):
            kpts += [kpts_without_vis[2*i], kpts_without_vis[2*i+1], 1]
        self.anns[self.ann_id]['keypoints'] = kpts

    def regenerate_annotations(self, hand_kpts, handedness, scores, bboxes):
        """重新检测当前图片

        Args:
            hand_kpts (list): num_hand * list(21*3) [x, y, 1]
            handedness (list): 手的偏向性 [h1, h2, ...], h = 'left' or 'right'
            scores (list): 手的预测得分 num_hand * [score] 
            bboxes(list): 手的边界框 num_hand * [x1, y1, w, h]
        """
        new_anns = []
        self.imgs[self.img_id]['state'] = "Unchecked"
        annIds = self.imgIdToAnnIds[self.img_id]
        num_hand = len(annIds)
        num_regenerate = len(hand_kpts)
        num_min = min(num_hand, num_regenerate)

        # 在旧的检测结果上修改
        for i in range(num_min):
            self.anns[annIds[i]]['keypoints'] = hand_kpts[i]
            self.anns[annIds[i]]['bbox'] = bboxes[i]
            self.anns[annIds[i]]['area'] = bboxes[i][2] * bboxes[i][3]
            self.anns[annIds[i]]['score'] = round(scores[i], 3)
            self.anns[annIds[i]]['handerness'] = handedness[i]
            new_anns.append(self.anns[annIds[i]])

        if num_regenerate <= num_hand:
            # 去除多余的旧检测结果
            for i in range(num_regenerate, num_hand):
                self.anns.pop(annIds[i])
                # self.reuse_stack.append(annIds[i])
        else:
            # 生成新的标注结果
            for i in range(num_min, num_regenerate):
                new_ann_id = self.annIds_count
                while new_ann_id not in self.anns.keys():
                    new_ann_id += 1  # 防止id重复
                self.annIds_count = new_ann_id + 1
                ann_dict = dict(
                    id=new_ann_id,
                    image_id=self.img_id,
                    keypoints=hand_kpts[i],
                    bbox=bboxes[i],
                    area=(bboxes[i][2] * bboxes[i][3]),
                    score=scores[i],
                    handedness=handedness[i],
                    discard=0,
                    poor=0,
                    state="Unchecked"
                )
                self.anns[new_ann_id] = ann_dict
                new_anns.append(ann_dict)

        new_annIds = [a['id'] for a in new_anns]
        self.imgIdToAnnIds[self.img_id] = new_annIds
        self.imgToAnns[self.img_id] = new_anns
        self.hand_index = 0
        return new_annIds

    def get_bbox(self):
        return copy(self.anns[self.ann_id]['bbox'])  # ! 需不需要添加当bbox不存在的情况
    
    def update_bbox(self, bbox):
        self.anns[self.ann_id]['bbox'] = bbox

    def get_info(self, info):
        info_dict = dict(index_of_images_processed=self.image_index,
                         date_created=self.timestamp,
                         year=time.strftime("%Y", time.localtime()))

        if info != None:
            info.update(info_dict)
        else:
            info = info_dict
        return info

    def save_annotations(self, override=False):
        """保存当前所有图像的修改

        Args:
            is_override (bool, optional): 是否覆盖原文件. Defaults to False.
        """
        with self.ann_file.open('r') as fd:
            ann_dict = json.load(fd)
        ann_dict['info'] = self.get_info(ann_dict.get('info', None))
        ann_dict['images'] = self.get_images()
        ann_dict['annotations'] = self.get_annotations()
        if 'categories' in self.dataset.keys():
            ann_dict['categories'] = self.dataset['categories']
        else:
            ann_dict['categories'] = self.cfg.get_categories()

        file = self.ann_file if override else self.new_ann_file
        with file.open('w') as fd:
            json.dump(ann_dict, fd, indent=4)
        return str(file)