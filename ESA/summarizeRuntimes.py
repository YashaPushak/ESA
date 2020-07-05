import math
import numpy as np
import os
import sys
import csvHelper
import latexHelper
import modelFittingHelper
import copy as cp 


def calStatistic( list, statistic ):
    if statistic.lower() == "mean":
        return np.mean( list )
    if statistic.lower() == "median":
        statistic = "q50"
    if statistic[0].lower() == "q":
        percent = float( statistic[1:] )
        if(percent < 0):
           raise ValueError("Invalid statistic: " + statistic)
        if percent<1:
            percent *= 100

        for elem in list:
            if(math.isnan(elem)):
                return float('NaN')

        list = sorted(list)
        I = len(list)*(percent/100.0) - 1
        #Check if I is an integer
        if(int(I) - I == 0):
           return (list[int(I)] + list[int(I+1)])/2
        else:
           return list[int(math.ceil(I))]

        #YP: The original code here used to always return a lower-bound on
        #the quantiles. I have changed this..
        #This is what Zongxu used to have: 
        #return sorted(list)[ int(len(list)*percent/100)-1 ]
    raise ValueError('Invalid summary statistic input: ' + statistic)

def calStatisticIntervals( list, statistic, numInsts ):
    if statistic == "mean" or len(list) == numInsts:
        return [ calStatistic( list, statistic ) for i in range(0,2) ]
    else:
        return [ calStatistic( list+[ 0 for i in range(0, numInsts-len(list)) ], statistic ), calStatistic( list+[ float('inf') for i in range(0, numInsts-len(list)) ], statistic ) ]


def getRuntimesFromFile(logger, dirName, filename, numRunsPerInstance, runtimeCutoff):
    #Author: YP 
    #Created: 2018-12-17
    #Updated: 2019-01-21

    numWarning = 0
    maxWarnings = 10
    with open(dirName + '/' + filename) as f_in:
        sizes = []
        runtimes = []
        for line in f_in:
            if('#' in line[0]):
                continue
            items = line.split(',')
            instRuntimes = []
            skip = False
            for i in range(2,len(items)):
                try:
                    runtime = float(items[i])
                    if(runtime > runtimeCutoff):
                        runtime = runtimeCutof
                except:
                    runtime = runtimeCutoff
                if(runtime < 0):
                    runtime = runtimeCutoff
                    numWarning += 1
                    if(numWarning <= maxWarnings):
                        logger.warning("Treating running time value of 0 as " + str(runtimeCutoff))
                instRuntimes.append(runtime)

            if(numRunsPerInstance == 0):
                numRunsPerInstance = len(instRuntimes)
                updatedNumRunsPerInstance = True
            #Check that the number of running times is consistent.
            if(not len(instRuntimes) == numRunsPerInstance):
                raise Exception("The number of runs per instance is inconsistent, starting with instance " + items[0])

            sizes.append(int(float(items[1])))
            runtimes.append(instRuntimes)

    sizes = np.array(sizes)
    runtimes = np.array(runtimes)
    sortInds = np.argsort(sizes)
    sizes = sizes[sortInds]
    runtimes = runtimes[sortInds]

    return sizes, runtimes, len(runtimes), numRunsPerInstance


def prepareRuntimesTexTable(st, ed, sizes, numInsts, means, q10s, q25s, medians, q75s, q90s):
    #print(str(st) + ' - ' + str(ed))
    #print(means)
    res = ""
    res += "\\begin{tabular}{c|" + "c"*len(sizes[st:ed]) + "} \n"
    res += "\\hline \n"
    res += latexHelper.prepareTableRow("$n$", sizes[st:ed])
    res += "\\hline \n"*2
    res += latexHelper.prepareTableRow("\\# instances", ['$' + str(latexHelper.numToTex(v,4)) + '$' for v in numInsts[st:ed]])
    res += latexHelper.prepareTableRow("mean", [ ("$%s$" % latexHelper.numToTex(means[i], 4)) for i in range(st,ed) ] )
    res += latexHelper.prepareTableRow("Q(0.1)",  [ ( "$%s$" % latexHelper.numToTex(v[0],4) if v[0]==v[1] else latexHelper.genInterval(latexHelper.numToTex(v[0], 3), latexHelper.numToTex(v[1], 4) ) ) for v in q10s[st:ed] ])
    res += latexHelper.prepareTableRow("Q(0.25)", [ ( "$%s$" % latexHelper.numToTex(v[0],4) if v[0]==v[1] else latexHelper.genInterval(latexHelper.numToTex(v[0], 3), latexHelper.numToTex(v[1], 4) ) ) for v in q25s[st:ed] ])
    res += latexHelper.prepareTableRow("median",  [ ( "$%s$" % latexHelper.numToTex(v[0],4) if v[0]==v[1] else latexHelper.genInterval(latexHelper.numToTex(v[0], 3), latexHelper.numToTex(v[1], 4) ) ) for v in medians[st: ed]])
    res += latexHelper.prepareTableRow("Q(0.75)", [ ( "$%s$" % latexHelper.numToTex(v[0],4) if v[0]==v[1] else latexHelper.genInterval(latexHelper.numToTex(v[0], 3), latexHelper.numToTex(v[1], 4) ) ) for v in q75s[st:ed] ])
    res += latexHelper.prepareTableRow("Q(0.9)",  [ ( "$%s$" % latexHelper.numToTex(v[0],4) if v[0]==v[1] else latexHelper.genInterval(latexHelper.numToTex(v[0], 3), latexHelper.numToTex(v[1], 4) ) ) for v in q90s[st:ed] ])
    res += "\\hline \n"
    res += "\\end{tabular} \n"
    res += "\\medskip{} \n"
    return res

