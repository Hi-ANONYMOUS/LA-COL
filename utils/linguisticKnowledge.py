import re

class LinguisticKnowledge:
    def __init__(self, text_dir, pos_dir, dep_dir, const_dir, srl_dir):
        self.text_dir = text_dir
        self.pos_dir = pos_dir
        self.dep_dir = dep_dir
        self.const_dir = const_dir
        self.srl_dir = srl_dir

        # ========read file =======
        self.text_list = read_text(self.text_dir)
        self.pos_list = read_knowledge(self.pos_dir)
        self.dep_list = read_knowledge(self.dep_dir)
        self.const_list = read_knowledge(self.const_dir)
        self.srl_list = read_knowledge(self.srl_dir)
        self.srl_string_list = read_srl(self.srl_dir)

        self.sample_num = len(self.text_list)

        # =========operation=======
        # ===========对POS列表进行处理==============
        self.pos_final_list = []
        for pos_sample in self.pos_list:
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
            self.pos_final_list.append(pos_sample_list)

        # ===========对DEP列表进行处理===============
        self.dep_final_list = []
        for dep_sample in self.dep_list:
            dep_sample_list = []
            for line in dep_sample:
                # 使用正则表达式提取括号内的内容
                matches = re.findall(r'\((.*?)\)', line)
                # 遍历分割后的字符串列表
                output_list = []
                # 遍历匹配到的内容
                for match in matches:
                    # 按逗号分割内容，并去除首尾空格，构建元组并添加到结果列表中
                    parts = match.split(',')
                    output_list.append((parts[0].strip(), parts[1].strip(), parts[2].strip()))
                dep_sample_list.append(output_list)
            self.dep_final_list.append(dep_sample_list)

        #==============对Const列表进行处理=============
        self.const_final_list = self.const_list

        # ===========对SRL列表进行处理==============
        self.srl_final_list = []
        for srl_sample in self.srl_list:
            srl_sample_list = []
            for line in srl_sample:
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
                srl_sample_list.append(pairs)
            self.srl_final_list.append(srl_sample_list)







def read_text(fileDir):
    data_list = []
    with open(fileDir, encoding='utf-8', errors='ignore') as file:
        for line in file:
            line.strip("\n")
            print(line)
            data_list.append(line)
    return data_list

def read_srl(fileDir):
    resource_list = []
    #      SRL 等
    with open(fileDir,  encoding='utf-8') as file:
        while True:
            resource_string = ""
            for line in file:
                if line == "\n":
                    # end of current AMR
                    break
                resource_string += line
            if resource_string == "":
                break
            resource_list.append(resource_string)

    return resource_list

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

