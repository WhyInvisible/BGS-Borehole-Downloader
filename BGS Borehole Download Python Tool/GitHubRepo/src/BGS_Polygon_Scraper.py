# -*- coding: utf-8 -*-
"""
Created on Fri Feb  5 16:20:06 2021

@author: garet
"""
import os
import glob
import io
import glob
import requests
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
import img2pdf
import json
import tkinter as tk


class BGS:
    # store hidden parameters - these might need editing for different users
    __proxies = {'http': None}
    __bgs_boreholes = (r"./borehole/borehole.shp")
    __cache = (r".tmp")

    def __init__(self, bbox=None, **kwargs):
        '''
        Initiates instance of the class.

        Parameters
        ----------

        bbox : bounding pass to pass to geopandas.read_file(). From geopandas:
                    "Filter features by given bounding box, GeoSeries, or
                     GeoDataFrame. CRS mis-matches are resolved if given a
                     GeoSeries or GeoDataFrame."
               If bbox is None, returns all BGS boreholes (slow and memory
               intensive - approx 1.3 million records).

        Returns
        -------
        Geopandas dataframe of the BGS boreholes within the specified bbox
        extent

        '''
        self.boreholes = gpd.read_file(BGS.__bgs_boreholes,
                                       bbox=bbox, crs='epsg:27700',
                                       **kwargs)
        self.bbox = bbox

        image_paths = pd.DataFrame()
        for index, row in self.boreholes.iterrows():
            if not image_paths.empty:
                image_paths = image_paths.append(
                        BGS.get_image_paths(bgs_id=int(row['BGS_ID'])))
            else:
                image_paths = BGS.get_image_paths(bgs_id=int(row['BGS_ID']))

        # merge data from BGS boreholes dataframe
        image_paths = self.boreholes.merge(
                image_paths, how='left', on='BGS_ID')

        self.image_paths = image_paths

    @classmethod
    def boreholes_from_polygon(cls, polygon_geom):
        '''
        Function to return a class instance from a point source based on
        British National Grid easting and northing within a specified buffer
        distance.

        Parameters
        ----------

        easting : the Easting (in British National Grid coordinates)

        northing : the Northing (in British National Grid coordinates)

        buffer : buffer distance from centre point (in m)

        Returns
        -------
        Pandas dataframe where each row gives the BGS_ID, page number for the
        report and the url for the report page

        '''
        
        
        polygon = gpd.GeoSeries(
                    polygon_geom, crs='epsg:27700')
        return cls(polygon)

    @classmethod
    def boreholes_from_bgs_ids(cls, bh_ids):
        '''
        Function to return a class instance from a BGS ID or IDs.

        Parameters
        ----------

        bh_ids : BH ID or IDs to return class instance for. May be string for
                 one borehole or list for multiple boreholes.

        Returns
        -------
        Pandas dataframe where each row gives the BGS_ID, page number for the
        report and the url for the report page

        '''
        if type(bh_ids) is str:
            print("string")
        elif type(bh_ids) is list:
            if not all([type(c) is str for c in bh_ids]):
                raise TypeError("Expected all values in bh_ids to be string")
            else:
                print("list")
        else:
            raise TypeError("Expected bh_ids to be str or list, but "
                            "encountered {}".format(type(bh_ids)))
