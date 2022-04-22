# -*- coding: utf-8 -*-
"""
Created on Tue Mar 22 12:51:24 2022

@author: DallinJ
"""

# -*- coding: utf-8 -*-


#import required libraries
import geopandas as gpd
from geopandas import overlay, GeoDataFrame
import pandas as pd
import matplotlib.pyplot as plt
import shapely

from shapely.geos import TopologicalError


import os
import time
from gc import collect
from psutil import virtual_memory
from datetime import datetime as dt



#first tree
#function polygon overlap
# splits the geodataframe into polygons that overlap and those that dont
#function begin
def polygon_overlap(non_focal_gdf, focal_gdf, column_names):
    
    #list for polygons that dont overlap
    no_overlap_list = []
    #list for polygons that do overlap
    overlap_list = []
    
    #iterate through the non focal fires 
    for row in non_focal_gdf.itertuples():
        
        main_poly_gdf= pd.Series(row).to_frame().T # convert pandas object to dataframe
        main_poly_gdf.columns = column_names #add the column names
        geom1 = gpd.GeoSeries(main_poly_gdf.geometry, crs = focal_gdf.crs)  #convert geometry to geoseries for intersection analysis  
        
       
        intersection = (focal_gdf.intersects(geom1)) #preform intersection anlysis result is boolean
        
        
        if any(intersection) == False: ## if the intersection is false
            
            no_overlap_list.append(main_poly_gdf) # append the non overlapping polygon to the no overlap list
           
        else: # if there is overlap 
            
            overlap_list.append(main_poly_gdf) # append the polygon to the overlap list
    try:
        
        no_overlap_df = pd.concat(no_overlap_list) # convert list of dataframes to a pandas dataframe
        
        no_overlap_gdf = gpd.GeoDataFrame(no_overlap_df, geometry = no_overlap_df['geometry']) # convert pandas dataframe to geopandas dataframe
        
    
    except ValueError:
        print('all polygons overlap') # if all polygons are overlapping this will appear
        
    
    try:
        
    
        overlap_df = pd.concat(overlap_list) # convert list of dataframes to a pandas dataframe
        
        overlap_gdf = gpd.GeoDataFrame(overlap_df, geometry = overlap_df['geometry'], crs = focal_gdf.crs) # convert pandas dataframe to geopandas dataframe
        
    except ValueError:
        print('no overlapping polygons') # if there are no overlapping polygons this will appear
        
    if 'no_overlap_gdf' in locals():
        print('polygons that dont overlap')
    else:
        no_overlap_gdf = []
        
    if 'overlap_gdf' in locals():
        print('polygons that  overlap')
    else:
        overlap_gdf = []
        
    
    return(overlap_gdf, no_overlap_gdf)

  #function overlap percentage
  
  #Does the non-focal fire overlap the focal fire by >=75%?
def overlapped_percentage(overlap_gdf, focal_gdf, column_names):
      
      #overlap_gdf = overlapping_polygons
      overlapped_percentage=[]
      small_overlap = []
      large_overlap = []
      
      
      #iterate through overlapping fire polygons
      for row in overlap_gdf.itertuples():
          
          temp_gdf= pd.Series(row).to_frame().T # convert pandas object to dataframe
          del temp_gdf[1]#delete repeated index
          temp_gdf.columns = column_names #add the column names
           
         
          temp_gdf_1 = temp_gdf.copy() #create a working copy gdf
          
          shape =  gpd.GeoSeries(temp_gdf.geometry) #create geoseries for intersection analysis
          shape = shape.buffer(0) #buffer to correct any invalid polygons
          temp_gdf['geometry'] = shape # add geoseries geometry to dataframe
             
          
          
          temp_gdf_1 =pd.DataFrame(temp_gdf_1) #create copy of dataframe
          
           
          geom_over =  shape.iloc[0] # grab geoemtry for intersection analysis
         
          focal_geo = focal_gdf.buffer(0) # correct potnetial focal invalid polygons
          
          
          try:
              print(temp_gdf['Fire_Name'])
              print(temp_gdf['Fire_ID'])
              new_intersect = focal_geo.intersection(geom_over) #preform intersection, output is polygon of overlap
              print(new_intersect)
              
              if any(new_intersect) != "POLYGON EMPTY": #if there is no a polygon 
                  temp_gdf_1['overlap_perc'] = new_intersect.area.sum()/geom_over.area*100 # caluclate overlap percentage
                  overlapped_percentage.append(temp_gdf_1) #append temp_gdf to overlapped percentage list
                  if temp_gdf_1['overlap_perc'].item() >= 75:  # if overlap percentage is greater than or equal to 75 then
                      large_overlap.append(temp_gdf_1) # add to large overlap list
                  else:
                      small_overlap.append(temp_gdf_1) # else add to small overlap list
              
              
              else:
                   print('no intersection')
          except TopologicalError: # if there is an error with the intersection preform this error
              print('invalid polygon type')
               
          
          
      
      try:
          small_overlap_df = pd.concat(small_overlap) # create df from list
          
          small_overlap_gdf = gpd.GeoDataFrame(small_overlap_df, geometry = small_overlap_df['geometry']) # create gdf from list
          small_overlap_gdf = small_overlap_gdf.drop(columns=['overlap_perc']) # delete overlap percentage column
      except ValueError:
          print('No polygons overlap by less then 75%')
          
      
      
      try:
          large_overlap_df = pd.concat(large_overlap) # create df from list
          
          large_overlap_gdf = gpd.GeoDataFrame(large_overlap_df, geometry = large_overlap_df['geometry'], crs = overlap_gdf.crs) # create gdf from df
          large_overlap_gdf = large_overlap_gdf.drop(columns=['overlap_perc'])# delete overlap percentage column
      except ValueError:
          print('No polygons overlap by more then 75%')
          
      
        
          
          
          
          
        
      if 'large_overlap_gdf' in locals():   
          fig, ax = plt.subplots(figsize  = (12, 8))
          large_overlap_gdf.plot('Fire_Name', ax=ax)
          ax.set_title("Perimeters with 75 overlap percentage")
      else:
          print('all polygons have small overlap')
          large_overlap_gdf = [] # if no polygons overlap by 75 then create an empty list to avoid error
          
      if 'small_overlap_gdf' in locals():
          print('small overlap polygons')
      else:
          small_overlap_gdf= [] ## if all polygons overlap by 75 then create an empty list to avoid error
      return large_overlap_gdf, small_overlap_gdf



#Acerage Comparison
#function 1A
#Is the non-focal fire’s acreage >=75% the focal fire?

