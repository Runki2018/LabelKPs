import json
from copy import deepcopy

class Config:
    """现在为了方便暂时以py文件作为配置文件"""
    def __init__(self, cfg_file=None):
        self.cfg_file = cfg_file
        with open(cfg_file, 'r') as fd:
                self.cfg = json.load(fd)

        self.dataset_name = self.cfg['dataset_name']
        self.mediapipe =  self.cfg['MediaPipe']
        self.categories_name = ['0-Background'] + self.cfg['categories_name']
        self.images_input_path = self.cfg['images_input_path']
        self.annotations_output_path = self.cfg['annotations_output_path']
        self.annotation_file = self.cfg['annotation_file']
        self.categories_template = self.cfg['categories_template']

    def set_input_path(self, input_path):
        self.images_input_path = input_path

    def set_annotations_output_path(self, annotations_output_path):
        self.annotations_output_path = annotations_output_path

    def set_merged_annotations_output_path(self, merged_annotations_output_path):
        self.merged_annotations_output_path = merged_annotations_output_path

    def save_config(self):
        self.cfg['MediaPipe'] = self.mediapipe
        self.cfg['annotation_file'] = self.annotation_file
        self.cfg['images_input_path'] = self.images_input_path
        self.cfg['annotations_output_path'] = self.annotations_output_path
        with open(self.cfg_file, 'w') as fd:
            json.dump(self.cfg, fd, indent=4)

    def get_categories(self):
        categories = []
        for i, name in enumerate(self.categories_name):
            category = deepcopy(self.categories_template)
            category['id'] = i
            category['name'] = name
            categories.append(category)
        return categories


    def __call__(self):
        print(f"{self.mediapipe=}")
        print(f"{self.categories_name=}")
        print(f"{self.images_input_path=}")
        print(f"{self.merge_output=}")
        print(f"{self.merged_annotations_output_path=}")
    
