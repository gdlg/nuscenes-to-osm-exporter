import os
import sys
from nuscenes.nuscenes import NuScenes
from datetime import datetime
from utils import *

# Prettyprint of a given value
# String are displayed as is.
# Other values are converted to a string using repr.
def getrepr(val):
    if isinstance(val, str):
        return val
    else:
        return repr(val)

# Export a whole scene.
def export_scene(nusc, scene_no):
    global token_to_id_table

    # Get the scene and attached log.
    scene = nusc.scene[scene_no]
    log = nusc.get('log',scene['log_token'])

    # Reset the global information for the current map.
    reset_map_location(log['location'])
    token_to_id_table = dict()
    
    # Open the output file.
    output_file = open("scene_%d_%s.osm" % (scene_no, log['location']), "w")
    
    # Header.
    output_file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    output_file.write('<osm version="0.6" generator="NuScenes to OSM 0.1">')

    # Loop through each sample and create a list of all the tracks
    tracks = dict()

    def append(token, data):
        if token not in tracks:
            tracks[token] = []
        tracks[token].append(data)

    sample = nusc.get('sample', scene['first_sample_token'])
    frame_no = 0
    while len(sample['next']) != 0:
        front_cam_data = nusc.get('sample_data',sample['data']['CAM_FRONT'])
        ego_pose = nusc.get('ego_pose',front_cam_data['ego_pose_token'])
        timestamp = datetime.fromtimestamp(sample['timestamp']/1000000).isoformat()
        
        append('egovehicle', (timestamp,ego_pose))

        for ann_token in sample['anns']:
            ann = nusc.get('sample_annotation', ann_token)
            append(ann['instance_token'], (timestamp,ann))

        frame_no += 1
        sample = nusc.get('sample', sample['next'])
    
    # Export each track.
    for token, track in tracks.items():

        # First pass: Create a node for each annotation along this track.
        for timestamp,ann in track:
            if token == "egovehicle":
                category_name = None
            else:
                category_name = ann['category_name']

            lat,lon = to_latlon(*tuple(ann['translation'][:2]))
            extra_tags = "\n".join(['<tag k="%s" v="%s"/>' % (key,getrepr(val)) for key,val in ann.items()])

            if token != "egovehicle":
                attrs = [nusc.get('attribute', attr)['name'] for attr in ann['attribute_tokens']]
                extra_tags += '<tag k="attributes" v="%s"/>' % '|'.join(attrs)

            output_file.write(
            """<node id="%s" lat="%f" lon="%f" visible="true" version="1">\n
                        <tag k="token" v="%s"/>\n
                        %s
                </node>\n
            """ % (get_token_id(ann['token']), lat, lon, ann['token'], extra_tags))


        # Second pass: Link all the nodes into an OSM way.
        output_file.write('<way id="%s" visible="true" version="1">\n' % get_token_id(token))
        output_file.write('<tag k="token" v="%s"/>\n' % token)
        if category_name is not None:
            output_file.write('<tag k="category_name" v="%s"/>\n' % category_name)

        if token != 'egovehicle':
            instance = nusc.get('instance', token)
            extra_tags = "\n".join(['<tag k="%s" v="%s"/>' % (key,getrepr(val)) for key,val in instance.items()])
            output_file.write(extra_tags)

        for timestamp,ann in track:
            output_file.write('<nd ref="%s"/>\n' % get_token_id(ann['token']))

        output_file.write("</way>\n")


    # Footer
    output_file.write('</osm>')


if __name__ == "__main__":
    dataroot = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/data/nuscenes')
    version = sys.argv[2] if len(sys.argv) > 2 else 'v1.0-mini'

    nusc = NuScenes(version=version, dataroot=dataroot, verbose=True)

    # Loop through and export each scene.
    for scene_no in range(len(nusc.scene)):
        export_scene(nusc, scene_no)

