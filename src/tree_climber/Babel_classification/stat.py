import json
from collections import Counter
from pathlib import Path

# Read all jsonl files from dataset/PrimeVul
dataset_path = Path("dataset/PrimeVul")
cwe_counter = Counter()

for jsonl_file in dataset_path.glob("*.jsonl"):
    with open(jsonl_file, 'r') as f:
        for line in f:
            item = json.loads(line)
            # Find items with target = 1
            if item.get("target") == 1:
                # Count CWE occurrences
                cwes = item.get("cwe", [])
                if isinstance(cwes, list):
                    for cwe in cwes:
                        cwe_counter[cwe] += 1

# Display results
print("CWE counts for target = 1:")
for cwe, count in cwe_counter.most_common():
    print(f"{cwe}: {count}")