import os
import uuid
import xmltodict

kml_dir = "./parking-lot-kmls"
kml_filepathes = [os.path.join(kml_dir, path) for path in os.listdir(kml_dir)]

placemarks = {}

for filepath in kml_filepathes:
    kml_file = open(filepath)

    data = xmltodict.parse(kml_file.read())
    for placemark in data["kml"]["Document"]["Folder"]["Placemark"]:
        placemark_name = placemark["name"]
        if placemark_name == "NULL":
            placemark_name = "NULL " + uuid.uuid4().hex

        print(placemark_name)
        if placemark_name not in placemarks:
            placemarks[placemark_name] = []

        polygon = placemark["MultiGeometry"]["Polygon"]

        if type(polygon) != list:
            polygon = [polygon, ]

        for p in polygon:
            boundaries = []
            if type(p["outerBoundaryIs"]) is list:
                boundaries += p["outerBoundaryIs"]
            else:
                boundaries.append(p["outerBoundaryIs"])

            # if "innerBoundaryIs" in p:
            #    if type(p["innerBoundaryIs"]) is list:
            #        boundaries += p["innerBoundaryIs"]
            #    else:
            #        boundaries.append(p["innerBoundaryIs"])

            for boundary in boundaries:
                placemark_rings = boundary["LinearRing"]["coordinates"]
                placemarks[placemark_name].append(
                    list(map(lambda coor: list(map(float, coor.split(",")[0:2])), placemark_rings.split(" "))))

    kml_file.close()
