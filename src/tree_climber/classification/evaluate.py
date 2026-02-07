import torch
import torch.nn as nn
from torch_geometric.loader import DataLoader
from sklearn.metrics import classification_report, accuracy_score, precision_score, recall_score, f1_score
from tqdm import tqdm
import os
import logging
from torch_geometric.data import Dataset

from model.model import Net


class CPGDataset(Dataset):
    def __init__(self, data_dir):
        super(CPGDataset, self).__init__()
        self.data_dir = data_dir
        self.file_list = [f for f in os.listdir(data_dir) if f.endswith('.pt')]

    def len(self):
        return len(self.file_list)

    def get(self, idx):
        file_path = os.path.join(self.data_dir, self.file_list[idx])
        data = torch.load(file_path, weights_only=False)
        return data


def evaluate():
   
    BATCH_SIZE = 8
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    MODEL_PATH = "./checkpoint_trvd_nor/best_model.pt"
    TEST_DATA_DIR = "/home/nguyenducduong/hienlt/treeclimber/src/tree_climber/classification/data/torch_data/mapped/test"
    LOG_FILE = "./logs/evaluation_results(trvd_nor).txt"
    
   
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO, 
                        format='%(message)s', filemode='w')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logging.getLogger('').addHandler(console)

    logging.info(f"Evaluation started on device: {DEVICE}")
    logging.info(f"Model path: {MODEL_PATH}")
    logging.info(f"Test data directory: {TEST_DATA_DIR}\n")

    test_dataset = CPGDataset(TEST_DATA_DIR)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)
    
    logging.info(f"Number of test samples: {len(test_dataset)}\n")

    gated_graph_conv_args = {
        "out_channels": 256,
        "num_layers": 6,
        "num_relations": 4  # CFG, DFG, AST, Link
    }
    
    conv_args = {
        "conv1d_1": {"in_channels": 1, "out_channels": 16, "kernel_size": 3, "stride": 1},
        "conv1d_2": {"in_channels": 16, "out_channels": 16, "kernel_size": 1, "stride": 1},
        "maxpool1d_1": {"kernel_size": 3, "stride": 1},
        "maxpool1d_2": {"kernel_size": 1, "stride": 1}
    }

    model = Net(gated_graph_conv_args, conv_args, emb_size=768, device=DEVICE)
    
    # Load trained model
    if not os.path.exists(MODEL_PATH):
        logging.error(f"Model file not found: {MODEL_PATH}")
        return
    
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE, weights_only=True))
    model.eval()
    logging.info("Model loaded successfully\n")

    # Evaluation
    all_preds = []
    all_labels = []
    all_probs = []
    
    criterion = nn.BCELoss()
    test_loss = 0
    
    with torch.no_grad():
        for data in tqdm(test_loader, desc="Evaluating"):
            data = data.to(DEVICE)
            output = model(data)
            
            loss = criterion(output, data.y.float())
            test_loss += loss.item()
            
            probs = output.cpu().numpy()
            preds = (output > 0.5).int().cpu().numpy()
            labels = data.y.cpu().numpy()
            
            all_probs.extend(probs)
            all_preds.extend(preds)
            all_labels.extend(labels)


    acc = accuracy_score(all_labels, all_preds)
    prec = precision_score(all_labels, all_preds, zero_division=0)
    rec = recall_score(all_labels, all_preds, zero_division=0)
    f1 = f1_score(all_labels, all_preds, zero_division=0)
    avg_loss = test_loss / len(test_loader)
    
    
    report = classification_report(all_labels, all_preds, digits=4, 
                                   target_names=['Non-Vulnerable', 'Vulnerable'])

    result_msg = (
        f"{'='*60}\n"
        f"EVALUATION RESULTS\n"
        f"{'='*60}\n\n"
        f"Test Loss: {avg_loss:.4f}\n\n"
        f"{'='*60}\n"
        f"PERFORMANCE METRICS\n"
        f"{'='*60}\n"
        f"Accuracy:  {acc:.4f}\n"
        f"Precision: {prec:.4f}\n"
        f"Recall:    {rec:.4f}\n"
        f"F1-Score:  {f1:.4f}\n\n"
        f"{'='*60}\n"
        f"CLASSIFICATION REPORT\n"
        f"{'='*60}\n"
        f"{report}\n"
        f"{'='*60}\n"
    )
    
    logging.info(result_msg)
    logging.info(f"\nResults saved to: {LOG_FILE}")

    return {
        'accuracy': acc,
        'precision': prec,
        'recall': rec,
        'f1_score': f1,
        'test_loss': avg_loss
    }


if __name__ == "__main__":
    evaluate()