def acerage_comparison(focal_gdf, overlapping_gdf, column_names):

    
    non_duplicate_fire = [] #list for fires that are not duplciates of the focal fire
    global duplicate_fire
    duplicate_fire = [] #list for fires that are  duplciates of the focal fire
    
    for row in overlapping_gdf.itertuples(): # iterate through the overlapping gdf
        
        
        main_poly_gdf = pd.Series(row).to_frame().T # convert each row to dataframe
        del main_poly_gdf[1]#delete repeated index
        main_poly_gdf.columns = column_names # add column names
        
        
        
        
        
        focal_acres = focal_gdf.GIS_Acres.item() # grab focal fires acres
        non_focal_acres = main_poly_gdf.GIS_Acres.item() # grab non focal fires acres
        if  non_focal_acres >= .75*focal_acres: #if polygon is greater then 76% of the focal fires
            duplicate_fire.append(main_poly_gdf) # this polygon is a duplicate fire
            
        else:
            non_duplicate_fire.append(main_poly_gdf) # if its less then 75 then it is liekly not a duplicate of the focal
            
    if not duplicate_fire:
        print('no duplicate fires')
        duplicate = [] # if there are no duplicates 
    else:
        duplicate_fire_df = pd.concat(duplicate_fire) #convert duplicates list to df
        duplicate_fire_gdf = gpd.GeoDataFrame(duplicate_fire_df, geometry = duplicate_fire_df['geometry'], crs = focal_gdf.crs)     
        duplicate_fire_gdf.append(focal_gdf)  # add focal fire to duplicate gdf
        duplicate_fire_gdf.reset_index() # reset index
        duplicate_fire_gdf['Fire_Name']= duplicate_fire_gdf['Fire_Name'].str.upper() #change fire name to all uppercase
        duplicate = duplicate_fire_gdf.dissolve(as_index= True)  # dissolve duplicate fires # new focal fire
    
    if not non_duplicate_fire: # if there is no
        print('all duplicate fires')
        non_duplicate_fire_gdf = []
    else:
        non_duplicate_fire_df = pd.concat(non_duplicate_fire) # no duplciate list to df
        non_duplicate_fire_gdf = gpd.GeoDataFrame(non_duplicate_fire_df, geometry = non_duplicate_fire_df['geometry'], crs = focal_gdf.crs) # df to gdf
        fig, ax = plt.subplots(figsize  = (12, 8)) # plot
        non_duplicate_fire_gdf.plot('Fire_Name',ax=ax)
        ax.set_title("Perimeters with <= 75% acerage of Focal Fire", fontsize=25)
    return duplicate, non_duplicate_fire_gdf



#ignition points
#function 1B
#Does the non-focal fire have a unique ignition point within the non-focal fire polygon with unique attributes* 
#that match the non-focal polygon



def ignition_point_intersection(large_overlap_gdf, ignition_point_shapefile, focal_gdf, final_output_gdf, column_names, ignition_fields):
    
    
    
    ignition_points = ignition_point_shapefile # bring in ignition points for that year
    ignition_points=ignition_points.to_crs(crs=focal_gdf.crs) # change crs to match fire polygons
    aoi_ignition_points = gpd.clip(ignition_points, large_overlap_gdf) # clip ignition points to polygons for easier processing
    
    
    
    #split gdf into polygons that have ignition points and those that do not
    ignition_point_shp = []
    no_ignition_points = []
    duplicate_names = []
    non_duplicated = []
    for row in large_overlap_gdf.itertuples():
        temp_gdf = pd.Series(row).to_frame().T # convert each row to dataframe
        del temp_gdf[1]#delete repeated index
        
        temp_gdf.columns = column_names # add column names
        geom1 = temp_gdf.geometry
        geom_over =  geom1.iloc[0]
        
        intersection = (aoi_ignition_points.intersects(geom_over))# find intersections between fire perimeters and ignition point
        
        
        if any(intersection) == False:
            
            no_ignition_points.append(temp_gdf) # if no ignition points intersect a fire perimeter
            
        
        
        else:
                for rows_ig in aoi_ignition_points.itertuples():
                    temp_gdf_ignition = pd.Series(rows_ig).to_frame().T # convert each row to dataframe
                    del temp_gdf_ignition[1]#delete repeated index
                    temp_gdf_ignition.columns = ignition_fields # add column names
                    geom1_i = temp_gdf_ignition.geometry[0]
                    
                    if geom1_i.within(temp_gdf.geometry[0]):
                        
                        if temp_gdf['Fire_Name'].item() == temp_gdf_ignition['FIRE_NAME'].item(): # if there is an intersection and there fire name is the same
                            ignition_point_shp.append(temp_gdf) # append the fire to the ignition point list
                        else:
                            no_ignition_points.append(temp_gdf) # if they dont match then append to no ignition point list
                    else:
                        continue
     
    try:
        ignition_point_df = pd.concat(ignition_point_shp)  # convert list to df
        
        ignition_point_gdf = gpd.GeoDataFrame(ignition_point_df, geometry = ignition_point_df['geometry'],crs = large_overlap_gdf.crs)    #df to gdf
    
        
    
        # duplicate names
        for row1 in ignition_point_gdf.itertuples():
            temp_gdf1 = pd.Series(row1).to_frame().T # convert each row to dataframe
            del temp_gdf1[1]#delete repeated index
            temp_gdf1.columns = column_names # add column names
            temp_gdf1['Fire_Name'] = temp_gdf1['Fire_Name'].str.upper() #make both fire names uppercase 
            
            if temp_gdf1.Fire_Name.item() == focal_gdf.Fire_Name.item(): #if both fires have the same name they are likely the same fire
                duplicate_names.append(temp_gdf1) # append to duplicate list
                ignition_point_gdf.drop(temp_gdf1.index.item(), inplace = True)# drop index so it isnt repeated
                
            
            else:
                continue
    except ValueError:
        print('No polygons contain ignition points') # error if there are no ignition points
    try:
        no_ignition_point_df = pd.concat(no_ignition_points) # convvert list to dataframe
        
        no_ignition_point_gdf = gpd.GeoDataFrame(no_ignition_point_df, geometry = no_ignition_point_df['geometry'],crs = large_overlap_gdf.crs)# df tp gdf
    except ValueError:
        print('All points have ignition points')
       
    try:
        duplicate_fires_df = pd.concat(duplicate_names) #list to df
        
        duplicate_fire_gdf = gpd.GeoDataFrame(duplicate_fires_df, geometry = duplicate_fires_df['geometry'],crs = large_overlap_gdf.crs)# gdf from df
    except ValueError:
        print('No duplicate fires')
    
    if 'duplicate_fire_gdf' in locals():
        
        focal_gdf.append(duplicate_fire_gdf) # add duplicate fires to focal fire
        focal_gdf.dissolve(by = 'Fire_Name', as_index= True)   # dissolve tool
    else:
        pass
    
    fig, ax = plt.subplots(figsize  = (12, 8)) #plotting
    no_ignition_point_gdf.plot('Fire_Name', ax=ax)
    ax.set_title("Perimeters with no intersecting ignition points")
    
    if 'ignition_point_gdf' in locals():
        if type(ignition_point_gdf) != list:
            temp_gdf_final = ignition_point_gdf.reset_index() # reset index
        
            
        
            del temp_gdf_final['index'] #del unneeded column
            
            
            #disolve duplicate distinct fires together
            non_duplicate_fire = []
            
            duplicate_fire_1 = []   
            for idx, row in temp_gdf_final.iterrows():
                
                main_poly_gdf = row 
                main_poly_gdf =pd.DataFrame(main_poly_gdf)
                
                main_poly_gdf_t = main_poly_gdf.T
                
                gdf = gpd.GeoDataFrame(main_poly_gdf_t, geometry = main_poly_gdf_t['geometry'], crs = focal_gdf.crs )
                
        
                other_poly_list = temp_gdf_final.index.tolist()
        
                other_poly_list.remove(idx)
        
                other_poly_gdf = temp_gdf_final[temp_gdf_final.index.isin(other_poly_list)]
                
                dissolved_gdf = gpd.GeoDataFrame()
                intersection_list = []
                for idx1, row1 in other_poly_gdf.iterrows():
                    secondary_poly = row1
                    secondary_poly_gdf =pd.DataFrame(secondary_poly)
                    
                    secondary_f_t = secondary_poly_gdf.T
                    geom1 = secondary_poly.geometry
                    intersection = gdf.intersects(geom1)
                    secondary_acres = secondary_poly.GIS_Acres
                    non_focal_acres = gdf.GIS_Acres.item()
                    intersection_result = intersection.all()
                    intersection_list.append(intersection_result)
                    if intersection_result == False:
                        print(gdf['Fire_Name'] + 'does not intersect with' + secondary_poly['Fire_Name'])
                       # non_duplicate_fire.append(main_poly_gdf_t)
                       
                    else:
                        print(gdf['Fire_Name'] + 'does intersect with' + secondary_poly['Fire_Name'])
                        if  non_focal_acres >= .25*secondary_acres:
                                duplicate_fire_1.append(main_poly_gdf_t)
                                duplicate_fire_1.append(secondary_f_t)
                                
                   
                    
                        
                           
        
        
        
        
        
        
                        else:
                            continue
                
                   
                if True in intersection_list:
                   continue
                else:
                    non_duplicate_fire.append(main_poly_gdf_t)
        
        try:  
            df_duplicate = pd.concat(duplicate_fire_1)
            gdf_duplicate = gpd.GeoDataFrame(df_duplicate, geometry = df_duplicate['geometry'], crs = focal_gdf.crs)
                        
            gdf_duplicate_dissolve = gdf_duplicate.dissolve('Fire_Name', as_index=False)
            
            dissolved_gdf = dissolved_gdf.append(gdf_duplicate_dissolve)
        
           
        except ValueError:
            print('no duplicate fire polygons')
       
        try:
        
            #create geodataframe from non duplicate fire
            df_non = pd.concat(non_duplicate_fire)
            
            gdf_non = gpd.GeoDataFrame(df_non, geometry = df_non['geometry'], crs = focal_gdf.crs)
            
        except ValueError:
            print('all values are duplicates')
                
    
    if "dissolved_gdf" in locals():
       final_output_gdf = final_output_gdf.append(dissolved_gdf)
    
     
  
    if "gdf_non" in locals(): 
        final_output_gdf = final_output_gdf.append(gdf_non)
   
  
   
    
    return no_ignition_point_gdf, focal_gdf, final_output_gdf





