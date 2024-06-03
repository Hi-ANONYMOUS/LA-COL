import json, os
import random
import time
import openai
import threading
import sys

cur_path = os.getcwd()
sys.path.append(cur_path)
from utils import Logger, bot_run, ReadSample, WriteSample
from config import get_opts_ee as get_opts
from ee_joint_report_metric import joint_report_metric


def get_prompt_list(event_types_list, roles_str):
    prompt_list = []

    prompt = 'Pre-defined event types include: {}.\n{}\n\nFrom the given text, recognize all event triggers with their corresponding event types, and recognize all arguments of each event and their corresponding roles. The event trigger is a word or phrase in the given text that indicates the occurrence of a pre-defined event. The corresponding event type answered must be one of the pre-defined event types. Each occurred event involves several arguments, and each argument belongs to a pre-defined role. The argument is an entity that appears in the given text and participates in this event. The corresponding role must be one of the given candidate roles.\nFor each occurred event, answer in the format \'["event_trigger", "event_type"]: [["argument_1", "role_1"], ["argument_2", "role_2"], ...]\' without any explanation. If no argument exists for the recognized event, then just answer in the format \'["event_trigger", "event_type"]: []\'. If no event trigger is involved (i.e., no event occurs), then just answer "[]". Please combine the given text and its constituency information to accomplish the task.'.format(
        json.dumps(sorted(event_types_list)), roles_str)
    prompt_list.append(prompt)

    # 2
    prompt = 'The list of pre-defined event types is {}.\n{}\n\nFrom the given text, first find out all event triggers from it and determine the corresponding event type for each event trigger, then find out all arguments of each event from the given text, then assign a role to each argument from the given candidate roles. The event trigger is a word or phrase in the given text that indicates the occurrence of a pre-defined event. The corresponding event type answered must be one of the pre-defined event types. Each occurred event involves several arguments, and each argument belongs to a pre-defined role. The argument is an entity that appears in the given text and participates in this event. The corresponding role must be one of the given candidate roles.\nFor each occurred event, answer in the format \'["event_trigger", "event_type"]: [["argument_1", "role_1"], ["argument_2", "role_2"], ...]\' without any explanation. If no argument exists for the recognized event, then just answer in the format \'["event_trigger", "event_type"]: []\'. If no event trigger is involved (i.e., no event occurs), then just answer "[]". Please combine the given text and its constituency information to accomplish the task.'.format(
        json.dumps(sorted(event_types_list)), roles_str)
    prompt_list.append(prompt)

    # 3
    prompt = 'Given the pre-defined event types: {}, the roles of each event type are as follows: {}\n\nGiven the text, first judge which words or phrases in the given text are event triggers and categorize each of them into one of the pre-defined event types, then identify all arguments of each event from the given text, and select a role from the given candidate roles for each argument. The event trigger is a word or phrase in the given text that indicates the occurrence of a pre-defined event. The corresponding event type answered must be one of the pre-defined event types. Each occurred event involves several arguments, and each argument belongs to a pre-defined role. The argument is an entity that appears in the given text and participates in this event. The corresponding role must be one of the given candidate roles.\nFor each occurred event, answer in the format \'["event_trigger", "event_type"]: [["argument_1", "role_1"], ["argument_2", "role_2"], ...]\' without any explanation. If no argument exists for the recognized event, then just answer in the format \'["event_trigger", "event_type"]: []\'. If no event trigger is involved (i.e., no event occurs), then just answer "[]". Please combine the given text and its constituency information to accomplish the task.'.format(
        json.dumps(sorted(event_types_list)), roles_str)
    prompt_list.append(prompt)

    # 4
    prompt = 'Pre-defined event types include: {}.\n{}\n\nGiven a piece of text, which words or phrases in the given text are event triggers? Which pre-defined event type is indicated by each event trigger? For each event, what are all arguments of this event in the given text? What is the corresponding role for each argument? The event trigger is a word or phrase in the given text that indicates the occurrence of a pre-defined event. The corresponding event type answered must be one of the pre-defined event types. Each occurred event involves several arguments, and each argument belongs to a pre-defined role. The argument is an entity that appears in the given text and participates in this event. The corresponding role must be one of the given candidate roles.\nFor each occurred event, answer in the format \'["event_trigger", "event_type"]: [["argument_1", "role_1"], ["argument_2", "role_2"], ...]\' without any explanation. If no argument exists for the recognized event, then just answer in the format \'["event_trigger", "event_type"]: []\'. If no event trigger is involved (i.e., no event occurs), then just answer "[]". Please combine the given text and its constituency information to accomplish the task.'.format(
        json.dumps(sorted(event_types_list)), roles_str)
    prompt_list.append(prompt)

    # 5
    prompt = 'The list of pre-defined event types is {}.\n{}\n\nGiven a piece of text, which words or phrases in the given text are event triggers for the above event types? What is the corresponding event type of each event trigger? For each event, what arguments of this event are included in this text? What is the corresponding role of each argument? The event trigger is a word or phrase in the given text that indicates the occurrence of a pre-defined event. The corresponding event type answered must be one of the pre-defined event types. Each occurred event involves several arguments, and each argument belongs to a pre-defined role. The argument is an entity that appears in the given text and participates in this event. The corresponding role must be one of the given candidate roles.\nFor each occurred event, answer in the format \'["event_trigger", "event_type"]: [["argument_1", "role_1"], ["argument_2", "role_2"], ...]\' without any explanation. If no argument exists for the recognized event, then just answer in the format \'["event_trigger", "event_type"]: []\'. If no event trigger is involved (i.e., no event occurs), then just answer "[]". Please combine the given text and its constituency information to accomplish the task.'.format(
        json.dumps(sorted(event_types_list)), roles_str)
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


