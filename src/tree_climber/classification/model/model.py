import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn.conv import RGCNConv
from torch_geometric.nn import global_mean_pool, global_max_pool

torch.manual_seed(2020)

gated_graph_conv_args = {
    "out_channels": 256,    # hidden vector size after GNN
    "num_layers": 6,        #  (Message Passing Steps)
    "num_relations": 4      # Compulsory: 4 edge types (CFG, DFG, AST, Link)
}

emb_size = 768
conv_args = {
    "conv1d_1": {"in_channels": 1, "out_channels": 16, "kernel_size": 3, "stride": 1},
    "conv1d_2": {"in_channels": 16, "out_channels": 16, "kernel_size": 1, "stride": 1},
    "maxpool1d_1": {"kernel_size": 3, "stride": 1},
    "maxpool1d_2": {"kernel_size": 1, "stride": 1}
}

def get_conv_mp_out_size(in_size, last_layer, mps):
    size = in_size
    for mp in mps:
        size = round((size - mp["kernel_size"]) / mp["stride"] + 1)
    size = size + 1 if size % 2 != 0 else size
    return int(size * last_layer["out_channels"])

class Conv(nn.Module):
    def __init__(self, conv1d_1, conv1d_2, maxpool1d_1, maxpool1d_2, fc_1_size, fc_2_size):
        super(Conv, self).__init__()
        self.conv1d_1_args = conv1d_1
        self.conv1d_1 = nn.Conv1d(**conv1d_1)
        self.conv1d_2 = nn.Conv1d(**conv1d_2)

        fc1_size = get_conv_mp_out_size(fc_1_size, conv1d_2, [maxpool1d_1, maxpool1d_2])
        fc2_size = get_conv_mp_out_size(fc_2_size, conv1d_2, [maxpool1d_1, maxpool1d_2])

        self.fc1 = nn.Linear(fc1_size, 1)
        self.fc2 = nn.Linear(fc2_size, 1)
        self.drop = nn.Dropout(p=0.2)
        self.mp_1 = nn.MaxPool1d(**maxpool1d_1)
        self.mp_2 = nn.MaxPool1d(**maxpool1d_2)

    def forward(self, hidden, x):
        # hidden: output of GNN, x: embedding from CodeBERT
        concat = torch.cat([hidden, x], 1)
        concat_size = hidden.shape[1] + x.shape[1]
        
        # Reshape Conv1d: (batch_size, channels, length)
        # Consider number of nodes is the length of the squence in batch
        concat = concat.view(-1, self.conv1d_1_args["in_channels"], concat_size)
        Z = self.mp_1(F.relu(self.conv1d_1(concat)))
        Z = self.mp_2(self.conv1d_2(Z))

        hidden_view = hidden.view(-1, self.conv1d_1_args["in_channels"], hidden.shape[1])
        Y = self.mp_1(F.relu(self.conv1d_1(hidden_view)))
        Y = self.mp_2(self.conv1d_2(Y))

        Z = Z.view(Z.size(0), -1)
        Y = Y.view(Y.size(0), -1)
        
        res = self.fc1(Z) * self.fc2(Y)
        res = self.drop(res)
        return torch.sigmoid(torch.flatten(res))

class Net(nn.Module):
    def __init__(self, gated_graph_conv_args, conv_args, emb_size, device):
        super(Net, self).__init__()
        
        # gated_graph_conv_args['num_relation] = 4
        # (0: CFG, 1: DFG, 2: AST, 3: Link)
        in_channels = emb_size
        out_channels = gated_graph_conv_args["out_channels"]
        num_relations = gated_graph_conv_args["num_relations"]
        num_layers = gated_graph_conv_args["num_layers"]
        
        # Use RGCN layers for multi-relational graphs
        self.convs = nn.ModuleList()
        for i in range(num_layers):
            if i == 0:
                self.convs.append(RGCNConv(in_channels, out_channels, num_relations))
            else:
                self.convs.append(RGCNConv(out_channels, out_channels, num_relations))
        
        self.convs = self.convs.to(device)
        
        # Graph-level classifier
        # After pooling we get: [batch_size, out_channels * 2] (mean + max pooling)
        self.fc1 = nn.Linear(out_channels * 2, 128).to(device)
        self.fc2 = nn.Linear(128, 1).to(device)
        self.dropout = nn.Dropout(p=0.2).to(device)

    def forward(self, data):
        # x: [num_nodes, 768] (CodeBERT embeddings)
        # edge_index: [2, num_edges]
        # edge_attr: [num_edges] (Loại cạnh)
        # batch: [num_nodes] (Chỉ số graph cho mỗi node)
        x, edge_index, edge_attr, batch = data.x, data.edge_index, data.edge_attr, data.batch
        
        # Handle graphs with no edges (empty edge_index)
        if edge_index.numel() == 0:
            # Create properly shaped empty edge_index [2, 0] for graphs without edges
            edge_index = edge_index.new_empty((2, 0))
            edge_attr = edge_attr.new_empty((0,))
        
        # Apply RGCN layers
        h = x
        for conv in self.convs:
            h = F.relu(conv(h, edge_index, edge_attr))
        
        # Graph-level pooling: aggregate node embeddings to graph embeddings
        # h: [num_nodes, out_channels] -> graph_emb: [batch_size, out_channels * 2]
        h_mean = global_mean_pool(h, batch)  # [batch_size, out_channels]
        h_max = global_max_pool(h, batch)    # [batch_size, out_channels]
        graph_emb = torch.cat([h_mean, h_max], dim=1)  # [batch_size, out_channels * 2]
        
        # Graph classification
        out = F.relu(self.fc1(graph_emb))
        out = self.dropout(out)
        out = self.fc2(out)
        
        return torch.sigmoid(out.squeeze(-1))  # [batch_size]

    def save(self, path):
        torch.save(self.state_dict(), path)

    def load(self, path):
        self.load_state_dict(torch.load(path, weights_only=True))