#%%
import traceback
import pandas as pd

df = pd.read_csv("/home/benjis/data/MSR_data_cleaned.csv")
df

#%%
from tree_climber.cpg import make_code_cpg
import networkx as nx
import json
from pathlib import Path
import traceback

dst_root = Path("output-bigvul")

def parse_to_cpg(row):
    try:
        cpg = make_code_cpg(row["func_before"])
        cpg_json = nx.node_link_data(cpg)
        return cpg_json, f"{row.name}.cpg.json"
    except Exception:
        print("error processing row:", row, traceback.format_exc(), sep="\n")
df.iloc[:5].apply(parse_to_cpg, axis=1)

#%%
# parse_to_cpg(df.loc[25])
# parse_to_cpg(df.loc[666])

#%%
import tqdm
# tqdm.pandas()
# it = df.apply(parse_to_cpg, axis=1)
# from pandas_multiprocess import multi_process
# it = multi_process(parse_to_cpg, df[["func_before"]], 6)
# pbar = tqdm.tqdm(it)
total = 0
warnings = 0
errors = 0
# for t in it:
for i, row in df.iterrows():
    t = parse_to_cpg(row)
    total += 1
    if t is None:
        errors += 1
    else:
        cpg_json, dst_filename = t
        with open(dst_root/dst_filename, "w") as f:
            json.dump(cpg_json, f)
    # pbar.set_postfix({"error": errors, "warning": warnings, "total": total,})
    print({"error": errors, "warning": warnings, "total": total,})
print("finished with", errors, "errors out of", all, "examples")
