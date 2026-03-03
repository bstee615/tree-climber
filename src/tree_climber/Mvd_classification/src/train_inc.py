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
import argparse
from tqdm import tqdm

EPOCHS = 10
BATCH_SIZE = 16
LEARNING_RATE = 2e-5
MODEL_NAME = 'microsoft/codebert-base'  # Adjust if needed
TEACHER_SAVE_PATH = './models/baseline_C_Primevul_model.pth'
INCREMENTAL_SAVE_PATH = './models/C_based_incremental_model.pth'
LOG_FILE = './logs/train_C_based_incremental.log'
TRAIN_FILES = ['/drive1/cuongtm/hienlt/mvd/dataset/SVEN/sven_train.csv']
VAL_FILES = ['/drive1/cuongtm/hienlt/mvd/dataset/SVEN/sven_val.csv']
NUMS_LABELS = 3  # Adjust based on your incremental learning setup (e.g., 2 for vul/non-vul, 3 for vul-C/vul-Python/non-vul, etc.)

class CodeDataset(Dataset):
    def __init__(self, data, tokenizer, max_len=512):
        self.data = data
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        row = self.data.iloc[idx]
        code = row['code']
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

def load_data(train_files, val_files):
    """Load and concatenate training and validation data from multiple CSV files."""
    train_data = pd.concat([pd.read_csv(f) for f in train_files])
    val_data = pd.concat([pd.read_csv(f) for f in val_files])
    return train_data, val_data

def create_data_loaders(train_data, val_data, tokenizer, batch_size=BATCH_SIZE):
    """Create DataLoader objects for training and validation."""
    train_dataset = CodeDataset(train_data, tokenizer)
    val_dataset = CodeDataset(val_data, tokenizer)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size)
    return train_loader, val_loader

def load_model(model_name, num_labels, model_path):
    """Load the teacher model from PTH file, and resize classifier if num_labels changed for incremental learning."""
    # First, load baseline model to get old num_labels
    temp_model = MVDModel(model_name, 2)  # Assume baseline is binary (vul/non-vul)
    temp_model.load_state_dict(torch.load(model_path))
    old_num_labels = temp_model.classifier.out_features  # Get actual num_labels from loaded model
    
    if num_labels != old_num_labels:
        logger = get_logger(__name__)
        logger.warning(f"num_labels changed from {old_num_labels} to {num_labels}. Resizing classifier layer for incremental labels (e.g., vul-C, vul-Python).")
        # Create new model with new num_labels
        model = MVDModel(model_name, num_labels)
        # Copy weights for existing labels (0: non-vul, 1: vul)
        model.bert.load_state_dict(temp_model.bert.state_dict())
        with torch.no_grad():
            model.classifier.weight[:old_num_labels] = temp_model.classifier.weight
            model.classifier.bias[:old_num_labels] = temp_model.classifier.bias
        # New neurons (for specific vul types like vul-C, vul-Python) are initialized randomly
    else:
        model = MVDModel(model_name, num_labels)
        model.load_state_dict(torch.load(model_path))
    return model

def setup_optimizer_and_criterion(model, lr=LEARNING_RATE):
    """Setup optimizer and loss criterion."""
    optimizer = AdamW(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()
    return optimizer, criterion

def train_incremental(model, train_loader, val_loader, optimizer, criterion, device, logger, epochs=EPOCHS, save_path=INCREMENTAL_SAVE_PATH):
    """Train the model incrementally."""
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
        logger.info(f"Incremental Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(train_loader):.4f}")
        
        # Validation
        model.eval()
        all_preds, all_labels = [], []
        val_bar = tqdm(val_loader, desc=f"Epoch {epoch+1}/{epochs} [Val]")
        with torch.no_grad():
            for batch in val_bar:
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                labels = batch['label'].to(device)
                outputs = model(input_ids, attention_mask)
                preds = torch.argmax(outputs, dim=1)
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
        
        f1 = f1_score(all_labels, all_preds, average='macro')
        logger.info(f"Incremental Validation F1: {f1:.4f}")
        if f1 > best_f1:
            best_f1 = f1
            best_model = model.state_dict()
    # Save best model
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    torch.save(best_model, save_path)
    logger.info(f"Incremental model saved to {save_path}")

def main():
    parser = argparse.ArgumentParser(description="Incremental Training Script")
    parser.add_argument('--model_path', type=str, default=TEACHER_SAVE_PATH, help='Path to teacher model PTH file')
    parser.add_argument('--train_files', nargs='+', default=TRAIN_FILES, help='List of training CSV files')
    parser.add_argument('--val_files', nargs='+', default=VAL_FILES, help='List of validation CSV files')
    parser.add_argument('--epochs', type=int, default=EPOCHS, help='Number of epochs')
    parser.add_argument('--batch_size', type=int, default=BATCH_SIZE, help='Batch size')
    parser.add_argument('--lr', type=float, default=LEARNING_RATE, help='Learning rate')
    parser.add_argument('--save_path', type=str, default=INCREMENTAL_SAVE_PATH, help='Path to save incremental model')
    parser.add_argument('--log_file', type=str, default=LOG_FILE, help='Log file path')
    parser.add_argument('--model_name', type=str, default=MODEL_NAME, help='Model name')
    parser.add_argument('--num_labels', type=int, default=NUMS_LABELS, help='Number of labels (e.g., 2 for vul/non-vul, 3 for vul-C/vul-Python/non-vul, etc.)')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(log_file=args.log_file)
    logger = get_logger(__name__)
    
    # Device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Using device: {device}")
    
    # Load data
    logger.info(f"Loading training data from: {args.train_files}")
    logger.info(f"Loading validation data from: {args.val_files}")
    train_data, val_data = load_data(args.train_files, args.val_files)
    
    # Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    
    # Data loaders
    train_loader, val_loader = create_data_loaders(train_data, val_data, tokenizer, args.batch_size)
    
    # Load model
    logger.info(f"Loading teacher model from: {args.model_path}")
    model = load_model(args.model_name, args.num_labels, args.model_path)
    
    # Optimizer and criterion
    optimizer, criterion = setup_optimizer_and_criterion(model, args.lr)
    
    # Log parameters
    logger.info(f"Training parameters: epochs={args.epochs}, batch_size={args.batch_size}, lr={args.lr}")
    
    # Train incrementally
    train_incremental(model, train_loader, val_loader, optimizer, criterion, device, logger, args.epochs, args.save_path)

if __name__ == "__main__":
    main()