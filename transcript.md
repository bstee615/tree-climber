# generate dots

```
~/code/tree-climber whole_project*
❯ ~/software/joern/joern-cli/joern-parse 1_complete/
Parsing code at: 1_complete/ - language: `NEWC`
[+] Running language frontend
[+] Applying default overlays
Successfully wrote graph to: /home/benjis/code/tree-climber/cpg.bin
To load the graph, type `joern /home/benjis/code/tree-climber/cpg.bin`

~/code/tree-climber whole_project* 6s
❯ ~/software/joern/joern-cli/joern-export --repr cpg14 --out 1_complete/out       

~/code/tree-climber whole_project*
❯ ~/software/joern/joern-cli/joern-parse 2_openmp/                        
Parsing code at: 2_openmp/ - language: `NEWC`
[+] Running language frontend
[+] Applying default overlays
Successfully wrote graph to: /home/benjis/code/tree-climber/cpg.bin
To load the graph, type `joern /home/benjis/code/tree-climber/cpg.bin`

~/code/tree-climber whole_project*
❯ ~/software/joern/joern-cli/joern-export --repr cpg14 --out 2_openmp/out  

~/code/tree-climber whole_project*
❯ ~/software/joern/joern-cli/joern-parse 3_incomplete/                   
Parsing code at: 3_incomplete/ - language: `NEWC`
[+] Running language frontend
[+] Applying default overlays
Successfully wrote graph to: /home/benjis/code/tree-climber/cpg.bin
To load the graph, type `joern /home/benjis/code/tree-climber/cpg.bin`

~/code/tree-climber whole_project*
❯ ~/software/joern/joern-cli/joern-export --repr cpg14 --out 3_incomplete/out
```


# convert to png

```
~/code/tree-climber whole_project*
❯ dot -Tpng {1,2,3}_*/main-cpg.dot -O
```
