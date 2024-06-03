import json
import os
import sys
import random
import time
import openai
import threading
from config import get_opts_re as get_opts
from re_triplet_report_metric import triplet_report_metric

cur_path = os.getcwd()
sys.path.append(cur_path)
from utils import Logger, bot_run, ReadSample, WriteSample


def get_prompt_list(r_types, e_types):
    na_item = r_types[-1]
    r_types = list(set(r_types[:-1]))
    prompt_list = []

    if len(e_types) != 0:
        prompt = 'Please extract all relational fact triples from the given text, which consist of subject entity, object entity and the relation between two entities. The subject/object entity can be of the following types {}. The relation between entities can be of the following types {}.\nAnswer in the format \'["subject_entity", "relation", "object_entity"]\' without any explanation. If no relation exists, then just answer "[]".'.format(
            json.dumps(e_types), json.dumps(r_types))
        prompt_list.append(prompt)

        prompt = 'From the list of relations: {}, first find out all relations expressed by the given text, then identify the subject and object entities for each expressed relation. The subject/object entity can be of the following types {}.\nAnswer in the format \'["subject_entity", "relation", "object_entity"]\' without any explanation. If no relation exists, then just answer "[]".'.format(
            json.dumps(r_types), json.dumps(e_types))
        prompt_list.append(prompt)

        prompt = 'Given the list of relations: {}, judge whether each relation is expressed by the given text, return all expressed relations along with their corresponding subject and object entities. The subject/object entity can be of the following types {}.\nAnswer in the format \'["subject_entity", "relation", "object_entity"]\' without any explanation. If no relation exists, then just answer "[]".'.format(
            json.dumps(r_types), json.dumps(e_types))
        prompt_list.append(prompt)

        prompt = 'Given the list of entity types: {}, recognize all named entities from the given text, then judge whether any subject-object entity pair express the relation in the predefined list. The list of predefined relations is {}.\nAnswer in the format \'["subject_entity", "relation", "object_entity"]\' without any explanation. If no relation exists, then just answer "[]".'.format(
            json.dumps(e_types), json.dumps(r_types))
        prompt_list.append(prompt)

        e_types = ['"' + item + '"' for item in e_types]
        prompt = 'Considering entity types of {} and {}, find out all named entities in the given text, then return all subject-object entity pairs that express predefined relations. The list of predefined relations is {}.\nAnswer in the format \'["subject_entity", "relation", "object_entity"]\' without any explanation. If no relation exists, then just answer "[]".'.format(
            ", ".join(e_types[:-1]), e_types[-1], json.dumps(r_types))
        prompt_list.append(prompt)
    else:

        prompt = 'Please extract relational fact triples from the given text, which consist of subject entity, object entity and the relation between two entities. The relation between entities can be of the following types {}.\nAnswer in the format \'["subject_entity", "relation", "object_entity"]\' without any explanation. If no relation exists, then just answer "[]". Please combine the given text and its constituency information to accomplish the task.'.format(
            json.dumps(r_types))
        prompt_list.append(prompt)

        prompt = 'From the list of relations: {}, first find out all relations expressed by the given text, then identify the subject and object entities for each expressed relation.\nAnswer in the format \'["subject_entity", "relation", "object_entity"]\' without any explanation. If no relation exists, then just answer "[]".'.format(
            json.dumps(r_types))
        prompt_list.append(prompt)

        prompt = 'Given the list of relations: {}, judge whether each relation is expressed by the given text, return all expressed relations along with their corresponding subject and object entities.\nAnswer in the format \'["subject_entity", "relation", "object_entity"]\' without any explanation. If no relation exists, then just answer "[]".'.format(
            json.dumps(r_types))
        prompt_list.append(prompt)

        prompt = 'Recognize all named entities from the given text, then judge whether any subject-object entity pair express the relation in the predefined list. The list of predefined relations is {}.\nAnswer in the format \'["subject_entity", "relation", "object_entity"]\' without any explanation. If no relation exists, then just answer "[]".'.format(
            json.dumps(r_types))
        prompt_list.append(prompt)

        e_types = ['"' + item + '"' for item in e_types]
        prompt = 'Find out all named entities in the given text, then return all subject-object entity pairs that express predefined relations. The list of predefined relations is {}.\nAnswer in the format \'["subject_entity", "relation", "object_entity"]\' without any explanation. If no relation exists, then just answer "[]".'.format(
            json.dumps(r_types))
        prompt_list.append(prompt)

    return prompt_list


def get_icl_cot_prompt_list(opts):
    prompt_icl_list, prompt_cot_list = {}, {}
    if opts.ICL:
        prompt_icl_file = os.path.join(opts.input_dir, opts.task, opts.dataset, opts.icl_prompt)
        prompt_icl_list = json.load(open(prompt_icl_file, "r", encoding="utf-8"))
        prompt_cot_list = {}
    elif opts.COT:
        prompt_cot_file = os.path.join(opts.input_dir, opts.task, opts.dataset, opts.cot_prompt)
        prompt_cot_list = json.load(open(prompt_cot_file, "r", encoding="utf-8"))
        prompt_icl_list = {}
    return prompt_icl_list, prompt_cot_list