#function 1C
#Does the highly overlapping non-focal fire have 2 or more attributes* that differ from the focal fire?

def compare_attributes(no_ignition_pointsgdf, focal_gdf, final_output_gdf):
    
    #comparing attributes
    common_attributes = []
    unique_attributes = [] 
    
    no_ignition_pointsgdf['Fire_Name'] = no_ignition_pointsgdf['Fire_Name'].str.upper() #covnert fire names to all upper case
    focal_copy = focal_gdf.copy()
    focal_copy['Fire_Name']= focal_copy['Fire_Name'].str.upper() # convert fire names to all upper case
    for idx, rows in no_ignition_pointsgdf.iterrows():
        
        test_rows = rows[['Fire_Type', 'Fire_Name']]
       
        rows_df = rows.to_frame().T
        
            
        for idx1, row1 in focal_copy.iterrows():
             
            test_value_focal = row1[['Fire_Name', 'Fire_Code']]
        compare = test_rows.eq(test_value_focal)
        
        
        if compare.any() == True:
                    common_attributes.append(rows_df) # polygon has name or fire code in common with focal fire
        else:
                    unique_attributes.append(rows_df)# polygon does not have those attributes in common
                
                
        
                
    try:
         non_similiar_attributes  = pd.concat(unique_attributes) # convert list to df
         
         non_similiar_gdf = gpd.GeoDataFrame(non_similiar_attributes, geometry = non_similiar_attributes['geometry'],crs = focal_gdf.crs) #df to gdf
    except ValueError:
         print('most attributes are similiar')
         non_similiar_gdf = []
         
    try:
        similiar_attributes = pd.concat(common_attributes)
        similiar_gdf = gpd.GeoDataFrame(similiar_attributes, geometry = similiar_attributes['geometry'],crs = focal_gdf.crs)
    
        focal_gdf.append(similiar_gdf)
        focal_gdf.dissolve(by = 'Fire_Name', as_index= True)
    except ValueError:
        print('most atttributes are different')
    
    if type(non_similiar_gdf) != list:
        temp_gdf_final = non_similiar_gdf.reset_index() #reset index

        
        # dossolve duplicate distinct polygons
        del temp_gdf_final['index']
        list_of_bools =[]
        non_duplicate_fire = []
        duplicate_fire = [] 
        for idx, rows in temp_gdf_final.iterrows():
            
            
            main_poly_gdf = rows
            main_poly_gdf =pd.DataFrame(main_poly_gdf)
           
            main_poly_gdf_t = main_poly_gdf.T
           
            gdf = gpd.GeoDataFrame(main_poly_gdf_t, geometry = main_poly_gdf_t['geometry'], crs = focal_gdf.crs )
           

            other_poly_list = temp_gdf_final.index.tolist()

            other_poly_list.remove(idx)

            other_poly_gdf = temp_gdf_final[temp_gdf_final.index.isin(other_poly_list)]
            
            dissolved_gdf_2 = gpd.GeoDataFrame()
            intersection_list = []
            for idx1, row1 in other_poly_gdf.iterrows():
                secondary_poly = row1
                secondary_poly_gdf =pd.DataFrame(secondary_poly)
               
                secondary_f_t = secondary_poly_gdf.T
                geom1 = secondary_poly.geometry
                intersection = gdf.intersects(geom1)
                secondary_acres = secondary_poly.GIS_Acres
                non_focal_acres = gdf.GIS_Acres.item()
                intersection_result = intersection.all()
                intersection_list.append(intersection_result)
                list_of_bools.append(intersection_list)
                if intersection_result == False:
                    print(gdf['Fire_Name'] + 'does not intersect with' + secondary_poly['Fire_Name'])
                   # non_duplicate_fire.append(main_poly_gdf_t)
                  
                else:
                    print(gdf['Fire_Name'] + 'does intersect with' + secondary_poly['Fire_Name'])
                    if  non_focal_acres >= .25*secondary_acres:
                            duplicate_fire.append(main_poly_gdf_t)
                            duplicate_fire.append(secondary_f_t)
                             
                 
                 
                
                
                 
                     
                        






                    else:
                          continue
                 
            if True in intersection_list:
                print('all duplicates')
            else:
                non_duplicate_fire.append(main_poly_gdf_t)
                print('not duplicate')
                
        try:    
         
                  df_duplicate = pd.concat(duplicate_fire)
                  gdf_duplicate = gpd.GeoDataFrame(df_duplicate, geometry = df_duplicate['geometry'], crs = focal_gdf.crs)
                              
                  gdf_duplicate_dissolve = gdf_duplicate.dissolve('Fire_Name', as_index=False)
                  
                  dissolved_gdf_2 = dissolved_gdf_2.append(gdf_duplicate_dissolve)
            
        except ValueError:
                                  print('no duplicate fire polygons')
             
        try:
         
                  #create geodataframe from non duplicate fire
                  df_non = pd.concat(non_duplicate_fire)
                  
                  gdf_non_duplicate = gpd.GeoDataFrame(df_non, geometry = df_non['geometry'], crs = focal_gdf.crs)
             
        except ValueError:
                                  print('all values are duplicates')
                 
         
        if "dissolved_gdf_2" in locals():
         final_output_gdf = final_output_gdf.append(dissolved_gdf_2)
         
          
           
        if "gdf_non_duplicate" in locals(): 
          final_output_gdf = final_output_gdf.append(gdf_non_duplicate)
    
    
    fig, ax = plt.subplots(figsize  = (12, 8))
    final_output_gdf.plot('Fire_Name', ax=ax)
    ax.set_title("Non-focal independent Fire Perimeters (left half)")

    return(focal_gdf, final_output_gdf)


    #function 2A
