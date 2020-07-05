import inspect
import os
import math
import logging
import sys
import time
import datetime

import numpy as np

import summarizeRuntimes
import modelFittingHelper
import bootstrapHelper
import csvHelper
import gnuplotHelper
import latexHelper
import args


#def inputDefToPythonDef( md ):
#    idx = md.find( 'p', 0 )
#    while idx>-1:
#        if idx+1<len(md) and md[idx+1].isdigit():
#            md = md[0:idx+1] + '[' + md[idx+1] + ']' + md[idx+2:]
#        idx = md.find( 'p', idx+1)
#    return md
#
def replaceRepsForOutput( modelOriReps ):
    modelReps = []
    for mr in modelOriReps:
        idx = mr.find( 'p', 0 )
        while idx>-1:
            if idx+1<len(mr) and mr[idx+1].isdigit():
                mr = mr[0:idx] + '%s' + mr[idx+2:]
            idx = mr.find( 'p', idx+1)
        modelReps.append( mr )
    return modelReps

def inputModelToInternal( instr, inPython ):
    while instr.find("@@") > -1:
        stIdx = instr.find("@@")
        edIdx = instr.find("@@", stIdx+2)+2
        if edIdx<2:
            break
        elif edIdx!=stIdx+5:
            #print(instr)
            raise Exception
        id = instr[stIdx+2]
        if inPython:
            instr = instr[0:stIdx] + ("p[%d]" % (ord(id)-ord('a'))) + instr[edIdx:]
        else:
            instr = instr[0:stIdx] + ("p%d" % (ord(id)-ord('a'))) + instr[edIdx:]
    return instr

def getModels(logger, fileDir, fileName):
    #Author: ZM
    #Edited by: YP
    #Last edit: 2019-01-04

    modelNames = []
    modelNumParas = []
    modelReps = []

    modelGnuplotDefs = []
    with open(fileDir+"/"+fileName, "r") as modelFile:
        for line in modelFile:
            if('#' in line[0]):
                continue
            terms = line.split(",")
            if len(terms)>=4:
                modelNames.append( terms[0].strip() )
                logging.debug('Parsing ' + modelNames[-1] + ' model.')
                modelNumParas.append( int(terms[1]) )
                modelReps.append( terms[2].strip() )
                modelGnuplotDefs.append( inputModelToInternal( terms[3].strip(), False ) )

    return modelNames, modelNumParas, modelReps, modelGnuplotDefs


def getIntervals(los, ups):
    intervals = []
    for i in range(0, len(los)):
        intervals.append( [] )
        for j in range(0, len(los[i])):
            intervals[i].append( "["+str(los[i][j])+","+str(ups[i][j])+"]" )
    return intervals

def evaluateModels( modelNames, threshold, statIntervals, predLos, predUps ):
    res = ""
    largerHalfIdx = (len(statIntervals)+threshold)/2
    for k in range(0, len(modelNames)):
        if k > 0:
            res += ", "
        if k == len(modelNames)-1:
            res += "and "
        numOverIntervals = 0
        numOverIntervalsLarger = 0
        numBelowIntervals = 0
        numBelowIntervalsLarger = 0
        numWithinIntervals = 0
        numWithinIntervalsLarger = 0
        for i in range(threshold, len(statIntervals)):
            if statIntervals[i][1]<predLos[k][i]:
                numBelowIntervals += 1
                if i>=largerHalfIdx:
                    numBelowIntervalsLarger += 1
            elif statIntervals[i][0]>predUps[k][i]:
                numOverIntervals += 1
                if i>=largerHalfIdx:
                    numOverIntervalsLarger += 1
            else:
                numWithinIntervals += 1
                if i>=largerHalfIdx:
                    numWithinIntervalsLarger += 1
        perAboveIntervals = 1.0*numOverIntervals/(len(statIntervals)-threshold)
        perAboveIntervalsLarger = 1.0*numOverIntervalsLarger/(len(statIntervals)-largerHalfIdx)
        perBelowIntervals = 1.0*numBelowIntervals/(len(statIntervals)-threshold)
        perBelowIntervalsLarger = 1.0*numBelowIntervalsLarger/(len(statIntervals)-largerHalfIdx)
        perWithinIntervals = 1.0*numWithinIntervals/(len(statIntervals)-threshold)
        perWithinIntervalsLarger = 1.0*numWithinIntervalsLarger/(len(statIntervals)-largerHalfIdx)
        #YP: Removed some old debugging messages
        #print perAboveIntervals
        #print perAboveIntervalsLarger
        #print perBelowIntervals
        #print perBelowIntervalsLarger
        #print perWithinIntervals
        #print perWithinIntervalsLarger
        if perWithinIntervals <= 0.70 or perWithinIntervalsLarger <= 0.70:
            if perBelowIntervals > 0.75 or perBelowIntervalsLarger > 0.75:
                res += "the %s model over-estimates the data" % modelNames[k]
            elif perAboveIntervals > 0.75 or perAboveIntervalsLarger > 0.75:
                res += "the %s model under-estimates the data" % modelNames[k]
            elif (perBelowIntervals > 0.3 and perAboveIntervals < 0.05) or \
                    (perBelowIntervalsLarger > 0.3 and perAboveIntervalsLarger < 0.05):
                res += "the %s model tends to over-estimate the data" % modelNames[k]
            elif (perAboveIntervals > 0.3 and perBelowIntervals < 0.05) or \
                    (perAboveIntervalsLarger > 0.3 and perBelowIntervalsLarger < 0.05):
                res += "the %s model tends to under-estimate the data" % modelNames[k]
            else:
                res += "the %s model does not fit the data well" % modelNames[k]
        elif perWithinIntervals > 0.95:
            res += "the %s model fits the data very well" % modelNames[k]
        else:
            res += "the %s model tends to fit the data" % modelNames[k]
    return res



