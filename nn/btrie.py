import pickle
#import random

dataset = []
with open('dataset.pickle', 'rb') as f:
     dataset = pickle.load(f)
     
     
class BTrieNode:
    def __init__(self):
        self.node0 = None
        self.node1 = None
        
        

class BTrie:
    def __init__(self):
        self.head = BTrieNode()
        self.max_length = 0
        
    def add(self, inputs):
        cur = self.head
        i = 0
        for inputentry in inputs:
            if inputentry == 0:
                if cur.node0 is None:
                    cur.node0 = BTrieNode()
                cur = cur.node0
            else:
                if cur.node1 is None:
                    cur.node1 = BTrieNode()
                cur = cur.node1
            i = i + 1
        self.max_length = max(self.max_length, i)

    def max_length(self):
        return self.max_length
        
    def count_mismatches(self,inputs):
        assert len(inputs) == self.max_length
        cur = self.head
        mismatches = 0
        for inputentry in inputs:
            if inputentry == 0:
                if cur.node0 is None:
                    mismatches = mismatches + 1
                    cur = cur.node1
                else:
                    cur = cur.node0
            else:
                if cur.node1 is None:
                    mismatches = mismatches + 1
                    cur = cur.node0
                else:
                    cur = cur.node1
        return mismatches

bTrie = BTrie()
for entry in dataset:
    bTrie.add(entry["input"])
    
#random.seed()
#inp = [0] * len(dataset[0]["input"])
#i = 0
#while i < len(inp):
#    inp[i] = random.choice([0, 1])
#    i = i + 1
#
#
#print(bTrie.count_mismatches(inp))