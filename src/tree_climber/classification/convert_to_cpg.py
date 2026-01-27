from tree_climber.classification.helper_parser import analyze_source_code
from tree_climber.cli.cpg import CPG
import json
import pandas as pd

source_code = """
int simple_sequence() {
    int x = 5;
    x = x + 1;
    x = x * 2;
    return x;
}
"""
CPG_DIR = "/home/nguyenducduong/hienlt/treeclimber/src/tree_climber/classification/data/cpg_data"
TRAIN_PATH = "/home/nguyenducduong/hienlt/treeclimber/src/tree_climber/classification/data/mul_go_train.csv"
VAL_PATH = "/home/nguyenducduong/hienlt/treeclimber/src/tree_climber/classification/data/mul_go_val.csv"
TEST_PATH = "/home/nguyenducduong/hienlt/treeclimber/src/tree_climber/classification/data/mul_go_test.csv"

def main():
    train_dataset = pd.read_csv(TRAIN_PATH)
    val_dataset = pd.read_csv(VAL_PATH)
    test_dataset = pd.read_csv(TEST_PATH)
    
    for index, row in train_dataset.iterrows():
        print(row['code'])
        cpg = analyze_source_code(row['code'], language="go")
        data = cpg.save_json()
        train_dataset.at[index, 'code'] = data
        
    for index, row in val_dataset.iterrows():
        cpg = analyze_source_code(row['code'], language="go")
        data = cpg.save_json()
        val_dataset.at[index, 'code'] = data
    
    for index, row in test_dataset.iterrows():
        cpg = analyze_source_code(row['code'], language="go")
        data = cpg.save_json()
        test_dataset.at[index, 'code'] = data
    
    train_dataset.to_csv(CPG_DIR + "/mul_go_train_cpg.csv", index=False)
    val_dataset.to_csv(CPG_DIR + "/mul_go_val_cpg.csv", index=False)
    test_dataset.to_csv(CPG_DIR + "/mul_go_test_cpg.csv", index=False)
    
    # cpg = analyze_source_code(source_code, language="go")
    # data = cpg.save_json()
    # new_cpg = CPG.load_json(data)
    # with open("output_cpg_new_c.json", "w", encoding="utf-8") as f:
    #     json.dump(new_cpg.to_dict(), f, indent=2)

if __name__ == "__main__":
    main()