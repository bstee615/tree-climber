import argparse
from pathlib import Path

from tree_climber.cpg_parser import CPGParser
from tree_climber.analysis.bug_detection import detect_npd


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="filename to parse")
    args = parser.parse_args()

    to_parse = Path(args.filename)
    assert to_parse.is_file(), to_parse
    print("Parsing file:", to_parse)
    try:
        cpg = CPGParser.parse(to_parse)
        detect_npd(cpg)
        CPGParser.draw(cpg)
    except Exception:
        print("Error parsing file:", to_parse)
        raise
