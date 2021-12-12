import os,sys
import osgeo.ogr as ogr
import osgeo.osr as osr

def usage():
	print("Usage:\n%s <dsfl file> <out file> -tab" %os.path.basename(sys.argv[0]))
	print("     <dsfl file>  : input file in dsfl format")
	print("     <out file>   : name of file(s) to create")
	print("     -tab         : create mapinfo tab instead of esri shp")
	print("     -code <file> : use a table to translate codes. If -code is not used")
	print("                    the dsfl codes (e.g. %KG4%U1) will be used")
	print("     -liststop    : stop after returning attribute fields")
	sys.exit(1)

#global variables to store code list (if used)
MyCodes = {}
UseCodes = False

# small function to retrieve a code
def gc(dsfl):
	if UseCodes == False:
		return dsfl
	if dsfl in MyCodes:
		return MyCodes[dsfl]
	else:
		return dsfl

def main(args):
	global MyCodes
	global UseCodes
	if len(args)<3:
		usage()

	fnam = args[1]
	f= open(fnam, "r")
	MyA = f.read()
	f.close()

	#try to read a code table
	UseCodes = False
	if "-code" in args:
		print ("Reading code table")
		UseCodes = True
		i=args.index("-code")
		cnam=args[i+1]
		f= open(cnam, "r")
		CfA = f.readlines()
		f.close()
		for line in CfA:
			if line[0]!='#':
				AktLin = line.split(' ')
				AktLin = list(filter(None, AktLin))
				MyCodes[AktLin[0]]=AktLin[1].replace('\n','').replace('\r','')
	print (MyCodes)

	MyAss = MyA.replace('\n','').replace('\r','').split('%') # just splitting MyAss... Caution if MyAss is big it will take some time!

	srs = osr.SpatialReference()
	srs.ImportFromEPSG(25832) #yup - only utm32etrs89, 3d data...
	path, ext = os.path.splitext(args[2])
	if path.isdigit():
		print ("Output file name must NOT be a number (shape file incompatibility)")
		sys.exit(1)
	ext = '.shp'
	if '-tab' in args:
		ext = '.tab'

	fnam_pts = path+'_pts'+ext
	fnam_pol = path+'_pol'+ext
	fnam_lin = path+'_lin'+ext
	if '-tab' in args:
		driver = ogr.GetDriverByName("MapInfo File")
	else:
		driver = ogr.GetDriverByName("ESRI Shapefile")

	if os.path.exists(fnam_pts):
		driver.DeleteDataSource(fnam_pts)
	if os.path.exists(fnam_pol):
		driver.DeleteDataSource(fnam_pol)
	if os.path.exists(fnam_lin):
		driver.DeleteDataSource(fnam_lin)

	#a list for the datasources
	dsA=[]
	dsA.append(driver.CreateDataSource(fnam_pts))
	dsA.append(driver.CreateDataSource(fnam_pol))
	dsA.append(driver.CreateDataSource(fnam_lin))

	#... and for the layers
	LayersA =[]
	LayersA.append (dsA[0].CreateLayer(fnam_pts, srs, geom_type=ogr.wkbPoint25D))
	LayersA.append (dsA[1].CreateLayer(fnam_pol, srs, geom_type=ogr.wkbPolygon25D))
	LayersA.append (dsA[2].CreateLayer(fnam_lin, srs, geom_type=ogr.wkbLineString25D))

	kodField = ogr.FieldDefn("code", ogr.OFTString)

	for layer in LayersA:
		layer.CreateField(kodField)

	#Collect a list of attribute types represented in MyAss
	AttribTypesA =[]
	for i in range(len(MyAss)):
#		print (MyAss[i])
		if len(MyAss[i].strip())>0:
			AktObj = MyAss[i].split(' ')
#			print (AktObj)
			#sys.exit()
			AktObj = list(filter(None, AktObj))