def evaluateModelsConsistency(logger, modelNames, statIntervals, obsvLos, obsvUps, predLos, predUps):
    #Author: Yasha Pushak
    #Created: April 5th, 2017
    #Last udpated: 2019-01-09
    #I am creating a third method for analysing the consistency of the data to create a text-based description. Unlike the original, this one
    #counts the number of instance sizes for which model predictions are both strongly and weakly consistent (instead of just strongly consistent)
    #with the observed data. 

    logger.debug('Interpretating results of scaling model fits.')

    types = set([])
    intervalsData = []

    res = ""
    #res = "Based on the observed data and the predicted bootstrap intervals from the models, we see that "
    largerHalfIdx = len(statIntervals)/2
    for k in range(0, len(modelNames)):
        if k == len(modelNames)-1:
            res += ", and "
        elif k > 0:
            res += ", "
        numOverIntervals = 0 
        numOverIntervalsLarger = 0 
        numBelowIntervals = 0 
        numBelowIntervalsLarger = 0 
        numStronglyWithinIntervals = 0 
        numStronglyWithinIntervalsLarger = 0 
        numWeaklyWithinIntervals = 0
        numWeaklyWithinIntervalsLarger = 0
        for size in range(0, len(statIntervals)):
            if obsvUps[size]<predLos[k][size]:
                numBelowIntervals += 1
                if size>=largerHalfIdx:
                    numBelowIntervalsLarger += 1
            elif obsvLos[size]>predUps[k][size]:
                numOverIntervals += 1
                if size>=largerHalfIdx:
                    numOverIntervalsLarger += 1
            else:
                numWeaklyWithinIntervals += 1
                if size>=largerHalfIdx:
                    numWeaklyWithinIntervalsLarger += 1
                if obsvLos[size] >= predLos[k][size] and obsvUps[size] <= predUps[k][size]:
                    numStronglyWithinIntervals += 1
                    if size>=largerHalfIdx:
                        numStronglyWithinIntervalsLarger += 1
                     
        perAboveIntervals = 1.0*numOverIntervals/(len(statIntervals))
        perAboveIntervalsLarger = 1.0*numOverIntervalsLarger/(len(statIntervals)-largerHalfIdx)
        perBelowIntervals = 1.0*numBelowIntervals/(len(statIntervals))
        perBelowIntervalsLarger = 1.0*numBelowIntervalsLarger/(len(statIntervals)-largerHalfIdx)
        perStronglyConsistent = 1.0*numStronglyWithinIntervals/(len(statIntervals))
        perStronglyConsistentLarger = 1.0*numStronglyWithinIntervalsLarger/(len(statIntervals)-largerHalfIdx)
        perWeaklyConsistent = 1.0*numWeaklyWithinIntervals/(len(statIntervals))
        perWeaklyConsistentLarger = 1.0*numWeaklyWithinIntervalsLarger/(len(statIntervals)-largerHalfIdx)

        logger.debug("Percentage above intervals for model " + modelNames[k] + ' - all: ' + str(perAboveIntervals) + '; larger: ' + str(perAboveIntervalsLarger))
        logger.debug("Percentage below intervals for model " + modelNames[k]+ ' - all: ' + str(perBelowIntervals) + '; larger: ' + str(perBelowIntervalsLarger))
        logger.debug("Percentage strongly consistent for model " + modelNames[k] + ' - all: ' + str(perStronglyConsistent)+ '; larger: ' + str(perStronglyConsistentLarger))
        logger.debug("Percentage weakly consistent for model " + modelNames[k] + ' - all: ' + str(perWeaklyConsistent) + '; larger: ' + str(perWeaklyConsistentLarger))

        if(perStronglyConsistent >= 0.90 or (perStronglyConsistentLarger >= 0.90 and perWeaklyConsistent >= 0.90)):
            res += "the %s model fits the data very well" % modelNames[k]
            types.add('stronglyConsistent')
        elif(perWeaklyConsistent >= 0.90 or perWeaklyConsistentLarger >= 0.90):
            res += "the %s model tends to fit the data" % modelNames[k]
            types.add('weaklyConsistent')
        elif(perAboveIntervals >= 0.70 or perAboveIntervalsLarger >= 0.70):
            res += "the %s model under-estimates the data" % modelNames[k]
            types.add('under')
        elif(perBelowIntervals >= 0.70 or perBelowIntervalsLarger >= 0.70):
            res += "the %s model over-estimates the data" % modelNames[k]
            types.add('over')
        elif(perBelowIntervals < 0.05 or perBelowIntervalsLarger < 0.05):
            res += "the %s model tends to under-estimate the data" % modelNames[k]
            types.add('tendUnder')
        elif(perAboveIntervals < 0.05 or perAboveIntervalsLarger < 0.05):
            res += "the %s model tends to over-estimate the data" % modelNames[k]
            types.add('tendOver')
        else:
            res += "the %s model does not fit the data well" % modelNames[k]
            types.add('noFit')

        intervalsData.append([perStronglyConsistent, perWeaklyConsistent, perAboveIntervals, perBelowIntervals, perStronglyConsistentLarger, perWeaklyConsistentLarger, perAboveIntervalsLarger, perBelowIntervalsLarger])


    with open('table_qualitative-results.csv','w') as f_out:
         f_out.write('strings, ' + res)

    csvHelper.genCSV('.','table_challenge-within-intervals.csv',['Percent Strongly Consistent', 'Percent Weakly Consistent', 'Percent above intervals','Percent below intervals','Percent Strongly Consistent (larger half)', 'Percent Weakly Consistent (larger half)', 'Percent above intervals (larger half)','Percent below intervals (larger half)'], modelNames, intervalsData)


    
    resExplain = " We base these statements on an analysis of the fraction of predicted bootstrap intervals that are strongly consistent, "
    resExplain += "weakly consistent and disjoint from the observed bootstrap intervals for the challenge data. To provide stronger emphasis "
    resExplain += "for the largest instance sizes, we also consider these fractions for the largest half of the challenge instance sizes. "
    resExplain += "To be precise, "

    num = 0
    for type in types:
        if(num == len(types) - 1):
            resExplain += "; and "
        elif(num > 0):
            resExplain += "; "
        num += 1

        if(type == 'stronglyConsistent'):
            resExplain += "we say a model predicts very well if $\geq 90\%$ of the predictions for challenge sizes are strongly consistent, or $\geq 90\%$ of the predictions for the larger half of the challenge sizes are strongly consistent and $ \geq 90\%$ of all of the predictions for all challenge sizes are weakly consistent"
        elif(type == 'weaklyConsistent'):
            resExplain += "we say a model tends to fit the data if 90\% or more of the predicted bootstrap intervals (or the larger half of the predicted intervals) are weakly consistent with the observed data"
        elif(type == 'under'):
            resExplain += "we say a model under-estimates the data if $\geq 70\%$ of the confidence intervals for predictions on all challenge instance sizes or $\geq 70\%$ of those on the larger half of the challenge sizes are below the observed intervals"
        elif(type == 'over'):
            resExplain += "we say a model over-estimates the data if $\geq 70\%$ of the confidence intervals for predictions on all challenge instance sizes or $\geq 70\%$ of those on the larger half of the challenge sizes are above the observed intervals"
        elif(type == 'tendUnder'):
            resExplain += "we say a model tends to under-estimate the data if $> 10\%$ of the confidence intervals for predictions on challenge instance sizes are disjoint from the confidence intervals for observed running time data and $\geq 90\%$ of the predicted intervals are below or are consistent with the observed intervals"
        elif(type == 'tendOver'):
            resExplain += "we say a model tends to over-estimate the data if $> 10\%$ of the confidence intervals for predictions on challenge instance sizes are disjoint from the confidence intervals for observed running time data and $\geq 90\%$ of the predicted intervals are above or are consistent with the observed intervals"
        elif(type == 'noFit'):
            resExplain += "we say a model does not fit the data very well if more than 10\% of the confidence intervals for predictions on challenge instance sizes are disjoint from the confidence intervals for observed running time data, more than 5\% of the predicted intervals are above the observed intervals, and more than 5\% of the predicted intervals are below the obvserved intervals"

    resExplain += ". "


    return [res, resExplain]

       
        



