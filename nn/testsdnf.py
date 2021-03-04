import pickle
from code import compute_model

dataset = []
with open('dataset.pickle', 'rb') as f:
     dataset = pickle.load(f)

i = 0
while i < len(dataset):
    j = i + 1
    while j < len(dataset):
        if ((dataset[i]["input"] == dataset[j]["input"]) and (dataset[i]["output"] != dataset[j]["output"])):
            print("Found duplicate: ", i, " and ", j)
            print(dataset[i])
            print(dataset[j])
        j = j + 1
    i = i + 1
    
i = 0
for entry in dataset:
    expected_output = entry["output"]
    out = compute_model(entry["input"])
    j = 0
    while j < len(out):
        if (expected_output[j] != out[j]):
            print("Found mismatch in output ", j, ", expected: ", expected_output[j], ", out:", out[j])
        j = j + 1
    if out == expected_output:
        print(i, ": matches")
    else:
        print(i, ": error")
    i = i + 1