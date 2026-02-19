
import os
import sys
import json
import random
from config import get_opts_ner
cur_path = os.getcwd()
sys.path.append(cur_path)
from utils import Logger, ReadSample, WriteSample, bot_run




# 从json文件中抽取出句子，写到句子文件中，方便进行后处理
def generate_sentence(opts):
    input_dir = os.path.join(opts.input_dir, os.path.join(os.path.join(opts.task, opts.dataset), "genia-test-sample500.json"))
    output_dir = os.path.join(opts.input_dir, os.path.join(os.path.join(opts.task, opts.dataset), "genia-test-sample500_sentence.txt"))
    with open(input_dir, 'r', encoding='utf-8') as fr:
        data = json.load(fr)
    test_data_sentence = [item["seq"] for item in data]
    test_data_sentence_len = [len(item) for item in test_data_sentence]
    print(test_data_sentence_len)
    # 将列表元素写入text文本文件
    with open(output_dir, "w") as text_file:
        for item in test_data_sentence:
            text_file.write(item + "\n")



# 从测试集中采样所需的样本
def ner_sample_main(opts):

    #================ 1. 读入所有数据并取样
    # input_dir = os.path.join(opts.input_dir, os.path.join(os.path.join(opts.task, opts.dataset), opts.test_file))
    input_dir = os.path.join(opts.test_file)
    # logger.write("loading data ...\n")
    with open(input_dir, 'r', encoding='utf-8') as fr:
        data = json.load(fr)

    index_list = list(range(len(data)))
    # logger.write("Sampling examples ...\n")
    selected_idx = random.sample(index_list, 10)
    selected_idx.sort()
    sample_data_list = [data[idx] for idx in selected_idx]
    # sample_data_list = data[selected_idx]
    print(len(sample_data_list))

    #================ 2. 将数据存入文件中
    # 将列表转换为 JSON 格式的字符串
    json_data = json.dumps(sample_data_list, indent=2)  # indent 参数可选，用于指定缩进空格数，使 JSON 文件更易读
    # 将 JSON 字符串写入文件
    output_dir = os.path.join(opts.input_dir, os.path.join(os.path.join(opts.task, opts.dataset), "genia-test-sample10.json"))
    with open(output_dir, "w") as json_file:
        json_file.write(json_data)


if __name__ == "__main__":
    opts = get_opts_ner()

    ner_sample_main(opts)

    # generate_sentence(opts)

