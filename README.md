# Flask, Datashader, and Leaflet for Creating Web Maps from NetCDF Files

Leveraging Datashader for on-demand tiling to create a Leaflet web map from a NetCDF file. Generates a visualization of predicted CESM2 2023 global mean surface temperature data. 

An adaptation of Scott Syms's methods described in Towards Data Science: _[Dynamically displaying millions of points on a web map with Python](https://towardsdatascience.com/dynamically-displaying-millions-of-points-on-a-web-map-with-python-ae2b39b2ebf)_, but using Flask instead of FastAPI and generating continuous quadmeshes from a NetCDF instead of plotting points from a CSV.

![Prototype Demo](static/datashader.gif)