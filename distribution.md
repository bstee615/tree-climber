# Distribution guide for devs

To publish to PyPi, I used Hatchling, following the official Guide: https://packaging.python.org/en/latest/tutorials/packaging-projects/

To publish a new TestPyPi build:

```
python -m build
python -m twine upload --repository testpypi dist/*
```

To test the pip install locally:

```
# <from root>
rootdir="$(pwd)"
tmpdir="$(mktemp -d)"
pushd "$tmpdir"
cp $rootdir/main.py .
python -m virtualenv testvenv
source testvenv/bin/activate
pip install $rootdir
pip install -r $rootdir/requirements.txt
git clone https://github.com/tree-sitter/tree-sitter-c.git lib/tree-sitter-c
python main.py $rootdir/tests/data/example.c --draw_ast --draw_cfg --draw_duc
popd
rm -rf "$tmpdir"
```
