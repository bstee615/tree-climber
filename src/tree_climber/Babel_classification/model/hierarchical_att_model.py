import numpy as np
import torch
import torch.nn as nn
from model.word_att_model import WordAttNet
from model.sent_han_attn_confusion import SentSelHANGCNConfusion

class HierAttNet(nn.Module):
    def __init__(self, args, embed_table: np.ndarray = None):
        super(HierAttNet, self).__init__()

        self.word_att_net = WordAttNet(args, embed_table=embed_table)
        self.sent_att_net = SentSelHANGCNConfusion(args)

    def forward(self, input_, attention_mask, labels, data_matrix, control_matrix):
        # shape: batch_size, seq_num, seq_len

        output_list = torch.empty(0, )
        if torch.cuda.is_available():
            output_list = output_list.cuda()

        input_ = input_.permute(1, 0, 2)  # shape: seq_num, batch_size, seq_len
        for i in input_:
            output = self.word_att_net(i.permute(1, 0))
            output_list = torch.cat((output_list, output))
        output = self.sent_att_net(output_list, attention_mask, labels, data_matrix, control_matrix)

        return output
