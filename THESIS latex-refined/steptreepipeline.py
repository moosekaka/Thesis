"""
    This module returns edgeslist,nodelist and graph objects from VTK files
"""
import vtk
import glob
import math
import numpy as np
import networkx as nx
import cPickle as pickle
import os


def disteuc(pt1, pt2):
    """returns euclidian dist btw pt1 and pt2
    """
    return math.sqrt(vtk.vtkMath.Distance2BetweenPoints(pt1, pt2))

# pylint: disable=C0103
fileloc = os.getcwd()+'\\'+'Norm*vtk'
fileglb = glob.glob(fileloc)
lab = fileglb[0].rsplit('\\', 1)[1][5:8]
print 'creating edge node lists for %s' % lab
print'number of files = %3d' % len(fileglb)

#               INITIALIZE
nnodes = 0
G = []  # list container for graphs of each cell
EDL = []
X = []
Y = []
files = fileglb
reader = vtk.vtkPolyDataReader()
# pylint: enable=C0103

for a in range(len(files)):
    # for a in range(len(files)):
    reader.SetFileName(files[a])
    reader.Update()
    data = reader.GetOutput()
    scalars = data.GetPointData().GetScalars("DY_raw")
    num_lines = data.GetNumberOfLines()
    fname = files[a].rsplit('\\', 1)[1][5:-13]
    G.append(nx.MultiGraph(cell=fname))

#   for every line in each cell, starting from the highest index compare the
#   end points of that line with another line of the next lower index, if
#   pythagorean dist==0, label it a node and add it to the graph object G[a]
    for i in range(num_lines-1, -1, -1):
        line1 = data.GetCell(i).GetPoints()
        np_pointsi = line1.GetNumberOfPoints()
        pointID = data.GetCell(i).GetPointIds()
        exist1 = exist2 = False
        r1 = line1.GetPoint(0)
        r2 = line1.GetPoint(np_pointsi-1)
        inten1 = scalars.GetTuple1(pointID.GetId(0))
        inten2 = scalars.GetTuple1(pointID.GetId(np_pointsi-1))

        for j in range(i+1):
            line2 = data.GetCell(j).GetPoints()
            np_pointsj = line2.GetNumberOfPoints()
            s1 = line2.GetPoint(0)
            s2 = line2.GetPoint(np_pointsj-1)

#    compare same line, will identify a line of zero length if true
            if i == j:
                d = disteuc(r1, r2)
                if d == 0:
                    exist2 = True
            else:
                d = disteuc(r1, s1)
                if d == 0:
                    exist1 = True
                d = disteuc(r1, s2)
                if d == 0:
                    exist1 = True
                d = disteuc(r2, s1)
                if d == 0:
                    exist2 = True
                d = disteuc(r2, s2)
                if d == 0:
                    exist2 = True
        if exist1 is False:
            G[a].add_node(nnodes, coord=r1, inten=inten1)
            nnodes += 1
        if exist2 is False:
            G[a].add_node(nnodes, coord=r2, inten=inten2)
            nnodes += 1
#    for every node identified in the list of nnodes, compare each line in
#    that cell with that node to identify the edges
    for i in range(num_lines):
        EDL = 0
        line1 = data.GetCell(i).GetPoints()
        np_pointsi = line1.GetNumberOfPoints()
        r1 = line1.GetPoint(0)
        r2 = line1.GetPoint(np_pointsi-1)
        pointID = data.GetCell(i).GetPointIds()
        mdpt = (
            (r1[0]+r2[0]) / 2, (r1[1]+r2[1]) / 2, (r1[2]+r2[2]) / 2)

#   for each line sum thru the line the distance between points to
#   get edge len EDL
        EDL = np.sum(
            [disteuc(line1.GetPoint(pid), line1.GetPoint(pid-1))
             for pid in range(1, np_pointsi)])

        for j in G[a].nodes_iter():
            nod = G[a].node[j]
            r = nod['coord']
            d = disteuc(r, r1)
            if d == 0:
                n1 = j
            d = disteuc(r, r2)
            if d == 0:
                n2 = j
        G[a].add_edge(
            n1, n2, weight=EDL, cellID=i, midpoint=mdpt)
			
#           OUTPUT number of nodes,edges, and total Length
    deg = nx.degree(G[a])
    for i in G[a].nodes_iter():
        G[a].node[i]['degree'] = deg[i]
    x = G[a].nodes(data=True)
    X.append(x)
    y = G[a].edges(data=True)
    Y.append(y)

    OUT = (X, Y, G)
    media = os.getcwd().rsplit('\\', 1)
    FILENAME = os.path.join(os.getcwd(), '%s_grph.pkl' % media[1])
    with open(FILENAME, 'wb') as OUTPUT:
        pickle.dump(OUT, OUTPUT)
