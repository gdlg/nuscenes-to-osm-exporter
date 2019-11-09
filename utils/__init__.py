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

