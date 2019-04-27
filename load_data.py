import networkx as nx
import csv
from os.path import join as pjoin

def load_raw_data(pa_data):
    # load adjacency
    neighbors = {}
    with open(pjoin(pa_data, "NEIGHBOR_LIST.txt")) as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            neighbors[int(row[0])] = [int(r) for r in row[1:]]

    # load border lengths
    edge_lengths = {}
    with open(pjoin(pa_data, "BORDER_LENGTHS.txt")) as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if int(row[1]) in edge_lengths:
                edge_lengths[int(row[1])][int(row[0])] = float(row[2])
            else:
                edge_lengths[int(row[1])] = {int(row[0]): float(row[2])}

    # load precinct populations
    populations = {}
    with open(pjoin(pa_data, "POPULATION.txt")) as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            populations[int(row[0])] = int(row[1])

    # load precinct areas
    areas = {}
    with open(pjoin(pa_data, "AREAS.txt")) as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            areas[int(row[0])] = float(row[1])
    return areas, populations, neighbors, edge_lengths


areas, populations, neighbors, edge_lengths = load_raw_data("../PennsylvaniaRedistrictingData/ExtractedData")

# create node attribute dicts
fids = []
dictys = []
for fid in areas.keys():
    dicty = {}
    dicty['population'] = populations[fid]
    dicty['area'] = areas[fid]
    dicty['perimeter'] = sum(edge_lengths[fid].values())
    fids.append(fid)
    dictys.append(dicty)

# initialize graph and add nodes
G = nx.Graph()
G.add_nodes_from(zip(fids, dictys))

# add edges with length attribute
for fid, ns in neighbors.items():
    for n in ns:
        if n == -1:
            continue
        border_length = edge_lengths[fid][n]
        G.add_edge(fid, n, length=border_length)
