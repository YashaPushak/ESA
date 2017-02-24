## Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/) 

## [Unreleased]

### Added
 - Exposed a new parameter to the configuration file 'modifyDefaultParameters' which can be either True or False. If True, then the default fitting parameters (in models.txt) are ignored, and instead replaced by fitting the models to the largest and smallest support instance sizes. This parameter only affects polynomial, exponential, and root-exponential models.
 - Nested bootstrapping can be performed to calculate per-instance statistics for randomized algorithms with multiple independent runs on each instance.
The user can specify multiple independent runs per instance by adding additional columns with running times to the running time csv file. 
 - There is a new, optional parameter for the configuration.txt file "numRunsPerInstance", which is used to validate that the number of running times provided for each instance matches the specified number. ESA will direct users towards any instances with the wrong number of running times if any exist. If not provided, ESA will automatically identify the correct number and issue a warning if the nuber is inconsistent.
 - More information printed to console to show when bootstrap samples have been made and when models have been fit to them.
 - Challenge RMSE is now reported with a bootstrap confidence interval across the bootstrap samples. The model with the best expected RMSE is selected as the best fit model. 
 - Created a change log.

### Changed
 - Minor refactoring done to improve running time of ESA.


## [1.1] - 2016-11-17

### Added
 - New error messages and handling for common problems

### Fixed
 - plotModels.plt template file contained a minor bug that occasionally caused the script the fail.

### Removed
 - Removed old debugging messages printed to the console.