def prepareRuntimesTexTables(logger, sizesTrain, runtimesTrain, sizesTest, runtimesTest, sizeThreshold, windowSize, dirName, specificObsvs, obsvs, supportTexFileName="table_Details-dataset-support.tex", challengeTexFileName="table_Details-dataset-challenge.tex"):
    dataTrain = {}
    dataTest = {}
    data = {}

    allSizes = list(cp.copy(sizesTrain))
    allSizes.extend(list(cp.copy(sizesTest)))
    start = int(max(calStatistic(allSizes,'q10')/1.1,min(allSizes)))
    stop = int(min(calStatistic(allSizes,'q90')*1.1,max(allSizes)))
    if(not specificObsvs):
        obsvs = np.array(range(start,stop,(stop-start)/10))

    #print(min(sizesTest))
    #print(str(start) + ' - ' + str(stop))

    obsvsTrain = obsvs[np.where(obsvs <= sizeThreshold)]
    obsvsTest = obsvs[np.where(obsvs > sizeThreshold)] 
 
    windowSize = calWindowSize(logger, sizesTrain,obsvsTrain,sizesTest,obsvsTest,windowSize)


    #print(len(obsvs))
    #print(len(obsvsTrain))
    #print(len(obsvsTest))
    #print(sizeThreshold)

    for stat in ['mean','q0.10','q0.25','q0.50','q0.75','q0.90']:
        statxTrain, statyTrain, statwTrain = calObsvStats(runtimesTrain,sizesTrain,stat,windowSize,obsvsTrain)
        statxTest, statyTest, statwTest = calObsvStats(runtimesTest,sizesTest,stat,windowSize,obsvsTest)
        #print('-'*10)
        #print(len(statyTrain))
        #print(len(statyTest))
        #print(len(obsvsTest))
        data[stat] = statyTrain
        data[stat].extend(statyTest)

        if(not stat == 'mean'):
            #Fake the intervals for now
            for i in range(0,len(data[stat])):
                data[stat][i] = [data[stat][i],data[stat][i]]
            #print(data[stat])
        
    statw = statwTrain
    statw.extend(statwTest)

    #print(statyTrain)
    #print(statyTest)
    #print(obsvsTrain)
    #print(obsvsTest)
    #print(obsvs)
    #print(len(statw))
    
    csvHelper.genCSV(".", "table_Details-dataset.csv", list(obsvs), ["# of instances", "mean", "Q(0.1)", "Q(0.25)", "median", "Q(0.75)", "Q(0.9)"], [statw, data['mean'], data['q0.10'], data['q0.25'], data['q0.50'], data['q0.75'], data['q0.90']])

    threshold = sum(np.array(obsvs) <= sizeThreshold)

    maxColsPerTable = 4
    with open(dirName+"/"+supportTexFileName, "w") as texFile:
        numTables = (threshold+maxColsPerTable-1)/maxColsPerTable
        numCols = (threshold+numTables-1)/numTables
        for i in range(0, numTables):
            print >>texFile, prepareRuntimesTexTable(i*numCols, min((i+1)*numCols, threshold), obsvs, statw, data['mean'], data['q0.10'], data['q0.25'],data['q0.50'], data['q0.75'], data['q0.90'])
    with open(dirName+"/"+challengeTexFileName, "w") as texFile:
        numTables = (len(obsvs)-threshold+maxColsPerTable-1)/maxColsPerTable
        numCols = (len(obsvs)-threshold+numTables-1)/numTables
        for i in range(0, numTables):
            print >>texFile, prepareRuntimesTexTable(threshold+i*numCols, min(threshold+(i+1)*numCols, len(obsvs)), obsvs, statw, data['mean'], data['q0.10'], data['q0.25'], data['q0.50'], data['q0.75'], data['q0.90'])

    
