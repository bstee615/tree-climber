set -e
bun build src/index.tsx --outdir=public --target=browser --minify
cp src/index.html public/index.html