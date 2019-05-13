from shapely.geometry import Polygon
import fiona
from load_graph import G, helper_flatten


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

path_to_initial_districts = (
    "../PA-Congressional-Districts-2011/BlockLevelFinalCongressionalPlan21Dec2011.shp"
)
districts = load_districts(G, path_to_initial_districts, "district")
