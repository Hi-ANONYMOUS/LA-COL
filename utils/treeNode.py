class TreeNode:
    def __init__(self, label, leaf=None):
        self.label = label
        self.leaf = leaf
        self.children = []

def parse_const_tree(linear_tree):
    # ===先转成char
    token = ''
    char_list = []
    for char in linear_tree:
        if char == '(' or char == ')':
            if token:
                char_list.append(token)
                token = ''
            char_list.append(char)
        elif char == ' ':
            if token:
                char_list.append(token)
                token = ''
        else:
            token += char

    if token:
        char_list.append(token)


    stack = []
    root = None
    token = ''
    leaf = ''
    for item in char_list:
        if item == '(':
            if token:
                if root is None:
                    root = TreeNode(token)
                    stack.append(root)
                else:
                    node = TreeNode(token)
                    stack[-1].children.append(node)
                    stack.append(node)
                token = ''
        elif item == ')':
            if token:
                # 在遇到右括号时将 token 作为叶子节点的标签
                stack[-1].children.append(TreeNode('', leaf=token))
                token = ''
            if stack:
                stack.pop()  # 出栈
        else:
            # 在遇到空格字符时将 token 作为当前节点的标签
            token += item

    return root


# 给定的线性化短语句法树
linear_tree = "(ROOT (S (S (NP (PRP I)) (VP (VBP love) (NP (PRP$ my) (NN mom)))) (CC and) (S (NP (PRP she)) (VP (VBZ loves) (NP (PRP me)))) (. .)))"

# 解析成树形结构
root = parse_const_tree(linear_tree)


# 打印树形结构
def print_tree(node, depth=0):
    if node:
        print('  ' * depth + node.label)
        for child in node.children:
            print_tree(child, depth + 1)


print_tree(root)
