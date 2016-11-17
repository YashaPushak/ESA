## Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/) 

## [Unreleased]

### Added
 - Nested bootstrapping can be performed to calculate per-instance statistics for randomized algorithms with multiple independent runs on each instance.
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
