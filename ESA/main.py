import os
import math
import numpy
import summarizeRuntimes
import modelFittingHelper
import bootstrapHelper
import csvHelper
import gnuplotHelper
import latexHelper
import logging

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
            print instr
            raise Exception
        id = instr[stIdx+2]
        if inPython:
            instr = instr[0:stIdx] + ("p[%d]" % (ord(id)-ord('a'))) + instr[edIdx:]
        else:
            instr = instr[0:stIdx] + ("p%d" % (ord(id)-ord('a'))) + instr[edIdx:]
    return instr

def getModels(logger, fileDir, fileName, toModifyModelDefaultParas, sizes, stats, threshold ):
    modelNames = []
    modelNumParas = []
    modelReps = []
    modelDefs = []
    modelGnuplotDefs = []
    modelParaDefaults = []
    modelFuncs = []
    with open(fileDir+"/"+fileName, "r") as modelFile:
        for line in modelFile:
            terms = line.split(",")
            if len(terms)>5:
                modelNames.append( terms[0].strip() )
                logging.debug('Parsing ' + modelNames[-1] + ' model.')
                modelNumParas.append( int(terms[1]) )
                modelReps.append( terms[2].strip() )
                modelDefs.append( inputModelToInternal( terms[3].strip(), True ) )
                modelGnuplotDefs.append( inputModelToInternal( terms[4].strip(), False ) )
                modelParaDefaults.append( [] )
                y1 = float(stats[threshold-1])
                y0 = float(stats[0])
                #print(threshold)
                x1 = float(sizes[threshold-1])
                x0 = float(sizes[0])
                #print(x1)
                #print(x0)
                #print(x1**(0.5))
                if toModifyModelDefaultParas and modelNames[-1].lower() == "exp" or modelNames[-1].lower() == "exponential":
                    #YP: My new way of pre-fitting:
                    #which exactly fits the mdoel to the smallest and
                    #largest support instance sizes.
                    b = math.exp((math.log(y1) - math.log(y0))/(x1 - x0))
                    a = math.exp(math.log(y0) - math.log(b)*x0)
                    #YP: Zongxu's old way of pre-fitting:
                    #b = ( stats[threshold]/stats[threshold-1] ) ** ( 1.0 / ( sizes[threshold]-sizes[threshold-1] ) )
                    #a = stats[threshold]/(b**sizes[threshold])
                    #b = 1+(b-1)/2
                    logger.info("Replacing %s model parameters as (%f, %f)" % (modelNames[-1], a, b))
                    modelParaDefaults[-1].append( a )
                    modelParaDefaults[-1].append( b )
                elif toModifyModelDefaultParas and modelNames[-1].lower() == "rootexp" or modelNames[-1].lower() == "root-exponential" or modelNames[-1].lower == "sqrtexp":
                    #YP: My new way of pre-fitting the parameters:
                    #which exactly fits the model to the smallest and
                    #largest support instance sizes.
                    b = math.exp((math.log(y1) - math.log(y0))/(x1**(0.5) - x0**(0.5)))
                    a = math.exp(math.log(y0) - math.log(b)*(x0**(0.5)))
                    #YP: Zongxu's old method for pre-fitting:
                    #b = ( stats[threshold]/stats[threshold-1] ) ** ( 1.0 / ( math.sqrt(sizes[threshold])-math.sqrt(sizes[threshold-1]) ) )
                    #a = stats[threshold] / (b**math.sqrt(sizes[threshold]))
                    #b = 1+(b-1)/2
                    logger.info("Replacing %s model parameters as (%f, %f)" % (modelNames[-1], a, b))
                    modelParaDefaults[-1].append( a )
                    modelParaDefaults[-1].append( b )
                elif toModifyModelDefaultParas and modelNames[-1].lower() == "poly" or modelNames[-1].lower() == "polynomial":
                    #YP: My new way of pre-fitting the parameters:
                    #which exactly fits the model to the smallest and
                    #largest support instance sizes.
                    b = (math.log(y1) - math.log(y0))/(math.log(x1) - math.log(x0))
                    a = math.exp(math.log(y0) - b*math.log(x0))
                    #YP: Zongxu's old way of pre-fitting the parameters:
                    #b = ( math.log(stats[threshold]) - math.log(stats[threshold-1]) ) / ( math.log(sizes[threshold]) - math.log(sizes[threshold-1]) )
                    #a = stats[threshold] / (sizes[threshold] ** b)
                    #b = min(1, b/2)
                    logger.info("Replacing %s model parameters as (%f, %f)" % (modelNames[-1], a, b))
                    modelParaDefaults[-1].append( a )
                    modelParaDefaults[-1].append( b )
                else:
                    for i in range(0, int(terms[1])):
                        modelParaDefaults[-1].append( float(terms[5+i] ) )
    for md in modelDefs:
        def func(p, x, modelDef=md):
            # print modelDef
            return eval( modelDef )
        modelFuncs.append( func )
    return (modelNames, modelNumParas, modelReps, modelDefs, modelGnuplotDefs, modelParaDefaults, modelFuncs)

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



