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

def read_knowledge(resourceDir):
    resource_list = []
    with open(resourceDir,  encoding='utf-8') as file:
        while True:
            resource_string = []
            for line in file:
                if line == "\n":
                    # end of current AMR
                    break
                resource_string.append(line.strip("\n"))
            if len(resource_string) == 0:
                break
            resource_list.append(resource_string)
    return resource_list

# ===========================================第1阶段：提取出分段的index====================================
text_dir = ""


pos_data_list = read_knowledge(text_dir)

# =========operation=======
# ===========对POS列表进行处理==============
pos_final_list = []
for pos_sample in pos_data_list:
    pos_sample_list = []
    for line in pos_sample:
        pairs = line.split()
        print(pairs)
        pairs = [pair.split('/') for pair in pairs]
        # 为了处理//这种情况，切分出来的元素数大于2个，做截断
        for i in range(len(pairs)):
            # 如果 pairs[i] 的长度大于 2
            if len(pairs[i]) > 2:
                # 只保留前两个元素，并赋值给 pairs[i]
                pairs[i] = pairs[i][:2]
        pairs = [(word, tag) for word, tag in pairs]
        pos_sample_list.append(pairs)
    pos_final_list.append(pos_sample_list)

sentence_classification = {
        "complex": [],
        "simple": []
    }

sentence_counts = {
        "complex": 0,
        "simple": 0
    }



# 步骤1 ===================================================
    # 判断文本类型，筛选出简单句
    # =========================================================
for index, pos_list in enumerate(pos_final_list):
    if len(pos_list) > 1:
        # 1.1. 直接判断出是复杂句，直接往下走
        sentence_classification["complex"].append(index)
        sentence_counts["complex"] += 1

    else:
        # 1.2 根据pos统计动词的个数，判断是简单句还是复杂句
        only_pos_list = [pos[1] for pos in pos_list[0]]
        VBZPD_num = only_pos_list.count('VBZ') + only_pos_list.count('VBP') + only_pos_list.count('VBD')
        for pos_i, pos in enumerate(only_pos_list):
            if pos == "VB":
                if only_pos_list[max(0,pos_i-1)] == "MD" or only_pos_list[max(0,pos_i-1)] == "CC" or only_pos_list[max(0,pos_i-2)] == "MD" or only_pos_list[max(0,pos_i-2)] == "CC":
                    VBZPD_num += 1
            if pos == "VB" and pos_i==0:
                VBZPD_num += 1
            if pos == "VB" and (only_pos_list[max(0,pos_i-1)] == "." or only_pos_list[max(0,pos_i-1)]==",") :
                VBZPD_num += 1

        if VBZPD_num > 1:
            sentence_classification["complex"].append(index)
            sentence_counts["complex"] += 1
        else:
            sentence_classification["simple"].append(index)
            sentence_counts["simple"] += 1


# 打印分组结果
for range_name, count_num in sentence_counts.items():
    print(f"Words in the range {range_name}, Count: {count_num}")


# ===================根据index，提取相应的结果json============
file_name = ""
result_list = []
with open(file_name, 'r', encoding='utf-8') as fr:
    result_list = json.load(fr)

samples_by_range= {}
for range_name, indices in sentence_classification.items():
    samples = [result_list[i] for i in indices]
    samples_by_range[range_name] = samples


# 写入
for range_name, samples in samples_by_range.items():
    dir = ""
    file_name = dir + "COL-turbo-Instruct-COM-hsvo-"+f"{range_name}.json"
    with open(file_name, "w", encoding="utf-8") as fw:
        fw.write(json.dumps(samples, indent=4, ensure_ascii=False))
    # with open(file_name, "w") as f:
    #     for sample in samples:
    #         f.write(sample + "\n")
print(samples_by_range)