def summarizeRuntimes(logger, sizes, runtimes, numInsts, algName, dirName, statistic, perInstanceStatistic, threshold, numObsv, obsvs, window):
    #Author: YP
    #Created: 2018-12-17
    #Last updated: 2019-01-02 
 
    #YP: Calculate the per-instance statistics and use them in place of what used to be the running times.    
    runtimeStatistics = np.array([calStatistic(runtimes[i], perInstanceStatistic) for i in range(0,len(runtimes))])

    sizeThreshold = sizes[int(len(sizes)*threshold)]

    #print('size Threshold: ' + str(sizeThreshold))

    #Take either the true min and max, or, in case there are a small number of outlying sizes,
    #we take the 80% confidence interval and then multiply/divide by 1.1 to obtain the location
    #for where the max and min would be if the data was all perfectly spaced. In case this pushes
    #the max and min outside of the actual range of the data, we take the max/min
    start = int(max(calStatistic(sizes,'q10')/1.1,min(sizes)))
    stop = int(min(calStatistic(sizes,'q90')*1.1,max(sizes)))
    if(obsvs is None):
        specificObsvs = False
        obsvs = np.array(range(start,stop,(stop-start)/numObsv))
    else:
        specificObsvs = True
        obsvs = np.array(obsvs)
    windowSize = float(stop-start)*window/(len(sizes)*0.8)
  
    #print('Window Size: ' + sr(windowSize))
    #print(obsvs)

    runtimeStatsTrain = runtimeStatistics[np.where(sizes <= sizeThreshold)]
    runtimesTrain = runtimes[np.where(sizes <= sizeThreshold)]
    sizesTrain = sizes[np.where(sizes <= sizeThreshold)]
    statxTrain = obsvs[np.where(obsvs <= sizeThreshold)]
    runtimeStatsTest = runtimeStatistics[np.where(sizes > sizeThreshold)]
    runtimesTest = runtimes[np.where(sizes > sizeThreshold)]
    sizesTest = sizes[np.where(sizes > sizeThreshold)]
    statxTest = obsvs[np.where(obsvs > sizeThreshold)]

    windowSize = calWindowSize(logger,sizesTrain,statxTrain,sizesTest,statxTest,windowSize)

    #print(runtimesTrain)
    #print("Before")
    #print(statxTest)
    statxTrain, statyTrain, statwTrain = calObsvStats(runtimeStatsTrain,sizesTrain,statistic,windowSize,statxTrain)
    statxTest, statyTest, statwTest = calObsvStats(runtimeStatsTest,sizesTest,statistic,windowSize,statxTest)

    statxTrain = np.array(statxTrain)
    statxTest = np.array(statxTest)
    #print("After")
    #print(statyTest)

    prepareRuntimesTexTables(logger, sizesTrain, runtimeStatsTrain, sizesTest, runtimeStatsTest, sizeThreshold, windowSize, dirName, specificObsvs, obsvs)
   
    return sizesTrain, runtimesTrain, runtimeStatsTrain, sizesTest, runtimesTest, runtimeStatsTest, sizeThreshold, windowSize, statxTrain, statyTrain, statxTest, statyTest


def calWindowSize(logger,sizesTrain,statxTrain,sizesTest,statxTest,windowSize,minInstances=11):
    #Author; YP
    #Created: 2018-01-21
    #Dynamically chooses the window size to ensure that there are always at least 
    #minInstances instances in each weighted window.

    sizes = [sizesTrain,sizesTest]
    statxs = [statxTrain, statxTest]

    for ind in [0,1]:
        #print('-'*10)
        for cWin in statxs[ind]:
            #If there aren't enough instances in a window, we make it larger.
            weights = [0]
            while(sum(weights) <= minInstances):
                #Get the indices of the data included in this window:
                windex = np.where(np.logical_and(cWin - windowSize/2 <= sizes[ind], sizes[ind] < cWin + windowSize/2))[0] # ;)

                #The middle of the curve is the midle of the window
                mu = cWin

                #capture two standard deviations within the window, everything else is truncated.
                #(Two standard deviations captures 95% of the probability mass)
                sigma = windowSize/4.0
                #sizes[windex[0]] = mu

                #Define the weights using a normal curve
                #weights = (1/(2*math.pi*sigma**2)**0.5)*np.exp(-((sizes[windex]-mu)**2)/(2*sigma**2))
                #Don't normalize the probability distribution, we want instances exactly at the peak of the
                #distribution to have weight 1.
                weights = np.exp(-((sizes[ind][windex]-mu)**2)/(2*sigma**2))
                #print(sum(weights))
                if(sum(weights) <= minInstances):
                    logger.debug("Increasing size...")
                    windowSize*=1.1


    return windowSize