def ignition_point_intersection_2(non_focal_gdf, ignition_point_shapefile, focal_gdf, final_output_gdf, column_names, ignition_fields):
   
    
    ignition_points = ignition_point_shapefile # bring in ignition points for that year
    ignition_points=ignition_points.to_crs(crs=focal_gdf.crs) # change crs to match fire polygons
    aoi_ignition_points = gpd.clip(ignition_points, non_focal_gdf) # clip ignition points to polygons for easier processing
    
    #split gdf into polygons that have ignition points and those that do not
    ignition_point_shp = []
    no_ignition_points = []
    
    
    for  row in non_focal_gdf.itertuples():
        temp_gdf = pd.Series(row).to_frame().T # convert each row to dataframe
        del temp_gdf[1]#delete repeated index

        temp_gdf.columns = column_names # add column names
        geom1 = temp_gdf.geometry
        geom_over =  geom1.iloc[0]
        
        intersection = (aoi_ignition_points.intersects(geom_over))
        
        
       
        
        if any(intersection) == False:
            
            no_ignition_points.append(temp_gdf) # if no ignition points intersect a fire perimeter
            
        
        
        else:
                for rows_ig in aoi_ignition_points.itertuples():
                    temp_gdf_ignition = pd.Series(rows_ig).to_frame().T # convert each row to dataframe
                    del temp_gdf_ignition[1]#delete repeated index
                    temp_gdf_ignition.columns = ignition_fields # add column names
                    geom1_i = temp_gdf_ignition.geometry[0]
                    
                    if geom1_i.within(temp_gdf.geometry[0]):
                        
                        if temp_gdf['Fire_Name'].item() == temp_gdf_ignition['FIRE_NAME'].item(): # if there is an intersection and there fire name is the same
                            ignition_point_shp.append(temp_gdf) # append the fire to the ignition point list
                        else:
                            no_ignition_points.append(temp_gdf) # if they dont match then append to no ignition point list
                    else:
                        continue
                   
        
            
    #convert to geodataframe
    try:
        ignition_point_df = pd.concat(ignition_point_shp)
        global ignition_point_gdf
        ignition_point_gdf = gpd.GeoDataFrame(ignition_point_df, geometry = ignition_point_df['geometry'],crs = focal_gdf.crs)    
        
    except ValueError:
        print('No polygons contain ignition points')
        ignition_point_gdf = []
    
   #convert to geodataframe
    try:
        no_ignition_point_df = pd.concat(no_ignition_points) 
        no_ignition_point_gdf = gpd.GeoDataFrame(no_ignition_point_df, geometry = no_ignition_point_df['geometry'],crs = focal_gdf.crs)
    except ValueError:
        print('All points have ignition points')
        no_ignition_point_gdf = gpd.GeoDataFrame()
  
    #dissolve duplicate distinct polygons
    if type(ignition_point_gdf) is list:
        print('no ignition points')
    else:
        temp_gdf_final = ignition_point_gdf.reset_index()
    
        
    
        del temp_gdf_final['index']
        
        non_duplicate_fire = []
        duplicate_fire = []
        for rows in temp_gdf_final.itertuples():
            
            
            main_poly_gdf_t = pd.Series(rows).to_frame().T
            del main_poly_gdf_t[1]
            main_poly_gdf_t.columns = column_names
            
            gdf = gpd.GeoDataFrame(main_poly_gdf_t, geometry = main_poly_gdf_t['geometry'], crs = focal_gdf.crs )
            idx = gdf.Index.item()

            other_poly_list = temp_gdf_final.index.tolist()

            other_poly_list.remove(idx)

            other_poly_gdf = temp_gdf_final[temp_gdf_final.index.isin(other_poly_list)]
            
            dissolved_gdf_3 = gpd.GeoDataFrame()
            intersection_list = []
            for idx1, row1 in other_poly_gdf.iterrows():
                secondary_poly = row1
                secondary_poly_gdf =pd.DataFrame(secondary_poly)
                
                secondary_f_t = secondary_poly_gdf.T
                geom1 = secondary_poly.geometry
                intersection = gdf.intersects(geom1)
                secondary_acres = secondary_poly.GIS_Acres
                non_focal_acres = gdf.GIS_Acres.item()
                intersection_result = intersection.all()
                intersection_list.append(intersection_result)
                if intersection_result == False:
                    print(gdf['Fire_Name'] + 'does not intersect with' + secondary_poly['Fire_Name'])
                   # non_duplicate_fire.append(main_poly_gdf_t)
                   
                else:
                    print(gdf['Fire_Name'] + 'does intersect with' + secondary_poly['Fire_Name'])
                    if  non_focal_acres >= .25*secondary_acres:
                            duplicate_fire.append(main_poly_gdf_t)
                            duplicate_fire.append(secondary_f_t)
                            
                
                
               
               
                
                    
                       






                    else:
                        continue
                
            if True in intersection_list:
               print('all duplicates')
            else:
                non_duplicate_fire.append(main_poly_gdf_t)
                print('not a duplicate')
        try:    
        
            df_duplicate = pd.concat(duplicate_fire)
            gdf_duplicate = gpd.GeoDataFrame(df_duplicate, geometry = df_duplicate['geometry'], crs = focal_gdf.crs)
                        
            gdf_duplicate_dissolve = gdf_duplicate.dissolve('Fire_Name', as_index=False)
            
            dissolved_gdf_3 = dissolved_gdf_3.append(gdf_duplicate_dissolve)
           
        except ValueError:
            print('no duplicate fire polygons')
            
        try:
        
            #create geodataframe from non duplicate fire
            df_non = pd.concat(non_duplicate_fire)
            
            gdf_non = gpd.GeoDataFrame(df_non, geometry = df_non['geometry'], crs = focal_gdf.crs)
            
        except ValueError:
            print('all values are duplicates')
                
    
    if "dissolved_gdf_3" in locals():
       final_output_gdf = final_output_gdf.append(dissolved_gdf_3)
    
     
  
    if "gdf_non" in locals(): 
        final_output_gdf = final_output_gdf.append(gdf_non)
    
    return no_ignition_point_gdf, focal_gdf, final_output_gdf, ignition_point_gdf

