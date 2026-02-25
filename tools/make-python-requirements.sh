dir=$(dirname "$0")
cd "$dir" || exit
cd ../ || exit

uv pip freeze > src/count_anywhere/requirements.txt