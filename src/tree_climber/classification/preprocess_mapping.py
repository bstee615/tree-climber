import pandas as pd
import torch
import json
import os
from tqdm import tqdm
from embedder import FullCPGEmbedder 

def preprocess_and_save(csv_path, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    embedder = FullCPGEmbedder()
    
    df = pd.read_csv(csv_path)
    
    processed_files = []

    print(f"Starting embedding for {len(df)} samples...")
    for index, row in tqdm(df.iterrows(), total=len(df)):
        try:
            
            cpg_json = json.loads(row['code'])
            
            pyg_data = embedder.transform(cpg_json)
            
            # Attach respective label (convert to tensor long)
            pyg_data.y = torch.tensor([row['label']], dtype=torch.long)
            
            # save data
            file_name = f"go_data_{index}.pt"
            file_path = os.path.join(output_dir, file_name)
            torch.save(pyg_data, file_path)
            
            processed_files.append(file_path)
            
        except Exception as e:
            print(f"Error at index {index}: {e}")

    print(f"Finished! Saved {len(processed_files)} files to {output_dir}")

if __name__ == "__main__":
    TRAIN_PATH = "/home/nguyenducduong/hienlt/treeclimber/src/tree_climber/classification/data/cpg_data_mapped/mul_go_train_cpg.csv"
    VAL_PATH = "/home/nguyenducduong/hienlt/treeclimber/src/tree_climber/classification/data/cpg_data_mapped/mul_go_val_cpg.csv"
    TEST_PATH = "/home/nguyenducduong/hienlt/treeclimber/src/tree_climber/classification/data/cpg_data_mapped/mul_go_test_cpg.csv"
    TRAIN_TORCH_DIR = "/home/nguyenducduong/hienlt/treeclimber/src/tree_climber/classification/data/torch_data/mapped/train"
    VAL_TORCH_DIR = "/home/nguyenducduong/hienlt/treeclimber/src/tree_climber/classification/data/torch_data/mapped/val"
    TEST_TORCH_DIR = "/home/nguyenducduong/hienlt/treeclimber/src/tree_climber/classification/data/torch_data/mapped/test"
    preprocess_and_save(TRAIN_PATH, TRAIN_TORCH_DIR)
    preprocess_and_save(VAL_PATH, VAL_TORCH_DIR)
    preprocess_and_save(TEST_PATH, TEST_TORCH_DIR)