#function 2B
def compare_attributes_1(no_ignition_pointsgdf, focal_gdf, final_output_gdf):
    #comparing attributes
    common_attributes = []
    unique_attributes = [] 
    
    no_ignition_pointsgdf['Fire_Name'] = no_ignition_pointsgdf['Fire_Name'].str.upper() #convert fire names to all upper case
    focal_copy = focal_gdf.copy()
    focal_copy['Fire_Name']= focal_copy['Fire_Name'].str.upper() # convert fire names to all upper case
    for idx, rows in no_ignition_pointsgdf.iterrows():
        
        test_rows = rows[['Fire_Type', 'Fire_Name']]
       
        rows_df = rows.to_frame().T
        
            
        for idx1, row1 in focal_copy.iterrows():
             
            test_value_focal = row1[['Fire_Name', 'Fire_Code']]
        compare = test_rows.eq(test_value_focal)
        
        
        if compare.any() == True:
                    common_attributes.append(rows_df) # polygon has name or fire code in common with focal fire
        else:
                    unique_attributes.append(rows_df)# polygon does not have those attributes in common
    
    
    #create a gdf
    try:
         non_similiar_attributes  = pd.concat(unique_attributes)
         
         non_similiar_gdf_2 = gpd.GeoDataFrame(non_similiar_attributes, geometry = non_similiar_attributes['geometry'],crs = focal_gdf.crs)
    except ValueError:
         print('most attributes are similiar')
    
         #create a gdf
    try:
        similiar_attributes = pd.concat(common_attributes)
        similiar_gdf = gpd.GeoDataFrame(similiar_attributes, geometry = similiar_attributes['geometry'],crs = focal_gdf.crs)
    
        focal_gdf.append(similiar_gdf)
        focal_gdf.dissolve(by = 'Fire_Name', as_index= True)
    except ValueError:
        print('most atttributes are different')
        
    if 'non_similiar_gdf_2' in locals():
        temp_gdf_final = non_similiar_gdf_2.reset_index()
    
        #dissolve duplicate distinct polygons
    
        del temp_gdf_final['index']
        list_of_bools =[]
        non_duplicate_fire = []
        duplicate_fire = [] 
        for idx, rows in temp_gdf_final.iterrows():
            
            
            main_poly_gdf = rows
            main_poly_gdf =pd.DataFrame(main_poly_gdf)
           
            main_poly_gdf_t = main_poly_gdf.T
           
            gdf = gpd.GeoDataFrame(main_poly_gdf_t, geometry = main_poly_gdf_t['geometry'], crs = focal_gdf.crs )
           
    
            other_poly_list = temp_gdf_final.index.tolist()
    
            other_poly_list.remove(idx)
    
            other_poly_gdf = temp_gdf_final[temp_gdf_final.index.isin(other_poly_list)]
            
            dissolved_gdf_attribute = gpd.GeoDataFrame()
            intersection_list = []
            for idx1, row1 in other_poly_gdf.iterrows():
                secondary_poly = row1
                secondary_poly_gdf =pd.DataFrame(secondary_poly)
               
                secondary_f_t = secondary_poly_gdf.T
                geom1 = secondary_poly.geometry
                intersection = gdf.intersects(geom1)
                secondary_acres = secondary_poly.GIS_Acres
                non_focal_acres = gdf.GIS_Acres.item()
                intersection_result = intersection.all()
                intersection_list.append(intersection_result)
                list_of_bools.append(intersection_list)
                if intersection_result == False:
                    print(gdf['Fire_Name'] + 'does not intersect with' + secondary_poly['Fire_Name'])
                   # non_duplicate_fire.append(main_poly_gdf_t)
                  
                else:
                    print(gdf['Fire_Name'] + 'does intersect with' + secondary_poly['Fire_Name'])
                    if  non_focal_acres >= .25*secondary_acres:
                            duplicate_fire.append(main_poly_gdf_t)
                            duplicate_fire.append(secondary_f_t)
                    
                    else:
                          continue
                 
            if True in intersection_list:
                print('all duplicates')
            else:
                non_duplicate_fire.append(main_poly_gdf_t)
                print('not duplicate')
                
        try:    
         
                  df_duplicate = pd.concat(duplicate_fire)
                  gdf_duplicate = gpd.GeoDataFrame(df_duplicate, geometry = df_duplicate['geometry'], crs = focal_gdf.crs)
                              
                  gdf_duplicate_dissolve = gdf_duplicate.dissolve('Fire_Name', as_index=False)
                  
                  dissolved_gdf_attribute = dissolved_gdf_attribute.append(gdf_duplicate_dissolve)
            
        except ValueError:
                                  print('no duplicate fire polygons')
             
        try:
         
                  #create geodataframe from non duplicate fire
                  df_non = pd.concat(non_duplicate_fire)
                  
                  gdf_non_duplicate_2 = gpd.GeoDataFrame(df_non, geometry = df_non['geometry'], crs = focal_gdf.crs)
             
        except ValueError:
                                  print('all values are duplicates')
                 
         
        if "dissolved_gdf_attribute" in locals():
         final_output_gdf = final_output_gdf.append(dissolved_gdf_attribute)
         
          
           
        if "gdf_non_duplicate_2" in locals(): 
          final_output_gdf = final_output_gdf.append(gdf_non_duplicate_2)
        
        
        fig, ax = plt.subplots(figsize  = (12, 8))
        final_output_gdf.plot('Fire_Name', ax=ax)
        ax.set_title("Non-focal independent Fire Perimeters")

    return(focal_gdf, final_output_gdf)

#function 3A
def adequate_attributes(non_overlapping, final_output_gdf):
    enough_attributes = []
    non_enough_attributes = []
    for idx, rows in non_overlapping.iterrows():
        x = 0
        test_rows = rows[['Fire_Name', 'Fire_Code']]
       
        rows_df = rows.to_frame().T
        for value in test_rows:
            if value == 'No code provided':
                x += 1 
            else:
                continue
            if value == 'No Fire Name Provided':
                x += 1
            else:
                continue
            if value == 'None':
                x+=1
            else:
                continue
            
        if x > 1:
            non_enough_attributes.append(rows_df)
        else:
            enough_attributes.append(rows_df)
        
        try:
             non_enough_df  = pd.concat(non_enough_attributes)
             non_enough_gdf = gpd.GeoDataFrame(non_enough_df, geometry = non_enough_df['geometry'],crs = final_output_gdf.crs)
             non_enough_gdf['Minimal Attribute Data'] = 'close to the larger local fire in the same year but not enough info to include'
             final_output_gdf = final_output_gdf.append(non_enough_gdf)
        except ValueError:
             print('no distinct fires')
             
        try:
            enough_df = pd.concat(enough_attributes)
            
            enough_gdf = gpd.GeoDataFrame(enough_df, geometry = enough_df['geometry'],crs = final_output_gdf.crs)
            
            
        except ValueError:
             print('all fires distinct')
     
    fig, ax = plt.subplots(figsize  = (12, 8))
    enough_gdf.plot('Fire_Name', ax=ax)
    ax.set_title("Fires with adequate attributes")
    return(final_output_gdf, enough_gdf)

