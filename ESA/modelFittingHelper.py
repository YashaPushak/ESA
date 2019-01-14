import sys
import os
import math
import csvHelper
import latexHelper
import numpy as np
import userDefinitions as ud


def adjustResiduals(r,statistic):
    if(statistic == 'mean'):
        return r**2
    else:
        if(statistic == 'median'):
            quantile = 0.5
        else:
            if('q' == statistic[0].lower()):
                statistic = statistic[1:]
            quantile = float(statistic)
        return np.where(r<0,r*(quantile)*2,r*(1-quantile)*2)
  

def getLoss(residuals,statistic):
    return sum(abs(adjustResiduals(residuals,statistic)))


def getLosses(logger, fittedModels, modelNames, sizes, runtimes, statistic):
    #Author: YP
    #Created: 2019-01-04
    #returns the losses for each model.

    losses = []

    for i in range(0,len(modelNames)):
        losses.append(getLoss(ud.evalModel(sizes,fittedModels[i],modelNames[i])-runtimes,statistic))

    return losses


def getResidues(logger, statx, staty, fittedModels, modelNames):
    #Author: YP
    #Created; 2019-01-08
    #Calculates the residues of the fitted models
    #from the fitted observations 

    staty = np.array(staty)

    residues = []

    for i in range(0,len(modelNames)):
        residues.append(staty - ud.evalModel(statx,fittedModels[i],modelNames[i]))

    return residues


def fitModelIRLS(logger, modelName, statx, staty, sizes, runtimes, statistic, delta=1e-4):
    #Author: YP
    #Created: 2018-11-14
    #last udpated: 2019-01-04
    #A new method that uses iteratively reweighted linear least squares to fit
    #the models to the log of the running times (or any other user-defined approximatation to
    #the optimization problem). We further modify the weights by
    #Mutliplying them by the running times so that longer running times are heuristically
    #weighted more (since we are downweighting them when we take their log to make the
    #Problem more tractable).

    sizes = np.array(sizes)
    runtimes = np.array(runtimes)

    a = ud.fitModelLS(statx,staty,modelName)
    newLoss = getLoss(ud.evalModel(sizes,a,modelName)-runtimes,statistic)
    oldLoss = newLoss

    #Use up to 100 iterations of the generalized iteratively reweighted linear least squares
    #to perform quantile regression.
    #We still use an iterated aproach even for fitting the mean, because we are performing a
    #weighted optimization procedure where the weights are defined by the previous iteration's
    #fitted model, so we need to allow the method to converge for the mean as well. 
    #IF the user is using a custom deisgned optimization procedure that is not iterative, then 
    #we are approximately doubling the running time of ESA here, because it will run twice, and assuming
    #It is a good procedure it should return losses within delta almost immediately, and hence it
    #should "converege" very quickly.
    maxIters = 100
    if(statistic == 'median'):
        statistic = 'q0.5'

    for i in range(0,maxIters):
        if(not statistic == 'mean'):
            #logger.debug("Original residuals: " + str(ud.getResiduals(sizes,runtimes,a,modelName)[0:10]))
            #We take one minus the quantile because we are dividing by the residuals when we turn them into weights. 
            residuals = abs(adjustResiduals(ud.getResiduals(sizes,runtimes,a,modelName),'q' + str(1-float(statistic[1:]))))
            #logger.debug("Adjusted residuals: " + str(residuals[0:10]))
            #min residual size to avoid numerical instability
            residuals[np.where(residuals < delta)] = delta
            #Normal IRLLS would just use W = np.diag(1.0/residuals)
            #we further multiple by "runtimes" to provide additional weight
            #to the instances with larger running times.
            W = 1.0/residuals
        else:
            #We don't need to use a 
            W = np.ones(len(sizes))
        
        oldA = a
        a = ud.fitModelLS(sizes,runtimes,modelName,W,oldA)
        newLoss = getLoss(ud.evalModel(sizes,a,modelName) - runtimes,statistic)

        if(oldLoss-newLoss < delta):
            if(oldLoss < newLoss):
                #The objective function loss can start to get worse, since we're only
                #approximately the true objective function with an easier one here.
                #If that happens, we can just stop early and use the best-known
                #solution.
                newLoss = oldLoss
                a = oldA
            break
        oldLoss = newLoss

    a = np.array(a)

    return a, newLoss



