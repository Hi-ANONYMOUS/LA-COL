# import utils.treeNode as const_tree
import utils.parseTreeNode as parse_tree
import nltk
import re
from utils.hieNode import HieNode
from utils.linguisticKnowledge import LinguisticKnowledge


# ========= 版本1========



# /**
# ** 将数字映射为单词
# **/
def transform_number2word(number):
    # 创建数字到单词的映射关系的字典
    number_to_word = {
        1: "first",
        2: "second",
        3: "third",
        4: "fourth",
        5: "fifth",
        6: "sixth",
        7: "seventh",
        8: "eighth",
        9: "ninth",
        10: "tenth"
    }
    return number_to_word[number]


# /**
# ** 将子句标识映射为子句类型
# **/
def transform_type2clause(type):
    # 创建数字到单词的映射关系的字典
    type_to_clase = {
        "REL": "relative",
        "ADV": "adverbial",
        "SUB": "subjective",
        "APP": "appositive",
        "PRE": "predicative",
        "OBJ": "objective"
    }
    return type_to_clase[type]



def split_text(text, pos_list, dep_list, const_list, srl_list, srl_string):


    result_string = ""
    sentence_num = 1
    sentences_list = []
    hie_struct_node = HieNode(text, 0)
    hie_struct_node.height = 0

    # 步骤1 ===================================================
    # 判断文本类型，筛选出简单句
    # =========================================================
    if len(pos_list) > 1:
        # 1.1. 判断出是复杂句

        # 使用两个嵌套的列表推导式获取每个句子中的单词
        words_list = [[word for word, _ in pos_sentence] for pos_sentence in pos_list]
        # 使用列表推导式和字符串的join方法将每个句子中的单词连接成一个句子
        sentences_list = [' '.join(words) for words in words_list]
        for sentence in sentences_list:
            hie_struct_node.add_child(HieNode(sentence, 1))
        sentence_num = len(sentences_list)

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
            hie_struct_node.add_child(HieNode(text, 1))
            print("======这是复杂句======")
        else:
            # ====================== 转变为SRL描述语言 ================
            result_string = "The text is a simple sentence without clauses."
            result_string += transformSRLtagstoString(srl_list)

            return result_string


    # 步骤2 =======================================================================
    # 判断是并列句或主从句,并进行hieNode的构建。【目前只判断一层】
    # =============================================================================
    for sent_index in range(0, sentence_num):
        # 使用nltk.Tree.fromstring()方法来生成constituency tree
        trees = nltk.Tree.fromstring(const_list[sent_index])
        # 转换成树状结构, 并存储每个节点下的token_list
        parseTrees = parse_tree.process_tree(trees)
        parse_tree.store_tokens_in_tree(parseTrees)
        # 判断是否是并列句或主从句
        coordinate_list, cc_words, cc_node_step = parse_tree.find_CC_with_sibling_S(parseTrees)
        isCoordinate = len(coordinate_list) > 0
        # 逗号的并列句
        # if not isCoordinate:
        #     coordinate_list, cc_words, cc_node_step = parse_tree.find_punc_with_sibling_S(parseTrees)
        # isCoordinate is True if len(coordinate_list) > 0 else False
        isMainSub, sub_node_height = parse_tree.find_SBAR(parseTrees)
        if isCoordinate and isMainSub:
            print("该句子需要进一步判断，有并列句和主从句："+text)
            if cc_node_step <= sub_node_height:
                isMainSub = False
            else:
                isCoordinate = False
            # return "该句子需要进一步判断，有并列句和主从句："+text
        if isCoordinate:
            # 构建并列句的数据结构
            print("该句子是并列句：" + text)
            hie_struct_node.children[sent_index].ccWord = cc_words
            for coordinate_clause in coordinate_list:
                hie_struct_node.children[sent_index].add_child(HieNode(coordinate_clause, 2))
        elif isMainSub:
            print("该句子是主从句：" + text)
            # 构建主从句的数据结构
            main_clause = ""
            SBAR_clause = parse_tree.extract_SBAR_sentence(parseTrees)[0]
            # SBAR_clause_new = parse_tree.extract_SBAR_sentence_new(parseTrees)
            complete_sentence = " ".join(parseTrees.token_list)
            if complete_sentence.startswith(SBAR_clause):
                main_clause = complete_sentence[len(SBAR_clause):]
            else:
                index = complete_sentence.find(SBAR_clause)
                main_clause = complete_sentence[:index]
            main_clause_node = HieNode(main_clause.strip(' ,'), 2)
            main_clause_node.isMain = True
            hie_struct_node.children[sent_index].add_child(main_clause_node)
            hie_struct_node.children[sent_index].add_child(HieNode(SBAR_clause.strip(' ,'), 2))
            # 判断子句的类型
            dep_relations = [relation[1] for relation in dep_list[sent_index]]
            # 判断是否是定语从句
            if 'acl:relcl' in dep_relations or 'advcl:relcl' in dep_relations:
                hie_struct_node.children[sent_index].subType = "REL"
                continue
            #  判断是否是状语从句
            elif 'advcl' in dep_relations:
                hie_struct_node.children[sent_index].subType = "ADV"
                continue
            # 判断是否是主语从句
            elif "csubj" in dep_relations or "csubj:pass" in dep_relations:
                hie_struct_node.children[sent_index].subType = "SUB"
                continue
            # 判断是否是宾语从句、标语从句和同位语从句
            elif "ccomp" in dep_relations:
                # 常见的系动词列表
                linking_verbs = ["be", "seem", "appear", "become", "feel", "look", "smell", "taste"]
                # "be" 动词的常见形式列表
                be_verbs = ["am", "is", "are", "was", "were", "being", "been"]
                # 提取具有关系类型为'ccomp'的元组中的头和尾单词
                ccomp_head_tails = [(head, tail) for head, dep, tail in dep_list[sent_index] if dep == 'ccomp']
                # 同位语从句方向：主句名词 -> 从句动词。 判断head是不是名词
                if pos_list[sent_index][parseTrees.token_list.index(ccomp_head_tails[0][0])][1] == "NN":
                    hie_struct_node.children[sent_index].subType = "APP"
                    continue
                # 表语从句方向：主句be动词 -> 从句动词。 判断head是不是动词，且在不在常用系动词列表中
                elif (pos_list[sent_index][parseTrees.token_list.index(ccomp_head_tails[0][0])][1] == "VBZ" or pos_list[sent_index][parseTrees.token_list.index(ccomp_head_tails[0][0])][1] == "VBD") and (pos_list[sent_index][parseTrees.token_list.index(ccomp_head_tails[0][0])][0] in linking_verbs or pos_list[sent_index][parseTrees.token_list.index(ccomp_head_tails[0][0])][0] in be_verbs):
                    hie_struct_node.children[sent_index].subType = "PRE"
                    continue
                # 宾语从句方向：主句动词 -> 从句动词
                else:
                    hie_struct_node.children[sent_index].subType = "OBJ"
                    continue
            else:
                hie_struct_node.children[sent_index].subType = "OBJ"
        else:
            # 这是个简单句，不做进一步处理【两种情况，一种是多句里的简单句，另一个是本来判断的是复杂单句，但是没能匹配出并列或主从】
            print("这是简单句")


    # 步骤3 ============================================================
    # 根据hieNode结构，返回结果
    # ==================================================================
    # ===多句===
    if sentence_num > 1:
        result_string = "The text contains " + str(sentence_num) + " sentences."
        for sent_index in range(0, sentence_num):
            result_string += " The " + transform_number2word(sent_index+1) + " sentence is " + "\""+ hie_struct_node.children[sent_index].text +"\"."
            clause_num = len(hie_struct_node.children[sent_index].children)
            # 处理的是 多句中的简单单句
            # The [first] sentence is a complex sentence containing
            if clause_num <=1:
                result_string += " This sentence is a simple sentence without clauses."
                continue
            #  该句子是主从句
            if hie_struct_node.children[sent_index].subType != "":
                for clause_index in range(0, clause_num):
                    if hie_struct_node.children[sent_index].children[clause_index].isMain:
                        main_clause = hie_struct_node.children[sent_index].children[clause_index].text
                    else:
                        sub_clause = hie_struct_node.children[sent_index].children[clause_index].text
                result_string += " This sentence has a main clause and a " + transform_type2clause(hie_struct_node.children[sent_index].subType) +" subordinate clause, which are \"" \
                                                                                                                          + main_clause +"\" and \"" + sub_clause + "\"."
            #  该句子是并列句
            if len(hie_struct_node.children[sent_index].ccWord) > 0:
                result_string += " This sentence has " + str(clause_num) + " coordinate clauses, which are "
                for clause_index in range(0, clause_num):
                    if clause_index == clause_num-1:
                        result_string += " and \"" +hie_struct_node.children[sent_index].children[clause_index].text + "\"."
                    else:
                        result_string += "\"" + hie_struct_node.children[sent_index].children[
                            clause_index].text + "\","
    #====单句
    else:
        clause_num = len(hie_struct_node.children[0].children)
        # ====【按简单句处理】
        if clause_num <= 1:
            # ===================转变为SRL描述信息===============
            result_string = "The text is a simple sentence without clauses."
            result_string += transformSRLtagstoString(srl_list)



        else:
        # ====该单句是并列句或主从句。
            #  该句子是主从句
            if hie_struct_node.children[0].subType != "":
                for clause_index in range(0, clause_num):
                    if hie_struct_node.children[0].children[clause_index].isMain:
                        main_clause = hie_struct_node.children[0].children[clause_index].text
                    else:
                        sub_clause = hie_struct_node.children[0].children[clause_index].text
                result_string += "The text is a complex sentence containing a main clause and a " + transform_type2clause(
                    hie_struct_node.children[0].subType) + " subordinate clause, which are \"" \
                                 + main_clause + "\" and \"" + sub_clause + "\"."
                # ===================转变为SRL描述信息===============
                result_string = "The text is a simple sentence without clauses."
                result_string += transformSRLtagstoString(srl_list)

            #  该句子是并列句
            if len(hie_struct_node.children[0].ccWord) > 0:
                result_string += "The text is a complex sentence containing " + str(clause_num) + " coordinate clauses, which are "
                for clause_index in range(0, clause_num):
                    if clause_index == clause_num - 1:
                        result_string += " and \"" + hie_struct_node.children[0].children[
                            clause_index].text + "\"."
                    else:
                        result_string += "\"" + hie_struct_node.children[0].children[
                            clause_index].text + "\","
                    # ===================转变为SRL描述信息===============
                    result_string = "The text is a simple sentence without clauses."
                    result_string += transformSRLtagstoString(srl_list)

    return result_string

