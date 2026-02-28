import json
import os
from pathlib import Path

# Configuration
input_file = "/drive1/cuongtm/BABEL/dataset/primevul_under.jsonl"
output_dir = "/drive1/cuongtm/BABEL/dataset/PrimeVul"
split_ratio = (0.8, 0.1, 0.1)  # train:valid:test = 9:1:1

# Create output directory
Path(output_dir).mkdir(parents=True, exist_ok=True)

# Read data
data = []
with open(input_file, 'r') as f:
    for line in f:
        data.append(json.loads(line))

# Calculate split indices
total = len(data)
train_idx = int(total * split_ratio[0])
valid_idx = int(total * (split_ratio[0] + split_ratio[1]))

train_data = data[:train_idx]
valid_data = data[train_idx:valid_idx]
test_data = data[valid_idx:]

# Write splits
splits = {
    'train': train_data,
    'valid': valid_data,
    'test': test_data
}

for split_name, split_data in splits.items():
    output_file = os.path.join(output_dir, f"{split_name}.jsonl")
    with open(output_file, 'w') as f:
        for item in split_data:
            f.write(json.dumps(item) + '\n')
    print(f"{split_name}: {len(split_data)} samples → {output_file}")