import math
import torch
import torch.nn as nn


def normalize(mx):
    """Row-normalize sparse matrix"""
    rowsum = mx.sum(dim=2)  # Compute row sums along the last dimension
    r_inv = rowsum.pow(-1)
    r_inv[torch.isinf(r_inv)] = 0.
    r_mat_inv = torch.diag_embed(r_inv)  # Create a batch of diagonal matrices
    mx = torch.matmul(r_mat_inv, mx)
    return mx


class RelationalGraphConvLayer(nn.Module):
    def __init__(self, num_rel, input_size, output_size, bias=True):
        super(RelationalGraphConvLayer, self).__init__()
        self.num_rel = num_rel
        self.input_size = input_size
        self.output_size = output_size

        self.weight = nn.Parameter(torch.FloatTensor(self.num_rel, self.input_size, self.output_size))
        if bias:
            self.bias = nn.Parameter(torch.FloatTensor(self.output_size))
            stdv = 1. / math.sqrt(self.bias.shape[0])
            torch.nn.init.uniform_(self.bias, a=-stdv, b=stdv)
        else:
            self.register_parameter("bias", None)

        torch.nn.init.xavier_uniform_(self.weight)

    def forward(self, text, adj):
        weights = self.weight.view(self.num_rel * self.input_size, self.output_size)  # r*input_size, output_size
        supports = []
        for i in range(self.num_rel):
            hidden = torch.bmm(normalize(adj[:, i]), text)
            supports.append(hidden)
        tmp = torch.cat(supports, dim=-1)
        output = torch.matmul(tmp.float(), weights)  # batch_size, seq_len, output_size)
        if self.bias is not None:
            return output + self.bias
        else:
            return output
