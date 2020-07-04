import os
import numpy as np
import math
import random
import summarizeRuntimes
import csvHelper
import latexHelper
import modelFittingHelper
import userDefinitions as ud


def makeBootstrapSamples(runtimes, sizes, numBootstrap, window, perInstanceStatistic, numBootstrapPerInstance):
    #Author: YP 
    #Created: 2019-01-02
    if(window%2 == 0):
       window += 1 #We must have an odd-numbered window so that we can center the window on a point.

    #Start with the original indices for each of the bootstrap samples
    indsMajorOnce = np.array([range(0,len(runtimes))]*numBootstrap)
    #Add a random offset to each index from within the window.
    indsMajorOnce += np.random.randint(-window/2,window/2+1,(numBootstrap,len(runtimes)))
    #Wrap around at the edges.
    indsMajorOnce = np.mod(indsMajorOnce,len(runtimes))
    indsMajorMany = np.array([[[b]*len(runtimes[0]) for b in a] for a in indsMajorOnce])
    #Subsample the independent runs per instance
    indsMinor = np.random.randint(0,len(runtimes[0]),(numBootstrap,len(runtimes),len(runtimes[0])))
    #Create the bootstrap samples
    bruntimes = np.array(runtimes)[(indsMajorMany,indsMinor)]
    #Calculate the per-instance statistics
    bruntimes = np.apply_along_axis(lambda k: summarizeRuntimes.calStatistic(k,perInstanceStatistic),2,bruntimes)
    bsizes = np.array(sizes)[indsMajorOnce]
    
    return bruntimes, bsizes



def calObsIntervals(logger,bruntimes,bsizes,statistic,numBootstrap,windowSize,statxObsvs,alpha):
    statsX = []
    statsY = []
    statsW = []
    for i in range(0,numBootstrap):
        runtimes = bruntimes[i,:]
        sizes = bsizes[i,:]
        statx, staty, statw = summarizeRuntimes.calObsvStats(runtimes,sizes,statistic,windowSize,statxObsvs)
        statsX.append(statx)
        statsY.append(staty)
        statsW.append(statw)
        if(i%10 == 9):
            logger.info('Statistics fitted to ' + str(i+1) + ' bootstrap samples...')

    statBounds = []
    statMedians = []
    statSizes = []
    printed = [False]*11
    printed[0] = True

    completed = 0
    for size in statxObsvs: 
        completed += 1
        lst = []
        for i in range(0,numBootstrap):
            #print(statsX[i])
            #print(size)
            ind = np.argmax(np.array(statsX[i])>=size)
            if(statsX[i][ind] == size):
                lst.append(statsY[i][ind])
            elif(statsX[i][ind] > size):
                if(ind == 0):
                    #Nothing is larger than this value, for now we just add the smallest size
                    lst.append(statsY[i][ind])
                else:
                    #Interpolate between the two nearest data points
                    totalDist = float(statsX[i][ind] - statsX[i][ind-1])
                    partDist = float(size - statsX[i][ind-1])
                    lst.append(statsY[i][ind-1]*(1 - partDist/totalDist) + statsY[i][ind]*(partDist/totalDist))
            else:
                #The above returns 0 if there is nothing larger, in which case we will just take the largest value we have for now.
                lst.append(statsY[i][-1])
        statSizes.append(size)
        statBounds.append([summarizeRuntimes.calStatistic(lst,'q' + str((100-alpha)/2.0)),summarizeRuntimes.calStatistic(lst,'q' + str(100-(100-alpha)/2.0))])

        percentDone = float(completed)/len(statxObsvs)
        printedIndex = min(int(percentDone*10),len(printed)-1)
        if(not printed[printedIndex]):
            logger.info("Intervals calculated for " + str(int(percentDone*100)) + "% of instance sizes...")
            printed[printedIndex] = True


    return statBounds, statsY



def getBootstrapIntervals(bStat, alpha=95):
    #bStat = doBootstrap(data, numInsts, numSamples, statistic, perInstanceStatistic)
    #los = [ numpy.percentile(d, 50-alpha/2.0) for d in bStat ]
    #ups = [ numpy.percentile(d, 50+alpha/2.0) for d in bStat ]
    los = [ summarizeRuntimes.calStatistic(d, "Q%f"%(50-alpha/2.0)) for d in bStat[0] ]
    ups = [ summarizeRuntimes.calStatistic(d, "Q%f"%(50+alpha/2.0)) for d in bStat[1] ]
    return (los, ups)