def evaluateModelsConsistency(logger, modelNames, threshold, statIntervals, obsvLos, obsvUps, predLos, predUps):
    #Author: Yasha Pushak
    #Last updated: April 5th, 2017
    #I am creating a third method for analysing the consistency of the data to create a text-based description. Unlike the original, this one
    #counts the number of instance sizes for which model predictions are both strongly and weakly consistent (instead of just strongly consistent)
    #with the observed data. 

    logger.debug('Interpretating results of scaling model fits.')

    types = set([])
    intervalsData = []

    res = ""
    #res = "Based on the observed data and the predicted bootstrap intervals from the models, we see that "
    largerHalfIdx = (len(statIntervals)+threshold)/2
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
        for size in range(threshold, len(statIntervals)):
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
                     
        perAboveIntervals = 1.0*numOverIntervals/(len(statIntervals)-threshold)
        perAboveIntervalsLarger = 1.0*numOverIntervalsLarger/(len(statIntervals)-largerHalfIdx)
        perBelowIntervals = 1.0*numBelowIntervals/(len(statIntervals)-threshold)
        perBelowIntervalsLarger = 1.0*numBelowIntervalsLarger/(len(statIntervals)-largerHalfIdx)
        perStronglyConsistent = 1.0*numStronglyWithinIntervals/(len(statIntervals)-threshold)
        perStronglyConsistentLarger = 1.0*numStronglyWithinIntervalsLarger/(len(statIntervals)-largerHalfIdx)
        perWeaklyConsistent = 1.0*numWeaklyWithinIntervals/(len(statIntervals)-threshold)
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
            resExplain += "we say a model fits the data very well if 90\% or more of the predicted bootstrap intervals (or the larger half of the predicted intervals) are strongly consistent with the observed data and at least 90\% of the predicted bootstrap intervals are weakly consistent with the observed data"
        elif(type == 'weaklyConsistent'):
            resExplain += "we say a model tends to fit the data if 90\% or more of the predicted bootstrap intervals (or the larger half of the predicted intervals) are weakly consistent with the observed data"
        elif(type == 'under'):
            resExplain += "we say a model under-estimates the data if more than 70\% of the predicted bootstrap intervals (or more than 70\% of the larger half of the predicted intervals) are disjoint from the observed bootstrap intervals and are below the observed intervals"
        elif(type == 'over'):
            resExplain += "we say a model over-estimates the data if more than 70\% of the predicted bootstrap intervals (or more than 70\% of the larger half of the predicted bootstrap intervals) are disjoint from the observed bootstrap intervals and are above the observed intervals"
        elif(type == 'tendUnder'):
            resExplain += "we say a model tends to under-estimate the data if more than 10\% of the predicted bootstrap intervals are disjoint from the observed bootstrap intervals, and at least 95\% of the predicted bootstrap intervals (or the larger half of the predicted intervals) are above or are consistent with the observed data"
        elif(type == 'tendOver'):
            resExplain += "we say a model tends to over-estimate the data if more than 10\% of the predicted bootstrap intervals are disjoint from the observed bootstrap intervals, and at least 95\% of the predicted bootstrap intervals (or the larger half of the predicted intervals) are consistent with or are below the observed data"
        elif(type == 'noFit'):
            resExplain += "we say a model does not fit the data very well if more than 10\% of the predicted bootstrap intervals are disjoint from the observed bootstrap intervals, more than 5\% of the predicted intervals are above the observed intervals, and more than 5\% of the predicted intervals are below the obvserved intervals"

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

        #YP: Removed some old debugging messages
        print perAboveIntervals
        print perAboveIntervalsLarger
        print perBelowIntervals
        print perBelowIntervalsLarger
        print perWithinIntervals
        print perWithinIntervalsLarger

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


