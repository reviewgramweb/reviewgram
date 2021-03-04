import torch
import os.path
import math
import pickle

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
        outputs.append(torch.cuda.FloatTensor(entry["output"], device=device) * 0.6 + 0.3)
else:
    for entry in dataset:
        inputs.append(torch.FloatTensor(entry["input"], device=device) * 0.6 + 0.3)
        outputs.append(torch.FloatTensor(entry["output"], device=device) * 0.6 + 0.3)

#print(outputs[0].size())
#print(outputs)

D_in = list(inputs[0].size())[0]
H1, H2, D_out = round(D_in / 2), round(D_in / 4), list(outputs[0].size())[0]
print(D_in)
print(H1)
print(H2)
print(D_out)
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
last_error = 100.0
learning_rate = 1e-3
error_grow_count = 0
current_sample_count = 3745
epochs = 100
for t in range(epochs):
    i = 0
    total  = 0.0
    maxe = 0.0
    while (i < current_sample_count): #len(inputs)
#        print("Working on sample ", i)
        y_pred = model(inputs[i])
        loss = loss_fn(y_pred, outputs[i])
        total = total + loss.item()
        maxe = max(maxe, loss.item())
#        print(t, i, y_pred, outputs[i], loss.item())
        model.zero_grad()
        loss.backward()
        with torch.no_grad():
            for param in model.parameters():
                param.data -= learning_rate * param.grad
        i  = i + 1
    current_avg = total / len(inputs)
    if (current_avg < 0.050):
        if (current_sample_count != len(inputs)):
            current_sample_count = current_sample_count + 1
            print("Increased sample count to ", current_sample_count, "on generation ", t)
    if (current_avg > last_error):
        if (error_grow_count > 3):
            error_grow_count = 0
            learning_rate = learning_rate / 1.5
            if (learning_rate < 1.0e-8):
                learning_rate = learning_rate * 1.78
            print ("Switched learning_rate to ", learning_rate, " on generation ", t)
        else:
            error_grow_count = error_grow_count + 1
    else:
        error_grow_count = 0
    last_error = current_avg
    if (t % 1 == 0):
        print(t, current_avg, maxe)

torch.save(model.state_dict(),"nnsaved.txt")