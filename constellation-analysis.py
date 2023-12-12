import os
import json
import math

culture_map = {}
culture_to_region = {}
star_map = {}
constellation_list = []

cutoff = 0.8

def edit_distacne(constellation1, constellation2):
    differences = 0
    for edge in constellation1["edges"]:
        if edge not in constellation2["edges"] and [edge[1], edge[0]] not in constellation2["edges"]:
            differences += 1
    differences += len(constellation2["edges"]) - (len(constellation1["edges"])-differences)
    return differences, len(constellation1["edges"]) + len(constellation2["edges"])

def similarity(constellation1, constellation2):
    distance, max_distance = edit_distacne(constellation1, constellation2)
    return 1-distance/max_distance

def get_constellation(id):
    for culture in culture_map:
        for constellation in culture_map[culture]:
            if constellation["id"] == id:
                return constellation

def get_constellation_culture(id):
    for culture in culture_map:
        for constellation in culture_map[culture]:
            if constellation["id"] == id:
                return culture_to_region[culture]

def angular_distance(starid1, starid2):
    ra1 = math.radians(float(star_map[str(starid1)]["RightAscensionDegrees"]))
    de1 = math.radians(float(star_map[str(starid1)]["DeclinationDegrees"]))
    ra2 = math.radians(float(star_map[str(starid2)]["RightAscensionDegrees"]))
    de2 = math.radians(float(star_map[str(starid2)]["DeclinationDegrees"]))
    return 2*math.asin(math.sqrt(math.sin((de2-de1)/2)**2+math.cos(de1)*math.cos(de2)*(math.sin((ra2-ra1)/2)**2)))
    # https://en.wikipedia.org/wiki/Haversine_formula

def hav(angle):
    return (1-math.cos(angle))/2
    # haversine https://en.wikipedia.org/wiki/Haversine_formula

def ahav(hav):
    return math.acos(1-2*hav)
    # inverse haversine https://en.wikipedia.org/wiki/Haversine_formula

def angle_formed(starid1, starid3, starid2):
    # A = starid1
    # B = starid2
    # C = starid3
    a = angular_distance(starid2, starid3)
    b = angular_distance(starid1, starid3)
    c = angular_distance(starid1, starid2)
    return ahav((hav(c)-hav(a-b))/(math.sin(a)*math.sin(b)))
    # law of haversines https://en.wikipedia.org/wiki/Haversine_formula

def angle_formed_in_line(staridbefore, starid1, starid3, starid2):
    first_angle = angle_formed(staridbefore, starid1, starid3)
    second_angle = angle_formed(starid1, starid3, starid2)
    determining_angle = angle_formed(staridbefore, starid1, starid2)
    if determining_angle > first_angle and determining_angle < first_angle+math.pi:
        return 2*math.pi-second_angle
    return second_angle

def get_constellation_graph(constellationid):
    constellation = get_constellation(constellationid)
    constellation_graph = {}
    for edge in constellation["edges"]:
        if edge[0] not in constellation_graph:
            constellation_graph[edge[0]] = []
        if edge[1] not in constellation_graph:
            constellation_graph[edge[1]] = []
        constellation_graph[edge[0]].append(edge[1])
        constellation_graph[edge[1]].append(edge[0])
    return constellation_graph

def get_lines(constellationid):
    constellation = get_constellation(constellationid)
    constellation_graph = get_constellation_graph(constellationid)
    lines = []
    def recurse_lines(constellation_graph, current_line):
        next_steps = False
        for next_star in constellation_graph[current_line[-1]]:
            if next_star not in current_line:
                next_steps = True
                recurse_lines(constellation_graph, current_line+[next_star])
        if not next_steps and len(current_line) >= 3:
            lines.append(current_line)
    for star in list(constellation_graph.keys()):
        recurse_lines(constellation_graph, [star])
    def sane_line(line1, line2):
        return line1 == line2 or line1 == line1[::-1]
    def subset_line(line1, line2): # if line2 subset of line1
        if len(line2) > len(line1):
            return False
        for i in range(len(line1)-len(line2)+1):
            is_subset = True
            for j in range(len(line2)):
                if line1[i+j] != line2[j]:
                    is_subset = False
            if is_subset:
                return is_subset
        return False
    i = 0
    while i < len(lines):
        current_line = lines[i]
        j = 0 
        while j < len(lines):
            if j != i and (sane_line(current_line, lines[j]) or subset_line(current_line, lines[j])):
                lines.pop(j)
            else:
                if j < i:
                    i -= 1
                j += 1
            i += 1
    return lines

