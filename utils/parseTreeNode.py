class ParseTreeNode:
    def __init__(self, val):
        self.value = val
        self.children = []
        self.height = 0
        self.leaf = ''
        self.parent = None
        self.token_list = []
        # attributes for generating S and hierarchical positional embeddings
        # self.leaf_order_idx = -1  # 0 indexed
        # self.leaf_list = []

    def add_child(self, child):
        self.children.append(child)
        child.parent = self

# /**
# 转化成树状数据结构 【ParseTreeNode】
# **/
def process_tree(root):
    current = ParseTreeNode(root.label())
    child_num = len(root)
    for index in range(0, child_num):
        ch = root[index]
        if not isinstance(ch, str):
            child = process_tree(ch)
            current.add_child(child)
            current.height = max(current.height, child.height + 1)
            child.parent = current
        else:
            current_leaf = ParseTreeNode(ch)
            current_leaf.height = 0
            current_leaf.leaf = ch
            current.add_child(current_leaf)
            current.height = max(current.height, current_leaf.height + 1)
    return current



# /**
# # 判断CC节点的兄弟节点是否为S，并抽取相应的并列子句
# **/
def has_sibling_S(node):
    coordinate_clause_list = []
    # 检查节点是否有兄弟节点
    if node.parent is None:
        return coordinate_clause_list
    parent_children = node.parent.children
    for sibling in parent_children:
        if sibling != node and (sibling.value == 'S' or sibling.value == 'SBAR'):
            coordinate_clause_list.append(" ".join(sibling.token_list))
    return coordinate_clause_list


# 定义递归函数向上遍历父节点
def traverse_up(node, count=0):
    # 如果当前节点是根节点，返回遍历次数
    if node.value == 'ROOT':
        return count
    # 否则，继续向上遍历父节点
    else:
        count += 1
        return traverse_up(node.parent, count)

# /**
# 在树中寻找 CC 标签，并检查它们的兄弟节点是否是 S 标签，从而返回并列子句和并列单词
# **/
def find_CC_with_sibling_S(root):
    coordinate_list = []
    cc_words = []
    node_step  = 0
    if root is None:
        return coordinate_list, cc_words
    stack = [root]
    while stack:
        node = stack.pop()
        # if (node.value == 'CC' or node.value == ',') and len(has_sibling_S(node)) > 0:
        if (node.value == 'CC') and len(has_sibling_S(node)) > 0:
            # 将并列子句抽出来
            coordinate_list = has_sibling_S(node)
            node_step = traverse_up(node)
            # 将并列词写出来
            for child in node.children:
                if child.value and child.value not in ['(', ')']:
                    cc_words.append(child.value)
            break
        stack.extend(node.children)
    return coordinate_list, cc_words, node_step



# /**
# 在树中寻找 SBAR 标签，并返回
# **/
def find_SBAR(root):
    node_step  = 0
    if root is None:
        return False, node_step
    stack = [root]
    while stack:
        node = stack.pop()
        if node.value == 'SBAR':
            node_step = traverse_up(node)
            return True, node_step
        stack.extend(node.children)
    return False, node_step






# /**
# # 截取相应的SBAR句子片段
# **/
def extract_SBAR_sentence(node):
    sentences = []
    if node.value == 'SBAR':
        sentences.append(" ".join(node.token_list))
        return sentences
    for child in node.children:
        sentences.extend(extract_SBAR_sentence(child))
    return sentences


# 深度优先搜索函数
# def extract_SBAR_sentence_new(node):
#     # 初始化一个空列表来存储兄弟节点的 token_list
#     sibling_token_lists = []
#     # 如果当前节点是 SBAR 标签
#     if node.value == "SBAR":
#         # 遍历当前节点的父节点的子节点，将兄弟节点的 token_list 收集起来
#         for sibling in node.parent.children:
#             if sibling != node:
#                 sibling_token_lists.append(sibling.token_list)
#         return sibling_token_lists
#     # 递归调用深度优先搜索函数处理当前节点的子节点
#     for child in node.children:
#         sibling_token_lists.extend(extract_SBAR_sentence_new(child))
#     return sibling_token_lists


# 遍历树结构，存储每个节点对应的token_list
def store_tokens_in_tree(root):
    def traverse(node):
        # 遍历当前节点的子节点
        for child in node.children:
            # 递归地遍历子节点
            traverse(child)
            # 将子节点的 token_list 添加到当前节点的 token_list 中
            node.token_list.extend(child.token_list)
        # 如果当前节点有值，则将其添加到 token_list 中
        if node.leaf != "":
            node.token_list.append(node.leaf)

    # 从根节点开始遍历
    traverse(root)



# 定义函数来提取词组
def extract_phrases(srl_list, label):
    phrases = []
    current_phrase = []
    for sentence in srl_list:
        for word, srl_label in sentence:
            if srl_label.startswith('B-' + label):
                if current_phrase:
                    phrases.append(' '.join(current_phrase))
                current_phrase = [word]
            elif srl_label.startswith('I-' + label):
                current_phrase.append(word)
        break
    if current_phrase:
        phrases.append(' '.join(current_phrase))
    return " ".join(phrases)


