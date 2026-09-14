dir=$(dirname "$0")
cd "$dir" || exit
cd ../src/count_anywhere || exit

pyside6-rcc resources.qrc -o rc_resources.py
