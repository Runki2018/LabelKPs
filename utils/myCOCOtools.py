from collections import defaultdict
import json
import time


class COCOtools:
    def __init__(self, annotation_file):
        self.dataset, self.anns, self.imgs = dict(),dict(),dict()
        self.imgToAnns, self.imgIdToAnnIds = defaultdict(list), defaultdict(list)
        # self.filenameToImgs = defaultdict(list)
    
        print('loading annotations into memory...')
        tic = time.time()
        with open(annotation_file, 'r') as f:
            dataset = json.load(f)
        assert type(dataset)==dict, 'annotation file format {} not supported'.format(type(dataset))
        print('Done (t={:0.2f}s)'.format(time.time()- tic))
        self.dataset = dataset
        self.createIndex()
        self.imgIds = list(self.imgs.keys())
        self.image_number = len(self.imgIds)

    def createIndex(self):
        if 'annotations' in self.dataset:
            for ann in self.dataset['annotations']:
                self.anns[ann['id']] = ann
                self.imgToAnns[ann['image_id']].append(ann)
                self.imgIdToAnnIds[ann['image_id']].append(ann['id'])

        if 'images' in self.dataset:
            for img in self.dataset['images']:
                self.imgs[img['id']] = img
                # self.filenameToImgs[img['file_name']] = img
        print('index created!')
    

    def get_images(self):
        images = [self.imgs[img_id] for img_id in self.imgIds]
        return images

    def get_annotations(self):
        annotations = []
        for img_id in self.imgIds:
            for ann_id in self.imgIdToAnnIds[img_id]:
                annotations.append(self.anns[ann_id])
        return annotations