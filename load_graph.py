import networkx as nx
import csv, fiona
from shapely.geometry import Polygon
from os.path import join as pjoin


def helper_flatten(iterable):
    """Helper function for loading shapefile data into shapely Polygons"""
    return iterable if type(iterable[0]) is tuple else helper_flatten(iterable[0])


def load_raw_data(pa_data, shp_file):
    """Load raw data on Pennsylvania precincts from Duke data and shp file"""
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
    geoids = {}
    with open(pjoin(pa_data, "GEOID.txt")) as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            fid_from_geoid[row[1].strip()] = int(row[0])
            geoids[int(row[0])] = row[1].strip()

    # load shapes
    geometries = {}
    with fiona.open(shp_file) as f:
        for row in f:
            geoid = row["properties"]["GEOID10"]
            fid = fid_from_geoid[geoid]
            # why this is  nested like this...
            geometries[fid] = Polygon(helper_flatten(row["geometry"]["coordinates"]))
    return areas, populations, neighbors, edge_lengths, geoids, geometries


def load_graph(pa_data, shp_file):
    areas, populations, neighbors, edge_lengths, geoids, geometries = load_raw_data(
        pa_data, shp_file
    )
    """
    """
    # create node attribute dicts
    fids = []
    dictys = []
    for fid in areas.keys():
        dicty = {}
        dicty["population"] = populations[fid]
        dicty["area"] = areas[fid]
        dicty["geometry"] = geometries[fid]
        dicty["GEOID"] = geoids[fid]
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

def load_districts(G, path_to_shp, node_attr_name, min_overlap=0.9):
    """
    Loads a shapefile of districts and assigns a district label to each precinct node in G
    :param G: networkx Graph with precinct nodes. Precinct nodes must have a 'geometry' attribute
        containing a shapely Polygon
    :param path_to_shp: Path to shp file of a districting plan
    :param node_attr_name: Name for district attribute in Graph node
    :param min_overlap: Minimum fraction of precinct Polygon that intersects with district polygon
        to consider contained within (no warning or count will be provided)
    """
    # load shapefile into dict
    with fiona.open(path_to_shp) as f:
        districts = {
            i: Polygon(helper_flatten(row["geometry"]["coordinates"]))
            for i, row in enumerate(f, start=1)
        }

    # map each district to a node
    for node in G.nodes:
        p_poly = G.nodes[node]["geometry"]
        districted = False
        d_cands = {}
        for district, d_poly in districts.items():
            # is precinct contained within district polygon?
            if p_poly.within(d_poly):
                G.nodes[node][node_attr_name] = district
                districted = True
                break
            # does precinct intersect district polygon?
            if min_overlap and p_poly.intersects(d_poly):
                area = p_poly.intersection(d_poly).area
                d_cands[district] = area
                # if more than 90% is contained within a district, let's call it rounding error
                if (area / p_poly.area) > min_overlap:
                    G.nodes[node][node_attr_name] = district
                    districted = True
                    break

        # if we have not mapped this precinct to a district
        if not districted:
            if len(d_cands) == 1:
                # this doesn't occur when the 90% rule is added
                G.nodes[node][node_attr_name] = list(d_cands.keys())[0]
            elif len(d_cands) > 1:
                print(f"Precinct with fid {node} is split between {n} districts:")
                G.nodes[node][node_attr_name] = max(d_cands.keys(), key=d_cands.get)
                for area in d_cands.values():
                    print(f"{area/p_poly.area*100}%")
            else:
                print(f"{node} is not contained within any district!")
    return districts



path_to_pa = "../PennsylvaniaRedistrictingData/ExtractedData"
path_to_shp = "../2011 Voting District Boundary Shapefiles/VTDS.shp"
path_to_initial_districts = (
    "../PA-Congressional-Districts-2011/BlockLevelFinalCongressionalPlan21Dec2011.shp"
)

G = load_graph(path_to_pa, path_to_shp)
districts = load_districts(G, path_to_initial_districts, "district")
