# Model Documentation - updated February 13, 2023


### Python and conda installation
First thing’s first, you’re going to need to install Python to run the code. Here, we’re using conda which will allow us to easily standardize Python packages across operating systems. 

Head to the miniconda installer and download the correct version for your operating system. Follow the instructions to install conda to your system.

Once that is downloaded and you’ve followed the necessary directions to install miniconda, open terminal.

The first step is to make a new conda environment. An environment is just a place to install packages to and keep them organized. Run the following commands in terminal to create and activate a new environment. You’ll only need to create the environment once but you’ll need to activate it each time you open a new terminal window:

- ```conda create -n myenv```
- ```conda activate myenv```

Run the following command in terminal to install all the packages that the model needs to run:

- ```conda install -c conda-forge xarray netcdf4 cfgrib requests matplotlib cartopy pandas metpy timezonefinder python-dateutil imageio adjusttext```

Now we’re all set! Next let’s take a look at how to install and configure my model to run whatever simulations you need to run.

### Initial model setup
First, download the directory. On this site, click the green button that says "Code". This will open a dropdown menu. There will be two available tabs beneath that, "Local" and "Codespaces"; make sure "Local" is selected. Beneath that, there will be a button titled "Download ZIP". This will save a file likely to your "downloads" directory, but feel free to move it wherever you please. Open the file and unzip it to decompress it and rename it to "model". Note the path to this directory. Here are a few example paths so you know what it might look like:

- MacOS: ```/Users/clamalo/documents/model/```
- Windows: ```C:\Users\clamalo\documents\model\```
- Linux: ```/home/clamalo/documents/model/```

In terms of installing the model, that’s all you need to do! You’re ready to start configuring the model.

### Installing future updates
Inevitably, I will make improvements to the model; adding new plot types, speeding up data ingest and processing, etc. You can check the model update log at https://clamalo.github.io/model/model_update_log.html. The easiest way for you to install the future updates is to simply delete your model directory and repeat the above step, installing the model directory from scratch (you do not need to set up conda each update). When the model updates, also be sure to check the documentation below to see if anything has changed from the previous version. If you'd like to be automatically notified when I implement a major model upgrade (not just minor bug fixes), fill out the following form with your email: https://forms.gle/xsa8vzTUWvcoPE7p8.

### Configuring the model
Open the folder that you just installed. Within that directory, there is a file called ```model_config.txt```. This is the only file you’ll ever need to edit to change the configuration of the model. Open the file in a text editor (most operating systems will do this for you automatically if you double click on the file).

The file should contain a list of parameters with the parameter name on the left side of an equals sign and the data for the parameter on the right side.

You can change each of these parameters to tweak the model. I’ll go through them one by one and explain what each of them does.

```directory```
- You’ll have to change this to the path to the model directory. Be sure to include a slash matching the formatting of the rest of the slashes in the path at the end:
- Example: ```directory = /Users/clamalo/documents/model/```

```ingest```
- This variable controls whether the model runs with new data or old data. This variable can only be set to True or False (capitalization is important!).
- Example: ```ingest = True```

```canadian```
- The model is configured to run with either American-only initialization data or a blend of American and Canadian initialization data. With this variable, you get to decide whether the initialization data is 50/50 American/Canadian (True) or 100% American (False). Using a blended approach is typically better but it depends on the situation.
- Example: ```canadian = True```

```american_data_percentage```
- This variable controls the ratio of American to Canadian initialization data. This number must be between 0 and 1 (inclusive). Obviously, this value only matters if canadian = True. For example, a value of 0.7 here would be 70% American initialization data and 30% Canadian. 0 is all Canadian, 1 is all American.
- Example: ```american_data_percentage = 0.5```

```compute_wind```
- This variable determines whether you want wind to be simulated or not. Toggling wind to True does increase processing time, since computing wind in complex terrain is computationally expensive. If this variable is toggled to False, the fifth subplot on the point forecast plots will only show temperature (instead of temperature and SLR) and the sixth subplot will be SLR rather than wind.
- Example: ```wind = True```

```step```
- This variable controls the timestep output of the model. This can be an integer from a minimum of 1 to a maximum of 6. For example, if the step is set to 3, the model will compute every third hour. Keep in mind that if you are using Canadian data, the step can only be either 3 or 6. Regardless of if you are using Canadian initialization data, it's recommended to keep the step to either 1, 3, or 6 for the most accurate data.
- Example: ```step = 3```

```first_frame```
- This variable controls the initial frame that the model starts at. It’s best to have this at 0.
- Example: ```first_frame = 0```

```max_frame```
- This variable controls the maximum hour that the model runs to. For example, a max_frame value of 120 would be a 5 day forecast. If the step variable is set to be less than 3, the maximum frame must be 120 or less. With other step values, the longest supported maximum frame is 240. If running without the Canadian data, the longest supported maximum frame is 384.
- Example: ```max_frame = 120```

```ingest_source```
- This controls the source of the American data, either from the NOAA’s NOMADS service or their cloud data partnership with AWS. It’s best to have this set to nomads, but if you are rate limited by NOAA, you can change this variable to aws.
- Example: ```ingest_source = nomads```

```detect_recent_run```
- This controls whether the model automatically selects the most recent initialization data to run with to reduce confusion that may arise from having to manually set it (more on this below). Generally speaking, unless your running a special case with older data, it's a good idea to have this toggled to True.
- Example: ```detect_recent_run = True```

```datestr```
- This variable controls the date that the initialization data is pulled from. The file nomenclature is as follows: YYYYMMDD. If ```detect_recent_run```is toggled to True, this variable doesn't matter.
- Example: ```datestr = 20230131```

```cycle```
- Similarly, this controls the model cycle that the initialization data is coming from. This is either 00, 06, 12, or 18 (00 or 12 only if using Canadian data). If ```detect_recent_run```is toggled to True, this variable doesn't matter.
- Example: ```cycle = 12```

```plot_types```
- This is where you can pick what variables you want to plot. Currently, the supported variables are: snow, total_snow, tp (precipitation), total_tp, t2m (temperature), slr (snow to liquid ratio), wind, and ptype (precipitation type). If you want to plot more than one parameter, separate them by commas. Stay tuned, as more variables will be added soon. Keep in mind that the more plot types you have, the longer the model will take to run.
- Example: ```plot_types = snow, total_snow, t2m```

```plot_states```
- You can toggle this True or False to control whether state and province lines are plotted on the charts.
- Example: ```plot_counties = True```

```plot_counties```
- You can toggle this True or False to control whether county lines are plotted on the charts.
- Example: ```plot_counties = True```

```plot_points```
- If this variable is toggled to True, your points will be plotted on the maps as scatter points. If you have a lot of points in the selected domain, it may clutter up the maps.
- Example: ```plot_points = False```

```domain```
- Now, perhaps the most important variable of all. This variable controls what area is computed by the model. The format is top latitude, west longitude, bottom latitude, east longitude. The longitudes must be in a -180-180 format, not 0-360. The model can now process any domain in the world north of -60 degrees latitude. Domains cannot cross the antimeridian (where 180 turns to -180 in the Pacific). Keep in mind that the larger the domain, the longer the model will take to process. A good place to get coordinates is https://caltopo.com/map.html.
- Example: ```domain = 52,-125,46,-115```
- Here are a few more preset domains:
- ```domain = 52,-125,35,-65``` (entire US)
- ```domain = 52,-125,35,-100``` (West)
- ```domain = 42,-125,36,-115``` (California)
- ```domain = 51,-125,45,-115``` (PNW)
- ```domain = 42,-113.5,37,-104``` (Utah & Colorado)
- ```domain = 46,-80.5,40,-69``` (Northeast)

When you’re done changing the parameters of your model run, be sure to save the file!


### Changing the points
The point forecast plots are completely customizable. In the model directory, there is a file called ```points.txt```. You can open this file the same way you opened ```model_config.txt```. Inside the file, you’ll find a lot of my presaved points. Feel free to use this list, add to it, or create your own. 

The format for a point is ```name,latitude,longitude,elevation,state/domain/region```. Make sure that the longitude is in a -180-180 format.

When running the model, it will only plot points that are within the selected domain.


### Running the model
If you’ve made it this far, congratulations! You’ve made it past the hardest part. Now for the fun part: running the model.

Open up a new terminal window and activate your conda environment. You'll have to do this each time you open a new terminal window to run the model:

- ```conda activate myenv```

Now, copy the path to your model directory and then use the cd command in the terminal window to navigate to that folder:

- ```cd path_to_directory```

Finally, run the following command and hit enter to run the model:

- ```python3 model.py```

From there, the model will begin running and saving the outputs. Inside the model directory that you downloaded, there are two subdirectories: figures and points. Point forecast charts set in the points.html file will go into the points folder and all other charts will be found in the figures folder in their respective subfolders according to variable!