def avg(list_to_average):
    if len(list_to_average) == 0:
        return None
    return sum(list_to_average)/len(list_to_average)

def safe_max(list_to_average):
    if len(list_to_average) == 0:
        return None
    return max(list_to_average)

def constellation_visual_score(constellationid):
    constellation = get_constellation(constellationid)
    lines = get_lines(constellationid)
    constellation_graph = get_constellation_graph(constellationid)
    constellation_star_scores = {}
    for edge in constellation["edges"]:
        for star in edge:
            if star not in constellation_star_scores:
                constellation_star_scores[star] = {
                    "magnitude": None, # magnitude
                    "distance": None, # distance to closest star
                    "equal_spacing": None, # minimum difference in distances between stars
                    "continuation": None, # minimum difference in neighboring angles
                    "colinearity": None # closest angle gets to 180
                }
    # magnitudes
    for star in constellation_star_scores:
        constellation_star_scores[star]["magnitude"] = star_map[str(star)]["Magnitude"]
    for star in constellation_graph:
        distances = [angular_distance(star, other_star) for other_star in constellation_graph[star]]
        distances.sort()
        constellation_star_scores[star]["distance"] = min(distances)
        if len(distances) >= 2:
            equal_spacing_list = [abs(0.5-distances[i]/(distances[i]+distances[i+1])) for i in range(len(distances)-1) if distances[i]+distances[i+1] != 0]
            if len(equal_spacing_list) != 0:
                constellation_star_scores[star]["equal_spacing"] = min(equal_spacing_list)
    for line in lines:
        for i in range(len(line)-2):
            angle = angle_formed(line[i], line[i+1], line[i+2])
            if constellation_star_scores[line[i+1]]["colinearity"] == None or abs(math.pi-angle) < constellation_star_scores[line[i+1]]["colinearity"]:
                constellation_star_scores[line[i+1]]["colinearity"] = abs(math.pi-angle)
        if len(line) > 4:
            for i in range(len(line)-3):
                first_angle = angle_formed(line[i], line[i+1], line[i+2])
                second_angle = angle_formed_in_line(line[i], line[i+1], line[i+2], line[i+3])
                angle_difference = abs(first_angle-second_angle)
                if constellation_star_scores[line[i+1]]["continuation"] == None or angle_difference < constellation_star_scores[line[i+1]]["continuation"]:
                    constellation_star_scores[line[i+1]]["continuation"] = angle_difference
                if constellation_star_scores[line[i+2]]["continuation"] == None or angle_difference < constellation_star_scores[line[i+2]]["continuation"]:
                    constellation_star_scores[line[i+2]]["continuation"] = angle_difference    
    return constellation_star_scores
 
culture_map_file = "culture_map.json"
culture_to_region_file = "culture_to_region.json"
if os.path.isfile(culture_map_file) and os.path.isfile(culture_to_region_file):
    culture_map = json.load(open(culture_map_file))
    culture_to_region = json.load(open(culture_to_region_file))
else:
    skycultures_folder = "stellarium-skycultures"
    for culture in [i for i in os.listdir(skycultures_folder) if os.path.isdir(skycultures_folder+"/"+i) and i != ".git"]:
        index = json.load(open(skycultures_folder+"/"+culture+"/index.json"))
        culture_to_region[culture] = index["region"]
        constellations = []
        for constellation in index["constellations"]:
            edges = []
            for line in constellation.get("lines", []):
                line = [x for x in line if isinstance(x,int)]
                for i in range(len(line)-1):
                    edges.append(line[i:i+2])
            if len(edges) != 0:
                constellations.append({
                    "id": constellation["id"],
                    "common_name": constellation["common_name"].get("english",""),
                    "edges": edges
                })
        culture_map[culture] = constellations
    open(culture_map_file, "w").write(json.dumps(culture_map))
    open(culture_to_region_file, "w").write(json.dumps(culture_to_region))

star_map_file = "star_map.json"
if os.path.isfile(star_map_file):
    star_map = json.load(open(star_map_file))
