import networkx as nx
import csv, fiona
from os.path import join as pjoin

def load_raw_data(pa_data, shp_file):
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

    # load GEOIDs for referencing with Shapefiles
    fid_from_geoid = {}
    with open(pjoin(pa_data, "GEOID.txt")) as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            fid_from_geoid[row[1].strip()] = int(row[0])

    # load shapes
    geometries = {}
    with fiona.open(shp_file) as f:
        i = 0
        for row in f:
            try:
                geoid = row['properties']['GEOID10']
                fid = fid_from_geoid[geoid]
                geometries[fid] = row['geometry']
            except KeyError:
                if i == 0:
                    print(row)
                i += 1

    return areas, populations, neighbors, edge_lengths, geometries

def load_graph(pa_data, shp_file):
    areas, populations, neighbors, edge_lengths, geometries = load_raw_data(pa_data, shp_file)
    # create node attribute dicts
    fids = []
    dictys = []
    for fid in areas.keys():
        dicty = {}
        dicty['population'] = populations[fid]
        dicty['area'] = areas[fid]
        dicty['geometry'] = geometries[fid]
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
    return G

path_to_pa = "../PennsylvaniaRedistrictingData/ExtractedData"
path_to_shp = "../2011 Voting District Boundary Shapefiles/VTDS.shp"

G = load_graph(path_to_pa, path_to_shp)
