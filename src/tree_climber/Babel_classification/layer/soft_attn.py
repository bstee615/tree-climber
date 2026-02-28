import torch
import torch.nn as nn
import torch.nn.functional as F


# Assuming X1 has shape (batch_size, hidden_dim)
# and X2 has shape (batch_size, sequence_length, hidden_dim)

# Define your attention mechanism
class SoftAttention(nn.Module):
    def __init__(self, text_hidde, graph_hidden, hidden_dim):
        super(SoftAttention, self).__init__()
        self.W_q = nn.Linear(text_hidde, hidden_dim, bias=False)
        self.W_k = nn.Linear(graph_hidden, hidden_dim, bias=False)

    def forward(self, X1, X2):
        # Apply linear transformations
        q = self.W_q(X1)  # (batch_size, hidden_dim)
        k = self.W_k(X2)  # (batch_size, sequence_length, hidden_dim)

        # Calculate attention scores
        attn_scores = torch.bmm(q.unsqueeze(1), k.permute(0, 2, 1))
        attn_weights = F.softmax(attn_scores, dim=-1)

        # Apply attention to X2
        attended_X2 = torch.multiply(attn_weights.permute(0, 2, 1), X2)
        attended_X2 = attended_X2.squeeze(1)

        return attended_X2

# Initialize the attention mechanism
# attention = SoftAttention(hidden_dim=your_hidden_dim)

# Apply attention
# attended_X2 = attention(X1, X2)
