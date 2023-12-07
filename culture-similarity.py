import os
import json

culture_map = {}
culture_to_region = {}
constellation_map = {}

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

                import json
 
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

constellation_map_file = "constellation_map_file.json"
if os.path.isfile(constellation_map_file):
    constellation_map = json.load(open(constellation_map_file))
else:
    hipparcos_file = open("Hipparcos.tsv")
    for line in hipparcos_file:
        if len(line.strip()) != 0 and line[0] != "#":
            star = [i.strip() for i in line.split(";")]
            constellation_map[star[0]] = {
                "Magnitude": star[3],
                "RightAscensionDegrees": star[4],
                "DeclinationDegrees": star[5],
                "Color": star[6],
            }
    open(constellation_map_file, "w").write(json.dumps(constellation_map))

# os.mkdir("constelation_proflicness")
constellations_ranked_by_proflicness = []
for culture in culture_map:
    for constellation in culture_map[culture]:
        constellation_profilication = 1
        similar_constellations = []
        region_to_profilication = {culture_to_region[culture]: 1}
        for other_culture in culture_map:
            if other_culture != culture:
                max_similarity = cutoff
                max_constellation = None
                for other_constellation in culture_map[other_culture]:
                    similarity_score = similarity(constellation, other_constellation)
                    if similarity_score > max_similarity:
                        max_similarity = similarity_score
                        max_constellation = other_constellation
                if max_constellation != None:
                    constellation_profilication += max_similarity
                    region_to_profilication[culture_to_region[other_culture]] = region_to_profilication.get(culture_to_region[other_culture], 0) + max_similarity
                    similar_constellations.append([max_constellation["id"], max_similarity])
        similar_constellations.sort(key=lambda x: x[1], reverse=True)
        constellations_ranked_by_proflicness.append([constellation["id"], constellation_profilication, similar_constellations, region_to_profilication])
constellations_ranked_by_proflicness.sort(key=lambda x: x[1], reverse=True)
i = 0
while i < len(constellations_ranked_by_proflicness):
    j = i+1
    while j < len(constellations_ranked_by_proflicness):
        found = False
        for same_constellation in constellations_ranked_by_proflicness[i][2]:
            if same_constellation[1] >= cutoff and same_constellation[0] == constellations_ranked_by_proflicness[j][0]:
                found = True
                constellations_ranked_by_proflicness.pop(j)
        if not found:
            j += 1
    i += 1

regions = ['Asia', 'America', 'Europe', 'Middle East', 'Oceania']
f = open("constelation_proflicness/constelation_proflicness.csv", "w")
f.write("Constellation, Prolificness, Asia, America, Europe, Middle East, Oceania \n")
for i in constellations_ranked_by_proflicness[:10]:
    f.write(i[0]+","+str(i[1])+","+str(i[-1].get("Asia",0))+","+str(i[-1].get("America",0))+","+str(i[-1].get("Europe",0))+","+str(i[-1].get("Middle East",0))+","+str(i[-1].get("Oceania",0))+","+str(i[2])+"\n")