# Compiler Design CS335
# Group 6
## Milestone 3:

#### Parser :


We implemented the parser for our compiler. We have LR-Parser automation in `src/graph.pdf` which we got by using `src/graph.py`   and `src/parser.out`. 

The grammer in `parser.out` is generated from `parser.py` using  python `ply.yacc` 


The procedure to run the program is as follows:

```
cd /src
make
cd ..
./bin/parser ./test/test.cpp
```