def ee_joint_get_prompt(opts, example, resource, prompt_list, prompt_icl_list, prompt_cot_list):
    tokens = example["text"].split(" ")
    if len(tokens) > 1024:
        seq_str = " ".join(tokens[:1024])
    else:
        seq_str = example["text"]

    if opts.irrelevant:
        file_name = os.path.join(opts.input_dir, opts.task, opts.dataset, "train_no_event.json")
        fr_no = open(file_name, "r", encoding="utf-8")
        data_no_term = json.load(fr_no)

        irrelevant_text_list = [item["text"] for item in data_no_term]

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
        #
        prompt = prompt_list[
                     opts.prompt - 1] + '\nGiven text:\n"{}"\nThe constituency information of the given text:\n"{}"\nAnswer:\n'.format(
            input_text, resource)
    return prompt


def get_best_prompt(opts, logger):
    file_name_list = ["ee_joint_result_" + str(i) + ".json" for i in range(1, 6)]

    f1_list = [joint_report_metric(opts, logger, file_name=file) for file in file_name_list]

    best_prompt = f1_list.index(max(f1_list))
    return best_prompt


def get_roles_str(event2roles):
    res = []
    for k, v in event2roles.items():
        tmp_str = 'The list of roles for event "{}" is {}.'.format(k, json.dumps(v))
        res.append(tmp_str)

    return " ".join(res)


def ee_joint_main(opts, bot, logger):
    start_time = time.time()

    logger.write("{}\n".format(opts.test_file))
    logger.write("{}\n".format(opts.type_file))
    ## load data
    logger.write("loading data ...\n")
    with open(opts.test_file, 'r', encoding='utf-8') as fr, open(opts.type_file, 'r', encoding='utf-8') as fr_type:
        data = json.load(fr)
        types = json.load(fr_type)
        event_types = types["event_types"]
        event_types_list = [event_types[key]["verbose"] for key in event_types]
        event2roles = types["event2roles"]

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

    roles_str = get_roles_str(event2roles)
    prompt_list = get_prompt_list(event_types_list, roles_str)
    # print(prompt_list)
    prompt_icl_list, prompt_cot_list = get_icl_cot_prompt_list(opts)

    if opts.ICL or opts.COT:
        opts.best_prompt = get_best_prompt(opts, logger)

        # ================将所需的外部资源文件读入=========
    resource_list = []
    if opts.resources:
        resource_dir = os.path.join(opts.input_dir,
                                    os.path.join(os.path.join(opts.task, opts.dataset), opts.resource_file))

        #  =======dep pos SRL 等========
        # with open(resource_dir, encoding='utf-8') as file:
        #     while True:
        #         resource_string = ""
        #         for line in file:
        #             if line == "\n":
        #                 # end of current AMR
        #                 break
        #             resource_string += line
        #         if resource_string == "":
        #             break
        #         resource_list.append(resource_string.strip())

        #  ==========AMR=========
        with open(resource_dir, encoding='utf-8') as file:
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

            print(example["text"])

            prompt = ee_joint_get_prompt(opts, example, resource, prompt_list, prompt_icl_list, prompt_cot_list)
            logger.write("EE-Joint | " + str(i) + "/" + str(len(data)) + " | Prompt:\n" + prompt + "\n")

            response, prompt_final = bot_run(bot, prompt, example["text"], model=opts.model)
            logger.write("EE-Joint | " + str(i) + "/" + str(len(data)) + " | Response:\n" + response + "\n")

            example.update({
                "prompt": prompt_final,
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


    ee_joint_main(opts, bot, logger)
