import torch
from transformers import AutoTokenizer, AutoModel
from torch_geometric.data import Data

EDGE_ATTR = {
    "CFG" : 0,
    "DFG" : 1,
    "AST_CHILD" : 2,
    "CFG_TO_AST": 3
}

class FullCPGEmbedder:
    def __init__(self, model_name="microsoft/codebert-base", device=None):
        self.device = device if device else torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device)
        self.model.eval()

    def get_embedding(self, text):
        with torch.no_grad():
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=64).to(self.device)
            outputs = self.model(**inputs)
            return outputs.last_hidden_state[:, 0, :].squeeze().cpu()

    def transform(self, cpg_json):
        cfg_nodes = cpg_json['cfg_nodes']
        ast_nodes = cpg_json['ast_nodes']
        
        # Create list of nodes (CFG + AST)
        all_node_ids = list(cfg_nodes.keys()) + list(ast_nodes.keys())
        node_mapping = {node_id: i for i, node_id in enumerate(all_node_ids)}
        
        node_features = []
        
        # Embed CFG Nodes
        for nid in cfg_nodes.keys():
            text = f"CFG_{cfg_nodes[nid]['node_type']}: {cfg_nodes[nid]['source_text']}"
            node_features.append(self.get_embedding(text))
            
        # Embed AST Nodes
        for nid in ast_nodes.keys():

            text = f"AST_{ast_nodes[nid]['node_type']}: {ast_nodes[nid]['text']}"
            node_features.append(self.get_embedding(text))

        x = torch.stack(node_features)

        # 4. Edges (Edge Index & Edge Attr)
        edge_index = []
        edge_attr = [] 

        # CFG edge
        for nid, ndata in cfg_nodes.items():
            u = node_mapping[nid]
            for succ in ndata['successors']:
                if str(succ) in node_mapping:
                    edge_index.append([u, node_mapping[str(succ)]])
                    edge_attr.append(EDGE_ATTR['CFG'])

        # DFG edge
        for dfg in cpg_json['dfg_edges']:
            u, v = str(dfg['source_id']), str(dfg['target_id'])
            if u in node_mapping and v in node_mapping:
                edge_index.append([node_mapping[u], node_mapping[v]])
                edge_attr.append(EDGE_ATTR['DFG'])

        # AST Edge
        for nid, ndata in ast_nodes.items():
            u = node_mapping[nid]
            for child_id in ndata['children_ids']:
                if child_id in node_mapping:
                    edge_index.append([u, node_mapping[child_id]])
                    edge_attr.append(EDGE_ATTR['AST_CHILD'])

        # CFG Node to AST Root
        for nid, ndata in cfg_nodes.items():
            if ndata['ast_root_id'] in node_mapping:
                u = node_mapping[nid]
                v = node_mapping[ndata['ast_root_id']]
                edge_index.append([u, v])
                edge_attr.append(EDGE_ATTR['CFG_TO_AST'])

        edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
        edge_attr = torch.tensor(edge_attr, dtype=torch.long)

        return Data(x=x, edge_index=edge_index, edge_attr=edge_attr)