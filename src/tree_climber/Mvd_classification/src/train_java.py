import os
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer
from torch.optim import AdamW
from sklearn.metrics import f1_score
from model import MVDModel
from log import setup_logging, get_logger
from tqdm import tqdm

class CodeDataset(Dataset):
    def __init__(self, data, tokenizer, max_len=512):
        self.data = data
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        row = self.data.iloc[idx]
        code = row['code']  # Use abs_code as per your data
        label = row['label']
        encoding = self.tokenizer(
            code,
            truncation=True,
            padding='max_length',
            max_length=self.max_len,
            return_tensors='pt'
        )
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'label': torch.tensor(label, dtype=torch.long)
        }

def train_model(model, train_loader, val_loader, optimizer, criterion, device, logger, epochs=20, save_path='models/baseline_model.pth'):
    model.to(device)
    best_model = None
    best_f1 = 0.0
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        train_bar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs} [Train]")
        for batch in train_bar:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['label'].to(device)
            
            optimizer.zero_grad()
            outputs = model(input_ids, attention_mask)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            train_bar.set_postfix({'loss': f"{loss.item():.4f}"})
        logger.info(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(train_loader):.4f}")
        
        # Validation
        model.eval()
        all_preds, all_labels = [], []
        with torch.no_grad():
            val_bar = tqdm(val_loader, desc=f"Epoch {epoch+1}/{epochs} [Val]")
            for batch in val_bar:
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                labels = batch['label'].to(device)
                outputs = model(input_ids, attention_mask)
                preds = torch.argmax(outputs, dim=1)
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
        
        f1 = f1_score(all_labels, all_preds, average='macro')
        logger.info(f"Validation F1: {f1:.4f}")
        if f1 > best_f1:
            best_f1 = f1
            best_model = model.state_dict()
    
    # Save best model
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    torch.save(best_model, save_path)
    logger.info(f"Best model saved to {save_path}")

def main():
    # Setup logging
    setup_logging(log_file='logs/train_single_py.log')
    logger = get_logger(__name__)
    
    # Device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Using device: {device}")
    
    # Load data
    train_data = pd.read_csv('/drive1/cuongtm/ntat/MVD_Function_Level/dataset/PythonSven/train.csv')
    val_data = pd.read_csv('/drive1/cuongtm/ntat/MVD_Function_Level/dataset/PythonSven/val.csv')
    # Tokenizer and model
    model_name = 'microsoft/codebert-base'  # Adjust if needed
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = MVDModel(model_name, num_labels=2)  # Binary classification: 0 non-vul, 1 vul
    
    # Datasets and loaders
    train_dataset = CodeDataset(train_data, tokenizer)
    val_dataset = CodeDataset(val_data, tokenizer)
    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=16)
    
    # Optimizer and loss
    optimizer = AdamW(model.parameters(), lr=2e-5)
    criterion = nn.CrossEntropyLoss()
    
    # Train
    train_model(model, train_loader, val_loader, optimizer, criterion, device, logger)

if __name__ == "__main__":
    main()