#        return cls(point_buffer, **kwargs) #kwargs to pass to fiona via geopandas on function call)

    @staticmethod
    def get_image_paths(bgs_id):
        '''
        Function to return a dataframe with urls for the provided BGS borehole
        ID

        Parameters
        ----------

        bgs_id : The BGS_ID to return a list of urls for

        Returns
        -------
        Pandas dataframe where each row gives the BGS_ID, page number for the
        report and the url for the report page

        '''

        pathToCache = BGS.__cache
        pathtoFile = pathToCache+"/"+str(bgs_id)+"_imgpath.json"
        image_paths = pd.DataFrame(data={
                                        'BGS_ID': [],
                                        'PAGE': [],
                                        'url': []
                                        }, dtype='int64')
        if not os.path.isfile(pathtoFile):
            # setup empty dataframe to append results

            # iterate over each line from the BGS website
            for i, line in enumerate(
                    requests.get(
                            r"http://scans.bgs.ac.uk/sobi_scans/"
                            "boreholes/{bgs_id}/images".format(bgs_id=bgs_id),
                            proxies=BGS.__proxies).text.split("\r\n")):
                # only consider lines with text
                if not line == "":
                    image_paths = image_paths.append(
                            pd.DataFrame(data={
                                    'BGS_ID': [bgs_id],
                                    'PAGE': [i+1],
                                    'url': [line.strip()]
                                            }
                                        ), ignore_index=True)
            if len(image_paths):
                # replace invalid urls
                image_paths.loc[
                        image_paths['url'].str.contains(
                                'the requested borehole does not exist',
                                case=False), 'url'
                                ] = 'Invalid location - likely to be confidential'
                data = image_paths.to_json(orient='index')
            else:
                print("Borehole "+str(bgs_id)+" data is not available")
                data = '{"url":"Invalid location"}'

            with open(pathtoFile, 'w', encoding='utf-8') as f:
                #data = json.dumps(data, indent=4, sort_keys=True)
                json.dump(data, f)

        else:
            #print(json,pathtoFile)
            with open(pathtoFile, 'r', encoding='utf-8') as f:
                data = json.load(f)
            #print(str(data)) 
            if "Invalid" not in str(data):
                image_paths = pd.read_json(data).T 
            #print("data",data)
            #image_paths
        return image_paths

    @staticmethod
    def download_images(image_paths_df, output_path, return_pdf=True):
        '''
        Function to download images from BGS website with functionality to
        convert all files to a combined PDF for each borehole (default
        behaviour)

        Parameters
        ----------

        image_paths_df : df returned from get_image_paths() function

        output_path : the root directory to save the output pdfs to

        Returns
        -------
        Pandas dataframe where each row gives the BGS_ID, page number for the
        report and the url for the report page

        '''
        # iterate over each row of df and download the image
        for index, row in image_paths_df.iterrows():
            # check url
            #print(row["url"])
            if not isinstance(row['url'], float):
                if not ("Invalid") in row['url']:
                    
                    OUTPUT_IMAGE = r"{path}\{borehole}_{page}.png".format(
                                    path=r'./.tmp', borehole=row['REGNO'],
                                    page=row['PAGE'])
                    if not os.path.isfile(OUTPUT_IMAGE):
                        if "localhost" in row['url']:
                            row['url'] = row['url'].replace("localhost:8080","scans.bgs.ac.uk")
                            print("Downloading : "+row["url"])
                            try:
                                open(OUTPUT_IMAGE, 'wb')\
                                        .write(
                                                requests.get("{url}.png".format(
                                                        url=row['url'].strip()),
                                                            proxies=BGS.__proxies)
                                                .content)
                            # in case there's a problem with the borehole name
                            # TODO: look at introducing a function to check the filename
                            # is compliant. If not, substitute characters (e.g. / for -)
                            except FileNotFoundError:
                                print("could not save image for BH {borehole} - {page}"
                                    .format(borehole=row['REGNO'], page=row['PAGE']))


        # convert images for each borehole to a PDF
        if return_pdf:
            #os.chdir(output_path)
            for bh in image_paths_df['REGNO'].unique():
                for index, row in image_paths_df.loc[
                        image_paths_df['REGNO'] == bh].iterrows():
                    # check url
                    if not isinstance(row['url'], float):
                        if not ("Invalid location - "
                            "likely to be confidential") in row['url']:
                            filename = r"{output_path}/{bh}.pdf".format(
                                    output_path=output_path, bh=row['REGNO'].replace('/','_'))
                            if not os.path.isfile(filename):
                                print(filename, bh)
                                with open(filename, "wb") as f:
                                    ListOfImage = [i for i in glob.glob(".tmp" + '/**/*.png', recursive=True)
                                            if (i.endswith(".png") and bh in i) ]
                                    try:
                                        f.write(img2pdf.convert(ListOfImage))
                                    except:
                                        # Add command to delete empty pdf
                                        print(f"Image not available for {row['REGNO']}")
            # For caching purposes, keeping images for later use
            # delete png files to clear up output folder
            #images = glob.glob("*.png")
            #for image in images:
            #    os.remove(image)


def scrape_BGS_csv():
    '''
    This function automatesthe creation of the polygon and method calls
    which have previously been done manually in the terminal.

    The function requests a .csv using tkinter and expects the format to
    match what you get from https://gridreferencefinder.com/

    The function also requsts where you want to save the pdf outputs
    '''
    # Usetkinter to request a file path for the csv with points
    print('Select csv input file from Gridreferencefinder\n')
    root = tk.Tk()
    root.filename = tk.filedialog.askopenfilename(
                                               initialdir="/",
                                               title="Select csv file",
                                               filetypes=(("csv files", "*.csv"),)
                                               )
    csv_path = root.filename
    print(csv_path)
    root.destroy()  # This closes the tk window once the operation is done

    # Convert csv to dataframe
    df = pd.read_csv(csv_path)

    # Turn easting and northing cols into lists
    easting_point_list = list(df['X (Easting)'])
    northing_point_list = list(df['Y (Northing)'])

    # Convert points to polygon
    polygon_geom = Polygon(zip(easting_point_list, northing_point_list))

    # Select output path with tkinter
    print('Select output folder\n')
    root = tk.Tk()
    root.directory = tk.filedialog.askdirectory()
    output_path = root.directory
    print(output_path)
    root.destroy()

    # Run methods
    XYZ = BGS.boreholes_from_polygon(polygon_geom)
    BGS.download_images(XYZ.image_paths, output_path)
    
    # Save csv of boreholes dataframe
    df2 = gpd.read_file(
                        r"./borehole/borehole.shp",
                        bbox=polygon_geom,
                        crs='epsg:27700',
                        )
    df2.to_csv(output_path + '/boreholes_in_polyline.csv')

    print('\nDownload complete')