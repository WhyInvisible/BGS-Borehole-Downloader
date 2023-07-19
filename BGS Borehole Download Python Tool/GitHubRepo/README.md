# BGS_BH_scraper

## Description
This tool downloads and creates pdfs of borehole logs within a polygon from the BGS website.

## Repository Ownership
* **Practice**: MMBC
* **Sector**: Geotechnical
* **Original Author(s)**: Gareth Nash, Luc Jonveaux, Sam Williams
* **Contact Details for Current Repository Owner(s)**: Mark Edmondson
## Installation Instructions
Sync the repository from the sharepoint location [here](https://mottmac.sharepoint.com/teams/bf-00835/Documents/Forms/AllItems.aspx?RootFolder=%2Fteams%2Fbf%2D00835%2FDocuments%2FGeotechnical%2FBGS%20Borehole%20Scraper&FolderCTID=0x01200026D8C69D60734D4EBB4ABAD041A19C5A). Please do not create your own clone, the reason for this is that the sharepoint folder caches all previously downloaded borehole logs so if they are requested more than once they are pulled from Sharepoint instead of the BGS website.

Once you have synced the sharepoint location right click the folder and select 'Always keep on this device'. This ensures the database files the script needs are read and the cache of previously downloaded images are made use of.

In order to successfully run the code in this respository, it is recommended that you create a virtual environment and install the required packages from the geo_env.yml file provided.

To install the environment open a Conda Powershell and navigate to the repository location. This is most easily done by navigating in Windows explorer and copying and pasting the path in. The path shown below will be user specific, please change as appropriate.
```
> cd -path 'C:\Users\YOUR USER NAME\Mott MacDonald\MMBC Team Site - BGS Borehole Scraper\GitHubRepo\src'
```
Install the conda environment using the command below
```
> conda env create -f geo_env.yml
```
Activate the environment using
```
> conda activate geo_env
```

## Running the Code
You can either copy the code from the 'Terminal text file.txt' after adding the desired coordinates and output path 

OR

1) go to [Grid reference finder](https://gridreferencefinder.com/)
2) pick points (using right mouse click) that would make the outline of a polygon if joined up enclosing the area of interest
3) click the 'Export points to csv' button
4) paste the text into Excel using the text import wizard or into notebook and save as a .csv file
5) run the following in a conda Powershell console (please adjust the path as appropriate)
```
> cd -path 'C:\Users\YOUR USER NAME\Mott MacDonald\MMBC Team Site - BGS Borehole Scraper\GitHubRepo\src'
> conda activate geo_env
> python
>>> from BGS_Polygon_Scraper import *
>>> scrape_BGS_csv()
```
6) when prompted navigate to the .csv and then to where you want the borehole pdfs saved
7) wait until the download completes
