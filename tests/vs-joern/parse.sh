if [ $1 == "--joern" ]
then
rm -r workspace
time ./joern/joern-cli/joern --script $(dirname $0)/get_func_graph.scala --params filename=$2
elif [ $1 == "--tree-sitter" ]
then
time python main.py $2 --cfg --file
fi