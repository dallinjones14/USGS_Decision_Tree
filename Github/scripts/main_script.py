

from geo_functions.decision_tree_functions_final import *

AOI = 'G:/Final Project/test_shapefiles/AOIs.shp' # file with combined datasets
gdf = gpd.read_file(AOI)
temp_gdf = gdf.copy()

temp_gdf_final = gpd.GeoDataFrame() # creates final geodataframe that outputs get appended to, adds crs from perimeter data 
ignition = gpd.read_file(r'G:/Final Project/USGS_DATA/RDS-2013-0009.5_GDB/Data/FPA_FOD_20210617.gdb') #import fire ignition data
ignition_fields = ignition.columns.values.tolist()


# select all fires in that year 
year_list = [] 
for years in temp_gdf['Fire_Calen']:
    year_list.append(years)
    aoi_years = set(year_list)
    
tier_list = []
for tiers in temp_gdf['Fire_Tier']:
    tier_list.append(tiers)
    aoi_tiers = set(tier_list)
    aoi_tiers = sorted(aoi_tiers, reverse= True)




for year in aoi_years:
    year_gdf = temp_gdf.query('Fire_Calen == @year')
    #year_gdf = year_gdf.sort_values('Fire_Calen', ascending = False)
    
    ignition_shp = ignition.query('FIRE_YEAR == @year' )
    #tier processing

    for ti in aoi_tiers:
        tier_gdf = year_gdf.query('Fire_Tier == @ti')
        
        
    
        indexes_to_drop = []
        column_names = ["Index"]
        for columns in tier_gdf:
            column_names.append(columns)
        tier_gdf = tier_gdf.sort_values(by=['GIS_Acres'], ascending = True)    
        for row in tier_gdf.itertuples():
            final_output_gdf = gpd.GeoDataFrame() # creates final geodataframe that outputs get appended to, adds crs from perimeter data 

            focal = row
            df = pd.Series(focal).to_frame().T
            df.columns = column_names
            geom = gpd.GeoSeries(df.geometry, crs = tier_gdf.crs)
            buffer = geom.buffer(500)
            non_focal_list = []
            new_tier_list = []
             
          
            other_poly_list = year_gdf.index.tolist()
          
            other_poly_list.remove(df.Index.item())
            if not indexes_to_drop:
                print('first iteration')
            else:
                for index in indexes_to_drop:
                    while index in other_poly_list:
                        other_poly_list.remove(index)
          
            other_poly_gdf = year_gdf[year_gdf.index.isin(other_poly_list)]
            for idx1, row1 in other_poly_gdf.iterrows():
                non_focal_gdf = gpd.GeoDataFrame()
                geom1 = row1.geometry
                if geom1.intersects(buffer.iloc[0]):
                    
                    try:
                        non_focal_df = row1.to_frame().T
                        non_focal_list.append(non_focal_df)
                        df_non = pd.concat(non_focal_list)
                        non_focal_gdf = gpd.GeoDataFrame(df_non, geometry = df_non['geometry'], crs = tier_gdf.crs)
                       
                        
                    except ValueError:
                        print('no polygons within 500m')
                        non_focal_gdf = []
                    
                    
                        
                    
                else:
                    
                    print('no intersection')
                    
            #tier_gdf.drop(tier_gdf[indexes_to_drop], inplace = True)
            focal_gdf = gpd.GeoDataFrame(df, geometry = df['geometry'], crs = tier_gdf.crs)
            
            
                
            indexes_to_drop.append(df.index.item()) # erase focal gdf from tier gdf for next round
            if non_focal_gdf.empty:
                ('no polygons to look at')
            else:
                
                if type(non_focal_gdf) != list:
                    non_focal_index = non_focal_gdf.index.to_list()
                    indexes_to_drop.extend(non_focal_index)
           
            
                    
                
        
                    
                    #first tree
                    #function polygon overlap
                    # splits the geodataframe into polygons that overlap and those that dont
                    #function begin
                    overlapping_polygons, non_overlapping = polygon_overlap(non_focal_gdf, focal_gdf, column_names)
       
                    
                    large_overlapping_gdf, small_overlap_gdf = overlapped_percentage(overlapping_polygons, focal_gdf, column_names)
                    
                    
                    
                    
               
                    
                if type(large_overlapping_gdf) == list:
                        print('no large overlapping polygons')
                else:
                        
                        #function 1A
                        duplicate, non_duplicate_fires = acerage_comparison(focal_gdf, large_overlapping_gdf, column_names)
                        if type(duplicate) == list:
                            print('no duplicate')
                        else:
                            focal_gdf = duplicate # new focal gdf
            
                        if type(non_duplicate_fires) == list:
                            print('all polygons were duplicates')
                        else:
                        
                        
                            
                            #function 1B
                            no_ignition_points_gdf, focal_gdf, final_output_gdf, ignition_gdf = ignition_point_intersection(non_duplicate_fires, ignition_shp, focal_gdf, final_output_gdf, column_names, ignition_fields)
                            
                            
                
                            
                            
                            #function 1C
                            focal_gdf, final_output_gdf = compare_attributes(no_ignition_points_gdf, focal_gdf, final_output_gdf)
                
                
                
                
                
                        #second tree 
                
                        #testing purposes
                        #small_overlap = test_gdf.copy()
                        if type(small_overlap_gdf) == list:
                            
                            print('no small overlapping polygons')
                        else:
                            
                            
                            #function 2A
                            non_focal_ignition_points_gdf, focal_gdf, final_output_gdf, fires_with_ignition =  ignition_point_intersection_2(small_overlap_gdf, ignition_shp, focal_gdf, final_output_gdf, column_names, ignition_fields )
                            #function 2B
                            focal_gdf, final_output_gdf = compare_attributes_1(non_focal_ignition_points_gdf, focal_gdf, final_output_gdf)
                
                
                        if type(non_overlapping) == list:
                            print('all polygons overlap')
                
                        else:
                            #third tree
                            #non overlapping varaible gdf#third tree
                            #non overlapping varaible gdf
                            #function 3A
                            final_output_gdf, attributes_gdf = adequate_attributes(non_overlapping, final_output_gdf)
                            
                            
                            
                   
                            
                            
                            #function 3B
                            non_overlapping_ignition_points_gdf, focal_gdf, final_output_gdf =  ignition_point_intersection_3(attributes_gdf, ignition_shp, focal_gdf, final_output_gdf, column_names, ignition_fields)
                            #function 3C
                        if not 'non_overlapping_ignition_points_gdf' in locals():
                            print('no overlapping')
                        else: 
                            if non_overlapping_ignition_points_gdf.empty:
                                print('all polygons had ignition points')
                                temp_final_output = final_output_gdf
                            else:
                                temp_final_output = compare_attributes_2(non_overlapping_ignition_points_gdf, focal_gdf, final_output_gdf)
    
    
    
    
                        if not 'temp_final_output' in locals():
                            temp_final_output = final_output_gdf
                        else: 
                            print('continue')
                            
                        temp_gdf_final.append(temp_final_output.reset_index(drop = True))
                        temp_gdf_final = temp_gdf_final.append(focal_gdf)
                        
                        #import matplotlib.pyplot as plt
                        #import matplotlib.cbook as cbook
                        #3from matplotlib_scalebar.scalebar import ScaleBar
                        gdf = temp_gdf_final.sort_values(by=['GIS_Acres'], ascending = False)
                        gdf = gdf.reset_index(drop = True)
                        fig, ax = plt.subplots(figsize  = (12, 8))
                        gdf.plot('Fire_Name', ax=ax)
                        #ax.set_title("FINAL AOI")
                        #ax.add_artist(ScaleBar(1, 'm'))   
                        
                        x, y, arrow_length = 0.05, 0.15, 0.1
                        ax.annotate('N', xy=(x, y), xytext=(x, y-arrow_length),
                                    arrowprops=dict(facecolor='black', width=5, headwidth=15),
                                    ha='center', va='center', fontsize=20,
                                    xycoords=ax.transAxes)
                       # break
gdf.to_file('Combined_AOI.shp')
        
