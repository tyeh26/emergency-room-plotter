# https://stackoverflow.com/questions/74054997/create-point-grid-inside-a-shapefile-using-python

import geopandas as gpd
import numpy as np
import shapely.geometry

gdf = gpd.read_file("California_State_Boundary.geojson")

STEP = 1000
crs = gdf.estimate_utm_crs()
# crs = "EPSG:3338"
a, b, c, d = gdf.to_crs(crs).total_bounds

# create a grid for geometry
gdf_grid = gpd.GeoDataFrame(
    geometry=[
        shapely.geometry.Point(x, y)
        for x in np.arange(a, c, STEP)
        for y in np.arange(b, d, STEP)
    ],
    crs=crs,
).to_crs(gdf.crs)


# restrict grid to only squares that intersect with geometry
gdf_grid = (
    gdf_grid.sjoin(gdf.dissolve().loc[:,["geometry"]])
    .pipe(lambda d: d.groupby(d.index).first())
    .set_crs(gdf.crs)
    .drop(columns=["index_right"])
)

# compute which points belong to which trauma center
trauma_centers = gpd.read_file("centers.geojson")

levels = ['I', 'II', 'III', 'IV']
cumulative_levels = []
for level in levels:
	cumulative_levels.append(level)
	
	tmp_gdf = gpd.sjoin_nearest(gdf_grid, trauma_centers.query("`Local EMS Agency Designation - Adult` in @cumulative_levels"))

	# group each point by trauma center
	tmp_gdf = tmp_gdf.dissolve(by="Trauma Center")

	# compute a polygon for each center
	tmp_gdf["geometry"] = tmp_gdf.convex_hull

	trauma_centers[level] = trauma_centers["Trauma Center"].map(dict(zip(tmp_gdf.index, tmp_gdf.geometry)))

trauma_centers.to_csv('trauma_centers_plotted.csv')
