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
real-world applications. The biggest disadvantage to ESA v2 compared to ESA
v1.1, is that ESA v2 requires substantially longer to fit all of the scaling
models to the data for large datasets. For example, running ESA v2 with
approximately 11 000 instances requires about 1.5 days, whereas this can
be completed within minutes using ESA v1.1. However, for datasets with
less than a thousand instances you should be able to run ESA v2 within 
seconds to minutes. Therefore, If you are constrained by time and
are able to obtain instances grouped into bins, you may prefer to
use ESA v1.1 instead (available as an online service, or a command line 
tool at http://www.cs.ubc.ca/labs/beta/Projects/ESA).  

# Table of Contents

   * [Empirical Scaling Analyzer (ESA) v2](#empirical-scaling-analyzer-esa-v2)
   * [Table of Contents](#table-of-contents)
   * [Quickstart Guide](#quickstart-guide)
      * [Performance Measurement Datasets](#performance-measurement-datasets)
         * [Instance Set Properties](#instance-set-properties)
         * [Collecting Performance Measurements - <strong>Important</strong>](#collecting-performance-measurements---important)
      * [Installing ESA](#installing-esa)
      * [Running ESA](#running-esa)
      * [Instance File Format](#instance-file-format)
      * [Custom Scaling Models](#custom-scaling-models)
   * [Configuration File Arguments](#configuration-file-arguments)

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

First, download the latest version of ESA from 
https://github.com/YashaPushak/ESA. 

Next, if you do not already have them, you will need to install gnuplot 
and python with the numpy package. ESA was designed and tested using python
v2.7.13 and gnuplot v5.0 patchlevel 0. However, preliminary tests indicate 
that ESA can run without modification using python v3.7.

If you don't already have it, you can install numpy by running 
`pip install -r requirements.txt` from inside ESA's root directory.

Finally, install ESA by running 
`pip install .`
or
`python setupy.py install --user`
in ESA's root directory.

## Running ESA

Before you can use ESA on your own data, you 
will need to create a directory for the input and output files, as well as a 
configuration file specifying the details ESA needs to run. The easiest way to 
learn this is by example. Try testing ESA using the following command line 
(which will also help you verify that everything was installed correctly):

    ./runESA.sh examples/lingeling

This should take about 20-30 seconds to run. ESA starts by reading the 
configuration file `examples/lingeling/configurations.txt`, and then
fits the specified models to the running time data.

You can set different properties of the scenario in the configuration file, 
such as `fileName`, which contains the performance measurements for your
algorithm or `algName`, which specifies the name ESA was will use to refer 
to your algorithm in the automatically generated LaTeX report. 

You can also specify different parameters used by ESA. For example, we 
recommend to increase the number of bootstrap samples in the example 
scenario from 51 to 1001 when used in practice.

You should see several output files created in the directory
`examples/lingeling`, most notably including an automatically generated
technical report in the form of a pdf:
 `examples/lingeling/scaling_Lingeline.pdf`. We have included an example
of what this report should look like for your reference:
`examples/lingeling/expected_output_report.pdf`. The exact details
of the analysis will vary, since ESA is itself a randomized procedure;
however, with high probability the report you produce should be 
qualitatively identical to the we provide as a reference.

## Instance File Format

To create your own running time file, you will need to create a csv file with 
one line per instance:
 - the first column is a unique string that identifies the instance, i.e., 
   the instance name. (ESA will ignore this column, it is for your reference
   only);
 - the second column is the size of the instance (as an integer); 
 - the third column is the running time, in seconds (of course, you can use
   any performance metric and unit as desired -- however, the units and words
   referring to the measurements will need to be manually modified in the LaTeX
   template in order to produce correct output);
 - you may also append any number of additional columns with running times 
   obtained from independent runs of the target algorithm. 
 
## Custom Scaling Models

You can also specify your own custom models. To do so, you will need to do 
two things: First, add four pieces of information about your model into a
file called `model.txt`. Each line in the file defines a model for ESA to 
fit to the running time data:
 - the first column is the model name; 
 - the second column is the number of parameters;
 - the third column is a snippet of LaTeX code to display the model;
 - the fourth column is the gnuplot expression for the model; and 

The model parameters must be of the form @@a@@, @@b@@, @@c@@, ... in the LaTeX
and gnuplot expressions. 

Second, you will need to implement a simple interface in the file 
`ESA/userDefinitions.py` that provides ESA with a python definition for the
model, as well as instructions on how to optimize it. ESA v2 comes with several
pre-supported scaling models scaling models, for which we provide both the 
`userDefinitions.py` implementations as well as example `model.txt` defintions.
To use any of these models, simple copy and paste the appropriate line(s) from
below into your `model.txt` file:

    Exp, 2, @@a@@ \times @@b@@^{n}, @@a@@*@@b@@**x
    RootExp, 2, @@a@@ \times @@b@@^{\sqrt{n}}, @@a@@*@@b@@**(x**(0.5))
    Poly, 2, @@a@@ \times n^{@@b@@}, @@a@@*x**@@b@@
    PolyLog, 2, @@a@@ \times \log(n) \times n^{@@b@@}, @@a@@*log(x)*x**@@b@@
    LinLog^2, 2, @@a@@ \times \log^2(n) + @@b@@, @@a@@*log(x)**2 + @@b@@
    LinLog+Lin, 2, @@a@@ \times \log(n) + @@b@@ \times n, @@a@@*x*log(x) + @@b@@*log(x)
    Lin, 2, @@a@@ \times n + @@b@@, @@a@@*x+@@b@@
   
Please see the inline comments in `ESA/userDefinitions.py` for instructions on
how to add additional custom scaling moels.

# Configuration File Arguments

These settings control the analysis performed by ESA.

### alg_name

<table>
<tr><td><b>Description</b></td><td>The name of the algorithm for which you are performing scaling analysis.</td></tr>
<tr><td><b>Default</b></td><td>Algorithm</td></tr>
<tr><td><b>Aliases</b></td><td><code>alg-name</code>, <code>alg_name</code>, <code>algName</code>, <code>algorithm-name</code>, <code>algorithm_name</code>, <code>algorithmName</code></td></tr>
</table>

### alpha

<table>
<tr><td><b>Description</b></td><td>The confidence level used to calculate the confidence intervals. If less than 1, will be interpretted as 100*alpha. Must be in (0, 100)</td></tr>
<tr><td><b>Default</b></td><td>95.0</td></tr>
<tr><td><b>Aliases</b></td><td><code>alpha</code>, <code>confidence-level</code>, <code>confidence_level</code>, <code>confidenceLevel</code></td></tr>
</table>

### file_name

<table>
<tr><td><b>Description</b></td><td>The name of the file that contains the running times (or other performance metric) of your algorithm.</td></tr>
<tr><td><b>Required</b></td><td>Yes</td></tr>
<tr><td><b>Aliases</b></td><td><code>file-name</code>, <code>file_name</code>, <code>fileName</code></td></tr>
</table>

### gnuplot_path

<table>
<tr><td><b>Description</b></td><td>The path to gnuplot's binary.</td></tr>
<tr><td><b>Default</b></td><td>auto</td></tr>
<tr><td><b>Aliases</b></td><td><code>gnuplot-path</code>, <code>gnuplot_path</code>, <code>gnuplotPath</code></td></tr>
</table>

### inst_name

<table>
<tr><td><b>Description</b></td><td>The name of the instance set on which your algorithm was evaluated.</td></tr>
<tr><td><b>Default</b></td><td>the problem instances</td></tr>
<tr><td><b>Aliases</b></td><td><code>inst-name</code>, <code>inst_name</code>, <code>instName</code>, <code>instance-name</code>, <code>instance_name</code>, <code>instanceName</code></td></tr>
</table>

### latex_template

<table>
<tr><td><b>Description</b></td><td>The name of the LaTeX template to use when generating the automated technical report pdf document.</td></tr>
<tr><td><b>Default</b></td><td>template-AutoScaling.tex</td></tr>
<tr><td><b>Aliases</b></td><td><code>latex-template</code>, <code>latex_template</code>, <code>latexTemplate</code></td></tr>
</table>

### log_file

<table>
<tr><td><b>Description</b></td><td>The file to which ESA should log information.</td></tr>
<tr><td><b>Default</b></td><td>stdout</td></tr>
<tr><td><b>Aliases</b></td><td><code>log-file</code>, <code>log_file</code>, <code>logFile</code></td></tr>
</table>

### log_level

<table>
<tr><td><b>Description</b></td><td>Controls the verbosity of the output. Choose from "warning", "info" and "debug"</td></tr>
<tr><td><b>Default</b></td><td>info</td></tr>
<tr><td><b>Aliases</b></td><td><code>log-level</code>, <code>log_level</code>, <code>logLevel</code></td></tr>
</table>

### model_file_name

<table>
<tr><td><b>Description</b></td><td>The name of the file that determines which models are fitted to the data. This file also defines how the models are formatted in the LaTeX report and provides the model definitions for gnuplot.</td></tr>
<tr><td><b>Default</b></td><td>models.txt</td></tr>
<tr><td><b>Aliases</b></td><td><code>model-file-name</code>, <code>model_file_name</code>, <code>modelFileName</code></td></tr>
</table>

### num_bootstrap_samples

<table>
<tr><td><b>Description</b></td><td>The number of (outer) bootstrap samples used.</td></tr>
<tr><td><b>Default</b></td><td>1001</td></tr>
<tr><td><b>Aliases</b></td><td><code>num-bootstrap-samples</code>, <code>num_bootstrap_samples</code>, <code>numBootstrapSamples</code>, <code>n-bootstrap</code>, <code>n_bootstrap</code>, <code>nBootstrap</code></td></tr>
</table>

### num_observations

<table>
<tr><td><b>Description</b></td><td>The number of points for which ESA will calculate statistics to determine whether or not the model predictions are consistent with the observations.</td></tr>
<tr><td><b>Default</b></td><td>50</td></tr>
<tr><td><b>Aliases</b></td><td><code>num-observations</code>, <code>num_observations</code>, <code>numObservations</code></td></tr>
</table>

### num_per_instance_bootstrap_samples

<table>
<tr><td><b>Description</b></td><td>The number of (inner) bootstrap samples. That is, the number of bootstrap samples used for independent runs per instance. This is known to be a less important parameter to set to a large value than the number of outer bootstrap samples.</td></tr>
<tr><td><b>Default</b></td><td>101</td></tr>
<tr><td><b>Aliases</b></td><td><code>num-per-instance-bootstrap-samples</code>, <code>num_per_instance_bootstrap_samples</code>, <code>numPerInstanceBootstrapSamples</code>, <code>per-instance-n-bootstrap</code>, <code>per_instance_n_bootstrap</code>, <code>perInstanceNBootstrap</code></td></tr>
</table>

### num_runs_per_instance

<table>
<tr><td><b>Description</b></td><td>The number of independent runs of the algorithm that were performed on each instance. This is only used for validating your dataset. ESA will automatically determine the number from the file provided.</td></tr>
<tr><td><b>Default</b></td><td>0</td></tr>
<tr><td><b>Aliases</b></td><td><code>num-runs-per-instance</code>, <code>num_runs_per_instance</code>, <code>numRunsPerInstance</code></td></tr>
</table>

### observations

<table>
<tr><td><b>Description</b></td><td>Instead of providing the number of observations you can also instead provide the locations of all of the observations. Should be an array of instance sizes.</td></tr>
<tr><td><b>Default</b></td><td>None</td></tr>
<tr><td><b>Aliases</b></td><td><code>observations</code></td></tr>
</table>

### per_instance_statistic

<table>
<tr><td><b>Description</b></td><td>The statistic calculated over independent runs of the algorithm on the same instance.</td></tr>
<tr><td><b>Default</b></td><td>median</td></tr>
<tr><td><b>Aliases</b></td><td><code>per-instance-statistic</code>, <code>per_instance_statistic</code>, <code>perInstanceStatistic</code></td></tr>
</table>

### residue_plot_template

<table>
<tr><td><b>Description</b></td><td>The name of the gnuplote templateto use for plotting the residues of the fitted models.</td></tr>
<tr><td><b>Default</b></td><td>template-plotResidues.plt</td></tr>
<tr><td><b>Aliases</b></td><td><code>residue-plot-template</code>, <code>residue_plot_template</code>, <code>residuePlotTemplate</code></td></tr>
</table>

### runtime_cutoff

<table>
<tr><td><b>Description</b></td><td>The running time cutoff that you used with your algorithm.</td></tr>
<tr><td><b>Default</b></td><td>inf</td></tr>
<tr><td><b>Aliases</b></td><td><code>runtime-cutoff</code>, <code>runtime_cutoff</code>, <code>runtimeCutoff</code></td></tr>
</table>

### statistic

<table>
<tr><td><b>Description</b></td><td>The statistic for which ESA should compute the scaling of the algorithm. Supported options are "median", "mean" and arbitrary quantiles. For example, the 95th quantile can be selected as "q95".</td></tr>
<tr><td><b>Default</b></td><td>median</td></tr>
<tr><td><b>Aliases</b></td><td><code>statistic</code></td></tr>
</table>

### train_test_split

<table>
<tr><td><b>Description</b></td><td>Determines how much of the data is used as the training set and how much is used as the test set. Should be in (0, 1).</td></tr>
<tr><td><b>Default</b></td><td>0.4</td></tr>
<tr><td><b>Aliases</b></td><td><code>train-test-split</code>, <code>train_test_split</code>, <code>trainTestSplit</code></td></tr>
</table>

### window

<table>
<tr><td><b>Description</b></td><td>The number of instances to be used in the sliding bootstrap window.</td></tr>
<tr><td><b>Default</b></td><td>50</td></tr>
<tr><td><b>Aliases</b></td><td><code>window</code>, <code>window-size</code>, <code>window_size</code>, <code>windowSize</code></td></tr>
</table>

