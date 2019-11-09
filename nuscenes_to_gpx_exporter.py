import os
import sys
from nuscenes.nuscenes import NuScenes
from datetime import datetime
from utils import *

# Export a whole scene.
def export_scene(nusc, scene_no):

    # Get the scene and attached log.
    scene = nusc.scene[scene_no]
    log = nusc.get('log',scene['log_token'])

    # Reset the global information for the current map.
    reset_map_location(log['location'])
    
    # Open the output file.
    output_file = open("scene_"+str(scene_no)+".gpx", "w")
    
    # Header.
    output_file.write('<?xml version="1.0" encoding="UTF-8" standalone="no" ?>')
    output_file.write('<gpx xmlns="http://www.topografix.com/GPX/1/1" xmlns:gpxx="http://www.garmin.com/xmlschemas/GpxExtensions/v3" xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1" creator="Oregon 400t" version="1.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd http://www.garmin.com/xmlschemas/GpxExtensions/v3 http://www.garmin.com/xmlschemas/GpxExtensionsv3.xsd http://www.garmin.com/xmlschemas/TrackPointExtension/v1 http://www.garmin.com/xmlschemas/TrackPointExtensionv1.xsd">\n')

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
        
        append('egovehicle', (timestamp,to_latlon(*tuple(ego_pose['translation'][:2]))))

        for ann_token in sample['anns']:
            ann = nusc.get('sample_annotation', ann_token)
            append(ann['instance_token'], (timestamp,to_latlon(*tuple(ann['translation'][:2]))))

        frame_no += 1
        sample = nusc.get('sample', sample['next'])
    
    # Export each track
    for token, track in tracks.items():
        output_file.write("<trk>\n")
        output_file.write("<name>%s</name>\n" % token)
        output_file.write("<trkseg>\n")

        for timestamp,latlon in track:
            output_file.write("""
            <trkpt lat="%f" lon="%f">
            <time>%s</time>
            </trkpt>\n""" % (latlon[0], latlon[1], timestamp))

        output_file.write("</trkseg>\n")
        output_file.write("</trk>\n")

    # Footer
    output_file.write('</gpx>')


if __name__ == "__main__":
    if len(sys.argv) > 1:
        dataroot = sys.argv[1]
    else:
        dataroot = os.path.expanduser('~/data/nuscenes')

    nusc = NuScenes(version='v1.0-mini', dataroot=dataroot, verbose=True)

    # Loop through and export each scene.
    for scene_no in range(len(nusc.scene)):
        export_scene(nusc, scene_no)

