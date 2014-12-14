#!/usr/bin/python

import xmltodict
import math
from opyscad import *


zoom = 0.1
buildingBase = 2.0 #map size, m
buildingFloorHeight = 3.0 #map size, m
substrateHeight = 0.4 #real size, mm 
highwayHeight = 0.2 #real size, mm 
highwayWidth = 0.8 #real size, mm 
highwayResidentialWidth = 1.2 #real size, mm 
waterDeep = 0.2 #real size, mm 


def coordsOld(lon, lat):
	lon = lon/180.0*math.pi
	lat = lat/180.0*math.pi
	R = 6378137.0
	x = R * lon * zoom;
	y = R * math.log(math.tan(math.pi/4 + lat/2)) * zoom
	
	return x, y

def coords(lon1, lat1, lon2, lat2):
	R = 6378137.0
	
	dLat = (lat2 - lat1) * math.pi / 180;
	dLon = (lon2 - lon1) * math.pi / 180;
	
	de = dLon * (R*math.cos(math.pi*lat2/180))
	dn = R * dLat
 
	return de * zoom, dn * zoom

def main():
	name = 'map2'
	
	f = open('%s.osm' % name, 'r')
	xml = f.read()
	f.close()

	osm = xmltodict.parse(xml)
	osm = osm['osm']

	nodes = {}
	
	first = True
	for node in osm['node']:
		id = int(node['@id'])
		lon = float(node['@lon'])
		lat = float(node['@lat'])
		
		if first:
			minLon = maxLon = lon
			minLat = maxLat = lat
			first = False
		else:
			if lon < minLon:
				minLon = lon
			if lon > maxLon:
				maxLon = lon
			if lat < minLat:
				minLat = lat
			if lat > maxLat:
				maxLat = lat

	baseLon = (maxLon - minLon) / 2 + minLon
	baseLat = (maxLat - minLat) / 2 + minLat
	
	first = True
	for node in osm['node']:
		id = int(node['@id'])
		lon = float(node['@lon'])
		lat = float(node['@lat'])
		
		x, y = coords(baseLon, baseLat, lon, lat)
		
		if first:
			minX = maxX = x
			minY = maxY = y
			first = False
		else:
			if x < minX:
				minX = x
			if x > maxX:
				maxX = x
			if y < minY:
				minY = y
			if y > maxY:
				maxY = y
		
		nodes[id] = (x, y)

	ways = []
	for way in osm['way']:
		nds = way['nd']
		wayNodes = []
		for nd in nds:
			nd = int(nd['@ref'])
			wayNodes.append(nodes[nd])
		
		tags = {}
		if 'tag' in way:
			if type(way['tag']) != list:
				way['tag'] = [way['tag']]
			for tag in way['tag']:
				tags[tag['@k']] = tag['@v']
				
		ways.append((wayNodes, tags))
	
	first = True
	for nodes, tags in ways:
		if 'building' in tags:
			for x, y in nodes:
				if first:
					minX = maxX = x
					minY = maxY = y
					first = False
				else:
					if x < minX:
						minX = x
					if x > maxX:
						maxX = x
					if y < minY:
						minY = y
					if y > maxY:
						maxY = y

	dx = (maxX - minX) / 2 + minX
	dy = (maxY - minY) / 2 + minY
	print dx, dy
	
	res = cube([maxX - minX, maxY - minY, substrateHeight + 0.01]) << [-(maxX - minX) / 2, -(maxY - minY) / 2, -substrateHeight ]

	for nodes, tags in ways:
		
		points = []
		for x, y in nodes:
			x -= dx
			y -= dy
			
			points.append([x, y])
		
		col = [0.3, 0.3, 0.3, 1]
		height = 0.1 * zoom
		
		if 'building' in tags or 'building:part' in tags:
			if 'height' in tags:
				height = float(tags['height'])
			else:
				height = int(tags.get('building:levels', 1)) * buildingFloorHeight + buildingBase

			if 'min_height' in tags:
				minHeight = float(tags['min_height'])
				height -= minHeight
			else:
				minHeight = 0
				
			col = [0.7, 1, 0.7, 1]
			
			building = color(col)(linear_extrude(height = height * zoom) (polygon(points)))
			if minHeight != 0:
				building <<= [0, 0, minHeight*zoom]
			
			res += building
			
		elif 'highway' in tags and highwayHeight != 0:
			col = [0.1, 0.5, 0.5, 1]
				
			if tags['highway'] == 'residential':
				width = highwayResidentialWidth
				col = [0.8, 0.5, 0.5, 1]
			else:
				width = highwayWidth
			
			ppp = points[:]
			points.reverse()
			for x, y in points:
				ppp.append([x+0.01, y+0.01])
			
			highway = color(col)(linear_extrude(height = highwayHeight)
						(offset(delta = width/2.0, join_type = '"round"')(polygon(ppp))))
	
			res += highway
			
		elif tags.get('natural') == 'water':
			water = color([0,0.7,1,1])(linear_extrude(height = waterDeep+1) (polygon(points)))
			water <<= [0, 0, -waterDeep]
			res -= water
	
	dx = (maxX - minX) / 2
	dy = (maxY - minY) / 2
	if False:
		cut = cube([200, 200, 100]) << [-100, -100, -10]
		res -= cut << [-100 - dx, 0, 0]
		res -= cut << [0, -100 - dy, 0]
		res -= cut << [100 + dx, 0, 0]
		res -= cut << [0, 100 + dy, 0]
	print dx/2, dy/2
	
	res.save('%s.scad' % name)

main()	