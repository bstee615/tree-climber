import torch
import torch.nn as nn
import torch.nn.functional as F

from layer.Attention import BertSelfAttention
from layer.GNNs import GraphConvolution


class SentSelTwoGCNCat(nn.Module):
    def __init__(self, args):
        super(SentSelTwoGCNCat, self).__init__()

        '''Self_Attention_GCN_Model'''
        self.data_gcn1 = GraphConvolution(in_features=args.sentence_hidden, out_features=args.graph_hidden)
        self.data_gcn2 = GraphConvolution(in_features=args.graph_hidden, out_features=args.graph_hidden)
        self.control_gcn1 = GraphConvolution(in_features=args.sentence_hidden, out_features=args.graph_hidden)
        self.control_gcn2 = GraphConvolution(in_features=args.graph_hidden, out_features=args.graph_hidden)
        self.dropout = nn.Dropout(p=0.5)

        self.lstm = nn.LSTM(input_size=args.sentence_hidden + args.graph_hidden + args.graph_hidden,
                            hidden_size=args.output_feature, batch_first=True, bidirectional=False, num_layers=1)
        self.attn = BertSelfAttention(hidden_size=args.output_feature, num_attention_heads=args.head_num,
                                      attention_probs_dropout_prob=0.1)
        self.fc = nn.Linear(in_features=args.output_feature, out_features=1)

    def forward(self, input_, attention_mask, labels, data_matrix=None, control_matrix=None):
        input_ = input_.permute(1, 0, 2)  # bz, seqence_len, hidden_states

        data_output = F.relu(self.data_gcn1(input_, data_matrix))  # bz, seq_len, 128
        data_output = self.dropout(data_output)
        data_output = F.relu(self.data_gcn2(data_output, data_matrix))

        control_output = F.relu(self.control_gcn1(input_, control_matrix))
        control_output = self.dropout(control_output)
        control_output = F.relu(self.control_gcn2(control_output, control_matrix))

        output_fusion = torch.cat((input_, data_output, control_output), -1)
        output, _ = self.lstm(output_fusion)
        output = self.attn(output, attention_mask)
        output = torch.sum(output, dim=1)
        prob = torch.sigmoid(self.fc(output))

        if labels is not None:
            labels = labels.float()
            loss = torch.log(prob[:, 0] + 1e-10) * labels + torch.log((1 - prob)[:, 0] + 1e-10) * (1 - labels)
            loss = -loss.mean()
            return loss, prob
        else:
            return prob
