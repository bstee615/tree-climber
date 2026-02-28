import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class WordAttNet(nn.Module):
    def __init__(self, args, embed_table: np.ndarray = None):
        super(WordAttNet, self).__init__()

        embed_table = torch.from_numpy(embed_table.astype(np.float32))
        self.lookup = nn.Embedding.from_pretrained(embeddings=embed_table)

        self.dropout = nn.Dropout(p=0.5)

        self.conv1 = nn.Conv1d(in_channels=args.word_hidden, out_channels=args.sentence_hidden,
                               kernel_size=5)

        self.attn_w = nn.Linear(in_features=args.sentence_hidden, out_features=args.attn_hidden)
        self.attn_v = nn.Linear(in_features=args.attn_hidden, out_features=1, bias=False)

    def forward(self, input_):
        # shape: seq_len * batch_size

        output = self.lookup(input_)

        output = self.dropout(output)  # shape: seq_len * batch_size * emb_dim
        output = output.permute(1, 2, 0)  # shape: batch_size * emb_dim * seq_len

        output = self.conv1(output)  # shape : batch_size * hidden_size * seq_len
        output = output.permute(2, 0, 1)  # shape : seq_len * batch_size * hidden_size

        weight = torch.tanh(self.attn_w(output))  # shape : seq_len * batch_size * hidden_size (f1_out_size)
        weight = self.attn_v(weight)  # shape : seq_len * batch_size * 1
        weight = F.softmax(weight, 0)  # shape : seq_len * batch_size * 1
        output = weight * output  # shape : seq_len * batch_size * hidden_size
        output = output.sum(0)  # shape: batch_size * hidden_size

        output = output.unsqueeze(0)  # shape: 1 * batch_size * hidden_size
        return output


if __name__ == "__main__":
    abc = WordAttNet()
