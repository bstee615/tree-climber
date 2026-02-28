import json
from collections import defaultdict

def analyze_repos_vul(file_path):
    """
    Analyze ReposVul.jsonl dataset and count functions by target label grouped by cve_language.
    
    Args:
        file_path: Path to ReposVul.jsonl file
    
    Returns:
        Dictionary with statistics grouped by language
    """
    stats = defaultdict(lambda: {"target_-1": 0, "target_0": 0, "target_1": 0, "total_functions": 0})
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    record = json.loads(line)
                    language = record.get('cve_language', 'Unknown')
                    details = record.get('details', [])[0].get('function_before', [])
                    details += record.get('details', [])[0].get('function_after', [])
                    
                    # Count functions from details array
                    num_functions = len(details)

                    # print(f"Processing record: language={language}, target={target}, num_functions={num_functions}")
                    
                    # Update stats
                    for funcData in details:
                        target = funcData.get('target', -1)
                        if target == -1:
                            stats[language]["target_-1"] += 1
                        elif target == 0:
                            stats[language]["target_0"] += 1
                        elif target == 1:
                            stats[language]["target_1"] += 1
                    
                    stats[language]["total_functions"] += num_functions
                    
                except json.JSONDecodeError:
                    print(f"Error decoding JSON line")
                    continue
    
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return {}
    
    return stats

def print_statistics(stats):
    """Pretty print the analysis results"""
    print("\n" + "="*70)
    print("ReposVul Dataset Analysis by CVE Language")
    print("="*70)
    
    for language in sorted(stats.keys()):
        data = stats[language]
        print(f"\n{language}:")
        print(f"  Functions with target -1: {data['target_-1']}")
        print(f"  Functions with target  0: {data['target_0']}")
        print(f"  Functions with target  1: {data['target_1']}")
        print(f"  Total functions: {data['total_functions']}")

if __name__ == "__main__":
    # Analyze the dataset
    results = analyze_repos_vul('/drive1/cuongtm/BABEL/dataset/ReposVul.jsonl')
    print_statistics(results)