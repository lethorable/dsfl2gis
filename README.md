# dsfl2gis

This is an ultra light open source DSFL file translator. At present it outputs an esri shape but can be modified to any ogr supported datasource.

Contributions are welcome.

## What is DSFL?

Dansk Selskab for Fotogrammetri og Landmåling (Danish Society for Photogrammetry and Land Surveying) quite early realised the need for a digital data exchange format in the 1970's. The format has been used widely for data transfers large and small and has even met some usecases whithin legal documentation (property boundaries etc).

The format was well ahead of its time. For instance attributes to geographical objects are handled - a precursor to the GIS systems that came much later. Today the format is still regarded as an official method of exchanging geographical data but fortunately is appears to be less and less used.

## What is DSFL2GIS?

dsfl2gis.py is a small script that will help you translate from DSFL to a shapefile (or mapinfo tab).

This script is in no way an encouragement to start using the DSFL format (more modern and better documented alternatives exists today) but if you happen to have an old file lying around and the need to translate it into something useful, this tool might be what you are looking for.

As for the code, I have tried to keep the size to a minumum. I intend to keep it below 350 lines and will only maintain it sporadically.

## Running

DSFL2GIS runs in the conda command shell environment which can be downloaded here:

https://docs.conda.io/en/latest/miniconda.html

Create an evironment with gdal installed ("conda install gdal") and you should be good to go.

Download dsfl2gis.py and run with the following command


```
#!cmd

python dsfl2gis.py <infile> <outfile>
```


dsfl2gis will create three shape files (points, lines, polygons). You will have to do some exercises to get the dsfl-themes sorted out afterwards and rename the attribute key names (easily done with sql).

If you wish to translate the rather un-friendly DSFL codes (e.g. %KG4%U91) to the more readable "Bygning" (building) you can edit a codetable and include it in the translation:

```
#!cmd

python dsfl2gis.py <infile> <outfile> -code codetable.txt
```

This will also handle the names of the attributes (%Dnnnn)

So far this script has only been tested on a few dsfl files and mileage may vary. If desireable the script can be altered to accommodate another OGR database or format as destination.

## Known limitations

Plenty - will elaborate later.
NB! Splines, circle segments etc are not supported


## Tips

Here will be some tricks and tricks.

## Disclaimer/License

See attached license

Copyright 2022 Thorbjørn Nielsen
