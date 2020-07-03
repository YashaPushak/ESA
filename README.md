# Empirical Scaling Analyzer (ESA) v2

The Empirical Scaling Analyzer (ESA) uses a combination of numerical
optimization and statistical methods to fit empirical scaling models to 
performance measurements of algorithms observed on problem instances of varying
sizes. ESA splits the dataset of performance measurements into two sets:
a *training* or *support* set, which contains the measurements on the
smallest instance sizes, and a *test* or *challenge* set, which contains the
measurements on the larger instance sizes. By fitting the models only to the
training data ESA is able to use the models to predict the performance of the
algorithm on the test instances, which it can then use to validate the
quality of these extrapolations.

By combining this procedure with a novel statistical analysis technique based
on bootstrap sampling, ESA is able to determine whether or not there is
sufficient evidence to reject a scaling model as being a poor fit for the data.
ESA allows for this methodology to be simultaneously applied to mutliple
candidate empirical scaling models or *hypothises* and produces a pdf technical
report as output that discusses the quality of each model fit.

This is the second version of ESA, which represents a substantial improvement
over its predecessor, ESA version 1.1. The previous implementation of ESA 
required the use of instance sets where instances were grouped into multiple
bins of the same size. In contrast, ESA v2 relaxes this requirement, which
allows it to be applied to a substantially broader range of interesting and
important problem applications, since it is often challenging or impossible
to obtain instance sets with instance sizes grouped in this way for many
real-world applications. 

# Quickstart Guide

This quickstart guide will demonstrate how to use ESA using a simple
dataset that contains running time measurements for Lingleling on
bounded model checking SAT instances that were obtained by unrolling
hardware circuits from the 2008 Hardware Model Checking Competition
to various depths. 

## Performance Measurement Datasets

Before running ESA, you will need to evaluate your algorithm on a set of 
instances with varying instance sizes, while measuring some aspect of
your algorithm's performance. Throughout the following, we will refer to
this performance metric as the running time of your algorithm. However, ESA
is agnostic to the performance metric used: you could count iterations, 
operations, the maximum memory usage or the total energy required to power
your algorithm. 

### Instance Set Properties

If possible, it is advantageous to obtain an instance set such that the
instance sizes are approximately spread out uniformly at random for some
range of instance sizes. However, this is not a strict requirement. More
importantly, you should take care that your instance set varies only a 
single notion of instance size or difficulty at a time. Since it is
common for there to be multiple features of an instance that can control
its difficulty, if there are two features that are varried in a correlated
fashion then ESA will be unable to distinguish whether or not the scaling
it has observed should be attributed to the measure of instance size that
you provide it, or if this is due to some other compounding factor. ESA
assumes that all such other features, are either fixed or independently and
identically distributed among the instances.

### Collecting Performance Measurements - **Important**

When collecting performance measurements for your algorithm, particularly
if you are measuring the running time of your algorithm, it is important
to randomize the order of the instances in which you perform the algorithm
runs. Not doing so could cause environmental noise effects to create errors
in your dataset that are not independently and identically distributed. This
is a common pitfall -- one to which we have fallen subject ourselves. There
can be many causes of environmental noise that can cause surprising problems
if not handled in this way: for example, the clock speed of your processor
may dynamically slow down to avoid over-heating, which, if not independently
and identically distributed among your performance measurements, could cause
all of the performance measurements on your test set to be large constant
factors slower than the rest of your data (we have observed factors up to
around 3.5 for extended periods of time).

## Installing ESA

First, if you do not already have them, you will need to install gnuplot 
and python with the numpy package. ESA was designed and tested using python
v2.7.13 and gnuplot v5.0 patchlevel 0. However, preliminary tests indicate 
that ESA can run without modification using python v3.8.

Next, download the latest version of ESA from https://github.com/YashaPushak/ESA.

## Running ESA

Once both are installed, and before you can use ESA on your own data, you 
will need to create a directory for the input and output files, as well as a 
configuration file specifying the details ESA needs to run. The easiest way to 
learn this is by example. Try testing ESA using the following command line 
(which will also help you verify that everything was installed correctly):

./runESA.sh example_scenarios/WalkSAT

This command line directs ESA to be run using the scenario found in 
example_scenarios/WalkSAT. In particular, it starts by reading the 
configuration file found in example_scenarios/WalkSAT/configurations.txt.

You can set different properties of the scenario in the configuration file, 
such as 'fileName', which contains the target algorithm running times, or 
'algName', which specifies the name ESA was will use to refer to the target 
algorithm in the LaTeX report. 

You can also specify different parameters used by ESA. For example, we 
recommend to increase the number of bootstrap samples in in the example 
scenario from 100 to 1000 when used in practice. For more information on what
 variables you can set in the confiugration file, please refer to 
UserGuide.pdf

To create your own running time file, you will need to create a csv file with 
one line per instance:
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
