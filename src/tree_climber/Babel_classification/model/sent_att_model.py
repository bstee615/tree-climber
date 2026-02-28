import torch
import torch.nn as nn
import torch.nn.functional as F


class SentAttNet(nn.Module):
    def __init__(self,args):
        super(SentAttNet, self).__init__()

        self.lstm = nn.LSTM(input_size=args.sentence_hidden, hidden_size=args.sentence_hidden)

        # self.attn_w = nn.Linear(in_features=100, out_features=100)
        # self.attn_v = nn.Linear(in_features=100, out_features=1, bias=False)
        self.attn_w = nn.Linear(in_features=args.sentence_hidden, out_features=args.sentence_hidden)
        self.attn_v = nn.Linear(in_features=args.sentence_hidden, out_features=1, bias=False)

        self.fc = nn.Linear(in_features=args.sentence_hidden, out_features=1)

    def forward(self, input_,labels):
        # shape: seq_num * batch_size * hidden_size

        output, _ = self.lstm(input_)  # shape: seq_num * batch_size * hidden_size

        weight = torch.tanh(self.attn_w(output))  # shape: seq_num * batch_size * hidden_size
        weight = self.attn_v(weight)  # shape: seq_num * batch_size * 1
        weight = F.softmax(weight, 0)  # shape: seq_num * batch_size * 1
        output = weight * output  # shape: seq_num * batch_size * hidden_size
        output = output.sum(0)  # shape: batch_size * hidden_size

        prob = torch.sigmoid(self.fc(output))  # shape: batch_size * 1

        if labels is not None:
            labels = labels.float()
            loss = torch.log(prob[:, 0] + 1e-10) * labels + torch.log((1 - prob)[:, 0] + 1e-10) * (1 - labels)
            loss = -loss.mean()
            return loss, prob
        else:
            return prob


if __name__ == "__main__":
    abc = SentAttNet()
