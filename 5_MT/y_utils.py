import json
import os, sys
import ast
import threading
import requests
import os
import json
import time



#!/usr/bin/env python
# coding=utf-8




# =========================================================VANILLA================================================
def bot_run_deepseek_vanilla(client, prompt):

    # ====HERE  GAI===========
    systemContent = "You are a famous expert on Machine Translation. "
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            # model="deepseek-reasoner",
            messages=[
                {"role": "system", "content": systemContent},
                {"role": "user", "content": prompt},
            ],
            # max_tokens=1024,
            # response_format={
            #     'type': 'text'
            # },
            temperature=1.0,
            stream=False
        )
    except Exception as e:
        print(f"API : {str(e)}")
        return "None Answer"

    return response.choices[0].message.content


def bot_run_llama_vanilla(bot, prompt):

    # Sleep for the delay
    # time.sleep(1)
    retry_count = 0
    while retry_count < 3:
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": "Bearer",
                    "Content-Type": "application/json"
                },
                data=json.dumps({
                    "model": "meta-llama/llama-3-8b-instruct",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert on Machine Translation.",
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    'provider': {
                        'sort': 'price',
                        'data_collection': 'deny'
                    }
                })
            )

            if response.status_code == 200:
                result = response.json()
                print(result['choices'][0]['message']['content'])
                return result['choices'][0]['message']['content']
            else:
                print("REQUEST WRONG：", response.status_code)
                return "REQUEST WRONG："+response.status_code
        except Exception as e:
            # print(f"API : {str(e)}")
            print(f"请求失败 (尝试 {retry_count + 1}/{3}): {str(e)}")
            retry_count += 1
            if retry_count < 3:
                time.sleep(1)  # 延迟后再重试



def bot_run_deepseek_ETE(client, prompt, model):


    # ====HERE  GAI===========
    systemContent = "You are a famous expert on Machine Translation. " \
                    "Linguistically, the constituency tree of the text could help you understand the text comprehensively. " \
                    "So you can combine the text and its constituency tree to accomplish MT task better. "

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            # model="deepseek-reasoner",
            messages=[
                {"role": "system", "content": systemContent},
                {"role": "user", "content": prompt},
            ],
            # max_tokens=1024,
            # response_format={
            #     'type': 'text'
            # },
            temperature=1.0,
            stream=False
        )
    except Exception as e:
        print(f"API : {str(e)}")
        return "None Answer", systemContent + prompt

    return response.choices[0].message.content, systemContent + prompt






def number_to_ordinal(num):
    ordinal_mapping = {
        0: 'first',
        1: 'second',
        2: 'third',
        3: 'fourth',
        4: 'fifth',
        # 可以继续添加更多数字的映射
    }
    return ordinal_mapping.get(num, str(num))  # 如果数字不在映射中，返回数字本身





# =========================================================COL================================================
def bot_run_COL(client, prompt, text, model="gpt-3.5-turbo-1106"):


    # =====================第一轮回合=============
    systemContent_round1 = "You are an expert on Language Parsing and Tagging."
    messages = [
        # {"role": "system", "content": "You are a famous expert on Relation Extraction, especially expertise in Relational Triplet Extraction."},
        {"role": "system",
         "content": systemContent_round1},
        {"role": "user",
         "content": "First, let's perform Abstract Meaning Representation (AMR) parsing for the given text. "
                    "Please only return the results directly without any explanation. \nGiven text:\n" + text},
    ]

    response1 = client.chat.completions.create(
        model="deepseek-chat",
        # model="deepseek-reasoner",
        messages=messages,
        # max_tokens=1024,
        # response_format={
        #     'type': 'text'
        # },
        temperature=1.0,
        stream=False
    )
    print(response1.choices[0].message.content)

    # ========================第二个回合==========
    systemContent_round2 = "You are a famous expert on Machine Translation. " \
                    "Linguistically, the AMR graph of the text could help you understand the text comprehensively. " \
                    "So you can combine the text and its AMR graph to accomplish the MT task. "

    messages.append(response1.choices[0].message.to_dict())
    messages.append(
        {"role": "system",
         "content": systemContent_round2}
    )
    messages.append({'role': 'user', 'content': prompt})
    json_string = json.dumps(messages)
    response2 = client.chat.completions.create(
        model="deepseek-chat",
        # model="deepseek-reasoner",
        messages=messages,
        # max_tokens=1024,
        # response_format={
        #     'type': 'text'
        # },
        temperature=1.0,
        stream=False
    )
    # response_2 = requests.post(
    #     url="https://openrouter.ai/api/v1/chat/completions",
    #     headers={
    #         "Authorization": "Bearer s",
    #         "Content-Type": "application/json"
    #     },
    #     data=json.dumps({
    #         "model": "meta-llama/llama-3-8b-instruct",
    #         "messages": messages,
    #         'provider': {
    #             'sort': 'price',
    #             'data_collection': 'deny'
    #         }
    #     })
    # )
    return response2.choices[0].message.content, json_string














def bot_run_http(prompt):
    # Sleep for the delay
    time.sleep(1)

    response = requests.post(
        url="https://api.deepseek.com/chat/completions",
        headers={
            "Authorization": "Bearer",
            "Content-Type": "application/json"
        },
        data=json.dumps({
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are an expert on Machine Translation."},
                {"role": "user", "content": prompt}
            ],
            "stream": False
        })
    )

    print(response)
    if response.status_code == 200:
        result = response.json()
        print(result['choices'][0]['message']['content'])
        return result['choices'][0]['message']['content']
    else:
        print("请求失败，错误码：", response.status_code)
        return response.status_code