def calObsvStats(runtimes,sizes,statistic,windowSize,obsvs,minInstances=1,delta=1e-4):
    #Author: YP
    #Created: 2018-12-17
    #Last udpated: 2019-01-21
    #Here the window size is defined by the instance size
    #But instead of ignoring the instance sie in the calculation
    #(and hence fitting the best constant function to the data)
    #we are going to instead fit the best linear function to the
    #data.
    #In this case, it likely also makes more sense to use a
    #system of decaying weights for the points to emphasize the
    #Ones in the middle of the interval more heavily.

    #window*=3

    sizes = np.array(sizes)
    runtimes = np.array(runtimes)

    statx = []
    staty = []
    statw = []

    #print('Sizes[0]: ' + str(sizes[0]))
    sizesSet = sorted(list(set(sizes)))
    sizesSet.append(float('inf'))

    sizesSet = np.array(sizesSet)

    done = False
    for cWin in obsvs:
        #Get the indices of the data included in this window:
        windex = np.where(np.logical_and(cWin - windowSize/2 <= sizes, sizes < cWin + windowSize/2))[0] # ;)

        #The middle of the curve is the midle of the window
        mu = cWin

        #capture two standard deviations within the window, everything else is truncated.
        #(Two standard deviations captures 95% of the probability mass)
        sigma = windowSize/4.0
        #sizes[windex[0]] = mu

        #Define the weights using a normal curve
        #weights = (1/(2*math.pi*sigma**2)**0.5)*np.exp(-((sizes[windex]-mu)**2)/(2*sigma**2))
        #Don't normalize the probability distribution, we want instances exactly at the peak of the
        #distribution to have weight 1.
        weights = np.exp(-((sizes[windex]-mu)**2)/(2*sigma**2))
        #print(sum(weights))
        #windowSize*=2

        #We only include windows which contain at least minInstances points.
        #print(sum(weights))
        if(sum(weights) >= minInstances):
            sampleSizes = sizes[windex]
            sampleTimes = runtimes[windex]

            W = np.diag(weights)
            #Fit the model
            X = np.transpose([sampleSizes,np.ones(len(sampleSizes))])
            y = np.transpose(sampleTimes)
            AAinv = np.linalg.pinv(np.linalg.multi_dot([np.transpose(X),W,X]))
            a = np.linalg.multi_dot([AAinv,np.transpose(X),W,y])

            #Calculate the weighted L1Loss
            oldLoss = sum(abs(modelFittingHelper.adjustResiduals(sampleTimes - linearModel(a,sampleSizes), statistic))*weights)

            if(statistic == 'mean'):
                #If we are fitting the mean, then we are already done.
                maxIters = 0
            else:
                #Use up to 100 iterations of the generalized iteratively reweighted linear least squares
                #to perform quantile regression. 
                maxIters = 100
                if(statistic == 'median'):
                    statistic = 'q0.5'

            for i in range(0,maxIters):

                residuals = abs(modelFittingHelper.adjustResiduals(sampleTimes - linearModel(a,sampleSizes),'q' + str(1-float(statistic[1:]))))
                #print(residuals)
                #min residual size to avoid numerical instability
                residuals[np.where(residuals < delta)] = delta
                #Normal IRLLS would just use W = np.diag(1.0/residuals)
                #we further multiple by "runtimes" to provide additional weight
                #to the instances with larger running times.
                #W = np.diag(1.0/residuals)
                W = np.diag(weights/residuals)

                oldA = a

                #Fit the model
                X = np.transpose([sampleSizes,np.ones(len(sampleSizes))])
                y = np.transpose(sampleTimes)
                AAinv = np.linalg.pinv(np.linalg.multi_dot([np.transpose(X),W,X]))
                a = np.linalg.multi_dot([AAinv,np.transpose(X),W,y])

                #Calculate the weighted L1Loss
                newLoss = sum(abs(modelFittingHelper.adjustResiduals(sampleTimes - linearModel(a,sampleSizes), statistic))*weights)

                if(oldLoss-newLoss < delta):
                    if(oldLoss < newLoss):
                        newLoss = oldLoss
                        a = oldA
                    break
                oldLoss = newLoss



            staty.append(a[0]*cWin + a[1])
            #Take the middle of the window?
            statx.append(cWin)
            #Or take the mean of the instances?
            #statx.append(calStatistic(sizes[windex],'mean'))
            statw.append(sum(weights))
            #print('window location: ' + str(statx[-1]) + ', observed statistic: '+ str(staty[-1]))i

    return statx, staty, statw


def linearModel(a,x):
    return a[0]*x + a[1]

