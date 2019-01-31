import json

fname1 = 'config_old.json'
fname2 = 'config_new.json'

with open(fname1) as fin :
    c1 = json.loads(fin.read())['parameters']

with open(fname2) as fin :
    c2 = json.loads(fin.read())['parameters']



print("SEARCHING FOR PARAMETER NAMES...")
print("In {} but not {}".format(fname1, fname2))
for item in c1 :
    if item not in c2:
        print(item)

print("In {} but not {}".format(fname2, fname1))
for item in c2 :
    if item not in c1:
        print(item)

print("SEARCHING FOR PARAMETER VALUE DIFFERENCES...")
for item in c1:
    if item in c2:
        if c1[item] != c2[item]:
            print(item)
            print(fname1, c1[item])
            print(fname2, c2[item])
            print()