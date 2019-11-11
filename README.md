# NuScenes Map to OpenStreetMap Exporter

This tool converts the maps of the [NuScenes dataset](https://www.nuscenes.org) to the OpenStreetMap file format (.osm) which can be used with JOSM. This is useful to interactively visualise and explore the map data.

## Exporting the maps

The tool is based on the NuScenes devkit and the UTM library. Install the requirements using pip:
```
pip install -r requirements.txt
```

Converting NuScenes maps to the OpenStreetMap format.
The tool will create a .osm file in the current directory for each map.
```
python nuscenes_map_to_osm_exporter.py ~/data/nuscenes
```

Converting NuScenes annotations to the OpenStreetMap format.
The tool will create a .osm file in the current directory for each scene.
```
python nuscenes_to_osm_exporter.py ~/data/nuscenes v1.0-trainval
```

Converting NuScenes annotations to GPX format.
The tool will create a .gpx file in the current directory for each scene. The script above is more useful than this one because it exports all the metadata associated with the annotations rather this one only export the tracks themselves.
```
python nuscenes_to_gpx_exporter.py ~/data/nuscenes v1.0-trainval
```

## Visualising the data

The .osm files can be viewed in [JOSM](https://josm.openstreetmap.de).

To render the map properly, you must add the provided `nuscenes.mapcss` to JOSM Paint Styles. To do so, open JOSM, go into the menu `Edit/Preferences`. Under the tab `Map Settings` (third from the top), go into the subtab `Map Paint Styles` then add the `nuscenes.mapcss` custom style by clicking on the `+` icon on the right and selecting the file.

Aerial photography can also be overlaid by using the `Imagery` menu. The NuScenes maps were experimentally aligned with the imagery data and the alignment is not perfect. The coordinates that are used to generate the map are hard-coded in the file `utils/__init__.py`.