#function 3B
def ignition_point_intersection_3(non_focal_gdf, ignition_point_shapefile, focal_gdf, final_output_gdf, column_names, ignition_fields):
    
    ignition_points = ignition_point_shapefile # bring in ignition points for that year
    ignition_points=ignition_points.to_crs(crs=focal_gdf.crs) # change crs to match fire polygons
    aoi_ignition_points = gpd.clip(ignition_points, non_focal_gdf) # clip ignition points to polygons for easier processing
    
    #split gdf into polygons that have ignition points and those that do not
    ignition_point_shp = []
    no_ignition_points = []
    
    
    for row in non_focal_gdf.itertuples():
        temp_gdf = pd.Series(row).to_frame().T # convert each row to dataframe
        del temp_gdf[1]#delete repeated index
    
        temp_gdf.columns = column_names # add column names
        geom1 = temp_gdf.geometry
        geom_over =  geom1.iloc[0]
    
        intersection = (aoi_ignition_points.intersects(geom_over))
    
    
    
    
        if any(intersection) == False:
    
            no_ignition_points.append(temp_gdf) # if no ignition points intersect a fire perimeter
    
    
    
        else:
                for rows_ig in aoi_ignition_points.itertuples():
                    temp_gdf_ignition = pd.Series(rows_ig).to_frame().T # convert each row to dataframe
                    del temp_gdf_ignition[1]#delete repeated index
                    temp_gdf_ignition.columns = ignition_fields # add column names
                    geom1_i = temp_gdf_ignition.geometry[0]
    
                    if geom1_i.within(temp_gdf.geometry[0]):
    
                        if temp_gdf['Fire_Name'].item() == temp_gdf_ignition['FIRE_NAME'].item(): # if there is an intersection and there fire name is the same
                            ignition_point_shp.append(temp_gdf) # append the fire to the ignition point list
                        else:
                            no_ignition_points.append(temp_gdf) # if they dont match then append to no ignition point list
                    else:
                        continue
            
    
    try:
        ignition_point_df = pd.concat(ignition_point_shp)
        
        ignition_point_gdf_2 = gpd.GeoDataFrame(ignition_point_df, geometry = ignition_point_df['geometry'],crs = focal_gdf.crs)    
        
    except ValueError:
        print('No polygons contain ignition points')
        ignition_point_gdf_2 = []
    
       
    try:
        no_ignition_point_df = pd.concat(no_ignition_points) 
        no_ignition_point_gdf = gpd.GeoDataFrame(no_ignition_point_df, geometry = no_ignition_point_df['geometry'],crs = focal_gdf.crs)
    except ValueError:
        print('All points have ignition points')
        no_ignition_point_gdf = gpd.GeoDataFrame()
      
    if type(ignition_point_gdf_2) != list:
        temp_gdf_final = ignition_point_gdf_2.reset_index()
    
        
    
        del temp_gdf_final['index']
        
        non_duplicate_fire = []
        duplicate_fire = []
        for idx, rows in temp_gdf_final.iterrows():
            
            
            main_poly_gdf = rows
            main_poly_gdf =pd.DataFrame(main_poly_gdf)
                
            main_poly_gdf_t = main_poly_gdf.T
                
            gdf = gpd.GeoDataFrame(main_poly_gdf_t, geometry = main_poly_gdf_t['geometry'], crs = focal_gdf.crs )
                
    
            other_poly_list = temp_gdf_final.index.tolist()
    
            other_poly_list.remove(idx)
    
            other_poly_gdf = temp_gdf_final[temp_gdf_final.index.isin(other_poly_list)]
            
            dissolved_gdf_4 = gpd.GeoDataFrame()
            intersection_list = []
            for idx1, row1 in other_poly_gdf.iterrows():
                secondary_poly = row1
                secondary_poly_gdf =pd.DataFrame(secondary_poly)
                    
                secondary_f_t = secondary_poly_gdf.T
                geom1 = secondary_poly.geometry
                intersection = gdf.intersects(geom1)
                secondary_acres = secondary_poly.GIS_Acres
                non_focal_acres = gdf.GIS_Acres.item()
                intersection_result = intersection.all()
                intersection_list.append(intersection_result)
                if intersection_result == False:
                    print(gdf['Fire_Name'] + 'does not intersect with' + secondary_poly['Fire_Name'])
                   # non_duplicate_fire.append(main_poly_gdf_t)
                   
                else:
                    print(gdf['Fire_Name'] + 'does intersect with' + secondary_poly['Fire_Name'])
                    if  non_focal_acres >= .25*secondary_acres:
                            duplicate_fire.append(main_poly_gdf_t)
                            duplicate_fire.append(secondary_f_t)
                            
              
                    else:
                        continue
                
            if True in intersection_list:
               print('all duplicates')
            else:
                non_duplicate_fire.append(main_poly_gdf_t)
                print('not a duplicate')
        try:    
        
            df_duplicate = pd.concat(duplicate_fire)
            gdf_duplicate = gpd.GeoDataFrame(df_duplicate, geometry = df_duplicate['geometry'], crs = focal_gdf.crs)
                        
            gdf_duplicate_dissolve = gdf_duplicate.dissolve('Fire_Name', as_index=False)
            
            dissolved_gdf_4 = dissolved_gdf_4.append(gdf_duplicate_dissolve)
           
        except ValueError:
            print('no duplicate fire polygons')
            
        try:
        
            #create geodataframe from non duplicate fire
            df_non = pd.concat(non_duplicate_fire)
           
            
            gdf_non_temp = gpd.GeoDataFrame(df_non, geometry = df_non['geometry'], crs = focal_gdf.crs)
            
        except ValueError:
            print('all values are duplicates')
                
    
        if "dissolved_gdf_4" in locals():
            final_output_gdf = final_output_gdf.append(dissolved_gdf_4)
    
     
      
        if "gdf_non_temp" in locals(): 
            final_output_gdf = final_output_gdf.append(gdf_non_temp)
    
    return no_ignition_point_gdf, focal_gdf, final_output_gdf

#function 3C
def compare_attributes_2(no_ignition_pointsgdf, focal_gdf, final_output_gdf):
    #comparing attributes
    common_attributes = []
    unique_attributes = [] 
    
    no_ignition_pointsgdf['Fire_Name'] = no_ignition_pointsgdf['Fire_Name'].str.upper() #convert fire names to all upper case
    focal_copy = focal_gdf.copy()
    focal_copy['Fire_Name']= focal_copy['Fire_Name'].str.upper() # convert fire names to all upper case
    for idx, rows in no_ignition_pointsgdf.iterrows():
        
        test_rows = rows[['Fire_Type', 'Fire_Name']]
       
        rows_df = rows.to_frame().T
        
            
        for idx1, row1 in focal_copy.iterrows():
             
            test_value_focal = row1[['Fire_Name', 'Fire_Code']]
        compare = test_rows.eq(test_value_focal)
        
        
        if compare.any() == True:
                    common_attributes.append(rows_df) # polygon has name or fire code in common with focal fire
        else:
                    unique_attributes.append(rows_df)# polygon does not have those attributes in common
                
    try:
         non_similiar_attributes  = pd.concat(unique_attributes)
         
         non_similiar_gdf_2 = gpd.GeoDataFrame(non_similiar_attributes, geometry = non_similiar_attributes['geometry'],crs = focal_gdf.crs)
    except ValueError:
         print('most attributes are similiar')
         non_similiar_gdf_22 = []
         
    try:
        similiar_attributes = pd.concat(common_attributes)
        similiar_gdf = gpd.GeoDataFrame(similiar_attributes, geometry = similiar_attributes['geometry'],crs = focal_gdf.crs)
    
        focal_gdf.append(similiar_gdf)
        focal_gdf.dissolve(by = 'Fire_Name', as_index= True)
    except ValueError:
        print('most atttributes are different')
        
    
    if type(non_similiar_gdf_2) != list:
        temp_gdf_final = non_similiar_gdf_2.reset_index()
    
        
    
        del temp_gdf_final['index']
        non_duplicate_fire = []
        duplicate_fire = []
        for idx, rows in temp_gdf_final.iterrows():
            
            
            main_poly_gdf = rows
            main_poly_gdf =pd.DataFrame(main_poly_gdf)
           
            main_poly_gdf_t = main_poly_gdf.T
           
            gdf = gpd.GeoDataFrame(main_poly_gdf_t, geometry = main_poly_gdf_t['geometry'], crs = focal_gdf.crs )
           
      
            other_poly_list = temp_gdf_final.index.tolist()
      
            other_poly_list.remove(idx)
      
            other_poly_gdf = temp_gdf_final[temp_gdf_final.index.isin(other_poly_list)]
            
            dissolved_gdf_5 = gpd.GeoDataFrame()
            intersection_list = []
            for idx1, row1 in other_poly_gdf.iterrows():
                secondary_poly = row1
                secondary_poly_gdf =pd.DataFrame(secondary_poly)
               
                secondary_f_t = secondary_poly_gdf.T
                geom1 = secondary_poly.geometry
                intersection = gdf.intersects(geom1)
                secondary_acres = secondary_poly.GIS_Acres
                non_focal_acres = gdf.GIS_Acres.item()
                intersection_result = intersection.all()
                intersection_list.append(intersection_result)
                if intersection_result == False:
                    print(gdf['Fire_Name'] + 'does not intersect with' + secondary_poly['Fire_Name'])
                   # non_duplicate_fire.append(main_poly_gdf_t)
                  
                else:
                    print(gdf['Fire_Name'] + 'does intersect with' + secondary_poly['Fire_Name'])
                    if  non_focal_acres >= .25*secondary_acres:
                            duplicate_fire.append(main_poly_gdf_t)
                            duplicate_fire.append(secondary_f_t)
                             
                 
                 
                
                
                 
                     
                        
        
        
        
        
        
        
                    else:
                          continue
                 
            if True in intersection_list:
                                         print('all duplicates')
            else:
                  non_duplicate_fire.append(main_poly_gdf_t)
                  print('not a duplicate')
        try:    
         
           df_duplicate = pd.concat(duplicate_fire)
           gdf_duplicate = gpd.GeoDataFrame(df_duplicate, geometry = df_duplicate['geometry'], crs = focal_gdf.crs)
                       
           gdf_duplicate_dissolve = gdf_duplicate.dissolve('Fire_Name', as_index=False)
           
           dissolved_gdf_5 = dissolved_gdf_5.append(gdf_duplicate_dissolve)
            
        except ValueError:
                                  print('no duplicate fire polygons')
             
        try:
         
           #create geodataframe from non duplicate fire
           df_non = pd.concat(non_duplicate_fire)
           
           gdf_non_duplicate_3 = gpd.GeoDataFrame(df_non, geometry = df_non['geometry'], crs = focal_gdf.crs)
             
        except ValueError:
                         print('all values are duplicates')
                 
         
        if "dissolved_gdf_5" in locals():
         final_output_gdf = final_output_gdf.append(dissolved_gdf_5)
         
          
           
        if "gdf_non_duplicate_3" in locals(): 
          final_output_gdf = final_output_gdf.append(gdf_non_duplicate_3)
        
        final_output_gdf.dissolve('Fire_Name', as_index = False)
        fig, ax = plt.subplots(figsize  = (12, 8))
        final_output_gdf.plot('Fire_Name', ax=ax)
        ax.set_title("FINAL AOI w/oout Focal Fire")
        temp_final_output = final_output_gdf.append(focal_gdf)
    return(temp_final_output)

