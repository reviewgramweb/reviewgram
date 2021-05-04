import pickle
     
     
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

    def get_max_length(self):
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


bTrie = None

def get_dataset_trie():
	global bTrie
	if bTrie is None:
		dataset = []
		with open('/root/reviewgram/dataset.pickle', 'rb') as f:
			 dataset = pickle.load(f)
		assert len(dataset) != 0
		bTrie = BTrie()
		for entry in dataset:
			bTrie.add(entry["input"])
	return bTrie