def re_triplet_get_prompt(opts, example, resource, prompt_list, prompt_icl_list, prompt_cot_list):
    tokens = example['seq'].split(" ")
    if len(tokens) > 1024:
        seq_str = " ".join(tokens[:1024])
    else:
        seq_str = example['seq']

    if opts.irrelevant:
        file_name = os.path.join(opts.input_dir, opts.task, opts.dataset, "train_no_relation.json")
        fr_no = open(file_name, "r", encoding="utf-8")
        data_no_term = json.load(fr_no)

        irrelevant_text_list = [item["seq"] for item in data_no_term]

        random_text = random.sample(irrelevant_text_list, 2)

        input_text = random_text[0] + " " + seq_str + " " + random_text[1]
    else:
        input_text = seq_str

    if opts.ICL:
        prompt = prompt_list[opts.best_prompt] + "\n" + prompt_icl_list[
            opts.prompt - 1] + '\nGiven text:\n"{}"\nAnswer:\n'.format(input_text)
    elif opts.COT:
        prompt = prompt_list[opts.best_prompt] + "\n" + prompt_cot_list[
            opts.prompt - 1] + '\nGiven text:\n"{}"\nAnswer:\n'.format(input_text)
    else:

        prompt = prompt_list[
                     opts.prompt - 1] + '\nGiven text:\n"{}"\nThe constituency information of the given text:\n"{}"\nAnswer:\n'.format(
            input_text, resource)
    return prompt


def get_best_prompt(opts, logger):
    file_name_list = ["re_triplet_result_" + str(i) + ".json" for i in range(1, 6)]

    f1_list = [triplet_report_metric(opts, logger, file_name=file) for file in file_name_list]

    best_prompt = f1_list.index(max(f1_list))
    return best_prompt


def re_triplet_main(opts, bot, logger):
    start_time = time.time()

    logger.write("{}\n".format(opts.test_file))
    logger.write("{}\n".format(opts.type_file))
    ## load data
    logger.write("loading data ...\n")
    with open(opts.test_file, 'r', encoding='utf-8') as fr, open(opts.type_file, 'r', encoding='utf-8') as fr_type:
        data = json.load(fr)
        types = json.load(fr_type)
        r_types = list(types["relation"].values())
        e_types = list(types["entity"].values())

    ## sample
    index_list = list(range(0, len(data)))
    if opts.sample:
        logger.write("Sampling examples ...\n")
        selected_idx = random.sample(index_list, opts.sample_k)
        selected_idx.sort()
        print(selected_idx)
    else:
        selected_idx = index_list
    ## sample end

    prompt_list = get_prompt_list(r_types, e_types)
    prompt_icl_list, prompt_cot_list = get_icl_cot_prompt_list(opts)

    if opts.ICL or opts.COT:
        opts.best_prompt = get_best_prompt(opts, logger)

        # ================将所需的外部资源文件读入=========
    resource_list = []
    if opts.resources:
        resource_dir = os.path.join(opts.input_dir,
                                    os.path.join(os.path.join(opts.task, opts.dataset), opts.resource_file))
        # with open(resource_dir) as file:
        #     for line in file:
        #         if line == "\n":
        #             continue
        #         resource_list.append(line.strip("\n"))

        #      SRL 等
        # with open(resource_dir) as file:
        #     while True:
        #         resource_string = ""
        #         for line in file:
        #             if line == "\n":
        #                 # end of current AMR
        #                 break
        #             resource_string += line
        #         if resource_string == "":
        #             break
        #         resource_list.append(resource_string)

        #  ====AMR===========
        with open(resource_dir) as file:
            while True:
                amr_string = ""
                for line in file:
                    if line == "\n":
                        # end of current AMR
                        break
                    if line.startswith("# ::annotator") or line.startswith("# ::date") or line.startswith("# ::snt"):
                        continue
                    amr_string += line
                if amr_string == "":
                    break
                resource_list.append(amr_string)
    print("*****************************************resource_list length :" + str(len(resource_list)))
    ## API
    with open(opts.result_file, 'a', encoding='utf-8') as fw:
        fw.seek(0)  # 定位
        fw.truncate()  # 清空文件
        fw.write("[\n")
        logger.write("Evaluation begining ...\n")
        i = 0
        while i < len(selected_idx):

            idx = selected_idx[i]
            i += 1
            logger.write(
                "No. " + str(i) + " | example's id: " + str(idx) + " | total examples: " + str(len(data)) + "\n")
            example = data[idx]
            resource = resource_list[idx]

            print(example["seq"])

            prompt = re_triplet_get_prompt(opts, example, resource, prompt_list, prompt_icl_list, prompt_cot_list)
            logger.write("RE-Triplet | " + str(i) + "/" + str(len(data)) + " | Prompt:\n" + prompt + "\n")

            response, prompt_final = bot_run(bot, prompt, example["seq"], model=opts.model)
            logger.write("RE-Triplet | " + str(i) + "/" + str(len(data)) + " | Response:\n" + response + "\n")

            # result_dict = get_result_dict(response)
            result_dict = {}

            example.update({
                "RE": result_dict,
                "prompt": prompt,
                "response": response
            })
            if opts.ICL or opts.COT:
                example["best_prompt"] = opts.best_prompt + 1

            fw.write(json.dumps(example, indent=4, ensure_ascii=False))
            if i != len(selected_idx):
                fw.write("\n,\n")
            else:
                fw.write("\n")
        fw.write("]\n")
    end_time = time.time()
    logger.write("The result is saved: {}\n".format(opts.result_file))
    logger.write("Times: {:.2f}s = {:.2f}m\n".format(end_time - start_time, (end_time - start_time) / 60.0))








if __name__ == "__main__":
    opts = get_opts()

    api_key_file = os.path.join("./api-keys", opts.api_key)
    openai.api_key_path = api_key_file
    bot = openai.ChatCompletion()

    ## log file
    logger_file = os.path.join(opts.task, opts.logger_file)
    logger = Logger(file_name=logger_file)
    # logger.write(json.dumps(opts.__dict__, indent=4) + "\n")


    re_triplet_main(opts, bot, logger)