#function 3C
def compare_attributes_2(no_ignition_pointsgdf, focal_gdf, final_output_gdf):
    #comparing attributes
    common_attributes = []
    unique_attributes = [] 
    
    no_ignition_pointsgdf['Fire_Name'] = no_ignition_pointsgdf['Fire_Name'].str.upper() #convert fire names to all upper case
    focal_copy = focal_gdf.copy()
    focal_copy['Fire_Name']= focal_copy['Fire_Name'].str.upper() # convert fire names to all upper case
    for idx, rows in no_ignition_pointsgdf.iterrows():
        
        test_rows = rows[['Fire_Type', 'Fire_Name']]
       
        rows_df = rows.to_frame().T
        
            
        for idx1, row1 in focal_copy.iterrows():
             
            test_value_focal = row1[['Fire_Name', 'Fire_Code']]
        compare = test_rows.eq(test_value_focal)
        
        
        if compare.any() == True:
                    common_attributes.append(rows_df) # polygon has name or fire code in common with focal fire
        else:
                    unique_attributes.append(rows_df)# polygon does not have those attributes in common
                
    try:
         non_similiar_attributes  = pd.concat(unique_attributes)
         
         non_similiar_gdf_2 = gpd.GeoDataFrame(non_similiar_attributes, geometry = non_similiar_attributes['geometry'],crs = focal_gdf.crs)
    except ValueError:
         print('most attributes are similiar')
         non_similiar_gdf_2 = []
         
    try:
        similiar_attributes = pd.concat(common_attributes)
        similiar_gdf = gpd.GeoDataFrame(similiar_attributes, geometry = similiar_attributes['geometry'],crs = focal_gdf.crs)
    
        focal_gdf.append(similiar_gdf)
        focal_gdf.dissolve(by = 'Fire_Name', as_index= True)
    except ValueError:
        print('most atttributes are different')
        
    
    if type(non_similiar_gdf_2) != list:
        temp_gdf_final = non_similiar_gdf_2.reset_index()
    
        
    
        del temp_gdf_final['index']
        non_duplicate_fire = []
        duplicate_fire = []
        for idx, rows in temp_gdf_final.iterrows():
            
            
            main_poly_gdf = rows
            main_poly_gdf =pd.DataFrame(main_poly_gdf)
           
            main_poly_gdf_t = main_poly_gdf.T
           
            gdf = gpd.GeoDataFrame(main_poly_gdf_t, geometry = main_poly_gdf_t['geometry'], crs = focal_gdf.crs )
           
      
            other_poly_list = temp_gdf_final.index.tolist()
      
            other_poly_list.remove(idx)
      
            other_poly_gdf = temp_gdf_final[temp_gdf_final.index.isin(other_poly_list)]
            
            dissolved_gdf_5 = gpd.GeoDataFrame()
            intersection_list = []
            for idx1, row1 in other_poly_gdf.iterrows():
                secondary_poly = row1
                secondary_poly_gdf =pd.DataFrame(secondary_poly)
               
                secondary_f_t = secondary_poly_gdf.T
                geom1 = secondary_poly.geometry
                intersection = gdf.intersects(geom1)
                secondary_acres = secondary_poly.GIS_Acres
                non_focal_acres = gdf.GIS_Acres.item()
                intersection_result = intersection.all()
                intersection_list.append(intersection_result)
                if intersection_result == False:
                    print(gdf['Fire_Name'] + 'does not intersect with' + secondary_poly['Fire_Name'])
                   # non_duplicate_fire.append(main_poly_gdf_t)
                  
                else:
                    print(gdf['Fire_Name'] + 'does intersect with' + secondary_poly['Fire_Name'])
                    if  non_focal_acres >= .25*secondary_acres:
                            duplicate_fire.append(main_poly_gdf_t)
                            duplicate_fire.append(secondary_f_t)
                             
                 
                 
                
                
                 
                     
                        
        
        
        
        
        
        
                    else:
                          continue
                 
            if True in intersection_list:
                                         print('all duplicates')
            else:
                  non_duplicate_fire.append(main_poly_gdf_t)
                  print('not a duplicate')
        try:    
         
           df_duplicate = pd.concat(duplicate_fire)
           gdf_duplicate = gpd.GeoDataFrame(df_duplicate, geometry = df_duplicate['geometry'], crs = focal_gdf.crs)
                       
           gdf_duplicate_dissolve = gdf_duplicate.dissolve('Fire_Name', as_index=False)
           
           dissolved_gdf_5 = dissolved_gdf_5.append(gdf_duplicate_dissolve)
            
        except ValueError:
                                  print('no duplicate fire polygons')
             
        try:
         
           #create geodataframe from non duplicate fire
           df_non = pd.concat(non_duplicate_fire)
           
           gdf_non_duplicate_3 = gpd.GeoDataFrame(df_non, geometry = df_non['geometry'], crs = focal_gdf.crs)
             
        except ValueError:
                         print('all values are duplicates')
                 
         
        if "dissolved_gdf_5" in locals():
         final_output_gdf = final_output_gdf.append(dissolved_gdf_5)
         
          
           
        if "gdf_non_duplicate_3" in locals(): 
          final_output_gdf = final_output_gdf.append(gdf_non_duplicate_3)
        
        final_output_gdf.dissolve('Fire_Name', as_index = False)
        fig, ax = plt.subplots(figsize  = (12, 8))
        final_output_gdf.plot('Fire_Name', ax=ax)
        ax.set_title("FINAL AOI w/oout Focal Fire")
        temp_final_output = final_output_gdf.append(focal_gdf)
    return(temp_final_output)


