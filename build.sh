jupyter-book build jb/
cp CNAME jb/_build/html/
ghp-import -n -p -f jb/_build/html
