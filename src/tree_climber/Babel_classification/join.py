import json
import random
from pathlib import Path

# File paths
file1 = "/drive1/cuongtm/BABEL/dataset/PrimeVul/valid.jsonl"
file2 = "/drive1/cuongtm/vul_fewshot/data/sven/0802.valid.jsonl"
output_dir = Path("/drive1/cuongtm/BABEL/dataset/PrimeVulBonus")
output_file = output_dir / "valid.jsonl"

# Create output directory
output_dir.mkdir(parents=True, exist_ok=True)

# Read and combine data
data = []
for file_path in [file1, file2]:
    with open(file_path, 'r') as f:
        for line in f:
            data.append(json.loads(line.strip()))

# Shuffle
random.shuffle(data)

# Write to output file
with open(output_file, 'w') as f:
    for item in data:
        f.write(json.dumps(item) + '\n')

print(f"✓ Joined {len(data)} records to {output_file}")