else:
    hipparcos_file = open("Hipparcos.tsv")
    for line in hipparcos_file:
        if len(line.strip()) != 0 and line[0] != "#":
            star = [i.strip() for i in line.split(";")]
            star_map[star[0]] = {
                "Magnitude": star[3],
                "RightAscensionDegrees": star[4],
                "DeclinationDegrees": star[5],
                "Color": star[6],
            }
    open(star_map_file, "w").write(json.dumps(star_map))

constellation_list_file = "constellation_list.json"
if os.path.isfile(constellation_list_file):
    constellation_list = json.load(open(constellation_list_file))
else:
    for culture in culture_map:
        for constellation in culture_map[culture]:
            found = False
            for constellation_listed in constellation_list:
                if similarity(constellation, constellation_listed) == 1:
                    constellation_listed["id_list"].append(constellation["id"])
                    found = True
            if not found:
                constellation_list.append({
                    "id_list": [constellation["id"]],
                    "edges": constellation["edges"]
                })
    for constellation in constellation_list:
        constellation["scores"] = constellation_visual_score(constellation["id_list"][0])
        constellation["average_magnitude"] = avg([float(constellation["scores"][i]["magnitude"]) for i in constellation["scores"]])
        constellation["average_distance"] = avg([float(constellation["scores"][i]["distance"]) for i in constellation["scores"]])
        constellation["average_equal_spacing"] = avg([float(constellation["scores"][i]["equal_spacing"]) for i in constellation["scores"] if constellation["scores"][i]["equal_spacing"] != None])
        constellation["average_continuation"] = avg([float(constellation["scores"][i]["continuation"]) for i in constellation["scores"] if constellation["scores"][i]["continuation"] != None])
        constellation["average_colinearity"] = avg([float(constellation["scores"][i]["colinearity"]) for i in constellation["scores"] if constellation["scores"][i]["colinearity"] != None])
        constellation["max_magnitude"] = safe_max([float(constellation["scores"][i]["magnitude"]) for i in constellation["scores"]])
        constellation["max_distance"] = safe_max([float(constellation["scores"][i]["distance"]) for i in constellation["scores"]])
        constellation["max_equal_spacing"] = safe_max([float(constellation["scores"][i]["equal_spacing"]) for i in constellation["scores"] if constellation["scores"][i]["equal_spacing"] != None])
        constellation["max_continuation"] = safe_max([float(constellation["scores"][i]["continuation"]) for i in constellation["scores"] if constellation["scores"][i]["continuation"] != None])
        constellation["max_colinearity"] = safe_max([float(constellation["scores"][i]["colinearity"]) for i in constellation["scores"] if constellation["scores"][i]["colinearity"] != None])
    open(constellation_list_file, "w").write(json.dumps(constellation_list))

constellations_ranked_by_proflicness_file = "constelation_proflicness.json"
if os.path.isfile(constellations_ranked_by_proflicness_file):
    constellations_ranked_by_proflicness = json.load(open(constellations_ranked_by_proflicness_file))
else:
    constellations_ranked_by_proflicness = []
    for constellation in constellation_list:
        region_to_profilication = {}
        def add_to_region_map(id, similarity):
            constellation_culture = get_constellation_culture(id)
            region_to_profilication[constellation_culture] = region_to_profilication.get(constellation_culture, 0) + similarity
        constellation_profilication = len(constellation["id_list"])
        similar_constellations = []
        for constellation_id in constellation["id_list"]:
            add_to_region_map(constellation_id, 1)
        for other_constellation in constellation_list:
            if other_constellation != constellation:
                similarity_score = similarity(constellation, other_constellation)
                if similarity_score > cutoff:
                    constellation_profilication += similarity_score*len(other_constellation["id_list"])
                    for constellation_id in other_constellation["id_list"]:
                        add_to_region_map(constellation_id, similarity_score)
                        similar_constellations.append([constellation_id, similarity_score])
        similar_constellations.sort(key=lambda x: x[1], reverse=True)
        constellations_ranked_by_proflicness.append([constellation["id_list"][0], constellation_profilication, similar_constellations+[[i, 1] for i in constellation["id_list"]], region_to_profilication])
    constellations_ranked_by_proflicness.sort(key=lambda x: x[1], reverse=True)
    i = 0
    while i < len(constellations_ranked_by_proflicness):
        j = i+1
        while j < len(constellations_ranked_by_proflicness):
            found = False
            for same_constellation in constellations_ranked_by_proflicness[i][2]:
                if same_constellation[0] == constellations_ranked_by_proflicness[j][0]:
                    found = True
                    constellations_ranked_by_proflicness.pop(j)
            if not found:
                j += 1
        i += 1

    open(constellations_ranked_by_proflicness_file, "w").write(json.dumps(constellations_ranked_by_proflicness))

    regions = ['Asia', 'America', 'Europe', 'Middle East', 'Oceania']
    f = open(constellations_ranked_by_proflicness_file.split(".")[0]+".csv", "w")
    f.write("Constellation, Prolificness, Asia, America, Europe, Middle East, Oceania \n")
    for i in constellations_ranked_by_proflicness[:10]:
        f.write(i[0]+","+str(i[1])+","+str(i[-1].get("Asia",0))+","+str(i[-1].get("America",0))+","+str(i[-1].get("Europe",0))+","+str(i[-1].get("Middle East",0))+","+str(i[-1].get("Oceania",0))+","+str(i[2])+"\n")

