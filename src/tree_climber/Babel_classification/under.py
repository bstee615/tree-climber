import json
from collections import Counter
import random

# Read the JSONL file
file_path = '/drive1/cuongtm/vul_fewshot/data/primevul_train.jsonl'

data_list = []
with open(file_path, 'r') as f:
    for line in f:
        data = json.loads(line)
        data_list.append(data)

# Separate by target
target_0 = [d for d in data_list if d['target'] == 0]
target_1 = [d for d in data_list if d['target'] == 1]

# Limit target 0 to 5000
target_0 = target_0[:5000]

# Combine and shuffle
combined = target_0 + target_1
random.shuffle(combined)

# Export to file
output_path = 'dataset/primevul_under.jsonl'
with open(output_path, 'w') as f:
    for data in combined:
        f.write(json.dumps(data) + '\n')

print(f"Total records: {len(combined)}")
print(f"Target 0: {len(target_0)}")
print(f"Target 1: {len(target_1)}")