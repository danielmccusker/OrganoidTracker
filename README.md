OrganoidTracker
===============

Code for tracking cell nuclei in (intestinal) organoids over time. Uses a convolutional neural network for nucleus detection, a min-cost flow solver ([Haubold, 2016]) for linking nuclei over time and tools for manual error correction.


Installation
------------
OrganoidTracker must be installed using Anaconda. See the [installation] page for details. If you are updating from an older version of OrganoidTracker, its dependencies might have changed, and in that case you also need to visit the [installation] page.


Running the main program
------------------------
Open an Anaconda Prompt, activate the correct environment and navigate to the 
The `organoid_tracker.py` script starts a graphical program that allows you to visualize and edit your data.


Reading the manual
------------------
After you have installed the software, please have a look at the [manual]. The manual is also available from the `Help` menu in the program; this works even when you're offline.


API
---
You can also use OrganoidTracker as a library to write your own scripts. All public functions in OrganoidTracker have docstrings to explain what they are doing. As a starting point for using the API, see the [API] page.


Editing the source code
-----------------------
Install the program as normal, and then point your Python editor (I recommend Pycharm or Visual Studio Code) to this directory. Make sure to select the `organoid_tracker` Anaconda environment as the Python environment.


[API]: manuals/API.md
[installation]: manuals/INSTALLATION.md
[manual]: manuals/INDEX.md
[Haubold, 2016]: https://doi.org/10.1007/978-3-319-46478-7_35
