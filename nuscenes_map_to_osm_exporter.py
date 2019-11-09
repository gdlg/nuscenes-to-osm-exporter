import os
import sys
from nuscenes.map_expansion.map_api import NuscenesMap
import utm

# UTM coordinates of the origin of each map in the dataset.
map_locations = {
    'singapore-onenorth': [48, 'N', 364802.37, 142396.09],
    'singapore-queenstown':[48, 'N', 362863.68, 141305.52],
    'singapore-hollandvillage':[48, 'N', 364510.57, 143641.40],
    'boston-seaport': [19, 'T', 330510.68, 4689209.05]
    }

# Set the UTM coordinates for the current map.
def reset_map_location(map_name):
    global zone_number, zone_letter, map_easting, map_northing
    zone_number = map_locations[map_name][0]
    zone_letter = map_locations[map_name][1]
    map_easting = map_locations[map_name][2]
    map_northing = map_locations[map_name][3]

# Convert the dataset coordinates to latitude and longitude
def to_latlon(x, y):
    lat,lon = utm.to_latlon(x+map_easting, y+map_northing, zone_number, zone_letter, strict=False)
    return lat, lon

# The dataset uses UUIDs token however OSM expect positive integers as IDs.
# Therefore we allocate OSM IDs for each token as we go along and keep track of the assigned IDs.
token_to_id_table = dict()

# Get or create an ID for a given NuScenes token.
def get_token_id(token):
    global token_to_id_table
    if token not in token_to_id_table:
        token_to_id_table[token] = len(token_to_id_table)+1
    return token_to_id_table[token]

# Generate a new unique ID (that is not associated with any specific NuScenes object).
def new_token():
    return get_token_id(len(token_to_id_table)+1)

# Export all the nodes in the current map.
def export_nodes(output_file, numap):
    for record in numap.node:
        lat,lon = to_latlon(record['x'], record['y'])
        output_file.write("""<node id="%s" lat="%f" lon="%f" visible="true" version="1">\n
                    <tag k="token" v="%s"/>\n
                    </node>
                """ % (get_token_id(record['token']), lat, lon, record['token']))

# Export the polygon corresponding to a given record. "layer" is the type of the record. tags are xml information which should be added to the polygon.
def export_polygon(output_file, numap, layer, record, tags):
    if 'holes' not in record or len(record['holes']) == 0 or (len(record['holes']) == 1 and len(record['holes'][0]['node_tokens']) == 0):
        # Case where the polygon has no hole. Represent the polygon with an OSM way.

        output_file.write('<way id="%s" visible="true" version="1">\n' % get_token_id(record['token']))
        nodes = record['exterior_node_tokens']
        for node in nodes:
            output_file.write('<nd ref="%s"/>\n' % get_token_id(node))
        output_file.write('<nd ref="%s"/>\n' % get_token_id(nodes[0]))
        output_file.write('<tag k="dtype" v="%s"/>\n' % layer)
        output_file.write(tags)
        output_file.write('</way>\n')
    else:
        # Case where the polygon has a hole.

        # Create an OSM way for the outer path
        outer_way = new_token()
        output_file.write('<way id="%s" visible="true" version="1">\n' % outer_way)
        nodes = record['exterior_node_tokens']
        for node in nodes:
            output_file.write('<nd ref="%s"/>\n' % get_token_id(node))
        output_file.write('<nd ref="%s"/>\n' % get_token_id(nodes[0]))
        output_file.write('<tag k="dtype" v="%s"/>\n' % layer)
        output_file.write('</way>\n')

        # Then create an OSM way for each inner hole in the polygon
        inner_ways = []

        for hole in record['holes']:
            inner_way = new_token()

            output_file.write('<way id="%s" visible="true" version="1">\n' % inner_way)
            nodes = hole['node_tokens']
            for node in nodes:
                output_file.write('<nd ref="%s"/>\n' % get_token_id(node))
            output_file.write('<nd ref="%s"/>\n' % get_token_id(nodes[0]))
            output_file.write('</way>\n')
            inner_ways.append(inner_way)

        # Finally link everything together using an OSM multipolygon
        output_file.write('<relation id="%s" visible="true" version="1">\n' % get_token_id(record['token']))
        output_file.write('<tag k="type" v="multipolygon"/>\n')
        output_file.write('<tag k="dtype" v="%s"/>\n' % layer)
        output_file.write('<member type="way" ref="%s" role="outer"/>\n' % outer_way)
        for inner_way in inner_ways:
            output_file.write('<member type="way" ref="%s" role="inner"/>\n' % inner_way)
        output_file.write(tags)
        output_file.write('</relation>\n')


