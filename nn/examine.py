import torch
import os.path
import math
import pickle
import numpy

print(torch.cuda.is_available())
dataset = []
with open('dataset.pickle', 'rb') as f:
     dataset = pickle.load(f)

device = torch.device('cpu')
if torch.cuda.is_available():
    device =  torch.device('cuda:0')

inputs = []
outputs = []
if torch.cuda.is_available():
    for entry in dataset:
        inputs.append(torch.cuda.FloatTensor(entry["input"], device=device) * 0.6 + 0.3)
        outputs.append(entry["output"])
else:
    for entry in dataset:
        inputs.append(torch.FloatTensor(entry["input"], device=device) * 0.6 + 0.3)
        outputs.append(entry["output"])

#print(outputs[0].size())
#print(outputs)

D_in = list(inputs[0].size())[0]
H1, H2, D_out = round(D_in / 2), round(D_in / 4), len(outputs[0])
print(D_in) # 819
print(H1)  # 410
print(H2) # 205
print(D_out) # 170
HK = round(D_in * H1 / 2)

model = torch.nn.Sequential(
          torch.nn.Linear(D_in, D_in),
          torch.nn.ReLU(),
          torch.nn.ReLU(),
          torch.nn.ReLU(),
          torch.nn.ReLU(),
          torch.nn.Linear(D_in, HK),
          torch.nn.ReLU(),
          torch.nn.Linear(HK, H1),
          torch.nn.ReLU(),
          torch.nn.ReLU(),
          torch.nn.ReLU(),
          torch.nn.ReLU(),
          torch.nn.Linear(H1, H2),
          torch.nn.ReLU(),
          torch.nn.ReLU(),
          torch.nn.ReLU(),
          torch.nn.Linear(H2, H2),
          torch.nn.ReLU(),
          torch.nn.ReLU(),
          torch.nn.ReLU(),
          torch.nn.Linear(H2, D_out),
        ).to(device)

if os.path.isfile('nnsaved.txt'):
    print("Loaded state")
    model.load_state_dict(torch.load('nnsaved.txt'))
    model.eval()

loss_fn = torch.nn.MSELoss()

i = 0
while i < len(inputs):
    print("Checking input: " + str(i))
    result = model(inputs[i])
    print("Computed result")
    local_tensor = result.cpu().detach().numpy()
    match = True
    j = 0
    while (j < D_out):
        output_val = outputs[i][j]
        output_model = local_tensor[j]
        output_model_src = output_model
        if (abs(output_model - 0.3) < abs(output_model - 0.9)):
            output_model = 0
        else:
            output_model = 1
        if (output_val != output_model):
            print("Mismatch in output: ", j, "output_model: ", output_model_src, "output_val: ", output_val)
            match = False
        j = j + 1
    if match:
        print("Matches")
    else:
        print("Mismatches")
    i = i + 1