#			print(AktObj)
			if (AktObj[0][0]).upper() == 'D':
				if not AktObj[0] in AttribTypesA:
					if (AktObj[0]).upper() != 'D':
						AttribTypesA.append((AktObj[0]))
	AttribTypesA.sort()
	print ("Found following attribute types in DSFL file...\n")

	for Att in AttribTypesA:
		print (Att)
#	print (args)
	if '-liststop' in args:
		sys.exit(1)

	#Get headerinfo
	stillheader = True
	HeaderA = {}
	i = -1
	while stillheader:
		i = i + 1
		if len(MyAss[i].strip())>0:
			AktObj = MyAss[i].split(' ')
			AktObj = list(filter(None, AktObj))
			if (((AktObj[0][0]).upper() == 'H') or ((AktObj[0][0]).upper() == 'B')):
				HeaderA[AktObj[0]]=' '.join(AktObj[1:])
			else:
				stillheader = False
	# The header could be stored in a file/database for future use or documentation.
	# This goes for the %N origin data as well
	# maybe in the future...

	#Check for coordinate sequence used.
	if len(HeaderA["H3"])==3:
		dim = 3 #It's either XYX,NEH, ENH, YXZ (three letters)
	else:
		dim = 2

	if (((HeaderA["H3"])[0]== "X") or ((HeaderA["H3"])[0]== "E")):
		coordsequence = 0 #Either XYZ, XYH, ENH, ENZ, EN, XY etc
	else:
		coordsequence = 1 #Either YXZ, NEZ, YX, NE etc.

	print("coordsequence %s" %coordsequence)
	print("dim %s" %dim)


	#Create the attribute fields on the shape file - we don't care if it makes sense or not
	#Unused attribute fields will be deleted later
	for aktFieldName in AttribTypesA:
		aktField = ogr.FieldDefn(gc(aktFieldName), ogr.OFTString)
		for layer in LayersA:
			layer.CreateField(gc(aktField))
	FeatureDefnA = []
	FeatureDefnA.append(LayersA[0].GetLayerDefn())
	FeatureDefnA.append(LayersA[1].GetLayerDefn())
	FeatureDefnA.append(LayersA[2].GetLayerDefn())

	#Now we parse the file. We only look for valid geometries (points, lines, polygons and polygon holes)
	PolyOpen=False
	aktAttribA ={}
	for i in range(len(MyAss)): #Keep going until MyAss is empty
		if len(MyAss[i].strip())>0:     #Every bit of MyAss is trimmed. See if it is a valid record...?
			AktObj = MyAss[i].split(' ') #Splitting MyAss again
			AktObj = list(filter(None, AktObj)) #remove empty strings from the list.
			AktTyp = AktObj[0]

			if AktTyp[0].upper()=='D':
				if len(AktTyp) == 1: #%D will cancel all attributes
					aktAttribA ={}
#					print ("attributes cancelled - all of them")
					continue
				if len(AktObj) > 1: #We have attribute with value(s).
					aktAttribA[AktObj[0]]=' '.join(AktObj[1:])
#					print ("attribute set: ", AktObj[0], ' '.join(AktObj[1:]))
					continue
				if len(AktObj) == 1:
					#This specific attribute is cancelled.
#					print ("attribute cancelled: ",AktObj[0])
					del aktAttribA[AktObj[0]]
					continue

			if (AktObj[0]).upper() != 'S': #S means end of dsfl file
				NextObj = MyAss[i+1].split(' ')
				NextObj = list(filter(None, NextObj))
				NextTyp = NextObj[0]

			if AktTyp[0]=='K': #The object code is set
				AktKod = '%'+AktObj[0]+'%'+NextObj[0]

			if (AktTyp == 'F1KR') or (AktTyp == 'F4KR'): #Either polygon or polygon hole
				#Polygon
				if PolyOpen == False:
					poly = ogr.Geometry(ogr.wkbPolygon25D)
					PolyOpen = True
				ring = ogr.Geometry(ogr.wkbLinearRing)
				PolA = AktObj[1:]
				if coordsequence ==1:
					PolA_Y = AktObj[1::dim]
					PolA_X = AktObj[2::dim]
				else:
					PolA_Y = AktObj[2::dim]
					PolA_X = AktObj[1::dim]
				if dim ==3:
					PolA_Z = AktObj[3::dim]
				else:
					PolA_Z =-999
				for j in range(len(PolA_Y)):
					if dim ==3:
						ring.AddPoint(float(PolA_X[j]),float(float(PolA_Y[j])), float(PolA_Z[j]))
					else:
						ring.AddPoint(float(PolA_X[j]),float(float(PolA_Y[j])), -999)
				poly.AddGeometry(ring)
				del(ring)
