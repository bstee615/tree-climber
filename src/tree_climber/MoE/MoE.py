import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import random
import json
import numpy as np
from transformers import AutoTokenizer, AutoModel
import copy
import logging
from pathlib import Path
from datetime import datetime
from collections import Counter
from sklearn.model_selection import train_test_split

# =====================================================================
# LOGGING SETUP - Write to both file and console
# =====================================================================
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# Also capture print statements
class PrintLogger:
    def __init__(self, log_func):
        self.log_func = log_func
    
    def write(self, message):
        if message.strip():
            self.log_func(message.strip())
    
    def flush(self):
        pass

# Redirect print to logging
original_print = print
def print(*args, **kwargs):
    message = ' '.join(str(arg) for arg in args)
    original_print(*args, **kwargs)  # Also print to console
    log.info(message)

# =====================================================================
# THÀNH PHẦN 1: MẠNG CHUYÊN GIA (EXPERT NETWORKS) - IMPROVED
# =====================================================================
class CWE_Expert(nn.Module):
    def __init__(self, input_dim, hidden_dim, dropout_rate=0.1):
        super(CWE_Expert, self).__init__()
        self.net = nn.Sequential(
            nn.LayerNorm(input_dim),
            nn.Linear(input_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout_rate),
            nn.LayerNorm(hidden_dim),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Dropout(dropout_rate),
            nn.LayerNorm(hidden_dim // 2),
            nn.Linear(hidden_dim // 2, 1)
        )
        self._init_weights()

    def _init_weights(self):
        for m in self.net:
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, nonlinearity='relu')
                nn.init.zeros_(m.bias)

    def forward(self, x):
        return self.net(x)

# =====================================================================
# THÀNH PHẦN 2: BỘ ĐỊNH TUYẾN ĐA NHIỆM (GATING NETWORK / ROUTER) - IMPROVED
# =====================================================================
class TopKRouter(nn.Module):
    def __init__(self, input_dim, num_experts, top_k=1):
        super(TopKRouter, self).__init__()
        self.num_experts = num_experts
        self.top_k = min(top_k, num_experts)
        self.norm = nn.LayerNorm(input_dim)
        self.routing_layer = nn.Linear(input_dim, num_experts)
        nn.init.kaiming_normal_(self.routing_layer.weight, nonlinearity='relu')
        nn.init.zeros_(self.routing_layer.bias)

    def forward(self, x):
        x_norm = self.norm(x)
        logits = self.routing_layer(x_norm)
        top_k_logits, top_k_indices = torch.topk(logits, self.top_k, dim=-1)
        top_k_weights = F.softmax(top_k_logits, dim=-1)
        sparse_weights = torch.zeros_like(logits).scatter(-1, top_k_indices, top_k_weights)
        return sparse_weights, top_k_indices, logits

# =====================================================================
# THÀNH PHẦN 3: KIẾN TRÚC TỔNG THỂ MOE-VD KẾT HỢP - IMPROVED WITH FINE-TUNING
# =====================================================================
class MoE_VulnerabilityDetector(nn.Module):
    def __init__(self, input_dim=768, hidden_dim=256, num_experts=4, top_k=1, dropout_rate=0.1, 
                 encoder_name="microsoft/codebert-base", freeze_encoder=False):
        super(MoE_VulnerabilityDetector, self).__init__()
        self.num_experts = num_experts
        
        # Add CodeBERT encoder to the model (like baseline)
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(encoder_name)
            self.encoder = AutoModel.from_pretrained(encoder_name)
            if freeze_encoder:
                for param in self.encoder.parameters():
                    param.requires_grad = False
            print(f"CodeBERT encoder loaded: {encoder_name} (freeze={freeze_encoder})")
        except Exception as e:
            print(f"Warning: Could not load CodeBERT: {e}")
            self.encoder = None
            self.tokenizer = None
        
        self.input_norm = nn.LayerNorm(input_dim)
        self.router = TopKRouter(input_dim, num_experts, top_k)
        self.experts = nn.ModuleList([CWE_Expert(input_dim, hidden_dim, dropout_rate) for _ in range(num_experts)])

    def encode_code(self, code_strings, device):
        """Encode code strings to embeddings using CodeBERT (on-the-fly, trainable)"""
        if self.encoder is None:
            raise ValueError("Encoder not loaded")
        
        inputs = self.tokenizer(
            code_strings,
            return_tensors="pt",
            max_length=512,
            truncation=True,
            padding=True
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        outputs = self.encoder(**inputs)
        # Mean pooling with attention mask
        hidden_states = outputs.last_hidden_state
        attention_mask = inputs['attention_mask'].unsqueeze(-1)
        masked_hidden = hidden_states * attention_mask
        sum_hidden = masked_hidden.sum(dim=1)
        sum_mask = attention_mask.sum(dim=1)
        embeddings = sum_hidden / sum_mask
        
        return embeddings

    def forward(self, x):
        x_orig = x
        x = self.input_norm(x)
        
        routing_weights, top_k_indices, router_logits = self.router(x)
        batch_size = x.size(0)
        final_output = torch.zeros(batch_size, 1, device=x.device, dtype=x.dtype)

        routing_probs = F.softmax(router_logits, dim=-1)
        fraction_routed = routing_weights.gt(0).float().mean(dim=0)
        prob_per_expert = routing_probs.mean(dim=0)

        # Vectorized expert processing
        for i, expert in enumerate(self.experts):
            expert_mask = (routing_weights[:, i] > 0)
            if expert_mask.any():
                expert_inputs = x[expert_mask]
                weights = routing_weights[expert_mask, i].unsqueeze(1)
                expert_outputs = expert(expert_inputs)
                final_output[expert_mask] += expert_outputs * weights

        return final_output, fraction_routed, prob_per_expert, router_logits

# =====================================================================
# THÀNH PHẦN 4: HÀM MẤT MÁT ĐA NHIỆM VÀ ĐÁNH GIÁ (LOSS & METRICS) - IMPROVED
# =====================================================================
def focal_loss(logits, targets, alpha=0.25, gamma=2.0, label_smoothing=0.0, pos_weight=None):
    """Focal Loss with label smoothing and class weighting for handling class imbalance"""
    # Apply label smoothing
    if label_smoothing > 0:
        targets = targets * (1 - label_smoothing) + 0.5 * label_smoothing
    
    # Apply class weighting if provided
    if pos_weight is not None:
        bce_loss = F.binary_cross_entropy_with_logits(logits, targets, reduction='none', pos_weight=pos_weight)
    else:
        bce_loss = F.binary_cross_entropy_with_logits(logits, targets, reduction='none')
    
    probs = torch.sigmoid(logits)
    pt = targets * probs + (1 - targets) * (1 - probs)
    focal_weight = (1 - pt) ** gamma
    loss = focal_weight * bce_loss
    return loss.mean()

def moe_multitask_loss(binary_logits, binary_targets, router_logits, cwe_labels,
                       fraction_routed, prob_per_expert, num_experts, 
                       pos_weight=None, use_focal=True, label_smoothing=0.05, alpha=0.005, beta=0.2):
    """Improved loss function with class weighting, focal loss, and label smoothing
    
    Changes from baseline to match performance:
    - Reduced label_smoothing: 0.1 -> 0.05 (less aggressive)
    - Reduced alpha (aux loss weight): 0.01 -> 0.005 (focus more on main task)
    - Reduced beta (CWE loss weight): 0.3 -> 0.2 (focus more on binary classification)
    - Pass pos_weight to focal_loss for class balance
    """
    if use_focal:
        # Pass pos_weight to focal loss for better class balance (like baseline)
        bce_loss = focal_loss(binary_logits, binary_targets, alpha=0.25, gamma=2.0, 
                             label_smoothing=label_smoothing, pos_weight=pos_weight)
    else:
        if pos_weight is not None:
            bce_loss = F.binary_cross_entropy_with_logits(binary_logits, binary_targets, pos_weight=pos_weight)
        else:
            bce_loss = F.binary_cross_entropy_with_logits(binary_logits, binary_targets)
    
    # Less aggressive label smoothing for CWE classification
    ce_loss_cwe = F.cross_entropy(router_logits, cwe_labels, label_smoothing=0.02)
    
    # Load balancing auxiliary loss (reduced weight)
    aux_loss = num_experts * torch.sum(fraction_routed * prob_per_expert)
    
    total_loss = bce_loss + beta * ce_loss_cwe + alpha * aux_loss
    return total_loss, bce_loss, ce_loss_cwe, aux_loss

def calculate_accuracy(logits, targets, threshold=0.5):
    probs = torch.sigmoid(logits)
    preds = (probs > threshold).float()
    correct = (preds == targets).float().sum()
    return correct / targets.numel()

def calculate_f1_score(preds, targets):
    """Calculate F1 score"""
    tp = ((preds == 1) & (targets == 1)).sum()
    fp = ((preds == 1) & (targets == 0)).sum()
    fn = ((preds == 0) & (targets == 1)).sum()
    
    precision = tp / (tp + fp + 1e-8)
    recall = tp / (tp + fn + 1e-8)
    f1 = 2 * precision * recall / (precision + recall + 1e-8)
    
    return f1.item(), precision.item(), recall.item()

def find_optimal_threshold(model, data_loader, device):
    """Find optimal classification threshold using F1 score on validation set"""
    model.eval()
    all_probs = []
    all_targets = []
    
    with torch.no_grad():
        for code_batch, vuln, cwe in data_loader:
            emb = model.encode_code(code_batch, device)
            logits, _, _, _ = model(emb)
            probs = torch.sigmoid(logits)
            all_probs.extend(probs.cpu().numpy())
            all_targets.extend(vuln.numpy())
    
    all_probs = np.array(all_probs).flatten()
    all_targets = np.array(all_targets).flatten()
    
    # Debug: Print probability distribution
    print(f"\nProbability distribution:")
    print(f"  Min: {all_probs.min():.4f}, Max: {all_probs.max():.4f}")
    print(f"  Mean: {all_probs.mean():.4f}, Std: {all_probs.std():.4f}")
    print(f"  Median: {np.median(all_probs):.4f}")
    print(f"  Q1: {np.percentile(all_probs, 25):.4f}, Q3: {np.percentile(all_probs, 75):.4f}")
    
    best_threshold = 0.5
    best_f1 = 0.0
    best_metrics = {}
    
    # Search with finer granularity
    thresholds_to_try = np.arange(0.05, 0.95, 0.02)
    
    print(f"\nSearching optimal threshold...")
    for threshold in thresholds_to_try:
        preds = (all_probs > threshold).astype(float)
        preds_tensor = torch.tensor(preds)
        targets_tensor = torch.tensor(all_targets)
        
        f1, precision, recall = calculate_f1_score(preds_tensor, targets_tensor)
        acc = (preds == all_targets).mean()
        
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = threshold
            best_metrics = {
                'f1': f1,
                'precision': precision,
                'recall': recall,
                'accuracy': acc
            }
    
    print(f"\nBest threshold search results:")
    print(f"  Threshold: {best_threshold:.3f}")
    print(f"  F1 Score: {best_metrics['f1']:.4f}")
    print(f"  Precision: {best_metrics['precision']:.4f}")
    print(f"  Recall: {best_metrics['recall']:.4f}")
    print(f"  Accuracy: {best_metrics['accuracy']:.4f}")
    
    return best_threshold, best_metrics

def get_num_classes_cwe(data_list):
    """Get number of CWE classes needed based on max CWE index in the data"""
    cwe_ids = set()
    for item in data_list:
        if 'cwe' in item:
            if isinstance(item['cwe'], list):
                cwe_ids.update(item['cwe'])
            else:
                cwe_ids.add(item['cwe'])
    
    if not cwe_ids:
        return 0, []
    
    # For CrossEntropy, we need num_classes = max_index + 1
    max_cwe_index = max(cwe_ids)
    min_cwe_index = min(cwe_ids)
    num_classes = max_cwe_index + 1
    
    print(f"Unique CWE indices found: {len(cwe_ids)}")
    print(f"CWE index range: [{min_cwe_index}, {max_cwe_index}]")
    print(f"Number of CWE classes (max+1): {num_classes}")
    
    return num_classes, sorted(list(cwe_ids))

def build_auto_cwe_clusters(data_list, target_experts=None, min_experts=8, max_experts=32, min_samples_threshold=20):
    """Automatically cluster CWE IDs into fewer balanced groups for router training.
    
    Args:
        data_list: full dataset containing CWE labels
        target_experts: target number of clusters (None = sqrt(num_unique))
        min_experts: minimum number of clusters to maintain
        max_experts: maximum number of clusters
        min_samples_threshold: CWEs with freq <= this are grouped into "rare" cluster
    """
    cwe_values = [int(item['cwe']) for item in data_list if 'cwe' in item]
    if not cwe_values:
        raise ValueError("No CWE values found for auto clustering")

    cwe_counter = Counter(cwe_values)
    unique_cwes = sorted(cwe_counter.keys())
    num_unique = len(unique_cwes)

    # Separate rare and frequent CWEs
    rare_cwes = {cwe_id: freq for cwe_id, freq in cwe_counter.items() if freq <= min_samples_threshold}
    frequent_cwes = {cwe_id: freq for cwe_id, freq in cwe_counter.items() if freq > min_samples_threshold}
    
    num_rare = len(rare_cwes)
    num_frequent = len(frequent_cwes)
    
    print("\nAuto CWE clustering enabled")
    print(f"  Unique CWE classes: {num_unique}")
    print(f"  CWEs with > {min_samples_threshold} samples: {num_frequent}")
    print(f"  CWEs with <= {min_samples_threshold} samples (will be merged): {num_rare}")
    
    # Determine target experts for frequent CWEs only
    if target_experts is None:
        # Scale experts by sqrt of frequent classes (not rare)
        target_experts = max(1, int(round(np.sqrt(num_frequent))))
    
    # Reserve 1 cluster for "rare" CWEs if there are any
    num_experts = max(1, min(int(target_experts), num_frequent))
    num_experts = max(min_experts, num_experts) if num_frequent >= min_experts else num_experts
    num_experts = min(max_experts, num_experts)
    num_experts = min(num_experts, num_frequent) if num_frequent > 0 else 1
    
    if num_rare > 0:
        num_experts += 1  # Add 1 for rare cluster
    
    # Assign frequent CWEs to clusters with load balancing
    cluster_loads = [0 for _ in range(num_experts)]
    cwe_to_cluster = {}
    
    sorted_by_freq = sorted(frequent_cwes.items(), key=lambda x: x[1], reverse=True)
    rare_cluster_idx = num_experts - 1 if num_rare > 0 else -1
    
    # Assign frequent CWEs first
    for cwe_id, freq in sorted_by_freq:
        # Find cluster with minimum load (excluding rare cluster)
        best_cluster = min(
            range(num_experts - (1 if num_rare > 0 else 0)),
            key=lambda idx: cluster_loads[idx]
        )
        cwe_to_cluster[cwe_id] = best_cluster
        cluster_loads[best_cluster] += freq
    
    # Assign all rare CWEs to rare cluster
    rare_cluster_total = 0
    for cwe_id, freq in rare_cwes.items():
        cwe_to_cluster[cwe_id] = rare_cluster_idx
        rare_cluster_total += freq
    
    if num_rare > 0:
        cluster_loads[rare_cluster_idx] = rare_cluster_total
    
    print(f"  Router experts/clusters: {num_experts}")
    print(f"  Cluster loads (samples): {cluster_loads}")
    if num_rare > 0:
        print(f"  Rare cluster (idx {rare_cluster_idx}): {num_rare} CWE types, {rare_cluster_total} samples")

    return num_experts, cwe_to_cluster, cwe_counter, cluster_loads

def calculate_class_weights(data_list):
    """Calculate class weights for imbalanced data"""
    vuln_count = sum(1 for item in data_list if item['vuln'] == 1)
    safe_count = len(data_list) - vuln_count
    
    if vuln_count == 0 or safe_count == 0:
        return None
    
    # Weight for positive class (vulnerable)
    pos_weight = safe_count / vuln_count
    print(f"Class distribution - Vulnerable: {vuln_count}, Safe: {safe_count}")
    print(f"Positive class weight: {pos_weight:.2f}")
    
    return torch.tensor([pos_weight])

def evaluate_by_cwe(model, data_loader, device, threshold=0.5):
    """Evaluate model performance grouped by CWE ID with detailed metrics"""
    model.eval()
    cwe_metrics = {}
    
    with torch.no_grad():
        for code_batch, vuln, cwe in data_loader:
            emb = model.encode_code(code_batch, device)
            vuln, cwe = vuln.to(device), cwe.to(device)
            logits, _, _, _ = model(emb)
            
            probs = torch.sigmoid(logits)
            preds = (probs > threshold).float()
            
            for i in range(len(cwe)):
                cwe_id = cwe[i].item()
                if cwe_id not in cwe_metrics:
                    cwe_metrics[cwe_id] = {
                        "tp": 0, "fp": 0, "tn": 0, "fn": 0, "total": 0
                    }
                
                pred = preds[i].item()
                target = vuln[i].item()
                
                if pred == 1 and target == 1:
                    cwe_metrics[cwe_id]["tp"] += 1
                elif pred == 1 and target == 0:
                    cwe_metrics[cwe_id]["fp"] += 1
                elif pred == 0 and target == 0:
                    cwe_metrics[cwe_id]["tn"] += 1
                else:
                    cwe_metrics[cwe_id]["fn"] += 1
                
                cwe_metrics[cwe_id]["total"] += 1
    
    # Calculate metrics
    for cwe_id in cwe_metrics:
        m = cwe_metrics[cwe_id]
        m["accuracy"] = (m["tp"] + m["tn"]) / m["total"] if m["total"] > 0 else 0
        m["precision"] = m["tp"] / (m["tp"] + m["fp"]) if (m["tp"] + m["fp"]) > 0 else 0
        m["recall"] = m["tp"] / (m["tp"] + m["fn"]) if (m["tp"] + m["fn"]) > 0 else 0
        m["f1"] = 2 * m["precision"] * m["recall"] / (m["precision"] + m["recall"]) if (m["precision"] + m["recall"]) > 0 else 0
    
    return cwe_metrics

def precompute_embeddings(data_list, encoder, device, batch_size=16):
    """Pre-compute all embeddings to avoid redundant encoding during training"""
    print("Pre-computing embeddings...")
    embeddings = []
    
    for i in range(0, len(data_list), batch_size):
        batch = data_list[i:i+batch_size]
        batch_embeddings = []
        
        for item in batch:
            emb = encoder.encode(item["code"])
            batch_embeddings.append(emb)
        
        embeddings.extend(batch_embeddings)
        print(f"Pre-computed {min(i+batch_size, len(data_list))}/{len(data_list)} embeddings")
    
    return embeddings

# =====================================================================
# THÀNH PHẦN 5: DỮ LIỆU MẪU VÀ BỘ MÔ PHỎNG EMBEDDING
# =====================================================================
# Dữ liệu thực tế: 10 mẫu mã nguồn C (2 cụm CWE, Nhãn: 1 = Lỗi, 0 = An toàn)
RAW_C_DATA = [
    {"code": "void secure_write(char *input) { char buffer[10]; strncpy(buffer, input, 9); buffer[9] = '\0'; }", "vuln": 0, "cwe": 0},
    {"code": "void use_after_free_vuln() { int *ptr = malloc(sizeof(int)); free(ptr); printf(\"%d\", *ptr); }", "vuln": 1, "cwe": 0},
    {"code": "void use_after_free_secure() { int *ptr = malloc(sizeof(int)); free(ptr); ptr = NULL; }", "vuln": 0, "cwe": 0},
    {"code": "void null_dereference_vuln(char *str) { char *match = strchr(str, 'A'); *match = 'B'; }", "vuln": 1, "cwe": 0},
    {"code": "void null_dereference_secure(char *str) { char *match = strchr(str, 'A'); if(match!=NULL) *match = 'B'; }", "vuln": 0, "cwe": 0},
    # Cụm 1: Injection (CWE-89, CWE-78)
    {"code": "void vulnerable_sql(char *usr) { char q; sprintf(q, \"SELECT * FROM u WHERE id='%s'\", usr); mysql_query(c, q); }", "vuln": 1, "cwe": 1},
    {"code": "void secure_sql(char *usr) { MYSQL_STMT *stmt = mysql_stmt_init(conn); /* parameterized execution */ }", "vuln": 0, "cwe": 1},
    {"code": "void vulnerable_os_cmd(char *file) { char cmd; sprintf(cmd, \"cat %s\", file); system(cmd); }", "vuln": 1, "cwe": 1},
    {"code": "void secure_os_cmd(char *file) { if(strspn(file, \"a-zA-Z0-9.\") == strlen(file)) { system(file); } }", "vuln": 0, "cwe": 1},
]

def load_raw_c_data(file_path):
    """Load C code data from JSONL file"""
    data = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    data.append(item)
        print(f"Loaded {len(data)} samples from {file_path}")
    except FileNotFoundError:
        print(f"Warning: File not found at {file_path}. Using fallback data.")
        return None
    return data

RAW_C_DATA = load_raw_c_data("/drive1/cuongtm/vul_fewshot/data/primevul/moe.jsonl")

class MockCodeEncoder:
    """CodeBERT encoder with attention pooling for better embeddings"""
    def __init__(self, dim=768, device="cpu", use_attention_pooling=True):
        self.dim = dim
        self.device = device
        self.use_attention_pooling = use_attention_pooling
        try:
            self.tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")
            self.model = AutoModel.from_pretrained("microsoft/codebert-base")
            self.model.to(device)
            self.model.eval()
            print(f"CodeBERT model loaded on {device} (Attention pooling: {use_attention_pooling})")
        except Exception as e:
            print(f"Warning: Could not load CodeBERT: {e}. Using random embeddings.")
            self.tokenizer = None
            self.model = None

    def encode(self, code_str):
        if self.model is None:
            return torch.randn(self.dim)
        
        with torch.no_grad():
            inputs = self.tokenizer(code_str, return_tensors="pt", max_length=512, truncation=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            outputs = self.model(**inputs)
            
            if self.use_attention_pooling:
                # Attention pooling: weighted average of all tokens
                hidden_states = outputs.last_hidden_state  # [1, seq_len, 768]
                attention_mask = inputs['attention_mask'].unsqueeze(-1)  # [1, seq_len, 1]
                
                # Mean pooling with attention mask
                masked_hidden = hidden_states * attention_mask
                sum_hidden = masked_hidden.sum(dim=1)
                sum_mask = attention_mask.sum(dim=1)
                embedding = (sum_hidden / sum_mask).squeeze(0)
            else:
                # [CLS] token only
                embedding = outputs.last_hidden_state[:, 0, :].squeeze(0)
        
        return embedding

class VulnerabilityDataset(Dataset):
    def __init__(self, data_list, encoder=None, embeddings=None):
        self.data = data_list
        self.encoder = encoder
        self.embeddings = embeddings
        self.use_cache = embeddings is not None

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        
        # Return raw code strings (not embeddings) for on-the-fly encoding
        code_str = item["code"]
        vuln_label = torch.tensor([item["vuln"]], dtype=torch.float32)
        cwe_label = torch.tensor(item["cwe"], dtype=torch.long)
        return code_str, vuln_label, cwe_label

# =====================================================================
# STRATIFIED DATA SPLIT - Maintain class balance across train/val/test
# =====================================================================
def build_stratified_data_split(data_list, seed=42, train_ratio=0.7, val_ratio=0.15):
    """Split data into stratified train/val/test subsets maintaining class balance.
    
    Args:
        data_list: List of data dictionaries with 'vuln' key
        seed: Random seed for reproducibility
        train_ratio: Proportion of data for training (default 0.7 = 70%)
        val_ratio: Proportion of data for validation (default 0.15 = 15%)
        test_ratio: Proportion of data for testing (default 0.15 = 15%)
    
    Returns:
        train_data, val_data, test_data: Stratified subsets of data
    """
    labels = [int(item['vuln']) for item in data_list]
    indices = np.arange(len(labels))
    
    # First split: 70% train, 30% temp
    train_idx, temp_idx, train_y, temp_y = train_test_split(
        indices,
        labels,
        test_size=(1 - train_ratio),
        random_state=seed,
        stratify=labels
    )
    
    # Second split: 50/50 of temp for val/test (15/15 of total)
    val_ratio_in_temp = val_ratio / (1 - train_ratio)
    val_idx, test_idx = train_test_split(
        temp_idx,
        test_size=(1 - val_ratio_in_temp),
        random_state=seed,
        stratify=temp_y
    )
    
    train_data = [data_list[i] for i in train_idx]
    val_data = [data_list[i] for i in val_idx]
    test_data = [data_list[i] for i in test_idx]
    
    # Log class distribution
    train_vuln = sum(1 for item in train_data if item['vuln'] == 1)
    val_vuln = sum(1 for item in val_data if item['vuln'] == 1)
    test_vuln = sum(1 for item in test_data if item['vuln'] == 1)
    
    print(f"\nStratified Data Split (seed={seed}):")
    print(f"  Train: {len(train_data)} samples ({train_vuln} vulnerable, {len(train_data)-train_vuln} safe)")
    print(f"  Val:   {len(val_data)} samples ({val_vuln} vulnerable, {len(val_data)-val_vuln} safe)")
    print(f"  Test:  {len(test_data)} samples ({test_vuln} vulnerable, {len(test_data)-test_vuln} safe)")
    print(f"  Train vuln%: {100*train_vuln/len(train_data):.1f}% | Val vuln%: {100*val_vuln/len(val_data):.1f}% | Test vuln%: {100*test_vuln/len(test_data):.1f}%")
    
    return train_data, val_data, test_data

# =====================================================================
# THÀNH PHẦN 6: QUY TRÌNH TRAIN - VALIDATE - TEST (OPTIMIZED)
# =====================================================================
def run_pipeline():
    if RAW_C_DATA is None or len(RAW_C_DATA) == 0:
        print("Error: No training data loaded!")
        return
    
    expanded_data = RAW_C_DATA
    
    # Use stratified split to maintain class balance across train/val/test
    train_data, val_data, test_data = build_stratified_data_split(
        expanded_data,
        seed=42,
        train_ratio=0.7,
        val_ratio=0.15
    )
    
    # Alternative: Load from separate files if available
    train_data = load_raw_c_data("./dataset/sven_primevul/primevul_sven_train_moe.jsonl")
    val_data = load_raw_c_data("./dataset/sven_primevul/primevul_sven_val_moe.jsonl")
    test_data = load_raw_c_data("./dataset/sven_primevul/primevul_sven_test_moe.jsonl")

    # 1. Khởi tạo thiết bị (GPU nếu có)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n{'='*60}")
    print(f"TRAINING DEVICE: {device}")
    print(f"{'='*60}")
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"CUDA Version: {torch.version.cuda}")
        print(f"Available Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    print(f"Training samples: {len(train_data)}, Val: {len(val_data)}, Test: {len(test_data)}")
    
    # 2. Analyze raw CWE space and build automatic clusters (from full data)
    print("\nAnalyzing CWE distribution...")
    all_data_for_cwe = train_data + val_data + test_data
    raw_num_classes, cwe_ids = get_num_classes_cwe(all_data_for_cwe)
    num_experts, cwe_to_cluster, cwe_counter, cluster_loads = build_auto_cwe_clusters(
        all_data_for_cwe,
        target_experts=None,
        min_experts=8,
        max_experts=32,
        min_samples_threshold=20  # Merge CWEs with <= 20 samples into rare cluster
    )
    print(f"Setting num_experts (clustered) = {num_experts}")
    
    # Validate raw CWE values and cluster mapping coverage
    print("\nValidating CWE indices and clusters...")
    all_cwes = []
    for item in train_data + val_data + test_data:
        all_cwes.append(item['cwe'])
    
    min_cwe = min(all_cwes)
    max_cwe = max(all_cwes)
    invalid_raw_cwes = [c for c in all_cwes if c < 0 or c >= raw_num_classes]
    missing_mapping_cwes = sorted(set(c for c in all_cwes if c not in cwe_to_cluster))
    all_cluster_labels = [cwe_to_cluster[c] for c in all_cwes if c in cwe_to_cluster]
    invalid_cluster_labels = [cl for cl in all_cluster_labels if cl < 0 or cl >= num_experts]
    
    print(f"  CWE range in data: [{min_cwe}, {max_cwe}]")
    print(f"  Raw CWE range required: [0, {raw_num_classes-1}]")
    print(f"  Cluster label range required: [0, {num_experts-1}]")
    print(f"  Invalid raw CWEs found: {len(invalid_raw_cwes)}")
    print(f"  Missing cluster mappings: {len(missing_mapping_cwes)}")
    print(f"  Invalid cluster labels found: {len(invalid_cluster_labels)}")
    
    if invalid_raw_cwes:
        print(f"    ERROR: Found {len(invalid_raw_cwes)} raw CWE values outside valid range!")
        print(f"    Sample invalid values: {sorted(set(invalid_raw_cwes))[:10]}")
        raise ValueError(f"Raw CWE indices must be in [0, {raw_num_classes}). Found [{min_cwe}, {max_cwe}]")

    if missing_mapping_cwes:
        print(f"    ERROR: Missing cluster mapping for {len(missing_mapping_cwes)} CWE values!")
        print(f"    Missing CWE IDs: {missing_mapping_cwes[:10]}")
        raise ValueError("CWE-to-cluster mapping is incomplete")

    if invalid_cluster_labels:
        print(f"    ERROR: Found invalid cluster labels!")
        print(f"    Sample invalid cluster labels: {sorted(set(invalid_cluster_labels))[:10]}")
        raise ValueError(f"Cluster labels must be in [0, {num_experts})")
    
    print(f"    All CWE indices are valid!")
    print("")
    
    # 3. Calculate class weights for imbalanced data
    pos_weight = calculate_class_weights(train_data)
    if pos_weight is not None:
        pos_weight = pos_weight.to(device)
    
    # 4. No precomputation - we'll encode on-the-fly for fine-tuning
    print("\n" + "="*60)
    print("Using on-the-fly encoding (fine-tuning enabled)")
    print("="*60)
    
    # 5. Tạo DataLoaders WITHOUT cached embeddings
    train_dataset = VulnerabilityDataset(train_data)
    val_dataset = VulnerabilityDataset(val_data)
    test_dataset = VulnerabilityDataset(test_data)
    
    # Create WeightedRandomSampler for class balance (like baseline)
    train_labels = [int(item['vuln']) for item in train_data]
    train_class_counts = np.bincount(train_labels, minlength=2)
    class_weights_sampling = 1.0 / np.maximum(train_class_counts, 1)
    sample_weights = [class_weights_sampling[label] for label in train_labels]
    train_sampler = torch.utils.data.WeightedRandomSampler(
        weights=torch.DoubleTensor(sample_weights),
        num_samples=len(sample_weights),
        replacement=True
    )
    
    print(f"\nWeighted Sampling (like baseline):")
    print(f"  Train class counts (safe/vuln): {train_class_counts[0]}/{train_class_counts[1]}")
    print(f"  Class weights for sampling: {class_weights_sampling}")
    
    train_loader = DataLoader(train_dataset, batch_size=16, sampler=train_sampler, num_workers=0)  # Smaller batch for fine-tuning
    val_loader = DataLoader(val_dataset, batch_size=16, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_dataset, batch_size=16, shuffle=False, num_workers=0)

    # 6. Khởi tạo Model với encoder (fine-tunable)
    model = MoE_VulnerabilityDetector(
        input_dim=768, 
        hidden_dim=256, 
        num_experts=num_experts, 
        top_k=1, 
        dropout_rate=0.1,
        encoder_name="microsoft/codebert-base",
        freeze_encoder=False  # CRITICAL: Allow fine-tuning
    ).to(device)
    
    # CRITICAL FIX: Lower learning rate like baseline (2e-5 instead of 2e-3)
    # High lr (2e-3) was causing instability and poor performance
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5, weight_decay=1e-5)
    
    # Adjust epochs and scheduler for lower learning rate
    epochs = 30  # Reduced from 50 since lower lr converges differently
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-6)
    
    best_val_loss = float('inf')
    best_val_f1 = 0.0  # Track F1 instead of just loss
    patience = 8
    patience_counter = 0
    best_model_state = None
    
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"\nModel parameters: {total_params:,} (trainable: {trainable_params:,})")
    print(f"Learning rate: 2e-5 (same as baseline)")
    print(f"Epochs: {epochs}")
    print(f"Patience: {patience}")
    
    print(f"\n{'='*60}")
    print(f"BẮT ĐẦU HUẤN LUYỆN KIẾN TRÚC MoE (OPTIMIZED)")
    print(f"{'='*60}")
    
    for epoch in range(epochs):
        # --- TRAIN LOOP ---
        model.train()
        train_loss, train_acc = 0.0, 0.0
        train_bce, train_ce, train_aux = 0.0, 0.0, 0.0

        for code_batch, vuln, cwe in train_loader:
            # Encode code on-the-fly (allows gradient flow to encoder)
            emb = model.encode_code(code_batch, device)
            vuln, cwe = vuln.to(device), cwe.to(device)
            cwe_cluster = torch.tensor(
                [cwe_to_cluster[int(c.item())] for c in cwe],
                dtype=torch.long,
                device=device
            )
            optimizer.zero_grad()

            logits, frac_routed, prob_exp, router_logits = model(emb)
            loss, bce, ce, aux = moe_multitask_loss(logits, vuln, router_logits, cwe_cluster,
                                                     frac_routed, prob_exp, num_experts=num_experts, 
                                                     pos_weight=pos_weight, use_focal=True,
                                                     label_smoothing=0.05,
                                                     alpha=0.005, beta=0.2)

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            train_loss += loss.item()
            train_bce += bce.item()
            train_ce += ce.item()
            train_aux += aux.item()
            train_acc += calculate_accuracy(logits, vuln).item()

        # --- VALIDATION LOOP ---
        model.eval()
        val_loss, val_acc = 0.0, 0.0
        
        with torch.no_grad():
            for code_batch, vuln, cwe in val_loader:
                # Encode code on-the-fly (no grad in eval)
                emb = model.encode_code(code_batch, device)
                vuln, cwe = vuln.to(device), cwe.to(device)
                cwe_cluster = torch.tensor(
                    [cwe_to_cluster[int(c.item())] for c in cwe],
                    dtype=torch.long,
                    device=device
                )
                logits, frac_routed, prob_exp, router_logits = model(emb)
                loss, _, _, _ = moe_multitask_loss(logits, vuln, router_logits, cwe_cluster,
                                                    frac_routed, prob_exp, num_experts=num_experts,
                                                    pos_weight=pos_weight, use_focal=True,
                                                    label_smoothing=0.05,
                                                    alpha=0.005, beta=0.2)

                val_loss += loss.item()
                val_acc += calculate_accuracy(logits, vuln).item()

        avg_train_loss = train_loss / len(train_loader)
        avg_train_acc = train_acc / len(train_loader)
        avg_val_loss = val_loss / len(val_loader)
        avg_val_acc = val_acc / len(val_loader)
        
        # Calculate validation F1 for better model selection (like baseline)
        model.eval()
        val_preds_all = []
        val_labels_all = []
        with torch.no_grad():
            for code_batch, vuln, cwe in val_loader:
                emb = model.encode_code(code_batch, device)
                logits, _, _, _ = model(emb)
                probs = torch.sigmoid(logits)
                preds = (probs > 0.5).float()
                val_preds_all.extend(preds.cpu().numpy().flatten())
                val_labels_all.extend(vuln.numpy().flatten())
        
        val_preds_tensor = torch.tensor(val_preds_all)
        val_labels_tensor = torch.tensor(val_labels_all)
        val_f1, val_precision, val_recall = calculate_f1_score(val_preds_tensor, val_labels_tensor)
        
        # Learning Rate Schedule
        scheduler.step()
        current_lr = optimizer.param_groups[0]['lr']
        
        print(f"Epoch {epoch+1:3d}/{epochs} | LR: {current_lr:.6f} | "
              f"Train Loss: {avg_train_loss:.4f} Acc: {avg_train_acc:.4f} | "
              f"Val Loss: {avg_val_loss:.4f} Acc: {avg_val_acc:.4f} F1: {val_f1:.4f}")
        
        # Early Stopping based on F1 score (like baseline)
        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            best_val_loss = avg_val_loss
            patience_counter = 0
            best_model_state = copy.deepcopy(model.state_dict())
            print(f"  ✓ New best F1: {val_f1:.4f} (Precision: {val_precision:.4f}, Recall: {val_recall:.4f})")
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"\nEarly stopping triggered! Best Val F1: {best_val_f1:.4f}, Loss: {best_val_loss:.4f}")
                model.load_state_dict(best_model_state)
                break
    
    # Load best model
    if best_model_state is not None:
        model.load_state_dict(best_model_state)
    
    # Find optimal threshold on validation set
    print("\n" + "="*60)
    print("Finding optimal classification threshold...")
    print("="*60)
    optimal_threshold, metrics = find_optimal_threshold(model, val_loader, device)
    print("="*60)

    # --- TEST LOOP ---
    print("\n" + "="*60)
    print("ĐÁNH GIÁ TRÊN TẬP KIỂM THỬ (TEST SET)")
    print("="*60)
    model.eval()
    
    # Collect all predictions and probabilities for comprehensive metrics
    test_probabilities = []
    test_labels = []
    test_cwe_labels = []
    
    with torch.no_grad():
        for code_batch, vuln, cwe in test_loader:
            emb = model.encode_code(code_batch, device)
            vuln, cwe = vuln.to(device), cwe.to(device)
            logits, _, _, _ = model(emb)
            probs = torch.sigmoid(logits)
            
            test_probabilities.extend(probs.cpu().numpy().flatten().tolist())
            test_labels.extend(vuln.cpu().numpy().flatten().tolist())
            test_cwe_labels.extend(cwe.cpu().numpy().tolist())
    
    # Convert to numpy for easier computation
    test_probs_np = np.array(test_probabilities)
    test_labels_np = np.array(test_labels)
    
    # Calculate metrics for BOTH thresholds
    # Threshold 0.5 (default)
    preds_default = (test_probs_np >= 0.5).astype(int)
    acc_default = (preds_default == test_labels_np).mean()
    
    # Calculate F1, precision, recall for default threshold
    preds_default_tensor = torch.tensor(preds_default, dtype=torch.float32)
    labels_tensor = torch.tensor(test_labels_np, dtype=torch.float32)
    f1_default, precision_default, recall_default = calculate_f1_score(preds_default_tensor, labels_tensor)
    
    # Optimal threshold
    preds_optimal = (test_probs_np >= optimal_threshold).astype(int)
    acc_optimal = (preds_optimal == test_labels_np).mean()
    
    # Calculate F1, precision, recall for optimal threshold
    preds_optimal_tensor = torch.tensor(preds_optimal, dtype=torch.float32)
    f1_optimal, precision_optimal, recall_optimal = calculate_f1_score(preds_optimal_tensor, labels_tensor)
    
    # Use optimal threshold predictions for detailed logging
    test_predictions = preds_optimal.tolist()
    
    # Log test predictions to file with timestamp
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    cluster_map_file = results_dir / f"cwe_cluster_map_{timestamp}.json"
    
    # Identify rare CWEs
    rare_cwes_info = {str(cwe_id): {"freq": int(freq), "cluster": int(cwe_to_cluster[cwe_id])} 
                      for cwe_id, freq in cwe_counter.items() if freq <= 20}
    
    with open(cluster_map_file, "w") as f:
        json.dump(
            {
                "raw_num_classes": int(raw_num_classes),
                "num_experts": int(num_experts),
                "min_samples_threshold": 20,
                "cluster_loads": [int(x) for x in cluster_loads],
                "cwe_to_cluster": {str(k): int(v) for k, v in sorted(cwe_to_cluster.items())},
                "cwe_frequency": {str(k): int(v) for k, v in sorted(cwe_counter.items())},
                "rare_cwes_merged": rare_cwes_info,
                "num_rare_cwes": len(rare_cwes_info)
            },
            f,
            indent=2
        )
    print(f"✓ CWE cluster mapping saved to {cluster_map_file}")
    print(f"  (Merged {len(rare_cwes_info)} CWEs with <= 20 samples into rare cluster)")
    
    pred_file = results_dir / f"test_predictions_{timestamp}.jsonl"
    print(f"\nSaving test predictions to {pred_file}...")
    with open(pred_file, "w") as f:
        for i in range(len(test_predictions)):
            pred_data = {
                "sample_id": i,
                "predicted_label": int(test_predictions[i]),
                "real_label": int(test_labels[i]),
                "probability": float(test_probabilities[i]),
                "cwe_id": int(test_cwe_labels[i]),
                "is_correct": int(test_predictions[i]) == int(test_labels[i])
            }
            f.write(json.dumps(pred_data) + "\n")
    print(f"✓ Test predictions saved to {pred_file}")
    
    # Save summary report
    report_file = results_dir / f"test_report_{timestamp}.txt"
    with open(report_file, "w") as f:
        f.write("="*70 + "\n")
        f.write("TEST PREDICTIONS SUMMARY\n")
        f.write("="*70 + "\n")
        f.write(f"Total test samples: {len(test_predictions)}\n")
        f.write(f"Correct predictions: {sum(test_predictions[i] == test_labels[i] for i in range(len(test_predictions)))}\n")
        f.write(f"Accuracy: {sum(test_predictions[i] == test_labels[i] for i in range(len(test_predictions))) / len(test_predictions) * 100:.2f}%\n")
        f.write("\nFirst 10 predictions:\n")
        f.write(f"{'ID':<5} {'Pred':<6} {'Real':<6} {'Prob':<10} {'CWE':<5} {'OK':<5}\n")
        f.write("-"*65 + "\n")
        for i in range(min(10, len(test_predictions))):
            is_correct = "✓" if test_predictions[i] == test_labels[i] else "✗"
            f.write(f"{i:<5} {int(test_predictions[i]):<6} {int(test_labels[i]):<6} "
                   f"{test_probabilities[i]:<10.4f} {int(test_cwe_labels[i]):<5} {is_correct:<5}\n")
    
    print(f"✓ Report saved to {report_file}\n")
    
    # Print sample predictions
    print("Sample Test Predictions (first 10):")
    print(f"{'Sample':<8} {'Predicted':<12} {'Real':<8} {'Probability':<12} {'CWE':<6} {'Correct':<9}")
    print("-" * 65)
    for i in range(min(10, len(test_predictions))):
        is_correct = "✓" if test_predictions[i] == test_labels[i] else "✗"
        print(f"{i:<8} {int(test_predictions[i]):<12} {int(test_labels[i]):<8} "
              f"{test_probabilities[i]:<12.4f} {int(test_cwe_labels[i]):<6} {is_correct:<9}")

    # Print comprehensive metrics comparison
    print("\n" + "="*80)
    print("TEST METRICS COMPARISON")
    print("="*80)
    print(f"\n{'Metric':<20} {'Threshold=0.5':<20} {'Threshold={:.3f}':<20} {'Diff':<15}".format(optimal_threshold))
    print("-"*80)
    
    acc_diff = (acc_optimal - acc_default) * 100
    precision_diff = (precision_optimal - precision_default) * 100
    recall_diff = (recall_optimal - recall_default) * 100
    f1_diff = (f1_optimal - f1_default) * 100
    
    print(f"{'Accuracy':<20} {acc_default*100:<19.2f}% {acc_optimal*100:<19.2f}% {acc_diff:+.2f}%")
    print(f"{'Precision':<20} {precision_default*100:<19.2f}% {precision_optimal*100:<19.2f}% {precision_diff:+.2f}%")
    print(f"{'Recall':<20} {recall_default*100:<19.2f}% {recall_optimal*100:<19.2f}% {recall_diff:+.2f}%")
    print(f"{'F1 Score':<20} {f1_default*100:<19.2f}% {f1_optimal*100:<19.2f}% {f1_diff:+.2f}%")
    print("-"*80)
    
    if f1_optimal > f1_default:
        print(f"✓ Optimal threshold IMPROVES F1 by {f1_diff:+.2f}%")
    elif f1_optimal < f1_default:
        print(f"✗ Optimal threshold DEGRADES F1 by {f1_diff:.2f}% (using default 0.5 is better)")
    else:
        print(f"= Optimal threshold has SAME F1 as default")
    print("="*80)
    
    # --- PER-CWE EVALUATION ---
    print("\n" + "="*60)
    print("ĐÁNH GIÁ THEO TỪNG CWE ID (with optimal threshold)")
    print("="*60)
    cwe_metrics = evaluate_by_cwe(model, test_loader, device, threshold=optimal_threshold)
    
    print(f"\n{'CWE ID':<10} {'Accuracy':<12} {'Precision':<12} {'Recall':<12} {'F1':<12} {'Samples':<10}")
    print("-" * 70)
    
    for cwe_id in sorted(cwe_metrics.keys()):
        metrics = cwe_metrics[cwe_id]
        print(f"{cwe_id:<10} {metrics['accuracy']*100:<11.2f}% {metrics['precision']*100:<11.2f}% "
              f"{metrics['recall']*100:<11.2f}% {metrics['f1']*100:<11.2f}% {metrics['total']:<10}")
    
    print("-" * 70)
    total_samples = sum(m["total"] for m in cwe_metrics.values())
    overall_acc = sum(m["tp"] + m["tn"] for m in cwe_metrics.values()) / total_samples
    overall_tp = sum(m["tp"] for m in cwe_metrics.values())
    overall_fp = sum(m["fp"] for m in cwe_metrics.values())
    overall_fn = sum(m["fn"] for m in cwe_metrics.values())
    overall_precision = overall_tp / (overall_tp + overall_fp) if (overall_tp + overall_fp) > 0 else 0
    overall_recall = overall_tp / (overall_tp + overall_fn) if (overall_tp + overall_fn) > 0 else 0
    overall_f1 = 2 * overall_precision * overall_recall / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0
    
    print(f"{'Overall':<10} {overall_acc*100:<11.2f}% {overall_precision*100:<11.2f}% "
          f"{overall_recall*100:<11.2f}% {overall_f1*100:<11.2f}% {total_samples:<10}")
    
    # Save comprehensive final report
    final_report_file = results_dir / f"final_report_{timestamp}.txt"
    with open(final_report_file, "w") as f:
        f.write("="*70 + "\n")
        f.write("MOE VULNERABILITY DETECTION - FINAL TRAINING REPORT\n")
        f.write("="*70 + "\n")
        f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Log file: {log_file}\n")
        f.write(f"Predictions file: {pred_file}\n")
        f.write(f"CWE cluster map: {cluster_map_file}\n")
        f.write("\n" + "="*70 + "\n")
        f.write("DATASET SUMMARY\n")
        f.write("="*70 + "\n")
        f.write(f"Training samples: {len(train_data)}\n")
        f.write(f"Validation samples: {len(val_data)}\n")
        f.write(f"Test samples: {len(test_data)}\n")
        f.write(f"Total samples: {len(train_data) + len(val_data) + len(test_data)}\n")
        f.write(f"Raw CWE classes (full data max+1): {raw_num_classes}\n")
        f.write(f"Router experts after auto-clustering: {num_experts}\n")
        f.write(f"Cluster loads: {cluster_loads}\n")
        
        f.write("\n" + "="*70 + "\n")
        f.write("MODEL CONFIGURATION\n")
        f.write("="*70 + "\n")
        f.write(f"Input dimension: 768\n")
        f.write(f"Hidden dimension: 256\n")
        f.write(f"Number of experts: {num_experts}\n")
        f.write(f"Auto-clustering: enabled (min_samples_threshold=20)\n")
        f.write(f"Rare cluster: {len(rare_cwes_info)} CWE types merged (total {sum(c for c_id, c in cwe_counter.items() if c <= 20)} samples)\n")
        f.write(f"Top-k routing: 1\n")
        f.write(f"Dropout rate: 0.1\n")
        
        f.write("\n" + "="*70 + "\n")
        f.write("TEST RESULTS - THRESHOLD COMPARISON\n")
        f.write("="*70 + "\n")
        f.write(f"{'Metric':<20} {'Threshold=0.5':<20} {'Optimal={:.3f}':<20} {'Diff':<15}\n".format(optimal_threshold))
        f.write("-"*70 + "\n")
        f.write(f"{'Accuracy':<20} {acc_default*100:<19.2f}% {acc_optimal*100:<19.2f}% {acc_diff:+.2f}%\n")
        f.write(f"{'Precision':<20} {precision_default*100:<19.2f}% {precision_optimal*100:<19.2f}% {precision_diff:+.2f}%\n")
        f.write(f"{'Recall':<20} {recall_default*100:<19.2f}% {recall_optimal*100:<19.2f}% {recall_diff:+.2f}%\n")
        f.write(f"{'F1 Score':<20} {f1_default*100:<19.2f}% {f1_optimal*100:<19.2f}% {f1_diff:+.2f}%\n")
        f.write("-"*70 + "\n")
        if f1_optimal > f1_default:
            f.write(f"✓ Optimal threshold IMPROVES F1 by {f1_diff:+.2f}%\n")
        elif f1_optimal < f1_default:
            f.write(f"✗ Optimal threshold DEGRADES F1 by {f1_diff:.2f}% (default is better)\n")
        else:
            f.write(f"= Optimal threshold has SAME F1 as default\n")
        
        f.write("\n" + "="*70 + "\n")
        f.write("OVERALL METRICS\n")
        f.write("="*70 + "\n")
        f.write(f"Overall Accuracy: {overall_acc*100:.2f}%\n")
        f.write(f"Overall Precision: {overall_precision*100:.2f}%\n")
        f.write(f"Overall Recall: {overall_recall*100:.2f}%\n")
        f.write(f"Overall F1 Score: {overall_f1*100:.2f}%\n")
        
        f.write("\n" + "="*70 + "\n")
        f.write("PER-CWE EVALUATION RESULTS\n")
        f.write("="*70 + "\n")
        f.write(f"{'CWE ID':<10} {'Accuracy':<12} {'Precision':<12} {'Recall':<12} {'F1':<12} {'Samples':<10}\n")
        f.write("-" * 70 + "\n")
        
        for cwe_id in sorted(cwe_metrics.keys()):
            metrics = cwe_metrics[cwe_id]
            f.write(f"{cwe_id:<10} {metrics['accuracy']*100:<11.2f}% {metrics['precision']*100:<11.2f}% "
                   f"{metrics['recall']*100:<11.2f}% {metrics['f1']*100:<11.2f}% {metrics['total']:<10}\n")
        
        f.write("-" * 70 + "\n")
        f.write(f"{'Overall':<10} {overall_acc*100:<11.2f}% {overall_precision*100:<11.2f}% "
               f"{overall_recall*100:<11.2f}% {overall_f1*100:<11.2f}% {total_samples:<10}\n")
        
        f.write("\n" + "="*70 + "\n")
        f.write("TRAINING COMPLETED SUCCESSFULLY\n")
        f.write("="*70 + "\n")
    
    print(f"✓ Final report saved to {final_report_file}")
    print("\n" + "="*60)
    print("Quy trình huấn luyện hoàn tất thành công!")
    print("="*60)
    print(f"Log file: {log_file}")
    print(f"Results directory: {results_dir}")
    print("="*60)

if __name__ == "__main__":
    run_pipeline()