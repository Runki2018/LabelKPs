import json
import os
from shutil import copyfile


def copy_file(json_file='./test.json', dst_dir='dst_dir'):
    """将json标注文件中的图片，复制到指定目录"""
    if not os.path.exists(dst_dir):
        os.mkdir(dst_dir)

    annotation_file = json.load(open(json_file, "r"))
    image_list = annotation_file["images"]
    # img_sum = len(image_list)
    for img_info in image_list:
        src_file_path = img_info["file_name"]
        file_name = src_file_path.split('/')[-1]
        dst_file_path = os.path.join(dst_dir, file_name)
        copyfile(src_file_path, dst_file_path)


def change_img_path(json_file='./test.json', dst_dir='dst_dir'):
    annotation_file = json.load(open(json_file, "r"))
    image_list = annotation_file["images"]
    for img_info in image_list:
        src_file_path = img_info["file_name"]
        file_name = src_file_path.split('/')[-1]
        # dst_file_path = os.path.join(dst_dir, file_name)
        dst_file_path = dst_dir + '/' + file_name
        img_info["file_name"] = dst_file_path
    annotation_file["images"] = image_list
    json.dump(annotation_file, open("./Scale1_test.json", "w"), indent=4)


if __name__ == '__main__':
    # copy_file('./test.json', 'dst_dir')
    change_img_path('scale_OneHand10k/good098.json', 'dst_dir')
    # with open("./dst_dir\\2_hand_det_scaled_img_90_id6_resize_0.jpg", "r") as f:
    #     # data = f.readline()
    #     # print(data)
    #     print("hello world!")

