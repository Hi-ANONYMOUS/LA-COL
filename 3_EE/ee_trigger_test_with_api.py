import json
import os
import sys
import random
import time
import openai
import threading
from config import get_opts_ee as get_opts
from ee_trigger_report_metric import trigger_report_metric

cur_path = os.getcwd()
sys.path.append(cur_path)
from utils import Logger, bot_run, ReadSample, WriteSample


def get_prompt_list(event_types_list):
    prompt_list = []


    prompt = 'Considering {} types of events: {}, recognize all event triggers with their corresponding event types in the given text. The event trigger is a word or phrase in the given text that indicates the occurrence of a pre-defined event. The corresponding event type answered must be one of the pre-defined event types.\nAnswer in the format ["event_trigger", "event_type"] without any explanation. If no event trigger is involved, then just answer "[]". Please combine the given text and its constituency information to accomplish the task.'.format(
        len(event_types_list), json.dumps(event_types_list))
    prompt_list.append(prompt)

    # 2
    prompt = 'From the pre-defined list of event types {}, first find out all event triggers in the given text, then determine the corresponding event type for each involved event trigger. The event trigger is a word or phrase in the given text that indicates the occurrence of a pre-defined event. The corresponding event type answered must be one of the pre-defined event types.\nAnswer in the format ["event_trigger", "event_type"] without any explanation. If no event trigger is involved, then just answer "[]". Please combine the given text and its constituency information to accomplish the task.'.format(
        json.dumps(event_types_list))
    prompt_list.append(prompt)

    # 3
    prompt = 'Judge which words or phrases in the given text are event triggers, and categorize each of them into one of the pre-defined event types. The event trigger is a word or phrase in the given text that indicates the occurrence of a pre-defined event. The pre-defined list of event types is {}.\nAnswer in the format ["event_trigger", "event_type"] without any explanation. If no event trigger is involved, then just answer "[]". Please combine the given text and its constituency information to accomplish the task.'.format(json.dumps(event_types_list))
    prompt_list.append(prompt)

    # 4
    prompt = 'Which words or phrases in the given text are event triggers? Which pre-defined event type is indicated by each event trigger? The event trigger is a word or phrase in the given text that indicates the occurrence of a pre-defined event. The answered event type must be one of the pre-defined event types. The pre-defined list of event types is {}.\nAnswer in the format ["event_trigger", "event_type"] without any explanation. If no event trigger is involved, then just answer "[]". Please combine the given text and its constituency information to accomplish the task.'.format(json.dumps(event_types_list))
    prompt_list.append(prompt)

    # 5
    prompt = 'Given the pre-defined list of event types {}, which words or phrases in the given text are event triggers for the above event types? What is the corresponding event type of each event trigger? The event trigger is a word or phrase in the given text that indicates the occurrence of a pre-defined event. The corresponding event type answered must be one of the pre-defined event types.\nAnswer in the format ["event_trigger", "event_type"] without any explanation. If no event trigger is involved, then just answer "[]". Please combine the given text and its constituency information to accomplish the task.'.format(json.dumps(event_types_list))
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


def ee_trigger_get_prompt(opts, example, resource, prompt_list, prompt_icl_list, prompt_cot_list):
    tokens = example['text'].split(" ")
    if len(tokens) > 1024:
        seq_str = " ".join(tokens[:1024])
    else:
        seq_str = example['text']

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
        basic_prompt = prompt_list[opts.best_prompt].split("\nAnswer")[
                           0] + " Let's think step by step, and answer in the format [\"event_trigger\", \"event_type\"]. If no event trigger is involved, then answer \"[]\"."
        prompt = basic_prompt + "\n" + prompt_cot_list[opts.prompt - 1] + '\nGiven text:\n"{}"\nAnswer:\n'.format(
            input_text)
    else:

        prompt = prompt_list[
                     opts.prompt - 1] + '\nGiven text:\n"{}"\nThe constituency information of the given text:\n"{}"\nAnswer:\n'.format(
            input_text, resource)
    return prompt


def get_best_prompt(opts, logger):
    file_name_list = ["ee_trigger_result_" + str(i) + ".json" for i in range(1, 6)]

    f1_list = [trigger_report_metric(opts, logger, file_name=file) for file in file_name_list]

    best_prompt = f1_list.index(max(f1_list))
    return best_prompt


def ee_trigger_main(opts, bot, logger):
    start_time = time.time()

    logger.write("{}\n".format(opts.test_file))
    logger.write("{}\n".format(opts.type_file))
    ## load data
    logger.write("loading data ...\n")
    with open(opts.test_file, 'r', encoding='utf-8') as fr, open(opts.type_file, 'r', encoding='utf-8') as fr_type:
        data = json.load(fr)
        types = json.load(fr_type)
        event_types = types["event_types"]
        event_types_list = [event_types[key]["verbose"].lower() for key in event_types]

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

    prompt_list = get_prompt_list(event_types_list)
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
        #         resource_list.append(resource_string)

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

            prompt = ee_trigger_get_prompt(opts, example, resource, prompt_list, prompt_icl_list, prompt_cot_list)
            logger.write("EE-Trigger | " + str(i) + "/" + str(len(data)) + " | Prompt:\n" + prompt + "\n")

            response, prompt_final = bot_run(bot, prompt, example["text"], model=opts.model)
            logger.write("EE-Trigger | " + str(i) + "/" + str(len(data)) + " | Response:\n" + response + "\n")

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

    ee_trigger_main(opts, bot, logger)
