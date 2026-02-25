dir=$(dirname "$0")
cd "$dir" || exit
cd ../ || exit

pyside6-rcc resources.qrc -o src/count_anywhere/rc_resources.py
