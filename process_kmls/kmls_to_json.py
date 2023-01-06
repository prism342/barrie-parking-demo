import os
import uuid
import xmltodict
import json
import uuid

kml_dir = "./parking-lot-kmls"
kml_filepathes = [os.path.join(kml_dir, path) for path in os.listdir(kml_dir)]

placemarks = []


def parse_polygon(raw_polygon):
    outerBoundaries = []
    innerBoundaries = []

    outerBoundaries = list(map(parse_rings,
                               parse_boundaries(raw_polygon["outerBoundaryIs"])))

    if "innerBoundaryIs" in raw_polygon:
        innerBoundaries = list(map(parse_rings,
                               parse_boundaries(raw_polygon["innerBoundaryIs"])))

    return {"outerBoundaries": outerBoundaries, "innerBoundaries": innerBoundaries}


def parse_boundaries(raw_boundaries):
    boundaries = []

    if type(raw_boundaries) is not list:
        raw_boundaries = [raw_boundaries]

    for raw_boundary in raw_boundaries:
        boundaries.append(raw_boundary["LinearRing"]["coordinates"])

    return boundaries


def parse_rings(raw_rings):
    return list(map(lambda coor: list(map(float, coor.split(",")[0:2])), raw_rings.split(" ")))


for filepath in kml_filepathes:
    kml_file = open(filepath)

    data = xmltodict.parse(kml_file.read())
    for placemark in data["kml"]["Document"]["Folder"]["Placemark"]:
        placemark_name = placemark["name"].replace(",", "")
        innerBoundaries = []
        outerBoundaries = []

        polygons = placemark["MultiGeometry"]["Polygon"]

        if type(polygons) != list:
            polygons = [polygons, ]

        for polygon in polygons:
            polygon_dict = parse_polygon(polygon)
            outerBoundaries += polygon_dict["outerBoundaries"]
            innerBoundaries += polygon_dict["innerBoundaries"]

        placemark_dict = {"uuid": str(uuid.uuid4()), "name": placemark_name, "outerBoundaries": outerBoundaries,
                          "innerBoundaries": innerBoundaries,
                          "from_file": os.path.split(filepath)[-1]}

        placemarks.append(placemark_dict)

    kml_file.close()

open("./placemarks/polygons.json", "w").write(json.dumps(placemarks))

# extract polygons names
with open("./placemarks/placemark_names.csv", "w") as placemark_names_file:
    for placemark in placemarks:
        placemark_names_file.write(
            ",".join([placemark["uuid"], placemark["from_file"], placemark["name"]]) + "\n")