def evaluateModelsBootstrap( modelNames, threshold, statIntervals, bData, obsvLos, obsvUps, preds, predLos, predUps ):
    #Author: Yasha Pushak
    #last updated: December 1st, 2016
    #I am creating a new version of the above function that uses the bootstrap values of the desired statistics, not just the observed ones. 
    
    intervalsData = []
    res = ""
    largerHalfIdx = (len(statIntervals)+threshold)/2
    for k in range(0, len(modelNames)):
        if k > 0:
            res += ", "
        if k == len(modelNames)-1:
            res += "and "
        
        (perAboveIntervals, perAboveIntervalsLarger, perWithinIntervals, perWithinIntervalsLarger, perBelowIntervals, perBelowIntervalsLarger) = calWithinIntervals(bData, predLos, predUps, threshold, largerHalfIdx,k)

        intervalsData.append([perAboveIntervals, perWithinIntervals, perBelowIntervals, perAboveIntervalsLarger, perWithinIntervalsLarger, perBelowIntervalsLarger])

        if perWithinIntervals <= 0.70 or perWithinIntervalsLarger <= 0.70:
            if perBelowIntervals > 0.75 or perBelowIntervalsLarger > 0.75:
                res += "the %s model over-estimates the data" % modelNames[k]
            elif perAboveIntervals > 0.75 or perAboveIntervalsLarger > 0.75:
                res += "the %s model under-estimates the data" % modelNames[k]
            elif (perBelowIntervals > 0.3 and perAboveIntervals < 0.05) or \
                    (perBelowIntervalsLarger > 0.3 and perAboveIntervalsLarger < 0.05):
                res += "the %s model tends to over-estimate the data" % modelNames[k]
            elif (perAboveIntervals > 0.3 and perBelowIntervals < 0.05) or \
                    (perAboveIntervalsLarger > 0.3 and perBelowIntervalsLarger < 0.05):
                res += "the %s model tends to under-estimate the data" % modelNames[k]
            else:
                res += "the %s model does not fit the data well" % modelNames[k]
        elif perWithinIntervals > 0.95:
            res += "the %s model fits the data very well" % modelNames[k]
        else:
            res += "the %s model tends to fit the data" % modelNames[k]
    
    with open('table_qualitative-results.csv','w') as f_out:
         f_out.write('strings, ' + res)

    csvHelper.genCSV('.','table_challenge-within-intervals.csv',['Percent above intervals','Percent within intervals','Percent below intervals','Percent above intervals (larger half)','Percent within intervals (larger half)','Percent below intervals'], modelNames, intervalsData)

    return res


