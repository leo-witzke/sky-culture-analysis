import os
import json

culture_map = {}
culture_to_region = {}

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

def culture_similarity(culture1, culture2):
    constellation_matches = []
    total_similarity = 0
    similar_constellations = 0
    for constellation in culture1:
        max_similarity = cutoff
        max_constellation = None
        for other_constellation in culture2:
            constellation_similarity = similarity(constellation, other_constellation)
            if constellation_similarity > max_similarity:
                max_similarity = constellation_similarity
                max_constellation = other_constellation
        if max_constellation != None:
            total_similarity += max_similarity
            similar_constellations += 1
            constellation_matches.append(max_constellation["id"])
    return total_similarity/(len(culture1)+len(culture2)-similar_constellations)

def get_constellation(id):
    for culture in culture_map:
        for constellation in culture_map[culture]:
            if constellation["id"] == id:
                return constellation

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
open("constelatins.json", "w").write(json.dumps(culture_map))

ranked_by_similarity = []
culture_map_keys = list(culture_map.keys())
for i in range(len(culture_map_keys)-1):
    for j in range(i+1, len(culture_map_keys)):
        ranked_by_similarity.append([culture_map_keys[i], culture_map_keys[j], culture_similarity(culture_map[culture_map_keys[i]], culture_map[culture_map_keys[j]])])
ranked_by_similarity.sort(key=lambda x: x[2], reverse=True)



# os.mkdir("culture_similarity")
f = open("culture_similarity/networkgraph.csv", "w")
f.write("Source, Target, Value \n")
for i in ranked_by_similarity:
    if i[2]*100 > 10:
        f.write(i[0]+","+i[1]+","+str(i[2]*100)+"\n")
    elif i in ranked_by_similarity:
        ranked_by_similarity = ranked_by_similarity[:ranked_by_similarity.index(i)]
f.close()

f = open("culture_similarity/cultures.csv", "w")
f.write("ID, Group, Size \n")
for culture in culture_map:
    total_sim = 0
    for similarity_rank in ranked_by_similarity:
        if culture in similarity_rank:
            total_sim += similarity_rank[2]
    if total_sim != 0:
        f.write(culture+","+culture_to_region[culture]+","+str(total_sim*10)+"\n")
f.close()

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
f.close()

# os.mkdir("connected_stars")
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
f.close()