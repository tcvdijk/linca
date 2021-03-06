"""Usage: linca.py [--ipe] [--scale=<s>] [--straightness=<s>]
          linca.py --help

Draws a linear cartogram.

Options:
  --ipe               Write IPE file.
  -s --scale=<s>      Scale all coordinates by a constant factor. [Default: 1]
  --straightness=<s>  Focus on direction rather than length. [Default: 10]
  --help              Display this message. 
"""
from docopt import docopt
if __name__ == '__main__': arguments = docopt(__doc__)

from math import sqrt
import numpy as np
from scipy.sparse import csr_matrix as sparse_matrix
from scipy.sparse.linalg import spsolve as sparse_solve

# read input
edges = []
from sys import stdin
for line in stdin:
  tokens = line.split()
  if len(tokens)>=4: edges.append((
    int(tokens[0]),
    int(tokens[1]),
    float(tokens[2]),
    float(tokens[3])
    ))

# rename vertices and set n
new_name = {}
old_name = {}
fresh = 0
for e in edges:
  if not e[0] in new_name:
    new_name[e[0]] = fresh
    old_name[fresh] = e[0]
    fresh = fresh + 1
  if not e[1] in new_name:
    new_name[e[1]] = fresh
    old_name[fresh] = e[1]
    fresh = fresh + 1
n = fresh
edges = [ (new_name[e[0]], new_name[e[1]], e[2], e[3]) for e in edges ]

## Solve

# Construct the least-squares formulation in a sparse matrix `A` and right-hand side `b`.
# In order to determine the system (as long as the graph is connected), we also fix the coordinate of vertex "0" to (0,0).

straightness = float(arguments['--straightness'])

# set up matrix through lists of rows, columns, and values
num_cols = 2*n
num_rows = 2*len(edges) + 2
def x_var(i): return 2*i
def y_var(i): return 2*i + 1
rows = [ i for i in range(2*len(edges)) for _ in range(4)] + [num_rows-2,num_rows-1]
cols = [ f(e) for e in edges for f in (lambda e: x_var(e[0]),
                                       lambda e: x_var(e[1]),
                                       lambda e: y_var(e[0]),
                                       lambda e: y_var(e[1]),
                                       lambda e: x_var(e[0]),
                                       lambda e: x_var(e[1]),
                                       lambda e: y_var(e[0]),
                                       lambda e: y_var(e[1]))] + [0,1]
vals = [ val for e in edges for val in (-e[2], e[2], -e[3], e[3],
                                         straightness*e[3],-straightness*e[3], -straightness*e[2], straightness*e[2])] + [1,1]
A = sparse_matrix((vals,(rows,cols)),shape=(num_rows,num_cols))

b = [ val for e in edges for val in (sqrt(e[2]**2+e[3]**2),0) ] + [0,0]

# Solve least squares problem by solving Gauß normal form: `A^T A positions = A^T b`
AtA = A.transpose()*A
Atb = A.transpose()*b
positions = sparse_solve(AtA,Atb)

# read the solution and apply scale
scale = float(arguments['--scale'])
pos = [ (scale*positions[x_var(i)],scale*positions[y_var(i)]) for i in range(n) ]

## Output
if( arguments['--ipe']):
  from miniipe import Document, polyline
  doc = Document()
  doc.import_stylefile()
  doc.add_layer('edges')
  doc.add_layer('nodes')
  doc.add_layer('labels')
  for e in edges:
    doc.path( polyline([ pos[e[0]], pos[e[1]] ]), layer='edges' )
  for i, p in enumerate(pos):
    doc.use( pos=p, layer='nodes' )
    doc.text( str(old_name[i]), pos=p, layer='labels')

  print(doc.tostring())

else: # not ipe
  for i, p in enumerate(pos):
    print( old_name[i], p[0], p[1] )
