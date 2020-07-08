# Change Log

All notable changes to this project will be documented in this file.


## [2.0] - 2020-07-08

### Added
 - ESA now uses a completely re-vamped underlying methodology. Conceptually it is very similar; however, it no longer requires instances grouped into bins of the sames size.
 - ESA now contains a substantially updated README file which is now the core documentation for using ESA, please see this README for instructions on how to use the new version of ESA.

### Changed
 - ESA can now be installed as a python package and run from any directory
 - The technical report preduced by ESA reflects the new methodology used
 - Custom models not already supported by ESA need to be implemented in userDefinitions.py

## [1.1] - 2017-07-26

### Added
 - New error messages and handling for common problems.
 - Added a new parameter to the configuration file 'logLevel' which can be set to any of 'Error', 'Warning', 'Info' or 'Debug',  to control the level of output printed to the console by ESA. 
 - Added a new parameter for the configuration file 'logFile' which can be used to specify a file where the logging information is stored, instead of having it printed to the console.
 - Nested bootstrapping can be performed to calculate per-instance statistics for randomized algorithms with multiple independent runs on each instance. The user can specify multiple independent runs per instance by adding additional columns with running times to the running time csv file. 
 - There is a new, optional parameter for the configuration.txt file "numRunsPerInstance", which is used to validate that the number of running times provided for each instance matches the specified number. ESA will direct users towards any instances with the wrong number of running times if any exist. If not provided, ESA will automatically identify the correct number and issue a warning if the nuber is inconsistent.
 - More information printed to console to show when bootstrap samples have been made and when models have been fit to them.
 - A new table in the latex report has been added to include support and challenge RMSE medians, and bootstrap confidence intervals across the bootstrap samples. The model with the smallest median (over bootstrap samplse) RMSE is selected as the best fit model. If unknown running times create lower and upper bounds as well for this, then we use the median (over bootstrap samples) of the geometric means of the intervals. If the medians are infinite, then we use the lower bounds of the RMSE to select the best fit model. 
 - Created a change log.
 - An example scenario and quickstart guide.

### Changed
 - Minor refactoring done to improve running time of ESA.
 - plotModels.plt tmeplate file contained a minor bug for some version of gnuplot that occasionally caused the script to fail.
 - The text-based analysis of the fit of the models is now based not only on the fraction of strongly consistent challenge instance sizes, but also the fraction of weakly consistent instance sizes. The exact decision tree used to generate the text has also been slightly modified to properly encorporate this change. Additional details are included in the LaTeX report and the user guide, which summarize what each descriptive statement means. 

### Removed
 - Removed old debugging messages printed to the console.
