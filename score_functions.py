def calculate_area(Graph, district):
	"""
        Parameters
        ----------
        Graph : Graph
        district : int
            district number 
    """

    total_area = 0 
    for i in G.nodes:
        if G.nodes[i]['district'] == 1:
            total_area += G.nodes[i]['area']

    return total_area

 def calculate_perimeter(Graph, district):
 	"""
        Parameters
        ----------
        Graph : Graph
        district : int
            district number 
    """

    visited = set()
    total_perimeter = 0
    for i in G.nodes:
        if G.nodes[i]['district'] == district:
            for neighbor in G[i]:
                if ((G.nodes[neighbor]['district'] != district) 
                    and ((i, neighbor) not in visited)):

                    total_perimeter += G[i][neighbor]['length']
    
    return total_perimeter

 def isoperimetric_score(G, districts):
 	"""
        Parameters
        ----------
        Graph : Graph
        district : list of ints
            list of all district numbers
    """

    score = 0
    for i in districts:
        score += pow(calculate_perimeter(G,i),2) / calculate_area(G,i)
    
    return score


def population_score(G, districts, population_total):
	"""
        Parameters
        ----------
        Graph : Graph
        district : list of ints
            list of all district numbers
        population_total: int
        	total population
    """
    population_ideal = population_total / len(districts)
    score = 0
    pops = {i:0 for i in districts}

    
    for i in pops.values():
        score += pow(i/population_ideal - 1, 2)
    
    return pow(score, 1/2)