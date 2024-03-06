class DataflowSolver:
    """
    generic dataflow problem solver with worklist algorithm
    https://en.wikipedia.org/wiki/Data-flow_analysis

    An instance of a dataflow problem includes:
    - a CFG,
    - a domain D of "dataflow facts",
    - a dataflow fact "init" (the information true at the start of the program for forward problems, or at the end of the program for backward problems),
    - an operator ⌈⌉ (used to combine incoming information from multiple predecessors),
    - for each CFG node n, a dataflow function fn : D → D (that defines the effect of executing n). 
    """

    def __init__(self, cfg, verbose):
        self.cfg = cfg
        self.verbose = verbose

    def solve(self):
        _in = {}
        out = {}
        for n in self.cfg.nodes():
            out[n] = set()  # can optimize by OUT[n] = GEN[n];

        q = list(self.cfg.nodes())
        i = 0
        while q:
            n = q.pop(0)

            # TODO: generalize to backward problems
            _in[n] = set()
            for pred in self.cfg.predecessors(n):
                _in[n] |= out[pred]

            # TODO: generalize to backward problems
            new_out_n = self.gen(n).union(_in[n].difference(self.kill(n)))

            if self.verbose >= 2:
                print(f"{i=}, {n=}, {_in=}, {out=}, {new_out_n=}")

            if out[n] != new_out_n:
                if self.verbose >= 1:
                    print(f"{i=}, {n=} changed {out[n]} -> {new_out_n}")
                out[n] = new_out_n
                for succ in self.cfg.successors(n):
                    q.append(succ)
            i += 1

        return _in, out