def run(fileDir, fileName="runtimes.csv", algName="Algorithm", instName="the problem instances", modelFileName="models.txt", threshold=0, alpha=95, numBootstrapSamples=100, statistic="median", toModifyModelDefaultParas=False, tableDetailsSupportFileName="table_Details-dataset-support", tableDetailsChallengeFileName="table_Details-dataset-challenge", tableFittedModelsFileName="table_Fitted-models", tableBootstrapIntervalsParaFileName="table_Bootstrap-intervals-of-parameters", tableBootstrapIntervalsSupportFileName="table_Bootstrap-intervals_support", tableBootstrapIntervalsChallengeFileName="table_Bootstrap-intervals_challenge", figureCdfsFileName="cdfs", figureFittedModelsFileName="fittedModels", figureFittedResiduesFileName="fittedResidues", latexTemplate = "template-AutoScaling.tex", modelPlotTemplate = "template-plotModels.plt", residuePlotTemplate = "template-plotResidues.plt", gnuplotPath = '', numRunsPerInstance = 0, perInstanceStatistic="median", numPerInstanceBootstrapSamples=10,logLevel = "INFO"):
    #   get parameter values
    if os.path.exists( fileDir+"/configurations.txt" ):
        with open( fileDir+"/configurations.txt", "r") as configFile:
            for line in configFile:
                terms = line.split(":")
                if len(terms) == 2:
                    if terms[0].strip() == "fileName":
                        fileName = terms[1].strip()
                    if terms[0].strip() == "algName":
                        algName = terms[1].strip()
                    if terms[0].strip() == "instName":
                        instName = terms[1].strip()
                    if terms[0].strip() == "modelFileName":
                        modelFileName = terms[1].strip()
                    if terms[0].strip() == "numTrainingData":
                        threshold = int( terms[1] )
                    if terms[0].strip() == "alpha":
                        alpha = int( terms[1] )
                    if terms[0].strip() == "numBootstrapSamples":
                        numBootstrapSamples = int( terms[1].strip() )
                    if terms[0].strip() == "statistic":
                        statistic = terms[1].strip()
                    if terms[0].strip() == "latexTemplate":
                        latexTemplate = terms[1].strip()
                    if terms[0].strip() == "modelPlotTemplate":
                        modelPlotTemplate = terms[1].strip()
                    if terms[0].strip() == "residuePlotTemplate":
                        residuePlotTemplate = terms[1].strip()
                    #YP: Added gnuplot path to configuration file
                    if terms[0].strip() == "gnuplotPath":
                        gnuplotPath = terms[1].strip() + '/'
                    #YP: Added numRunsPerInstance to configuration file
                    if terms[0].strip() == "numRunsPerInstance":
                        numRunsPerInstance = int( terms[1].strip() )
                    #YP: Added perInstanceStatistic to configuration file
                    if terms[0].strip() == "perInstanceStatistic":
                        perInstanceStatistic = terms[1].strip()
                    #YP: Added numPerInstanceBootstrapSamples to configuration file
                    if terms[0].strip() == "numPerInstanceBootstrapSamples":
                        numPerInstanceBootstrapSamples = int(terms[1].strip())
                    #YP: Added modifyDefaultParameters to configuration file
                    if terms[0].strip() == "modifyDefaultParameters":
                        toModifyModelDefaultParas = (terms[1].strip() == "True")
                    if terms[0].strip() == 'logLevel':
                        logLevel = terms[1].strip()

    numericLevel = getattr(logging, logLevel.upper(), None)
    if not isinstance(numericLevel, int):
        raise ValueError('Invalid log level: %s' % logLevel)
    logging.basicConfig(format='[%(levelname)s]: %(message)s',level=numericLevel) 
    logger = logging.getLogger('ESA logger')

    #logger.warning('test')


    if(threshold == 1):
        raise ValueError('The number of support instance sizes used (numTrainingData) must be greater than 1')

    #   prepare template files
    logger.debug('Preparing template files')
    if not os.path.exists( fileDir+"/"+modelFileName ):
        os.system( "cp models.txt %s" % (fileDir+"/"+modelFileName) )
    if not os.path.exists( fileDir+"/"+latexTemplate ):
        os.system( "cp template-AutoScaling.tex %s" % (fileDir+"/"+latexTemplate) )
    if not os.path.exists( fileDir+"/"+modelPlotTemplate ):
        os.system( "cp template-plotModels.plt %s" % (fileDir+"/"+modelPlotTemplate) )
    if not os.path.exists( fileDir+"/"+residuePlotTemplate ):
        os.system( "cp template-plotResidues.plt %s" % (fileDir+"/"+residuePlotTemplate) )
    #   move the pdflatex input file
    if not os.path.exists( fileDir+"/pdflatex-input.txt" ):
        if(not os.path.exists('pdflatex-input.txt')):
            with open('pdflatex-input.txt','w') as f_out:
                f_out.write('R\n\n')
        os.system( "cp pdflatex-input.txt " + fileDir +"/pdflatex-input.txt" )    
    #print(numRunsPerInstance)
    #   read in runtimes and summarize
    logger.debug('Reading running times from file')
    (sizes, runtimes, numInsts, numRunsPerInstance) = summarizeRuntimes.getRuntimesFromFile(logger, fileDir, fileName, numRunsPerInstance )

    cwd = os.getcwd()
    os.chdir( fileDir )
    logger.debug('Calculating summary statistics for running times.')
    (counts, stats, statIntervals, threshold) = summarizeRuntimes.summarizeRuntimes( sizes, runtimes, numInsts, algName, ".", statistic, perInstanceStatistic, threshold )
    # stats = [ summarizeRuntimes.calStatistic( runtimes[i], statistic ) for i in range(0, len(sizes)) ]

    #   read in model names and definitions
    logger.debug('Reading in model names and definitions')
    (modelNames, modelNumParas, modelOriReps, modelDefs, modelGnuplotDefs, modelParaDefaults, modelFuncs) = getModels(logger, '.', modelFileName, toModifyModelDefaultParas, sizes, stats, threshold )
    modelReps = replaceRepsForOutput( modelOriReps )

    #   prepare gnuplot scripts
    logger.debug('Creating gnuplot scripts')
    gnuplotHelper.genGnuplotScripts( modelNames, modelGnuplotDefs, modelNumParas, modelParaDefaults, '.', sizes, modelPlotTemplate, residuePlotTemplate )
    

    #YP: Refactored code to only create bootstrap samples once to save time.
    logger.debug('Creating bootstrap samples of running time data')
    bStat = bootstrapHelper.doBootstrap(logger, runtimes, numInsts, numBootstrapSamples, statistic, perInstanceStatistic, numPerInstanceBootstrapSamples)


    #   calculate confidence intervals of observed data
    logger.debug('Calculating confidence intervals of observed data.')
    (obsvLos, obsvUps) = bootstrapHelper.getBootstrapIntervals( bStat )

    #   fit models
    logger.debug('Fitting models to the observed point estimates.')
    (para, rmseTrains, rmseTests) = modelFittingHelper.fitModels(logger, algName, modelNames, modelNumParas, modelReps, modelFuncs, sizes, stats, statIntervals, threshold, gnuplotPath, modelFileName)


    #   calculate bootstrap intervals of fitted models
    logger.debug('Fitting models to the bootstrap samples.')
    (paras, preds) = bootstrapHelper.doBootstrapAnalysis(logger, bStat[0], sizes, runtimes, threshold, statistic, modelNames, modelNumParas, modelFuncs, numBootstrapSamples, gnuplotPath )

    #YP: added a function call to check which model is considered the best
    #fit after the bootstrap sampling
    logger.debug('Calculating bootstrap sample RMSE statistics.')
    (rmseTrainBounds, rmseTestBounds, medianTrainRMSEGeoMean, meanTrainRMSEGeoMean, medianTestRMSEGeoMean, meanTestRMSEGeoMean) = bootstrapHelper.getBootstrapRMSE(preds, bStat, sizes, threshold, modelNames)

    #print(rmseTests)
    #print(rmseTestBounds)
    #YP: Now we create the fitted model tables.
    logger.debug('Creating Tables for the fitted models.')
    modelFittingHelper.makeTableFittedModels(para, rmseTrains, rmseTests, modelNumParas, modelReps, modelNames, threshold, algName, sizes)


    #YP: Now we create the bootstrap model RMSE tables (new in ESA v1.1)
    #Note that we do not currently include the meanTrain/TestRMSEGeoMean values;
    #however, they could be added at a later time if desired, so we incldue them
    logger.debug('Creating bootstrap RMSE tables.')
    (tableBootstrapModelRMSEFileName, winnerSelectRule) = bootstrapHelper.makeTableBootstrapModelRMSEs(rmseTrainBounds, rmseTestBounds, medianTrainRMSEGeoMean, meanTrainRMSEGeoMean, medianTestRMSEGeoMean, meanTestRMSEGeoMean, modelNames, algName)


    #   fit models
    #modelFittingHelper.fitModels(logger, algName, modelNames, modelNumParas, modelReps, modelFuncs, sizes, stats, statIntervals, threshold, gnuplotPath, modelFileName)

    logger.debug('Calculating confidence intervals for the model parameters.')
    (paraLos, paraUps) = bootstrapHelper.getLoUps( modelNames, paras )

    logger.debug('Creating tables containing intervals for the model parameters.')
    csvHelper.genCSV( ".", "table_Bootstrap-intervals-of-parameters.csv", [ ("Confidence intervals of p%d" % i) for i in range(0, max(modelNumParas)) ], [ algName+" "+modelName+". model" for modelName in modelNames ], getIntervals(paraLos, paraUps))
    latexHelper.genTexTableBootstrapParas( algName, modelNames, modelNumParas, paraLos, paraUps )


    logger.debug('Calculating confidence intervals for model predictions')
    (predLos, predUps) = bootstrapHelper.getLoUps( modelNames, preds )

    #YP: Testing stuff out here:
    #bootstrapHelper.getRelativeRMSEsAndIntervals(medianTestRMSEGeoMean,stats,obsvLos,obsvUps,predLos,predUps,threshold,sizes,modelNames)

    logger.debug('Creating tables with bootstrap intervals of running time predictions')
    csvHelper.genCSV( ".", "table_Bootstrap-intervals.csv", [algName for i in range(threshold, len(sizes))], ["n"] + [modelName+". model confidence intervals" for modelName in modelNames ] + ["observed point estimates", "observed confidence intervals"], [sizes[threshold:]] + getIntervals([predLos[k][threshold:] for k in range(0, len(modelNames))], [predUps[k][threshold:] for k in range(0, len(modelNames))]) + [stats[threshold:]] + getIntervals([obsvLos[threshold:]], [obsvUps[threshold:]]) )
    latexHelper.genTexTableBootstrap( algName, modelNames, sizes, 0, threshold, predLos, predUps, statIntervals, obsvLos, obsvUps, tableBootstrapIntervalsSupportFileName+".tex" )
    latexHelper.genTexTableBootstrap( algName, modelNames, sizes, threshold, len(sizes), predLos, predUps, statIntervals, obsvLos, obsvUps, tableBootstrapIntervalsChallengeFileName+".tex" )

    #   add above data into gnuplot files
    logger.debug('Setting up gnuplot figure files.')
    gnuplotHelper.genGnuplotFiles( fileDir, sizes, stats, statIntervals, obsvLos, obsvUps, predLos, predUps, threshold, statistic )

    #   generate plots
    #YP: Added gnuplotPath
    #YP: Instead of directing output to /dev/null I'm sending it to a log file and checking for the beginning of an error message in the gnuplot file. If there is one, we print a message and save the output file.
    logger.debug('Creating fittedModels.pdf')
    os.system(gnuplotPath + "gnuplot plotModels.plt >& plotModels.log")
    logger.debug('Creating fittedResidues.pdf')
    os.system(gnuplotPath + "gnuplot plotResidues.plt >& plotResidues.log")
    logFiles = ['plotModels', 'plotResidues']
    for logFile in logFiles:
        with open(logFile + '.log') as f_log:
            logText = f_log.read()
            if('"' + logFile + '.plt", line' in logText):
                logger.warning('There may have been an error in ' + logFile + '.plt. If you encounter any problems, please try running it manually and checking the corresponding gnuplot template file you used. The output was saved in ' + logFile + '.log')
            else: 
                os.system('rm -f ' + logFile + '.log')

    #   generate files
    logger.debug('Populating the LaTeX report template.')
    latexHelper.genTexFile( fileDir, algName, instName, sizes, counts, numInsts, threshold, modelNames, modelOriReps, modelNumParas, numBootstrapSamples, statistic, numRunsPerInstance, perInstanceStatistic, numPerInstanceBootstrapSamples, tableDetailsSupportFileName, tableDetailsChallengeFileName, tableFittedModelsFileName, tableBootstrapIntervalsParaFileName, tableBootstrapIntervalsSupportFileName, tableBootstrapIntervalsChallengeFileName, tableBootstrapModelRMSEFileName, winnerSelectRule, figureCdfsFileName, figureFittedModelsFileName, figureFittedResiduesFileName, evaluateModelsConsistency(logger,modelNames, threshold, statIntervals, obsvLos, obsvUps, predLos, predUps), latexTemplate )
    logger.debug('Running pdflatex and bibtex to create the LaTeX report.')
    os.system( "pdflatex 'scaling_%s.tex' >& /dev/null < pdflatex-input.txt" % latexHelper.removeSubstrs( algName, '/' ) )
    os.system( "bibtex 'scaling_%s' >& /dev/null < pdflatex-input.txt" %       latexHelper.removeSubstrs( algName, '/' ) )
    os.system( "pdflatex 'scaling_%s.tex' >& /dev/null < pdflatex-input.txt" % latexHelper.removeSubstrs( algName, '/' ) )
    os.system( "pdflatex 'scaling_%s.tex' >& /dev/null < pdflatex-input.txt" % latexHelper.removeSubstrs( algName, '/' ) )

    #YP: Added a check for the pdf file and error message
    if(not os.path.isfile('scaling_' + latexHelper.removeSubstrs(algName, '/') + '.pdf')):
        logger.error('scaling_' + latexHelper.removeSubstrs(algName, '/') + '.pdf was not successfully created. This may be due to a tex complication error. If you are not sure why, please try compiling scaling_' + latexHelper.removeSubstrs(algName, '/') + '.tex manually to check for errors.')

    #   wrap up
    os.chdir( cwd )