# Export the line corresponding to a given record. "layer" is the type of the record. tags are xml information which should be added to the line.
def export_line(output_file, numap, layer, record, tags):
    output_file.write('<way id="%s" visible="true" version="1">\n' % get_token_id(record['token']))
    nodes = record['node_tokens']
    for node in nodes:
        output_file.write('<nd ref="%s"/>\n' % get_token_id(node))
    output_file.write('<tag k="dtype" v="%s"/>\n' % layer)
    output_file.write(tags)
    output_file.write('</way>\n')

# Prettyprint of a given value
# String are displayed as is.
# Other values are converted to a string using repr.
def getrepr(val):
    if isinstance(val, str):
        return val
    else:
        return repr(val)

# Export a whole map.
def export_map(dataroot, map_name):
    global token_to_id_table

    # Reset the global information for the current map.
    reset_map_location(map_name)
    token_to_id_table = dict()

    # Open the NuScenes dataset.
    numap = NuscenesMap(dataroot=dataroot, map_name=map_name)
    
    # Open the output file.
    output_file = open(map_name+".osm", "w")
    
    # Header.
    output_file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    output_file.write('<osm version="0.6" generator="NuScenes to OSM 0.1">')

    # Export all the nodes.
    export_nodes(output_file, numap)

    # Export the drivable area.
    for drivable_area in numap.drivable_area:
        for polygon_token in drivable_area['polygon_tokens']:
            record = numap.get('polygon', polygon_token)
            export_polygon(output_file, numap, 'drivable_area', record, '')
    
    # Export all the layers that are based on polygons.
    polygon_geometry = ['road_segment', 'road_block', 'lane', 'ped_crossing', 'walkway', 'stop_line', 'carpark_area',]
    
    for layer in polygon_geometry:
        for record in getattr(numap, layer):
            extra_tags = "\n".join(['<tag k="%s" v="%s"/>' % (key,getrepr(val)) for key,val in record.items()])
            export_polygon(output_file, numap, layer, record, extra_tags)

    
    # Export all the layers that are based on lines.
    line_geometry = ['road_divider', 'lane_divider', 'traffic_light']

    for layer in line_geometry:
        for record in getattr(numap, layer):
            extra_tags = "\n".join(['<tag k="%s" v="%s"/>' % (key,getrepr(val)) for key,val in record.items()])
            export_line(output_file, numap, layer, record, extra_tags)
    
    # For each traffic light, we also draw a node at the actual traffic light position.
    for record in numap.traffic_light:
        pose = record['pose']
        lat,lon = to_latlon(pose['tx'], pose['ty'])
        output_file.write('<node id="%s" lat="%f" lon="%f" visible="true" version="1"><tag k="ntype" v="traffic_light"/></node>\n' % (new_token(), lat, lon))

    # Footer
    output_file.write('</osm>')


if __name__ == "__main__":
    if len(sys.argv) > 1:
        dataroot = sys.argv[1]
    else:
        dataroot = os.path.expanduser('~/data/nuscenes')

    # Loop through and export each map.
    for map_name in map_locations.keys():
        export_map(dataroot, map_name)

