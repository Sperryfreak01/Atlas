__author__ = 'matt'

import simplejson as json
from folium import plugins, folium
import decimal
import bisect
import ijson.backends.yajl2 as ijson
import argparse
from geopy.geocoders import Nominatim


parser = argparse.ArgumentParser(description='Process Google Location data and generate maps')
parser.add_argument("filename", help="path to location data files (JSON format)",
                    type=argparse.FileType('rb'), nargs='+')
parser.add_argument("-t", "--heatmap", help="generate a heatmap from the datafiles",
                    action="store_true")
parser.add_argument("-c", "--cluster", help="plot location data from the datafiles",
                    action="store_true")
parser.add_argument("-f", "--fast", help="Faster JSON processing (WARNING MUCH HIGHER MEMORY USAGE)",
                    action="store_true")
parser.add_argument("-n", "--night", help="Overlays the current day and night period on the map",
                    action="store_true")
parser.add_argument("-s", "--stats", help="Overlays the current day and night period on the map",
                    action="store_true")
args = parser.parse_args()
decimal.getcontext().prec = 9

def parser(files):
    datapoints = []
    x = 0

    for filename in files:
        with open(filename, 'rb') as f:
            print "Parsing %s" % (filename)
            if args.fast == True:
                jsondata = json.load(f)
                data = jsondata["locations"]

            else:
                objects = ijson.items(f, 'locations.item')
                data = (o for o in objects)

            for entry in data:
                try:
                    if entry["accuracy"] > 15:
                        lat = str(decimal.Decimal(entry["latitudeE7"]) * decimal.Decimal(0.0000001))
                        long = str(decimal.Decimal(entry["longitudeE7"]) * decimal.Decimal(0.0000001))
                        location = (lat, long, 1)
                        if len(datapoints) > 2:  #make sure the list is long enough to bisect
                            lookuplocation = (bisect.bisect_left(datapoints, location)) #bisect based on current location from google
                            #print "length: %s, location: %s" % (len(datapoints), lookuplocation)

                            if lookuplocation + 1 < len(datapoints): #check to see if we are at the end of the data set, if so append
                                # print "listlat: %s, lat: %s" %(datapoints[lookuplocation+1][0], lat)
                                if datapoints[lookuplocation + 1][0] == lat: # if the value is not a duplicate insert it
                                    if datapoints[lookuplocation + 1][1] == long: # if the value is not a duplicate insert it
                                        datapoints[lookuplocation+1] = (lat, long, datapoints[lookuplocation+1][2]+1)
                                        # print "duplicate found: %s, %s" % (datapoints[lookuplocation+1], datapoints[lookuplocation+1][2])
                                    else:
                                        # print "long didnt match"
                                        datapoints.insert(lookuplocation, location)
                                else:
                                    # print "lat didnt match"
                                    datapoints.insert(lookuplocation, location)
                            else:  # if the data goes at the end just append it instead of inserting it
                                #print "length: %s, location: %s" % (len(datapoints), lookuplocation)
                                datapoints.append(location)
                        else:
                            datapoints.append(location)
                except KeyError:
                    #print "entry contained no accuracy information, excluding"
                    continue
    count, frequent = 0,[]
    for data in datapoints:
        if data[2] > count:
            frequent = data
            count = frequent[2]

    return datapoints, frequent

def heatmap(locationdata):
    print "generating a heatmap"
    map_osm.add_children(plugins.HeatMap(locationdata))


def cluster(locationdata):
    print "generating a clustered map"
    map_osm.add_children(plugins.MarkerCluster(locationdata))



if __name__ == "__main__":

    input_files =[]
    for filename in args.filename:
        input_files.append(filename.name)

    parsedlocations, frequentLocation = parser(input_files)

    geolocator = Nominatim()
    location = geolocator.reverse("%s,%s" % (frequentLocation[0],frequentLocation[1]))
    print frequentLocation
    print ((location.latitude, location.longitude))
    print(location.address)


    if args.heatmap:
        map_osm = folium.Map(location=[frequentLocation[0], frequentLocation[1]])
        heatmap(parsedlocations)
        if args.night:
            map_osm.add_children(plugins.Terminator())
        map_osm.save('./heat_map.html')
        map_osm._repr_html_()

    if args.cluster:
        map_osm = folium.Map(location=[frequentLocation[0], frequentLocation[1]])
        cluster(parsedlocations)
        if args.night:
            map_osm.add_children(plugins.Terminator())
        map_osm.save('./cluster_map.html')
        map_osm._repr_html_()

