import os
import json
from pathlib import Path

# Configuration
base_path = Path("/drive1/cuongtm/BABEL/dataset/SARD/JAVA")
cwe_folders = [d for d in base_path.iterdir() if d.is_dir() and d.name.startswith("CWE-")]

for cwe_folder in cwe_folders:
    output_file = cwe_folder / "data.jsonl"
    
    with open(output_file, 'w') as outf:
        # Process bad files
        bad_dir = cwe_folder / "bad"
        if bad_dir.exists():
            for txt_file in bad_dir.glob("*.txt"):
                with open(txt_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    # Cut text at ^^^^^
                    if "^^^^^" in content:
                        content = content.split("^^^^^")[0]
                    
                    content = content[:-2]
                    record = {"func": content.strip(), "target": 0}
                    outf.write(json.dumps(record) + "\n")
        
        # Process good files
        good_dir = cwe_folder / "good"
        if good_dir.exists():
            for txt_file in good_dir.glob("*.txt"):
                with open(txt_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    # Cut text at ^^^^^
                    if "^^^^^" in content:
                        content = content.split("^^^^^")[0]
                    
                    record = {"func": content.strip(), "target": 1}
                    outf.write(json.dumps(record) + "\n")
    
    print(f"Created {output_file}")