def fitBootstrapModels(logger, modelNames, statx, bstaty, bsizes, bruntimes, statistic):
    #Author: YP
    #Created; 2019-01-04
    #Fits the models to the bootstrap samples.

    bfittedModels = []
    blosses = []
    for j in range(0,len(modelNames)):
        bfittedModels.append([])
        blosses.append([])

    for i in range(0,len(bstaty)):
        staty = bstaty[i]
        sizes = bsizes[i]
        runtimes = bruntimes[i]

        fittedModels, losses = modelFittingHelper.fitModels(logger, modelNames, statx, staty, sizes, runtimes, statistic)

        if i%10 == 9:
            logger.info("%d models fitted to bootstrap samples..." % (i+1))
 
        for j in range(0,len(modelNames)):
            bfittedModels[j].append(fittedModels[j])
            blosses[j].append(losses[j])

    return bfittedModels, blosses


def makePredictions(logger, bfittedModels, modelNames, statxTrain, statxTest):
    #Author: YP
    #Created: 2019-01-07
    #Calculated the model predictions for the bootstrap models
    #and returns them.

    predsTrain = []
    predsTest = []
    #preds[model number][size number][bootstrap number] = prediction

    for i in range(0,len(modelNames)):
        predsTrain.append([])
        predsTest.append([])
        for x in statxTrain:
            predsTrain[-1].append([])
        for x in statxTest:
            predsTest[-1].append([])
        
        for a in bfittedModels[i]:
            preds = ud.evalModel(statxTrain,a,modelNames[i])
            for j in range(0,len(preds)):
                predsTrain[-1][j].append(preds[j])
            preds = ud.evalModel(statxTest,a,modelNames[i])
            for j in range(0,len(preds)):
                predsTest[-1][j].append(preds[j])

    return predsTrain, predsTest
        

def getLosses(logger, bfittedModels, modelNames, bsizes, bruntimes, statistic):
    #Author: YP
    #Created; 2019-01-04
    #Get the losses for the bootstrap models. 

    #losses[model number][bootstrap number] = loss
    blosses = []

    for i in range(0,len(modelNames)):
        blosses.append([])

        for j in range(0,len(bfittedModels[i])):
            blosses[-1].append(modelFittingHelper.getLoss(bruntimes[i]-ud.evalModel(bsizes[j],bfittedModels[i][j],modelNames[i]),statistic))

    return blosses


def getLoUps( modelNames, data, alpha):
    dataLos = []
    dataUps = []
    
    for k in range(0, len(modelNames)):
        #dataLos.append( [ numpy.percentile(d, 50-alpha/2.0) for d in data[k] ] )
        #dataUps.append( [ numpy.percentile(d, 50+alpha/2.0) for d in data[k] ] )
        dataLos.append( [ summarizeRuntimes.calStatistic(d, 'Q%f'%(50-alpha/2.0)) for d in data[k] ] )
        dataUps.append( [ summarizeRuntimes.calStatistic(d, 'Q%f'%(50+alpha/2.0)) for d in data[k] ] )
    return dataLos, dataUps


def getLossIntervals(logger, blossesTrain, blossesTest, alpha):
    #Author: YP
    #Created: 2019-01-04
    #Calculates intervals for the training and test losses.

    ilossTrain = []
    ilossTest = []

    for i in range(0,len(blossesTrain)):
        lo = summarizeRuntimes.calStatistic(blossesTrain[i],'q' + str(50-alpha/2.0))
        up = summarizeRuntimes.calStatistic(blossesTrain[i],'q' + str(50+alpha/2.0))
        ilossTrain.append([lo,up])
        lo = summarizeRuntimes.calStatistic(blossesTest[i],'q' + str(50-alpha/2.0))
        up = summarizeRuntimes.calStatistic(blossesTest[i],'q' + str(50+alpha/2.0))
        ilossTest.append([lo,up])
        
    return ilossTrain, ilossTest


      

def getResidueBounds(logger, bstaty, bpreds, alpha):
    #Author: YP
    #Created: 2019-01-09
    #updated: 2019-01-09

    residues = []

    bstaty = np.array(bstaty)
    bpreds = np.array(bpreds)

    #print(bstaty)

    for i in range(0,len(bpreds)):
        #print(np.shape(bstaty))
        #print(np.shape(bpreds[i]))
        res = bstaty - np.transpose(bpreds[i]) 
        residues.append(res)
       
    iresidues = []

    for i in range(0,len(residues)):
        los = np.apply_along_axis(lambda k: summarizeRuntimes.calStatistic(k,'q' + str(50 - alpha/2.0)),0,residues[i])
        ups = np.apply_along_axis(lambda k: summarizeRuntimes.calStatistic(k,'q' + str(50 + alpha/2.0)),0,residues[i])

        iresidues.append([los,ups])


    return iresidues    





















 