#				if NextTyp == 'F4KR': #Hole in polygon
#					print ("HOLE")
				if NextTyp !='F4KR': #Holes have to be in sequence. If the next obj is not a hole - close the object
					feature = ogr.Feature(FeatureDefnA[1])
					feature.SetGeometry(poly)
					feature.SetField("code", gc(AktKod))
					for key,val in aktAttribA.items():
						feature.SetField(gc(key),val)
					LayersA[1].CreateFeature(feature)
					del(poly)
					PolyOpen = False

			if AktTyp == 'L1KR': #Line string
				line = ogr.Geometry(ogr.wkbLineString25D)
				LinA = AktObj[1:]
				if coordsequence ==1:
					LinA_Y = AktObj[1::dim]
					LinA_X = AktObj[2::dim]
				else:
					LinA_Y = AktObj[2::dim]
					LinA_X = AktObj[1::dim]
				if dim == 3:
					LinA_Z = AktObj[3::3]
				else:
					LinA_Z = -999
				for j in range(len(LinA_Y)):
					if dim == 3:
						line.AddPoint(float(LinA_X[j]),float(float(LinA_Y[j])), float(LinA_Z[j]))
					else:
						line.AddPoint(float(LinA_X[j]),float(float(LinA_Y[j])), -999)
				feature = ogr.Feature(FeatureDefnA[2])
				feature.SetGeometry(line)
				feature.SetField("code", gc(AktKod))
				for key,val in aktAttribA.items():
					feature.SetField(gc(key),val)
				LayersA[2].CreateFeature(feature)
				del(line)

			if (AktTyp == 'P1K') or (len(AktTyp) ==2 and AktTyp[0] == 'T') : #point
				#Point
				point = ogr.Geometry(ogr.wkbPoint25D)
				if coordsequence ==1:
					if dim == 3:
						point.AddPoint(float(AktObj[2]),float(AktObj[1]), float(AktObj[3]))
					else:
						point.AddPoint(float(AktObj[2]),float(AktObj[1]), -999)
				else:
					if dim == 3:
						point.AddPoint(float(AktObj[1]),float(AktObj[2]), float(AktObj[3]))
					else:
						point.AddPoint(float(AktObj[1]),float(AktObj[2]), -999)

				feature = ogr.Feature(FeatureDefnA[0])
				feature.SetGeometry(point)
				feature.SetField("code", gc(AktKod))
				for key,val in aktAttribA.items():
					feature.SetField(gc(key),val)
				LayersA[0].CreateFeature(feature)

	#Clean up empty attributes
	print("Translation done - cleaning up unused attributes. May take a while")
	for key in AttribTypesA:
		for i in range(len(LayersA)):
			lnam = LayersA[i].GetName()
			#A bit of SQL to save the day. We test how many items are found by querying on the field. Returns with 0: must be unused.
			testLayer = dsA[i].ExecuteSQL('select * from %s where %s is not null' %(lnam,gc(key)))
			if testLayer.GetFeatureCount() == 0:
				testdef = LayersA[i].GetLayerDefn()
				testid = testdef.GetFieldIndex(gc(key))
#				print ("Deleting empty attribute %s from layer %s" %(gc(key), lnam))
				LayersA[i].DeleteField(testid)

	#close the datasources
	for ds in dsA:
		ds.Destroy()
	print ("All is well that ends well")

if __name__=="__main__":
	main(sys.argv)