if __name__ == '__main__':

    linguisticList = LinguisticKnowledge(text_dir, pos_dir, dep_dir, const_dir, srl_dir)

    # （2）循环处理每个样本，获取每个样本的结构描述
    result_list = []
    sample_num = linguisticList.sample_num
    for sample_index in range(0, sample_num):
        print("这是第"+str(sample_index+1)+"个句子: \n"+linguisticList.text_list[sample_index])
        result = split_text(linguisticList.text_list[sample_index], linguisticList.pos_final_list[sample_index],
                            linguisticList.dep_final_list[sample_index], linguisticList.const_final_list[sample_index],
                            linguisticList.srl_final_list[sample_index], linguisticList.srl_string_list[sample_index])
        result_list.append(result)


    # 统计一下简单句有多少
    simpleSentenceNum = 0
    for line in result_list:
        if "The text is a simple sentence without clauses." in line:
            simpleSentenceNum += 1
    ratio = round(simpleSentenceNum / sample_num, 2)
    print("样本的总数为："+str(sample_num))
    print("简单句的个数为："+str(simpleSentenceNum))
    print("简单句的比例为："+str(ratio))

    # （3）保存结果
    # 打开文件以写入模式
    with open("output.txt", "w",  encoding='utf-8') as f:
        # 使用换行符将列表中的每个元素写入文件
        for line in result_list:
            f.write(line + "\n\n")


