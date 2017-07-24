Quickstart Guide to ESA v1.1

You have collected some running time data for an algorithm on a set of instances with different sizes, and you want to analyze the empirical scaling of the target algorithm. This quickstart guide will show you how to use ESA by walking you through the provided exampling scenario for WalkSAT/SKC. First, we need to download ESA, which can be done on any *nix system using:

wget http://www.cs.ubc.ca/~w-esa/ESA/ESA-v1.0.zip
unzip ESA-v1.0.zip
cd ESA

Next, if you do not already have them, you will need to install gnuplot and python with the numpy package. ESA was designed and tested using python v2.7.13 and gnuplot v5.0 patchlevel 0.

Once both are installed, you can test ESA using the following command line:

./runESA.sh example_scenarios/WalkSAT

This command line directs ESA to be run using the scenario found in example_scenarios/WalkSAT. In particular, it starts by reading the configuration file found in example_scenarios/WalkSAT/configurations.txt.

You can set different properties of the scenario in the configuration file, such as 'fileName', which contains the target algorithm running times, or 'algName', which specifies the name ESA was will use to refer to the target algorithm in the LaTeX report. 

You can also specify different parameters used by ESA. For example, we recommend to increase the number of bootstrap samples in in the example scenario from 100 to 1000 when used in practice. For more information on what variables you can set in the confiugration file, please refer to UserGuide.pdf

To create your own running time file, you will need to create a csv file with one line per instance:
 - the first column is a unique string that identifies the instance, i.e., 
   the instance name. (ESA will ignore this column, it is for your reference
   only);
 - the second column is the size of the instance (as an integer); 
 - the third column is the running time (in seconds);
 - you may also append any number of additional columns with running times 
   obtained from independent runs of the target algorithm. 
 
You can also specify your own custom models to the model.txt file for ESA to
use. Each line in the file defines a model for ESA to fit to the running 
time data:
 - the first column is the model name; 
 - the second column is the number of parameters;
 - the third column is a snippet of LaTeX code to display the model;
 - the fourth column is the python expression for the model;
 - the fifth column is the gnuplot expression for the model; and 
 - the remaining columns are the default values for the model parameters 
   (one per column).
The model parameters must be of the form @@a@@, @@b@@, @@c@@, ... in the LaTeX, python and gnuplot expressions. 

As an example, try adding the following line to the models.txt file in the example scenario:

RootExp,2,@@a@@\times @@b@@^{\sqrt{x}},@@a@@*@@b@@**(x**(0.5)),@@a@@*@@b@@**(x**(0.5)),1e-6,1.8

Try running ESA again. You should find that the RootExp. model tends to over-estimate the running time data. 

For more information about how to use more advanced features of ESA, please see the user guide. 