def fitModels(logger, modelNames, statx, staty, sizes, runtimes, statistic):
    #Author: YP
    #Created: 2019-01-04
    #Last updated: 2019-01-04

    fittedModels = []
    losses = []

    for modelName in modelNames:   
        a, loss = fitModelIRLS(logger, modelName, statx, staty, sizes, runtimes, statistic)
        fittedModels.append(a)
        losses.append(loss)

    #logger.debug("Fitted Models: " + str(fittedModels))

    return fittedModels, losses




def unused():
    para = []
    for k in range(0, len(modelNames)):
        para.append( [] )
    try:
        with open("fit-models.log", "r") as fitsFile:
            for line in fitsFile:
                terms = line.split(":")
                k = modelNames.index(terms[0].split()[0].strip())
                if terms[0].split()[1].strip() == "fit":
                    values = terms[1].split()
                    para[k] = [ float(v) for v in values ]
    except Exception:
        logger.error("Model fitting failed! Please check to make sure gnuplot is installed correctly, or try specifying the directory containing gnuplot configurations.txt using the gnuplotPath variable. (see fit.log for more details about the error message.)")
        system.exit(-1)

    #YP: fixed check to ensure that all of the models were fit correctly and updated the error
    #message to include information about which model failed to fit and how to fix it.
    for k in range(0, len(modelNames)):
        if len(para[k]) == 0:
            logger.error("Model fitting failed for the " + modelNames[k] + " model!")
            logger.error("This is often due to poor default fitting parameters; however, you can find more information in 'fit.log'.")
            logger.error("Please try updating the initial values for the " + modelNames[k] + " model parameters in " + modelFileName + ".")
            logger.error("Ideally these values should be within one order of magnitude of their fitted values.")
            sys.exit(-1)
    seTrains = []
    seTests = []
    for k in range(0, len(modelNames)):
        seTrains.append( 0.0 )
        seTests.append( [0.0, 0.0] )
        for i in range(0, threshold):
            seTrains[k] += (modelFuncs[k](para[k], sizes[i]) - medians[i])**2 
        for i in range(threshold, len(sizes)):
            predValue = modelFuncs[k](para[k], sizes[i])
            if medianIntervals[i][0] > predValue or predValue > medianIntervals[i][1]:
                seTests[k][0] += min( (medianIntervals[i][0]-predValue)**2, (medianIntervals[i][1]-predValue)**2 )
            seTests[k][1] += max( (medianIntervals[i][0]-predValue)**2, (medianIntervals[i][1]-predValue)**2 )

    with open("./residueTrainFile.txt", 'w') as gnuplotFile:
        for i in range(0, threshold):
            gnuplotFileLine = "%d" % sizes[i]
            for k in range(0, len(modelNames)):
                gnuplotFileLine += " %f" % (medians[i] - modelFuncs[k](para[k], sizes[i]))
            print >>gnuplotFile, gnuplotFileLine
    with open("./residueTestFile.txt", 'w') as gnuplotFile:
        for i in range(threshold, len(sizes)):
            gnuplotFileLine = "%d" % sizes[i]
            for k in range(0, len(modelNames)):
                gnuplotFileLine += " %f" % (medians[i] - modelFuncs[k](para[k], sizes[i]))
            print >>gnuplotFile, gnuplotFileLine
    os.system( 'cat residueTrainFile.txt residueTestFile.txt >residueFile.txt' )

    #Convert the squared errors to root mean squared errors.
    for i in range(0,2):
        seTrains[k] = math.sqrt( seTrains[k]/threshold )
        for k in range(0,len(modelNames)):
            seTests[k][i] = math.sqrt( seTests[k][i]/(len(sizes)-threshold))

    #YP: The original function did not return these values, but instead
    #calculated the table_Fitted-models.* files and the residue* files
    #here. I am returning this instead, and creating this files in new
    #functions so that I can replace some of the data with statistics
    #from the bootstrap models.
    return (para, seTrains, seTests)