def calWithinIntervals(data,los,ups,threshold,largerHalfIdx,k):
    #Author: Yasha Pushak
    #Last updated: December 1st, 2016
    #Calculates the number of data poitns about, below, and within the specified intervals for each instance size.

    numOverIntervals = 0
    numOverIntervalsLarger = 0
    numBelowIntervals = 0
    numBelowIntervalsLarger = 0
    numWithinIntervals = 0
    numWithinIntervalsLarger = 0
    numData = 0
    numDataLargerHalf = 0
    for s in range(threshold, len(data[0])):
        for b in range(0,len(data[0][s])):
            numData += 1
            if s>= largerHalfIdx:
                numDataLargerHalf += 1
            if data[1][s][b]<los[k][s]:
                numBelowIntervals += 1
                if s>=largerHalfIdx:
                    numBelowIntervalsLarger += 1
            elif data[0][s][b]>ups[k][s]:
                numOverIntervals += 1
                if s>=largerHalfIdx:
                    numOverIntervalsLarger += 1
            else:
                numWithinIntervals += 1
                if s>=largerHalfIdx:
                    numWithinIntervalsLarger += 1
    #numData = (len(data[0]) - threshold)*len(data[0][0])
    #numDataLargerHalf = (len(data[0]) - largerHalfIdx)*len(data[0][0])
    perAboveIntervals = 1.0*numOverIntervals/numData
    perAboveIntervalsLarger = 1.0*numOverIntervalsLarger/numDataLargerHalf
    perBelowIntervals = 1.0*numBelowIntervals/numData
    perBelowIntervalsLarger = 1.0*numBelowIntervalsLarger/numDataLargerHalf
    perWithinIntervals = 1.0*numWithinIntervals/numData
    perWithinIntervalsLarger = 1.0*numWithinIntervalsLarger/numDataLargerHalf
    
    return (perAboveIntervals, perAboveIntervalsLarger, perWithinIntervals, perWithinIntervalsLarger, perBelowIntervals, perBelowIntervalsLarger)


