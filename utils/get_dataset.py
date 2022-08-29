import json
import time
from copy import deepcopy

# 从5000多张数据中，每类手势各取100张， 共900个样本
json_path = "../annotation/2021-05-17.json"
save_path = "../annotation/900.json"
num_per_category = 100  # 每类手势需要多少张

data = json.load(open(json_path, 'r'))
images_list = deepcopy(data["images"])
annotations_list = deepcopy(data["annotations"])
count_list = [0 for _ in range(9)]

images_new = []
annotations_new = []

for i, image_info in enumerate(images_list):
    if sum(count_list) == (num_per_category * 9):
        break

    label = int(image_info["label"])
    if count_list[label] < num_per_category:
        count_list[label] += 1
        images_new.append(image_info)
        annotations_new.append(annotations_list[i])
    else:
        continue

print(f"{count_list=}")

# save
data["year"] = time.strftime("%Y".format(time.localtime()))
data["data_created"] = time.strftime("%Y/%m/%d".format(time.localtime()))

data["images"] = images_new
data["annotations"] = annotations_new

json.dump(data, open(save_path, "w"), indent=4)
