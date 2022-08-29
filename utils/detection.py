import json
import cv2
import time
import numpy as np
from pathlib import Path
from copy import deepcopy
from mediapipe import solutions as mps
from os import listdir
from random import shuffle
# from PySide2.QtCore import Signal, Slot


class Detector:
    # 发送信号到app
    # app_signal = Signal((int,),)  
    
    def __init__(self, cfg):
        self.hand_detector =  None
        self.setConfig(cfg)
        self.results = dict(images=[], annotations=[])
        self.img_info_template = dict(id=0, file_name="", height=0, width=0)
        self.ann_info_template = dict(id=0,image_id=0, category_id=1, num_keypoints=21,
                                      area=0, bbox=[], iscrowd=0, keypoints=[])
        self.img_id, self.ann_id = 0, 0
        self.images = []       # coco标注文件中的图片标注列表
        self.annotations = []  # coco标注文件中的实例标注列表
        self.img_suffix_type = ['jpg', 'bmp', 'png']  # 支持的图片类型

    def setConfig(self, cfg):
        self.cfg = cfg
        if self.hand_detector != None:
            del self.hand_detector
            del self.hand_solution
            del self.mpDraw
            del self.mpDrawStyles
            
        # 导入solution 指定为手势姿态估计
        self.hand_solution =  mps.hands
        # 导入绘图函数
        self.mpDraw = mps.drawing_utils
        self.mpDrawStyles = mps.drawing_styles
        # https://google.github.io/mediapipe/solutions/hands#min_detection_confidence
        self.hand_detector = self.hand_solution.Hands(
                static_image_mode=True,  # 检测静态图片
                max_num_hands=cfg.mediapipe['max_num_hands'],  
                min_detection_confidence=cfg.mediapipe['min_detection_confidence'],
                # min_tracking_confidence=cfg.mediapipe['min_tracking_confidence']
        )

    def detect_all_images(self, progress_bar, is_shuffle=True):
        """检测图片加载目录下所有的图片, 并将结果输出到先择的输出目录下
        Args:
            img_suffix_type (list, optional): 支持的图片格式. Defaults to ['jpg', 'bmp', 'png'].
        Returns:
            _type_: _description_
        """
        image_dir = Path(self.cfg.images_input_path)
        image_files = self.get_image_files(is_shuffle)
        num_images = self.cfg.mediapipe['num_images']
        if num_images == -1:
            num_images = len(image_files)
        for i in range(num_images):
            file_name = image_files[i]
            file = str(image_dir.joinpath(file_name))
            img_rgb, hand_kpts, handedness, scores, bboxes = self.detect_one_image(file)
            h_img, w_img = img_rgb.shape[:2]

            img_info = deepcopy(self.img_info_template)
            img_info['id'] = int(self.img_id)
            img_info['file_name'] = str(file_name.name)
            img_info['height'] = int(h_img)
            img_info['width'] = int(w_img)

            for hand_i in range(len(hand_kpts)):
                bbox = bboxes[hand_i]
                area = bbox[2] * bbox[3]
                if area == 0:
                    continue
                ann_info = deepcopy(self.ann_info_template)
                ann_info['id'] = self.ann_id
                ann_info['image_id'] = self.img_id
                ann_info['keypoints'] = hand_kpts[hand_i]
                ann_info['bbox'] = bbox
                ann_info['area'] = area
                ann_info['score'] = round(scores[hand_i], 3)
                ann_info['handerness'] = handedness[hand_i]
                self.annotations.append(ann_info)
                self.ann_id += 1

            self.images.append(img_info)
            self.img_id += 1
            percentage = int((i+1) / num_images * 100)  # [1, 100]
            # self.app_signal[int].emit(percentage)   # update progressBar
            # signal[int].emit(percentage)   # update progressBar
            progress_bar.setValue(percentage)

        json_file = str(self._save_ann_file())
        return json_file

    def detect_one_image(self, img_file):
        img = cv2.imread(img_file)
        # 水平镜像反转图像，使得图片中左右手与真实左右手相对应
        # cv2.flip(img, arg) => arg参数：
        # 0=>上下翻转 | 1=>水平翻转 | -1=> 上下和水平都反转
        # img = cv2.flip(img, 1)  # ! 不区分左右手，需要翻转吗？
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = self.hand_detector.process(img_rgb.copy())
        hand_kpts, handedness, scores, bboxes = self._parse_results(img_rgb, results)
        img_rgb = self._vis_results(img_rgb, results)
        return img_rgb, hand_kpts, handedness, scores, bboxes
  
    def get_image_files(self, is_shuffle=True):
        files = listdir(self.cfg.images_input_path)
        image_files = []
        for file in files:
            if file.split('.')[-1].lower() in self.img_suffix_type:
               image_files.append(Path(file)) 
        if is_shuffle:
            shuffle(image_files)
        return image_files
        
    def _get_bbox(self, keypoints, h_img, w_img):
        factor = self.cfg.mediapipe.get('bbox_scale_factor', 0.3)
        keypoints = np.array(keypoints, dtype=np.float32).reshape((21, 3))
        x1y1 = keypoints.min(axis=0)[:2]
        x2y2 = keypoints.max(axis=0)[:2]
        x1y1 = x1y1.clip((0, 0), (w_img-1, h_img-1))
        x2y2 = x2y2.clip(x1y1, (w_img-1, h_img-1))
        wh = x2y2 - x1y1

        # 放大tight-bbox
        padding = np.power(wh, 0.5) * factor
        wh += padding
        x1y1 = x1y1 - padding / 2
        x1, y1 = x1y1.clip((0,0), (w_img-1, h_img-1)).astype(np.int16).tolist()
        w, h = wh.clip((0,0), (w_img-1, h_img-1)).astype(np.int16).tolist()
        return [x1, y1, w, h]


    def _parse_results(self, img_rgb, results):
        h, w = img_rgb.shape[:2]
        hand_kpts = []  # [[x1, y1, ..., x21, y21], ...]
        handedness = []  # ['left', 'right']
        scores = []  # detection score for each hand
        bboxes = []  # [[x1, y1, w, h]]
        if results.multi_hand_landmarks:
            for hand_idx in range(len(results.multi_hand_landmarks)):
                kpts = []  # [x1, y1, ..., x21, y21]
                hand_21 =  results.multi_hand_landmarks[hand_idx]
                for i in range(21):
                    xi = hand_21.landmark[i].x * w
                    yi = hand_21.landmark[i].y * h
                    kpts += [xi, yi, 1]
                hand_kpts.append(kpts)
                bboxes.append(self._get_bbox(kpts, h, w))

                classification = results.multi_handedness[hand_idx].classification[0]
                handedness.append(classification.label)
                scores.append(classification.score)

        return hand_kpts, handedness, scores, bboxes

    def _vis_results(self, img_rgb, results):
        if results.multi_hand_landmarks:  # 如果检测到了手部
            for i in range(len(results.multi_hand_landmarks)):
                # 获取关键点
                kpts_21 = results.multi_hand_landmarks[i]   
                # 可视化21个关键
                self.mpDraw.draw_landmarks(img_rgb, kpts_21, self.hand_solution.HAND_CONNECTIONS)
        return img_rgb

    def _save_ann_file(self):
        timestamp = time.strftime("%Y_%m_%d", time.localtime())
        info = dict(dataset=self.cfg.dataset_name,
                    index_of_images_processed=0,
                    date_created=timestamp,
                    year=time.strftime("%Y", time.localtime()))
        categories = self.cfg.get_categories()
        
        # 保存COCO数据标注格式的json文件
        json_dict = dict(
            info=info,
            images=self.images,
            annotations=self.annotations,
            categories=categories
        )

        json_dir = Path(self.cfg.annotations_output_path)
        json_file = json_dir.joinpath(self.cfg.dataset_name + timestamp + '.json')
        
        with json_file.open('w') as fd:
            json.dump(json_dict, fd, indent=4)
        
        return json_file
        