def rank_constellations(file, function_name, sort_function, reverse_bool=True):
    constellation_list_copy = constellation_list.copy()
    i = 0
    while i < len(constellation_list_copy):
        if sort_function(constellation_list_copy[i]) == None:
            constellation_list_copy.pop(i)
        else:
            i += 1
    constellation_list_copy.sort(key=sort_function, reverse=reverse_bool)
    f = open(file, "w")
    f.write("Constellation, "+function_name+", Same Constellations Accross Cultures \n")
    for i in constellation_list_copy:
        for id in i["id_list"]:
            if id in [
                "CON macedonian 001",
                "CON macedonian 016",
                "CON arabic_arabian_peninsula 4202",
                "CON ruelle Cru",
                "CON arabic_arabian_peninsula 2801",
                "CON arabic_arabian_peninsula 300",
                "CON western UMi",
                "CON indian N13",
                "CON indian N07",
                "CON indian N22"
            ]:
                f.write("#")
        f.write(i["id_list"][0]+","+str(sort_function(i))+", "+str(len(i["id_list"]))+"\n")

rank_constellations("constelation_ranked_by_avg_magnitude.csv", "Average Magnitude", lambda x: x["average_magnitude"], False)
rank_constellations("constelation_ranked_by_avg_distance.csv", "Average Distance", lambda x: x["average_distance"], False)
rank_constellations("constelation_ranked_by_avg_equal_spacing.csv", "Average Equal Spacing", lambda x: x["average_equal_spacing"], False)
rank_constellations("constelation_ranked_by_avg_continuation.csv", "Average Continuation", lambda x: x["average_continuation"], False)
rank_constellations("constelation_ranked_by_avg_colinearity.csv", "Average Colinearity", lambda x: x["average_colinearity"], False)

rank_constellations("constelation_ranked_by_max_magnitude.csv", "Max Magnitude", lambda x: x["max_magnitude"], False)
rank_constellations("constelation_ranked_by_max_distance.csv", "Max Distance", lambda x: x["max_distance"], False)
rank_constellations("constelation_ranked_by_max_equal_spacing.csv", "Max Equal Spacing", lambda x: x["max_equal_spacing"], False)
rank_constellations("constelation_ranked_by_max_continuation.csv", "Max Continuation", lambda x: x["max_continuation"], False)
rank_constellations("constelation_ranked_by_max_colinearity.csv", "Min Colinearity", lambda x: x["max_colinearity"], False)

# "magnitude": None, # magnitude
# "distance": None, # distance to closest star
# "equal_spacing": None, # minimum difference in distances between stars
# "continuation": None, # minimum difference in neighboring angles
# "colinearity": None # pi-(closest angle gets to pi)

def simulated_prolificness(constellation):
    sim_score = 0
    if constellation["max_magnitude"]:
        sim_score -= constellation["max_magnitude"]
    if constellation["max_equal_spacing"]:
        sim_score -= 10*constellation["max_equal_spacing"]
    return sim_score

rank_constellations("constelation_ranked_by_simulated_prolificness.csv", "Simulated Prolificness", simulated_prolificness)

