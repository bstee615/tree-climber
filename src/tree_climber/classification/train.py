import torch
import torch.nn as nn
import torch.optim as optim
from torch_geometric.loader import DataLoader
from sklearn.metrics import classification_report, accuracy_score, precision_score, recall_score, f1_score
from tqdm import tqdm
import os
import logging
from torch_geometric.data import Dataset

from model.model import Net
# from full_cpg_embedder import FullCPGEmbedder


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



def train():
    EPOCHS = 10
    BATCH_SIZE = 8
    LEARNING_RATE = 1e-4
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    MODEL_SAVE_PATH = "./checkpoint_primevul/best_model.pt"
    MODEL_SAVE_DIR = "./checkpoint_primevul"
    if not os.path.exists(MODEL_SAVE_DIR):
        os.makedirs(MODEL_SAVE_DIR)
        
    LOG_FILE = "./logs/training_log(primevul).txt"
    TRAIN_DATA_DIR = "/drive1/cuongtm/hienlt/treeclimber/src/tree_climber/classification/data/torch_data/primevul/train"
    VAL_DATA_DIR = "/drive1/cuongtm/hienlt/treeclimber/src/tree_climber/classification/data/torch_data/primevul/val"

    # --- 2. Chuẩn bị Logging ---
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO, 
                        format='%(message)s', filemode='w')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logging.getLogger('').addHandler(console)

    logging.info(f"Training started on device: {DEVICE}")

    
    train_dataset = CPGDataset(TRAIN_DATA_DIR)
    val_dataset = CPGDataset(VAL_DATA_DIR)
    
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)

    gated_graph_conv_args = {
        "out_channels": 256,
        "num_layers": 6,
        "num_relations": 4 
    }
    
    conv_args = {
        "conv1d_1": {"in_channels": 1, "out_channels": 16, "kernel_size": 3, "stride": 1},
        "conv1d_2": {"in_channels": 16, "out_channels": 16, "kernel_size": 1, "stride": 1},
        "maxpool1d_1": {"kernel_size": 3, "stride": 1},
        "maxpool1d_2": {"kernel_size": 1, "stride": 1}
    }

    model = Net(gated_graph_conv_args, conv_args, emb_size=768, device=DEVICE)
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    criterion = nn.BCELoss() # Binary cross entropy loss 

    best_val_f1 = 0.0

    # Train
    for epoch in range(1, EPOCHS + 1):
        model.train()
        train_loss = 0
        
        # Tqdm progression
        pbar = tqdm(train_loader, desc=f"Epoch {epoch}/{EPOCHS} [Train]")
        for data in pbar:
            data = data.to(DEVICE)
            optimizer.zero_grad()
            
            output = model(data)
            
            loss = criterion(output, data.y.float())
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
            pbar.set_postfix({"loss": f"{loss.item():.4f}"})

        # Validation
        model.eval()
        all_preds = []
        all_labels = []
        val_loss = 0
        
        with torch.no_grad():
            for data in tqdm(val_loader, desc=f"Epoch {epoch}/{EPOCHS} [Val]"):
                data = data.to(DEVICE)
                output = model(data)
                
                loss = criterion(output, data.y.float())
                val_loss += loss.item()
                
                preds = (output > 0.5).int().cpu().numpy()
                all_preds.extend(preds)
                all_labels.extend(data.y.cpu().numpy())

        acc = accuracy_score(all_labels, all_preds)
        prec = precision_score(all_labels, all_preds, zero_division=0)
        rec = recall_score(all_labels, all_preds, zero_division=0)
        f1 = f1_score(all_labels, all_preds, zero_division=0)
        report = classification_report(all_labels, all_preds, digits=4)

        log_msg = (f"\n--- Epoch {epoch} Results ---\n"
                   f"Train Loss: {train_loss/len(train_loader):.4f} | Val Loss: {val_loss/len(val_loader):.4f}\n"
                   f"Accuracy: {acc:.4f} | Precision: {prec:.4f} | Recall: {rec:.4f} | F1-Score: {f1:.4f}\n"
                   f"Classification Report:\n{report}\n")
        
        logging.info(log_msg)
        model.save(MODEL_SAVE_DIR + f"/model_{epoch}.pt")
        # Lưu model tốt nhất
        if f1 > best_val_f1:
            best_val_f1 = f1
            model.save(MODEL_SAVE_PATH)
            logging.info(f"--> Best model saved with F1: {f1:.4f}")

    logging.info("Training Complete!")

if __name__ == "__main__":
    train()