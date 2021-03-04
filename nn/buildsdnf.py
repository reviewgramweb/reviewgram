import math
import pickle

dataset = []
with open('dataset.pickle', 'rb') as f:
     dataset = pickle.load(f)
     
countinput = len(dataset[0]["input"])
countoutput = len(dataset[0]["output"])
#print(countinput)
registers = {}
registercount = 0
lines = []
outputdefs = []
lines.append("def compute_model(input):")
lines.append("\ta = [e != 0 for e in input]")

for entry in dataset:
    entry["hashval"] = "".join(str(inp) for inp in entry["input"])



i = 0
while i < countoutput:
    defs = []
    for entry in dataset:
        if entry["output"][i] != 0:
            if entry["hashval"] in registers:
                defs.append("r" + str(registers[entry["hashval"]]["index"]))
            else:
                inpands = ""
                j = 0
                while (j < countinput):
                    v = "a[" + str(j) + "]"
                    if (entry["input"][j] == 0):
                        v = "(not " + v + ")"
                    if len(inpands) == 0:
                        inpands = v
                    else:
                        inpands += " and "
                        inpands += v
                    j = j + 1
                registers[entry["hashval"]] = {"index" : registercount, "definition": inpands}
                defs.append("r" + str(registercount))
                registercount = registercount + 1
    if (len(defs) == 0):
        outputdefs.append("\to[" + str(i) + "] = False")
    else:
        outputdefs.append("\to[" + str(i) + "] = " + " or ".join(defs))
    i = i + 1

for item in registers.keys():
    val = registers[item]
    lines.append("\tr" + str(val["index"]) + " = " + val["definition"])

lines.append("\to = [0] * " + str(countoutput))
for outputdef in outputdefs:
    lines.append(outputdef)

lines.append("\treturn [(1 if k else 0) for k in o]")
for line in lines:
    print(line)