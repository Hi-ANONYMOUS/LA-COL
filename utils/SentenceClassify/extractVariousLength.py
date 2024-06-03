
import nltk
import re
import json



def read_text(fileDir):
    data_list = []
    with open(fileDir, encoding='utf-8', errors='ignore') as file:
        for line in file:
            line.strip("\n")
            print(line)
            data_list.append(line)
    return data_list



# ==============================================第1阶段：提取出分段的index


text_dir = ""


text_list = read_text(text_dir)

word_ranges = {
        "1-10": [],
        "11-20": [],
        "21-30": [],
        "31-40": [],
        "41-50": [],
        "51+": [],
        # "61+": []
    }

word_counts = {
        "1-10": 0,
        "11-20": 0,
        "21-30": 0,
        "31-40": 0,
        "41-50": 0,
        # "51-60": 0,
        "51+": 0
    }


for index, text in enumerate(text_list):
    word_length = len(text.split())  # 计算单词总长度
    if word_length <= 10:
        word_ranges["1-10"].append(index)
        word_counts["1-10"] += 1
    elif word_length <= 20:
        word_ranges["11-20"].append(index)
        word_counts["11-20"] += 1
    elif word_length <= 30:
        word_ranges["21-30"].append(index)
        word_counts["21-30"] += 1
    elif word_length <= 40:
        word_ranges["31-40"].append(index)
        word_counts["31-40"] += 1
    elif word_length <= 50:
        word_ranges["41-50"].append(index)
        word_counts["41-50"] += 1
    # elif word_length <= 60:
    #     word_ranges["51-60"].append(index)
    #     word_counts["51-60"] += 1
    else:
        word_ranges["51+"].append(index)
        word_counts["51+"] += 1

# 打印分组结果
for range_name, count_num in word_counts.items():
    print(f"Words in the range {range_name}, Count: {count_num}")


# ===================根据index，提取相应的结果json============
file_name = ""
result_list = []
with open(file_name, 'r', encoding='utf-8') as fr:
    result_list = json.load(fr)

samples_by_range= {}
for range_name, indices in word_ranges.items():
    samples = [result_list[i] for i in indices]
    samples_by_range[range_name] = samples


# 写入
for range_name, samples in samples_by_range.items():
    dir = ""
    file_name = dir + "COL-turbo-1106-casie-srl-"+f"{range_name}.json"
    with open(file_name, "w", encoding="utf-8") as fw:
        fw.write(json.dumps(samples, indent=4, ensure_ascii=False))
    # with open(file_name, "w") as f:
    #     for sample in samples:
    #         f.write(sample + "\n")
print(samples_by_range)