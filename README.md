# Model Documentation - updated February 25, 2023

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
Open the folder that you just installed. Within that directory, there is a file called ```model_config.txt```. Open the file in a text editor (most operating systems will do this for you automatically if you double click on the file).

The file should contain a list of parameters with the parameter name on the left side of an equals sign and the data for the parameter on the right side.

You can change each of these parameters to tweak the model. I’ll go through them one by one and explain what each of them does.

```ingest```
- This variable controls whether the model runs with new data or old data. This variable can only be set to True or False (capitalization is important!).
- Example: ```ingest = True```

```canadian```
- The model is configured to run with either American-only initialization data or a blend of American and Canadian initialization data. With this variable, you get to decide whether the initialization data is a mix of American and Canadian data (True) or 100% American (False). Using a blended approach is typically better, but it depends on the situation.
- Example: ```canadian = True```

```compute_wind```
- This variable determines whether you want wind to be simulated or not. Toggling wind to True does increase processing time, since computing wind in complex terrain is computationally expensive. If this variable is toggled to False, the fifth subplot on the point forecast plots will only show temperature (instead of temperature and SLR) and the sixth subplot will be SLR rather than wind.
- Example: ```wind = True```

```step```
- This variable controls the timestep output of the model. This can be an integer from a minimum of 1 to a maximum of 6. For example, if the step is set to 3, the model will compute every third hour. Keep in mind that if you are using Canadian data, the step can only be either 3 or 6. Regardless of if you are using Canadian initialization data, it's recommended to keep the step to either 1, 3, or 6 for the most accurate data.
- Example: ```step = 3```

```first_frame```
- This variable controls the initial frame that the model starts at. It’s best to have this at 0, but this number can be any multiple of 6.
- Example: ```first_frame = 0```

```max_frame```
- This variable controls the maximum hour that the model runs to. For example, a max_frame value of 120 would be a 5 day forecast. If the step variable is set to be less than 3, the maximum frame must be 120 or less. With other step values, the longest supported maximum frame is 240. If running without the Canadian data, the longest supported maximum frame is 384.
- Example: ```max_frame = 120```

```model_cycle```
- This variable controls the model cycle that the initialization data is pulled from. Typically, it's best to have this set to "Detect" (capitalization is important!), as that will automatically detect the most recent data. If you want to manually select a model cycle, input the following format: YYYYMMDDHH. Note that if using Canadian data, their data archive only goes back a few cycles.
- Example: ```model_cycle = Detect```

```plot_types```
- This is where you can pick what variables you want to plot. Currently, the supported variables are: snow, total_snow, tp (precipitation), total_tp, t2m (temperature), slr (snow to liquid ratio), wind, and ptype (precipitation type). If you want to plot more than one parameter, separate them by commas. Stay tuned, as more variables will be added soon. Keep in mind that the more plot types you have, the longer the model will take to run.
- Example: ```plot_types = snow, total_snow, ptype```

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
- Now, perhaps the most important variable of all. This variable controls what area is computed by the model. The format is top latitude, west longitude, bottom latitude, east longitude. The longitudes must be in a -180-180 format, not 0-360. The model can now process any domain in the world north of -60 degrees latitude. Domains cannot cross the antimeridian (where 180 turns to -180 in the Pacific). Keep in mind that the larger the domain, the longer the model will take to process. A good place to get coordinates is https://caltopo.com/map.html. The model can now save domains as strings (see ```Saving domains``` below).
- Example: ```domain = 52,-125,46,-115```
- Example 2: ```domain = West``` (the West domain is defined in ```domains.txt```)

```scatters_only```
- This variable controls whether the model only plots the daily snowfall total scatter plots for your points for your domain. Typically, this should be set to False. However, if you've already run the model cycle and want to check out some scatter plots for another domain, you can change the ```domain``` variable and run the script with this parameter set as True.
- Example: ```scatters_only = False```

```day_and_night_scatter_separate```
- If this variable is set as True, it will plot both day (8am-4pm) and night (4pm-8am) scatter plots. If it is set as False, it will plot the scatters with day and night included (4pm prior day-4pm).
- Example: ```day_and_night_scatter_separate = False```

```points_tag```
- You can now tag points with keywords (more on this in the ```Changing points``` section). This variable makes it so that the total scatter plots will only plot points that are only tagged with the desired keyword. If you want all points to be plotted, set this variable as None.
- Example: ```points_tag = None```

When you’re done changing the parameters of your model run, be sure to save the file!

### Changing points
The point forecast plots are completely customizable. In the model directory, there is a file called ```points.txt```. You can open this file the same way you opened ```model_config.txt```. Inside the file, you’ll find a lot of my presaved points. Feel free to use this list, add to it, or create your own. 

The format for a point is ```name,latitude,longitude,elevation,tag```. Make sure that the longitude is in a -180-180 format. Be sure that there are no extra/empty lines in the file. The major resorts in my ```points.txt``` file are tagged with "Work", meaning if I set the ```points_tag``` variable in ```model_config.txt``` as "Work", it will only plot these points.

When running the model, it will only plot points that are within the selected domain (automatically detected based on the latitudes and longitudes).

### Saving domains
You can save frequented domains in the ```domains.txt``` file. To do so, open the file and follow the same top latitude, west longitude, bottom latitude, east longitude format as before. Inside the file, you’ll find several of my presaved domains. Feel free to use this list, add to it, or create your own. Be sure that there are no extra/empty lines in the file. The domains in this file are referenced by the ```domain``` parameter if a string domain is set in ```model_config.txt```. 

### Running the model
If you’ve made it this far, congratulations! You’ve made it past the hardest part. Now for the fun part: running the model.

Open up a new terminal window and activate your conda environment. You'll have to do this each time you open a new terminal window to run the model:

- ```conda activate myenv```

Now, copy the path to your model directory and then use the cd command in the terminal window to navigate to that folder:

- ```cd path_to_directory```

Finally, run the following command and hit enter to run the model:

- ```python3 model.py```

If you're getting any ```ModuleNotFoundError```s, try running this instead:
- ```python model.py```

From there, the model will begin running and saving the outputs in the subdirectories in the ```outputs``` directory. Point forecast charts are plotted every 24 forecast hours and at the end of the run. These are saved in the ```points``` folder within ```outputs```. Charts are generated at every forecast step and are saved in the ```figures``` folder. The day/night snowfall scatter plots are generated at the end of the model run and are saved in the ```scatters``` directory. GIF outputs are generated at the end of the model run and are saved in the ```gifs``` folder.

### Custom GIF generation
You can also now generate custom GIFs by running the ```gif-maker.py``` script the same way you ran ```model.py```. This script will ask for the start frame, end frame, step, and parameter to plot. Note that the images must have already been plotted by a prior model run for this script to work. The output GIF will save as ```custom.gif``` in the ```outputs``` directory.