def tier_processing(tier_gdf, column_names, ignition_fields, ignition_shp, temp_gdf_final, year_gdf, row, x, focal_list ):
        indexes_to_drop = []
        
        final_output_gdf = gpd.GeoDataFrame() # creates final geodataframe that outputs get appended to, adds crs from perimeter data 
        non_focal_gdf = gpd.GeoDataFrame()
        
        focal = row
        df = pd.Series(focal).to_frame().T
        df.columns = column_names
        
        
        
        geom = gpd.GeoSeries(df.geometry, crs = tier_gdf.crs)
        buffer = geom.buffer(500)
        non_focal_list = []
        new_tier_list = []
        
        
        other_poly_list = year_gdf.index.tolist()
        
        other_poly_list.remove(df.Index.item())
        
        
        other_poly_gdf = year_gdf[year_gdf.index.isin(other_poly_list)]
        for idx1, row1 in other_poly_gdf.iterrows():
            
            geom1 = row1.geometry
            if geom1.intersects(buffer.iloc[0]):
                
                try:
                    
                    
                    non_focal_list.append(row1.to_frame().T)
                    
                   
                    
                except ValueError:
                    print('no polygons within 500m')
                    non_focal_gdf = []
                
                
                    
                
            else:
                
                continue
        try:
            df_non = pd.concat(non_focal_list)
            non_focal_gdf = gpd.GeoDataFrame(df_non, geometry = df_non['geometry'], crs = tier_gdf.crs)  
        except ValueError:
            print('no non focal polygons')
        #tier_gdf.drop(tier_gdf[indexes_to_drop], inplace = True)
        focal_gdf = gpd.GeoDataFrame(df, geometry = df['geometry'], crs = tier_gdf.crs)
        #non_focal_gdf.plot('Fire_Name')
        print(focal_gdf['Fire_Name'])
        
                
        
           
        indexes_to_drop.append(df.index.item()) # erase focal gdf from tier gdf for next round
        '''
        if not indexes_to_drop:
            print('first iteration')
        else:
            #tier gdf
            list_test = tier_gdf.index.values.tolist()
            drop_list = []
            for index_1 in indexes_to_drop:
            
                if index_1 in list_test:
                    drop_list.append(index_1)
                
            update = tier_gdf.drop(tier_gdf.index[drop_list])
            tier_gdf_2 = update
            
            #year gdf
            list_test_year = year_gdf.index.values.tolist()
            drop_list_year = []
            for index_2 in indexes_to_drop:
                
                if index_1 in list_test_year:
                    drop_list_year.append(index_2)
                    
                    
            update_2 = year_gdf.drop(year_gdf.index[drop_list_year])
            year_gdf_2 = update_2
        '''
        focal_list.append(focal_gdf)
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
                
                #print('completed function begin', file =open('output.txt', 'a+') )
                
                
                large_overlapping_gdf, small_overlap_gdf = overlapped_percentage(overlapping_polygons, focal_gdf, column_names)
                
                #print('completed function overlap percentage', file =open('output.txt', 'w+' ))
                
                
                
           
                
                if type(large_overlapping_gdf) == list:
                        print('no large overlapping polygons')
                else:
                        
                        #function 1A
                        duplicate, non_duplicate_fires = acerage_comparison(focal_gdf, large_overlapping_gdf, column_names)
                        #print('completed function 1A', file =open('output.txt', 'a+' ))
                        if type(duplicate) == list:
                            print('no duplicate')
                        else:
                            focal_gdf = duplicate # new focal gdf
            
                        if type(non_duplicate_fires) == list:
                            print('all polygons were duplicates')
                        else:
                        
                        
                            
                            #function 1B
                            no_ignition_points_gdf, focal_gdf, final_output_gdf = ignition_point_intersection(non_duplicate_fires, ignition_shp, focal_gdf, final_output_gdf, column_names, ignition_fields)
                            #print('completed function 1B', file =open('output.txt', 'a+') )
                            
                            
                
                            
                            
                            #function 1C
                            focal_gdf, final_output_gdf = compare_attributes(no_ignition_points_gdf, focal_gdf, final_output_gdf)
                            #print('completed function 1C', file =open('output.txt', 'a+') )
                
                
                
                
                #second tree 
            
                #testing purposes
                #small_overlap = test_gdf.copy()
                if type(small_overlap_gdf) == list:
                    
                    print('no small overlapping polygons')
                else:
                    
                    
                    #function 2A
                    non_focal_ignition_points_gdf, focal_gdf, final_output_gdf, fires_with_ignition =  ignition_point_intersection_2(small_overlap_gdf, ignition_shp, focal_gdf, final_output_gdf, column_names, ignition_fields )
                   # print('completed function 2A', file =open('output.txt', 'a+') )
                    #function 2B
                    focal_gdf, final_output_gdf = compare_attributes_1(non_focal_ignition_points_gdf, focal_gdf, final_output_gdf)
                    
                    #print('completed function 2B', file =open('output.txt', 'a+') )
                
                
                if type(non_overlapping) == list:
                    print('all polygons overlap')
            
                else:
                    #third tree
                    #non overlapping varaible gdf#third tree
                    #non overlapping varaible gdf
                    #function 3A
                    final_output_gdf, attributes_gdf = adequate_attributes(non_overlapping, final_output_gdf)
                    #print('completed function 3A', file =open('output.txt', 'a+') )
                    
                    
                    
            
                    
                    
                    #function 3B
                    non_overlapping_ignition_points_gdf, focal_gdf, final_output_gdf =  ignition_point_intersection_3(attributes_gdf, ignition_shp, focal_gdf, final_output_gdf, column_names, ignition_fields)
                    #print('completed function 3B', file =open('output.txt', 'a+') )
                    #function 3C
                if not 'non_overlapping_ignition_points_gdf' in locals():
                    print('no overlapping')
                else: 
                    if non_overlapping_ignition_points_gdf.empty:
                        print('all polygons had ignition points')
                        temp_final_output = final_output_gdf
                    else:
                        temp_final_output = compare_attributes_2(non_overlapping_ignition_points_gdf, focal_gdf, final_output_gdf)
                        #print('completed function 3C', file =open('output.txt', 'a+') )
            
            
            
            
                if not 'temp_final_output' in locals():
                    temp_final_output = final_output_gdf
                    
                else: 
                    print('continue')
                    
                    temp_gdf_final = temp_gdf_final.append(temp_final_output.reset_index(drop = True))
                
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
        #print('completed decision tree for:{}'.format(focal_gdf['Fire_Name']), file =open('output.txt', 'a+') )
        del gdf['Index']
        return gdf, indexes_to_drop, focal_list
    