import json
import os


# Collect shape filepaths
shapedir = '../semantics/'
shapepaths = [p for p in os.listdir(shapedir) if p.endswith('.ttl')]

for shapepath in shapepaths:
    with open(os.path.join(shapedir, shapepath), 'r') as shapefile:
        shape = shapefile.read()

    outpath = shapepath + '.json'
    with open(outpath, 'w') as outfile:
        outfile.write(json.dumps(shape))

    # print(json.dumps(shape))
