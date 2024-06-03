class HieNode:
    def __init__(self, text, height=0):
        self.text = text
        self.children = []
        self.height = height
        self.parent = None
        self.ccWord = []
        self.isMain = False
        self.subType = ""


    def add_child(self, child):
        self.children.append(child)
        child.parent = self