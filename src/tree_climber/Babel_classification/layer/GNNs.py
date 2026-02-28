import torch
import torch.nn as nn
from torch.nn.parameter import Parameter
import math

class GraphConvolution(nn.Module):
    """
    Simple GCN layer, similar to https://arxiv.org/abs/1609.02907
    """

    def __init__(self, in_features, out_features, bias=True):
        super(GraphConvolution, self).__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.weight = nn.Parameter(torch.FloatTensor(in_features, out_features))
        if bias:
            self.bias = nn.Parameter(torch.FloatTensor(out_features))
            stdv = 1. / math.sqrt(self.bias.shape[0])
            torch.nn.init.uniform_(self.bias, a=-stdv, b=stdv)
        else:
            self.register_parameter('bias', None)

        torch.nn.init.xavier_uniform_(self.weight)

    def forward(self, text, adj):
        hidden = torch.matmul(text, self.weight) # hideen = WX
        denom = torch.sum(adj, dim=2, keepdim=True) + 1
        output = torch.matmul(adj, hidden) / denom
        if self.bias is not None:
            return output + self.bias
        else:
            return output



""" Simple GCN layer, similar to https://arxiv.org/abs/1609.02907 """

# class GraphConvolution(torch.nn.Module):
#     def __init__(self, in_features, out_features, dropout=0.1, act=torch.relu, bias=False):
#         super(GraphConvolution, self).__init__()
#         self.weight = Parameter(torch.FloatTensor(in_features, out_features))
#         if bias:
#             self.bias = Parameter(torch.FloatTensor(out_features))
#         else:
#             self.register_parameter('bias', None)
#         self.reset_parameters()
#
#         self.act = act
#         self.dropout = nn.Dropout(dropout)
#
#     def reset_parameters(self):
#         stdv = math.sqrt(6.0 / (self.weight.size(0) + self.weight.size(1)))
#         self.weight.data.uniform_(-stdv, stdv)
#         if self.bias is not None:
#             self.bias.data.uniform_(-stdv, stdv)
#
#     def forward(self, input, adj):
#         x = self.dropout(input)
#         support = torch.matmul(x.double(), self.weight.double())
#         output = torch.matmul(adj.double(), support.double())
#         if self.bias is not None:
#             output = output + self.bias
#         return self.act(output)