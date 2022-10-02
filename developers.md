# Development guide

## Development environment

To setup my dev environment:

```
export PYTHONPATH="$PWD:$PYTHONPATH"
python -m tree_climber tests/data/example.c --draw_ast --draw_cfg --draw_duc
```

## Distribution

To publish to PyPi, I used Hatchling, following the official Guide: https://packaging.python.org/en/latest/tutorials/packaging-projects/

Install dependencies:

```
pip install twine build
```

To publish a new TestPyPi build:

```
python -m build
python -m twine upload --repository testpypi dist/*
```

To publish a new PyPi build:

```
python -m build
python -m twine upload dist/*
```

To test the pip install locally:

```
# <from root>
rootdir="$(pwd)"
tmpdir="$(mktemp -d)"
pushd "$tmpdir"
python -m virtualenv testvenv
source testvenv/bin/activate
pip install $rootdir
python -m tree_climber $rootdir/tests/data/example.c --draw_ast --draw_cfg --draw_duc
popd
rm -rf "$tmpdir"
```

Expected output:
```
/tmp/tmp.8gF7npirpv ~/code/tree_climber
created virtual environment CPython3.10.7.final.0-64 in 116ms
  creator CPython3Posix(dest=/tmp/tmp.8gF7npirpv/testvenv, clear=False, no_vcs_ignore=False, global=False)
  seeder FromAppData(download=False, pip=bundle, setuptools=bundle, wheel=bundle, via=copy, app_data_dir=/home/benjis/.local/share/virtualenv)
    added seed packages: pip==22.2.2, setuptools==65.3.0, wheel==0.37.1
  activators BashActivator,CShellActivator,FishActivator,NushellActivator,PowerShellActivator,PythonActivator
Processing /home/benjis/code/tree_climber
  Installing build dependencies ... done
  Getting requirements to build wheel ... done
  Preparing metadata (pyproject.toml) ... done
Collecting pygraphviz
  Using cached pygraphviz-1.10-cp310-cp310-linux_x86_64.whl
Collecting networkx
  Using cached networkx-2.8.6-py3-none-any.whl (2.0 MB)
Collecting tree-sitter
  Using cached tree_sitter-0.20.1-cp310-cp310-linux_x86_64.whl
Collecting matplotlib
  Using cached matplotlib-3.6.0-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (11.8 MB)
Collecting gitpython
  Using cached GitPython-3.1.27-py3-none-any.whl (181 kB)
Collecting gitdb<5,>=4.0.1
  Using cached gitdb-4.0.9-py3-none-any.whl (63 kB)
Collecting cycler>=0.10
  Using cached cycler-0.11.0-py3-none-any.whl (6.4 kB)
Collecting fonttools>=4.22.0
  Using cached fonttools-4.37.3-py3-none-any.whl (959 kB)
Collecting pyparsing>=2.2.1
  Using cached pyparsing-3.0.9-py3-none-any.whl (98 kB)
Collecting python-dateutil>=2.7
  Using cached python_dateutil-2.8.2-py2.py3-none-any.whl (247 kB)
Collecting kiwisolver>=1.0.1
  Using cached kiwisolver-1.4.4-cp310-cp310-manylinux_2_12_x86_64.manylinux2010_x86_64.whl (1.6 MB)
Collecting packaging>=20.0
  Using cached packaging-21.3-py3-none-any.whl (40 kB)
Collecting contourpy>=1.0.1
  Using cached contourpy-1.0.5-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (295 kB)
Collecting pillow>=6.2.0
  Using cached Pillow-9.2.0-cp310-cp310-manylinux_2_28_x86_64.whl (3.2 MB)
Collecting numpy>=1.19
  Using cached numpy-1.23.3-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (17.1 MB)
Collecting smmap<6,>=3.0.1
  Using cached smmap-5.0.0-py3-none-any.whl (24 kB)
Collecting six>=1.5
  Using cached six-1.16.0-py2.py3-none-any.whl (11 kB)
Building wheels for collected packages: tree_climber
  Building wheel for tree_climber (pyproject.toml) ... done
  Created wheel for tree_climber: filename=tree_climber-0.0.2-py3-none-any.whl size=17567 sha256=e8ae863d0adc686e3d341b6a74c833c5bcf5e8ddd7090324baac3c698dd30073
  Stored in directory: /tmp/pip-ephem-wheel-cache-7zaviu7b/wheels/ed/02/b3/ae0519f966dc654260892ca550440ddd53f4d4ef08e2a51297
Successfully built tree_climber
Installing collected packages: tree-sitter, smmap, six, pyparsing, pygraphviz, pillow, numpy, networkx, kiwisolver, fonttools, cycler, python-dateutil, packaging, gitdb, contourpy, matplotlib, gitpython, tree_climber
Successfully installed contourpy-1.0.5 cycler-0.11.0 fonttools-4.37.3 gitdb-4.0.9 gitpython-3.1.27 kiwisolver-1.4.4 matplotlib-3.6.0 networkx-2.8.6 numpy-1.23.3 packaging-21.3 pillow-9.2.0 pygraphviz-1.10 pyparsing-3.0.9 python-dateutil-2.8.2 six-1.16.0 smmap-5.0.0 tree-sitter-0.20.1 tree_climber-0.0.2
parsing 1 files [PosixPath('/home/benjis/code/tree_climber/tests/data/example.c')]
successfully parsed /home/benjis/code/tree_climber/tests/data/example.c
~/code/tree_climber
```