def run(fileDir, fileName="runtimes.csv", algName="Algorithm", instName="the problem instances", modelFileName="models.txt", threshold=0, alpha=95, numBootstrapSamples=100, statistic="median", toModifyModelDefaultParas=False, tableDetailsSupportFileName="table_Details-dataset-support", tableDetailsChallengeFileName="table_Details-dataset-challenge", tableFittedModelsFileName="table_Fitted-models", tableBootstrapIntervalsParaFileName="table_Bootstrap-intervals-of-parameters", tableBootstrapIntervalsSupportFileName="table_Bootstrap-intervals_support", tableBootstrapIntervalsChallengeFileName="table_Bootstrap-intervals_challenge", figureCdfsFileName="cdfs", figureFittedModelsFileName="fittedModels", figureFittedResiduesFileName="fittedResidues", latexTemplate = "template-AutoScaling.tex", modelPlotTemplate = "template-plotModels.plt", residuePlotTemplate = "template-plotResidues.plt", gnuplotPath = 'auto', numRunsPerInstance = 0, perInstanceStatistic="median", numPerInstanceBootstrapSamples=10,logLevel = "INFO", logFile='stdout', stretchSize=[]):
    startTime = time.time()

    # Parse the arguments using the new argument parser. Note that this completely
    # ignores some of the default values defined above.
    arguments, _ = args.ArgumentParser().parse_arguments(fileDir)
    fileName = arguments['file_name']
    algName = arguments['alg_name']
    instName = arguments['inst_name']
    if 'model_file_name' in arguments:
        modelFileName = arguments['model_file_name']
    threshold = arguments['train_test_split']
    alpha = arguments['alpha']
    numBootstrapSamples = arguments['num_bootstrap_samples']
    statistic = arguments['statistic']
    if 'latex_template' in arguments:
        latexTemplate = arguments['latex_template']
    if 'model_plot_template' in arguments:
        modelPlotTemplate = arguments['model_plot_template']
    if 'residue_plot_template' in arguments:
        residuePlotTemplate = arguments['residue_plot_template']
    gnuplotPath = arguments['gnuplot_path']
    numRunsPerInstance = arguments['num_runs_per_instance']
    perInstanceStatistic = arguments['per_instance_statistic']
    numPerInstanceBootstrapSamples = arguments['num_per_instance_bootstrap_samples']
    logLevel = arguments['log_level']
    logFile = arguments['log_file']
    numObsv = arguments['num_observations']
    obsvs = arguments['observations']
    window = arguments['window']
    runtimeCutoff = arguments['runtime_cutoff']

    if(statistic[0].lower() == 'q'):
        quantile = float(statistic[1:])
        if(quantile > 1):
            quantile/=100
        statistic = 'Q' + str(quantile)
    if gnuplotPath != 'auto':
        gnuplotPath += '/'
    if obsvs == 'None':
        obsvs = None
    else:
        terms = ['', obsvs]
        if('[' in terms[1]):
            obsvs = []
            for item in terms[1].strip().replace('[','').replace(']','').split(','):
                obsvs.append(float(item))
            obsvs = sorted(obsvs)
            numObsv = len(obsvs)

    numericLevel = getattr(logging, logLevel.upper(), None)
    if not isinstance(numericLevel, int):
        raise ValueError('Invalid log level: %s' % logLevel)
    if(logFile.lower() == 'stdout'):
        logging.basicConfig(format='[%(levelname)s]: %(message)s',level=numericLevel) 
    else:
        logging.basicConfig(format='[%(levelname)s]: %(message)s',level=numericLevel,filename=fileDir + '/' + logFile)
    
    logger = logging.getLogger('ESA logger')

    if(gnuplotPath.lower().replace('/','') == 'auto'):
         gnuplotPath = ''

    if(threshold == 0):
        threshold = 0.5
    if(threshold >= 1):
        raise ValueError('The fraction of data used as support instances (trainTestSplit) must be less than 1')

    esaDir = os.path.dirname(os.path.realpath(inspect.getfile(inspect.currentframe())))
    #   prepare template files
    logger.debug('Preparing template files')
    if not os.path.exists( fileDir+"/"+modelFileName ):
        os.system( "cp %s/models.txt %s" % (esaDir, fileDir+"/"+modelFileName) )
    if not os.path.exists( fileDir+"/"+latexTemplate ):
        os.system( "cp %s/template-AutoScaling.tex %s" % (esaDir, fileDir+"/"+latexTemplate) )
    if not os.path.exists( fileDir+"/"+modelPlotTemplate ):
        os.system( "cp %s/template-plotModels.plt %s" % (esaDir, fileDir+"/"+modelPlotTemplate) )
    if not os.path.exists( fileDir+"/"+residuePlotTemplate ):
        os.system( "cp %s/template-plotResidues.plt %s" % (esaDir, fileDir+"/"+residuePlotTemplate) )
    #   move the pdflatex input file
    if not os.path.exists( fileDir+"/pdflatex-input.txt" ):
        if(not os.path.exists('pdflatex-input.txt')):
            with open('pdflatex-input.txt','w') as f_out:
                f_out.write('R\n\n')
        os.system( "cp " + esaDir + "/pdflatex-input.txt " + fileDir +"/pdflatex-input.txt" )    
  
    #   read in runtimes and summarize
    logger.debug('Reading running times from file.')
    sizes, runtimes, numInsts, numRunsPerInstance = summarizeRuntimes.getRuntimesFromFile(logger, fileDir, fileName, numRunsPerInstance, runtimeCutoff)

    cwd = os.getcwd()
    os.chdir( fileDir )
    logger.info('Calculating summary statistics for running times.')
    sizesTrain, runtimesTrain, flattenedRuntimesTrain, sizesTest, runtimesTest, flattenedRuntimesTest, sizeThreshold, windowSize, statxTrain, statyTrain, statxTest, statyTest = summarizeRuntimes.summarizeRuntimes(logger, sizes, runtimes, numInsts, algName, ".", statistic, perInstanceStatistic, threshold, numObsv, obsvs, window)
    # stats = [ summarizeRuntimes.calStatistic( runtimes[i], statistic ) for i in range(0, len(sizes)) ]

    #fittedModels = [[0.19899198603609397, 1.1304343525093121]]
    #modelNames = ['sqrt-exp']
    #fittedModels = [[7.29720138243327e-05, 1.03188952955068]]
    #modelNames = ['exp']
    #lossesTrain = modelFittingHelper.getLosses(logger, fittedModels, modelNames, sizesTrain, flattenedRuntimesTrain, statistic)
    #print("Train Loss:")
    #print(lossesTrain)
    #lossesTest = modelFittingHelper.getLosses(logger, fittedModels, modelNames, sizesTest, flattenedRuntimesTest, statistic)
    #print("Test Loss:")
    #print(lossesTest)
    #exit()


    #   read in model names and definitions
    logger.debug('Reading in model names and definitions.')
    modelNames, modelNumParas, modelOriReps, modelGnuplotDefs = getModels(logger, '.', modelFileName)
    modelReps = replaceRepsForOutput( modelOriReps )
 

    #YP: Refactored code to only create bootstrap samples once to save time.
    logger.info('Creating bootstrap samples of support data.')
    bruntimesTrain, bsizesTrain = bootstrapHelper.makeBootstrapSamples(runtimesTrain, sizesTrain, numBootstrapSamples, window, perInstanceStatistic, numPerInstanceBootstrapSamples)
    logger.info('Creating bootstrap samples of challenge data.')
    bruntimesTest, bsizesTest = bootstrapHelper.makeBootstrapSamples(runtimesTest, sizesTest, numBootstrapSamples, window, perInstanceStatistic, numPerInstanceBootstrapSamples)


    #   calculate confidence intervals of observed data 
    #YP: Renaming and regrouping obsvsLos and obsvsUps to statyTrainBounds[0] and [1]
    logger.debug('Calculating confidence intervals of observed support data.')

    statyTrainBounds, bstatyTrain = bootstrapHelper.calObsIntervals(logger,bruntimesTrain,bsizesTrain,statistic,numBootstrapSamples,windowSize,statxTrain,alpha)

    logger.debug('Calculating confidence intervals of observed challenge data.')

    statyTestBounds, bstatyTest = bootstrapHelper.calObsIntervals(logger,bruntimesTest,bsizesTest,statistic,numBootstrapSamples,windowSize,statxTest,alpha)
 

    #   fit models
    logger.debug('Fitting models to the observed support data.')
    fittedModels, lossesTrain = modelFittingHelper.fitModels(logger, modelNames, statxTrain, statyTrain, sizesTrain, flattenedRuntimesTrain, statistic)

    lossesTest = modelFittingHelper.getLosses(logger, fittedModels, modelNames, sizesTest, flattenedRuntimesTest, statistic)


    #YP: I added an extra 'stretch size' here for predictions beyond the
    #largest challenge instance size
    #   calculate bootstrap intervals of fitted models
    logger.debug('Fitting models to the bootstrap samples.')
    bfittedModels, blossesTrain = bootstrapHelper.fitBootstrapModels(logger, modelNames, statxTrain, bstatyTrain, bsizesTrain, bruntimesTrain, statistic)


    logger.debug('Calculating bootstrap model predictions.')
    bpredsTrain, bpredsTest = bootstrapHelper.makePredictions(logger, bfittedModels, modelNames, statxTrain, statxTest)

    #YP: added a function call to check which model is considered the best
    #fit after the bootstrap sampling
    logger.debug('Calculating bootstrap model losses.')
    blossesTest = bootstrapHelper.getLosses(logger, bfittedModels, modelNames, bsizesTest, bruntimesTest, statistic)

    logger.debug('Calculating prediction loss intervals')
    ilossTrain, ilossTest = bootstrapHelper.getLossIntervals(logger, blossesTrain, blossesTest, alpha)


    #YP: Now we create the fitted model tables.
    logger.debug('Creating Tables for the fitted models.')
    latexHelper.makeTableFittedModels(fittedModels, lossesTrain, lossesTest, modelReps, modelNames, algName)


    #YP: Now we create the bootstrap model RMSE tables (new in ESA v1.1)
    #Note that we do not currently include the meanTrain/TestRMSEGeoMean values;
    #however, they could be added at a later time if desired, so we incldue them
    logger.debug('Creating bootstrap model loss tables.')
    tableBootstrapModelLossFileName, winnerSelectRule = latexHelper.makeTableBootstrapModelLosses(ilossTrain, ilossTest, modelNames, algName)


    logger.debug('Calculating confidence intervals for the model parameters.')
    #print([[[bfittedModels[k][b][i]  for b in range(0,len(bfittedModels[0]))] for i in range(0,modelNumParas[k])] for k in range(0,len(bfittedModels))])
    paraLos, paraUps = bootstrapHelper.getLoUps( modelNames, [[[bfittedModels[k][b][i]  for b in range(0,len(bfittedModels[0]))] for i in range(0,modelNumParas[k])] for k in range(0,len(bfittedModels))], alpha )

    #print(paraLos)

    logger.debug('Creating tables containing intervals for the model parameters.')
    csvHelper.genCSV( ".", "table_Bootstrap-intervals-of-parameters.csv", [ ("Confidence intervals of p%d" % i) for i in range(0, max(modelNumParas)) ], [ algName+" "+modelName+". model" for modelName in modelNames ], getIntervals(paraLos, paraUps))
    latexHelper.genTexTableBootstrapParas( algName, modelNames, modelNumParas, paraLos, paraUps )

    logger.debug('Creating csv file with all bootstrap fitted models.')
    csvHelper.genCSV(".", "table_Bootstrap-fitted-models.csv", \
                    [ modelNames[i] + ' parameter ' + chr(ord('a') + j) for i in range(0,len(modelNumParas)) for j in range(0,modelNumParas[i])], \
                    list(range(0,numBootstrapSamples)), \
                    [[p for fittedModel in bfittedModels for p in fittedModel[b]] for b in range(0,numBootstrapSamples)])


    logger.debug('Calculating confidence intervals for model predictions.')
    predTrainLos, predTrainUps = bootstrapHelper.getLoUps( modelNames, bpredsTrain, alpha )
    predTestLos, predTestUps = bootstrapHelper.getLoUps( modelNames, bpredsTest, alpha)


    logger.debug('Calculating fitted model residues.')
    residuesTrain = modelFittingHelper.getResidues(logger, statxTrain, statyTrain, fittedModels, modelNames)
    residuesTest = modelFittingHelper.getResidues(logger, statxTest, statyTest, fittedModels, modelNames)

    logger.debug('Calculating bootstrap fitted model residues.')
    iresiduesTrain = bootstrapHelper.getResidueBounds(logger, bstatyTrain, bpredsTrain, alpha )
    iresiduesTest = bootstrapHelper.getResidueBounds(logger, bstatyTest, bpredsTest, alpha)
    #YP: Testing stuff out here:
    #bootstrapHelper.getRelativeRMSEsAndIntervals(medianTestRMSEGeoMean,stats,obsvLos,obsvUps,predLos,predUps,threshold,sizes,modelNames)

    logger.debug('Creating tables with bootstrap intervals of running time predictions')
    csvHelper.genCSV( ".", "table_Bootstrap-intervals.csv", \
                    list(statxTest), \
                    [modelName+". model confidence intervals" for modelName in modelNames ] + ["observed point estimates", "observed confidence intervals"], \
                    getIntervals([predTestLos[k] for k in range(0, len(modelNames))], [predTestUps[k] for k in range(0, len(modelNames))]) + \
                    [statyTest] + \
                    [statyTestBounds] )

    latexHelper.genTexTableBootstrap( algName, modelNames, statxTrain, predTrainLos, predTrainUps, [[stat, stat] for stat in statyTrain], [bounds[0] for bounds in statyTrainBounds], [bounds[1] for bounds in statyTrainBounds], tableBootstrapIntervalsSupportFileName+".tex" , statistic)
    latexHelper.genTexTableBootstrap( algName, modelNames, statxTest, predTestLos, predTestUps, [[stat, stat] for stat in statyTest], [bounds[0] for bounds in statyTestBounds], [bounds[1] for bounds in statyTestBounds], tableBootstrapIntervalsChallengeFileName+".tex" , statistic)

    #   add above data into gnuplot files
    logger.debug('Setting up gnuplot figure files.')
    gnuplotHelper.genGnuplotFiles(modelNames, statxTrain, statxTest, statyTrain, statyTest, statyTrainBounds, statyTestBounds, predTrainLos, predTrainUps, predTestLos, predTestUps, sizesTrain, flattenedRuntimesTrain, sizesTest, flattenedRuntimesTest, residuesTrain, residuesTest, iresiduesTrain, iresiduesTest)

    gnuplotHelper.genGnuplotScripts(logger, algName, modelNames, fittedModels, statistic, sizes, sizeThreshold, flattenedRuntimesTrain, flattenedRuntimesTest, modelGnuplotDefs, runtimeCutoff, alpha)

    #   generate plots
    #YP: Added gnuplotPath
    #YP: Instead of directing output to /dev/null I'm sending it to a log file and checking for the beginning of an error message in the gnuplot file. If there is one, we print a message and save the output file.
    logger.debug('Creating fittedModels.pdf')
    os.system(gnuplotPath + "gnuplot plotModels.plt >& plotModels.log")
    logger.debug('Creating fittedResidues.pdf')
    os.system(gnuplotPath + "gnuplot plotResidues.plt >& plotResidues.log")
    logFiles = ['plotModels', 'plotResidues']
    for logFile in logFiles:
        logger.debug('Checking for errors in ' + logFile + '.log...')
        with open(logFile + '.log') as f_log:
            logText = f_log.read()
            if('"' + logFile + '.plt", line' in logText):
                logger.warning('There may have been an error in ' + logFile + '.plt. If you encounter any problems, please try running it manually and checking the corresponding gnuplot template file you used. The output was saved in ' + logFile + '.log')
            else: 
                os.system('rm -f ' + logFile + '.log')


    #   generate files
    logger.debug('Populating the LaTeX report template.')
    latexHelper.genTexFile( fileDir, algName, instName, numObsv, sizesTrain, sizesTest, len(flattenedRuntimesTrain), len(flattenedRuntimesTest), sizeThreshold, modelNames, modelOriReps, modelNumParas, numBootstrapSamples, statistic, numRunsPerInstance, perInstanceStatistic, numPerInstanceBootstrapSamples, tableDetailsSupportFileName, tableDetailsChallengeFileName, tableFittedModelsFileName, tableBootstrapIntervalsParaFileName, tableBootstrapIntervalsSupportFileName, tableBootstrapIntervalsChallengeFileName, tableBootstrapModelLossFileName, figureCdfsFileName, figureFittedModelsFileName, figureFittedResiduesFileName, evaluateModelsConsistency(logger,modelNames,[[stat, stat] for stat in statyTest], [bounds[0] for bounds in statyTestBounds], [bounds[1] for bounds in statyTestBounds], predTestLos, predTestUps), winnerSelectRule, latexTemplate, alpha)
    logger.debug('Running pdflatex and bibtex to create the LaTeX report.')
    os.system( "pdflatex 'scaling_%s.tex' >& /dev/null < pdflatex-input.txt" % latexHelper.removeSubstrs( algName, '/' ) )
    os.system( "bibtex 'scaling_%s' >& /dev/null < pdflatex-input.txt" %       latexHelper.removeSubstrs( algName, '/' ) )
    os.system( "pdflatex 'scaling_%s.tex' >& /dev/null < pdflatex-input.txt" % latexHelper.removeSubstrs( algName, '/' ) )
    os.system( "pdflatex 'scaling_%s.tex' >& /dev/null < pdflatex-input.txt" % latexHelper.removeSubstrs( algName, '/' ) )

    #YP: Added a check for the pdf file and error message
    if(not os.path.isfile('scaling_' + latexHelper.removeSubstrs(algName, '/') + '.pdf')):
        logger.error('scaling_' + latexHelper.removeSubstrs(algName, '/') + '.pdf was not successfully created. This may be due to a tex complication error. If you are not sure why, please try compiling scaling_' + latexHelper.removeSubstrs(algName, '/') + '.tex manually to check for errors.')

    with open('time.log','a') as f_out:
        f_out.write('-'*60 + '\n')
        f_out.write('Run at: ' + str(datetime.datetime.now()) + '\n')
        f_out.write('Took a total of: ' + str(time.time()-startTime) + '\n')
        f_out.write('Outer Samples: ' + str(numBootstrapSamples) + '\n')
        f_out.write('Inner Samples: ' + str(numPerInstanceBootstrapSamples) + '\n')

    #   wrap up
    os.chdir( cwd )

