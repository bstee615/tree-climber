import torch
import torch.nn as nn
import torch.nn.functional as F

from layer.Attention_confusion import BertSelfAttention_confusion
from layer.Attention import BertSelfAttention
from layer.GNNs import GraphConvolution


class SentSelTwoGCNConfusion(nn.Module):
    def __init__(self, args):
        super(SentSelTwoGCNConfusion, self).__init__()

        '''sent_att_model'''
        self.sent_lstm = nn.LSTM(input_size=args.sentence_hidden, hidden_size=args.sentence_hidden)
        self.attn = BertSelfAttention(hidden_size=args.sentence_hidden, num_attention_heads=args.head_num,
                                      attention_probs_dropout_prob=0.1)
        '''Self_Attention_GCN_Model'''
        self.data_gcn1 = GraphConvolution(in_features=args.sentence_hidden, out_features=args.graph_hidden)
        self.data_gcn2 = GraphConvolution(in_features=args.graph_hidden, out_features=args.graph_hidden)
        self.control_gcn1 = GraphConvolution(in_features=args.sentence_hidden, out_features=args.graph_hidden)
        self.control_gcn2 = GraphConvolution(in_features=args.graph_hidden, out_features=args.graph_hidden)

        self.dropout = nn.Dropout(p=0.5)

        self.attn_confusion = BertSelfAttention_confusion(graph_hidden=args.graph_hidden,
                                                          sentence_hidden=args.sentence_hidden,
                                                          num_attention_heads=8,
                                                          attention_probs_dropout_prob=0.1)
        self.linear = nn.Linear(in_features=args.graph_hidden, out_features=args.graph_hidden)
        self.ln = nn.LayerNorm(args.graph_hidden)
        self.ffn_1 = nn.Linear(in_features=args.graph_hidden, out_features=2 * args.graph_hidden)
        self.ffn_2 = nn.Linear(in_features=2 * args.graph_hidden, out_features=args.graph_hidden)

        self.lstm = nn.LSTM(input_size=args.sentence_hidden + args.graph_hidden,
                            hidden_size=args.output_feature, batch_first=True, bidirectional=False, num_layers=1)

        self.fc = nn.Linear(in_features=args.output_feature, out_features=1)

    def text_graph_confusion(self, graph, text, attn_mask):
        data_confusion = self.attn_confusion(graph, text, attn_mask)
        data_confusion = self.linear(data_confusion)
        data_confusion = self.ln(data_confusion + text)
        data_confusion_ffn = F.relu(self.ffn_1(data_confusion))
        data_confusion_ffn = self.ffn_2(data_confusion_ffn)
        data_confusion = self.ln(data_confusion_ffn + data_confusion)
        return data_confusion

    def forward(self, input_, attention_mask, labels, data_matrix=None, control_matrix=None):
        input_ = input_.permute(1, 0, 2)  # bz, seqence_len, hidden_states

        sentence_output, _ = self.sent_lstm(input_)
        sentence_output = self.attn(sentence_output, attention_mask)

        data_output = F.relu(self.data_gcn1(input_, data_matrix))  # bz, seq_len, 128
        data_output1 = self.dropout(data_output)
        data_output2 = F.relu(self.data_gcn2(data_output1, data_matrix))
        data_confusion = self.text_graph_confusion(data_output2, sentence_output, attention_mask)
        data_confusion = self.text_graph_confusion(data_output2, data_confusion, attention_mask)

        control_output = F.relu(self.control_gcn1(input_, control_matrix))
        control_output1 = self.dropout(control_output)
        control_output2 = F.relu(self.control_gcn2(control_output1, control_matrix))
        control_confusion = self.text_graph_confusion(control_output2, sentence_output, attention_mask)
        control_confusion = self.text_graph_confusion(sentence_output, control_confusion, attention_mask)

        output_fusion = torch.cat((sentence_output, data_confusion,control_confusion), -1)
        output, _ = self.lstm(output_fusion)
        output = torch.max(output, dim=1)[0]
        prob = torch.sigmoid(self.fc(output))

        if labels is not None:
            labels = labels.float()
            loss = torch.log(prob[:, 0] + 1e-10) * labels + torch.log((1 - prob)[:, 0] + 1e-10) * (1 - labels)
            loss = -loss.mean()
            return loss, prob
        else:
            return prob
