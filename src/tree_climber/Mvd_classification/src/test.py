import os
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer
from sklearn.metrics import f1_score, classification_report, accuracy_score, precision_score, recall_score
from model import MVDModel
from log import setup_logging, get_logger
import argparse

BATCH_SIZE = 16
MODEL_NAME = 'microsoft/codebert-base'  # Adjust if needed
LOG_FILE = './logs/c_based_sven_test.log'
PREDICTIONS_FILE = 'c_based_sven__test_predictions.csv'
SAVE_PATH = './models/C_based_incremental_model.pth'
TEST_FILES = ['/drive1/cuongtm/hienlt/mvd/dataset/SVEN/sven_test.csv']  # List of test CSV files (for different languages)
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
        language = row['language']
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
            'label': torch.tensor(label, dtype=torch.long),
            'code': code,
            'language': language
        }

def load_test_data(test_files):
    """Load and concatenate test data from multiple CSV files, adding language column."""
    data_list = []
    for f in test_files:
        df = pd.read_csv(f)
        lang = os.path.basename(os.path.dirname(f))  # Infer language from folder name
        df['language'] = lang
        data_list.append(df)
    test_data = pd.concat(data_list, ignore_index=True)
    return test_data

def create_test_loader(test_data, tokenizer, batch_size=BATCH_SIZE):
    """Create DataLoader for test data."""
    test_dataset = CodeDataset(test_data, tokenizer)
    test_loader = DataLoader(test_dataset, batch_size=batch_size)
    return test_loader

def load_model_for_test(model_name, num_labels, model_path):
    """Load the model for testing."""
    model = MVDModel(model_name, num_labels)
    model.load_state_dict(torch.load(model_path))
    return model

def test_model(model, test_loader, device, logger):
    model.to(device)
    model.eval()
    all_preds, all_labels, all_codes, all_languages = [], [], [], []
    with torch.no_grad():
        for batch in test_loader:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['label'].to(device)
            codes = batch['code']
            languages = batch['language']
            outputs = model(input_ids, attention_mask)
            preds = torch.argmax(outputs, dim=1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            all_codes.extend(codes)
            all_languages.extend(languages)
    
    f1 = f1_score(all_labels, all_preds, average='macro')
    accuracy = accuracy_score(all_labels, all_preds)
    precision = precision_score(all_labels, all_preds, average='macro')
    recall = recall_score(all_labels, all_preds, average='macro')
    logger.info(f"Test F1 Score: {f1:.4f}")
    logger.info(f"Test Accuracy: {accuracy:.4f}")
    logger.info(f"Test Precision: {precision:.4f}")
    logger.info(f"Test Recall: {recall:.4f}")
    logger.info("Classification Report:\n" + classification_report(all_labels, all_preds))
    return f1, all_preds, all_labels, all_codes, all_languages

def main():
    parser = argparse.ArgumentParser(description="Test Script for Multi-Language Vulnerability Detection")
    parser.add_argument('--model_path', type=str, default=SAVE_PATH, help='Path to model PTH file (baseline or incremental)')
    parser.add_argument('--model_name', type=str, default=MODEL_NAME, help='Model name')
    parser.add_argument('--save_predictions', action='store_true', default=True, help='Whether to save predictions to CSV')
    parser.add_argument('--test_files', nargs='+', default=TEST_FILES, help='List of test CSV files (for different languages)')
    parser.add_argument('--batch_size', type=int, default=BATCH_SIZE, help='Batch size')
    parser.add_argument('--log_file', type=str, default=LOG_FILE, help='Log file path')
    parser.add_argument('--num_labels', type=int, default=NUMS_LABELS, help='Number of labels (e.g., 2 for vul/non-vul, 3 for vul-C/vul-Python/non-vul, etc.)')
    parser.add_argument('--results_file', type=str, default=PREDICTIONS_FILE, help='Name of the CSV file to save predictions')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(log_file=args.log_file)
    logger = get_logger(__name__)
    
    # Device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Using device: {device}")
    
    # Load model
    logger.info(f"Loading model from: {args.model_path}")
    model = load_model_for_test(args.model_name, args.num_labels, args.model_path)
    logger.info("Model loaded")
    
    # Load test data
    logger.info(f"Loading test data from: {args.test_files}")
    test_data = load_test_data(args.test_files)
    
    # Tokenizer and loader
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    test_loader = create_test_loader(test_data, tokenizer, args.batch_size)
    
    # Test
    logger.info("Test by model: " + args.model_path)
    logger.info("Data set: " + ', '.join(args.test_files))
    logger.info("Test size: " + str(len(test_data)))
    logger.info("Starting testing...")
    f1, preds, labels, codes, languages = test_model(model, test_loader, device, logger)
    
    # Save predictions if requested
    if args.save_predictions:
        results_dir = './results'
        os.makedirs(results_dir, exist_ok=True)
        predictions_df = pd.DataFrame({
            'code': codes,
            'true_label': labels,
            'pred_label': preds,
            'language': languages
        })
        predictions_path = os.path.join(results_dir, args.results_file)
        predictions_df.to_csv(predictions_path, index=False)
        logger.info(f"Predictions saved to {predictions_path}")

if __name__ == "__main__":
    main()