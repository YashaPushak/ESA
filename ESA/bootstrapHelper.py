import os
import numpy
import math
import random
import summarizeRuntimes
import csvHelper
import latexHelper

def doBootstrap(logger, data, numInsts, numSamples, statistic, perInstanceStatistic, numSamplesPerInstance):
    #Author: Zongxu Mu, Yasha Pushak
    #Last updated: February 7th, 2017
    #For the bootstrap samples of statistics of nested bootstrap samples
    bStat = [[],[]]
    #For the per-instance statistics of bootstrap samples for each instance
    bData = []
    for j in range(0, len(data)):
        bStat[0].append( [] )
        bStat[1].append( [] )

    if(len(data[0][0]) > 1):
        #Generate the inner bootstrap samples
        for size in range(0, len(data)):
            bData.append([])
            for inst in range(0, len(data[size])):
                bData[size].append([])
                for b in range(0,numSamplesPerInstance):
                    bTmpInstData = []
                    for i in range(0,len(data[size][inst])):
                        p = random.randrange(0,len(data[size][inst]))
                        bTmpInstData.append(data[size][inst][p])
                    bData[size][inst].append(summarizeRuntimes.calStatistic( bTmpInstData, perInstanceStatistic))
            logger.info('Nested bootstrap samples for ' + str(size+1) + ' instance sizes made...')
    else:
        #bootstrap samples will all be degenerate here, so there's no use
        #in making any.
        bData = data


    for i in range(0, numSamples):
        for j in range(0, len(data)):
            bTmpData = []
            size = numInsts[j]  #len(data[j])
            for k in range(0, size):
                p = random.randrange(0, size)
                if p<len(data[j]):
                    #YP: Select one of the nested bootstrap sample statistics.
                    q = random.randrange(0,len(bData[j][p]))
                    bTmpData.append( bData[j][p][q] )

            bStat[0][j].append( summarizeRuntimes.calStatistic( bTmpData+[ 0 for ind in range(0, size-len(bTmpData)) ], statistic ) )
            bStat[1][j].append( summarizeRuntimes.calStatistic( bTmpData+[ float('inf') for ind in range(0, size-len(bTmpData)) ], statistic ) )
        if(i%10 == 9):
            logger.info(str(i+1) + " bootstrap samples made...")
    return bStat

def getBootstrapIntervals(bStat, alpha=95):
    #bStat = doBootstrap(data, numInsts, numSamples, statistic, perInstanceStatistic)
    #los = [ numpy.percentile(d, 50-alpha/2.0) for d in bStat ]
    #ups = [ numpy.percentile(d, 50+alpha/2.0) for d in bStat ]
    los = [ summarizeRuntimes.calStatistic(d, "Q%f"%(50-alpha/2.0)) for d in bStat[0] ]
    ups = [ summarizeRuntimes.calStatistic(d, "Q%f"%(50+alpha/2.0)) for d in bStat[1] ]
    return (los, ups)

def doBootstrapAnalysis(logger, bStat, sizes, data, threshold, statistic, modelNames, modelNumParas, modelFuncs, numSamples, gnuplotPath, alpha=95):
    #bStat = doBootstrap(data, numInsts, numSamples, statistic, perInstanceStatistic)[0]
    logger.debug("bStat size: %d x %d" % ( len(bStat), len(bStat[0]) ))

    warningCount = 0

    owd = os.getcwd()
    os.chdir("bootstrap")
    files = []
    for modelName in modelNames:
        files.append( open(modelName+"-fits.dat", "w") )
    for i in range(0, numSamples):
        runtimes = []
        for j in range(0, len(data)):
            runtimes.append( bStat[j][i] )
        summarizeRuntimes.genGnuplotFiles(".", sizes, runtimes, threshold, statistic)
        os.system(gnuplotPath + "gnuplot bootstrap-fit.plt >& fit.log")
        with open('fit.log') as f_fit:
            fileText = f_fit.read()
            if('No such file or directory' in fileText):
                logger.error('Unable to run gnuplot.')
                logger.error('Please ensure gnuplot is in your path, or verify that you have correctly entered the path in the configuration file using the \'gnuplotPath\' variable.')
                raise Exception("Gnuplot not found")
            elif('After 1 iterations the fit converged' in fileText):
                warningCount += 1
                if(warningCount < 10):
                    failedModel = fileText.split('After 1 iterations the fit converged')[0].split('lambda')[-1].split('_p0')[0].strip()
                    logger.warning('The ' + failedModel + ' model converged after only 1 iteration. This is often a sign that the model is a very bad fit for the data (or that the default fitting parameters you choose were very good).') 
 
        with open("fit-models.log") as fitsFile:
            #YP: added in counting stuff
            count = 0 
            for line in fitsFile:
                count += 1
                terms = line.split(":")
                k = modelNames.index(terms[0].split()[0].strip())
                if terms[0].split()[1].strip() == "fit":
                    print >>files[k], terms[1].strip()
            if(not count == len(modelNames)):
                raise Exception('Error, gnuplot failed to fit all of the models for one of the bootstrap samples.')
        if i%10 == 9:
            logger.info("%d models fitted to bootstrap samples..." % (i+1))
    for file in files:
        file.close()

    if(warningCount > 10):
        logger.warning(str(warningCount - 10) + ' addition warnings about models converging after 1 iteration suppressed.')

    os.chdir(owd)
    return readBootstrapDatFile( modelNames, modelNumParas, modelFuncs, sizes )

def readBootstrapDatFile( modelNames, modelNumParas, modelFuncs, sizes ):                 
    paras = []
    preds = []
    for k in range(0, len(modelNames)):
        paras.append( [] )
        preds.append( [] )
        for j in range(0, modelNumParas[k]):
            paras[k].append( [] )
        for j in range(0, len(sizes)):
            preds[k].append( [] )

    for k in range(0, len(modelNames)):
        modelName = modelNames[k]
        with open("bootstrap/%s-fits.dat" % modelName) as fitsDat:
            for line in fitsDat:
                terms = line.split()
                if len(terms) == 0:
                    continue
                for j in range(0, modelNumParas[k]):
                    paras[k][j].append( float( terms[0+j] ) )
                for j in range(0, len(sizes)):
                    preds[k][j].append( modelFuncs[k]( [ paras[k][i][-1] for i in range(0,modelNumParas[k]) ], sizes[j] ) )

    return paras, preds

def getLoUps( modelNames, data, alpha=95 ):
    dataLos = []
    dataUps = []
    for k in range(0, len(modelNames)):
        #dataLos.append( [ numpy.percentile(d, 50-alpha/2.0) for d in data[k] ] )
        #dataUps.append( [ numpy.percentile(d, 50+alpha/2.0) for d in data[k] ] )
        dataLos.append( [ summarizeRuntimes.calStatistic(d, 'Q%f'%(50-alpha/2.0)) for d in data[k] ] )
        dataUps.append( [ summarizeRuntimes.calStatistic(d, 'Q%f'%(50+alpha/2.0)) for d in data[k] ] )
    return (dataLos, dataUps)



def getBootstrapRMSE(preds, bStat, sizes, threshold, modelNames, alpha=95):
    #Author: Yasha Pushak
    #Last updated: February 24th, 2017
    #Calculates bootstrap confidence intervals for the challenge RMSE by 
    #combining two sources of uncertainty: unknown running times and 
    #bootstrap samples of fitted models and challenge data. 

    #Initialize the squared error for the train and test sizes to zero for 
    #all of the bootstrap models.
    seTests = []
    seTrains = []

    for model in range(0,len(modelNames)):
        seTests.append([])
        seTrains.append([])
        #loop over the bootstrap samples, j
        for j in range(0,len(preds[model][0])):
            #The first position is for the lower bound on the RMSE
            #The second position is for the RMSE of the geometric mean of the point estimate intervals
            #The last position is for the upper bound on the RMSE
            seTests[model].append([0.0, 0.0, 0.0])
            seTrains[model].append([0.0, 0.0, 0.0])

    

    for model in range(0,len(modelNames)):

        #Calculate the squared errors for the support instance sizes
        for size in range(0, threshold):
            #loop over the bootstrap samples, j
            for j in range(0,len(preds[model][size])):
                predValue = preds[model][size][j]

                #calculate a lower bound on the squared error (zero if the prediction is within the inteveral)
                if bStat[0][size][j] > predValue or predValue > bStat[1][size][j]:
                    #rmseTests[k][j][0] += (statIntervals[i][1]-predValue)**2 
                    seTrains[model][j][0] += min( (bStat[0][size][j]-predValue)**2, (bStat[1][size][j]-predValue)**2) 

                #Calculate the squared error for the geometric mean of the interval
                
                geoMean = (bStat[0][size][j]*bStat[1][size][j])**0.5
                #Replace NaN with infinity.
                #if(math.isnan(geoMean)):
                #    geoMean = float('inf')
                seTrains[model][j][1] += (geoMean-predValue)**2

                #calculate an upper bound on the squared error
                seTrains[model][j][2] += max( (bStat[0][size][j]-predValue)**2, (bStat[1][size][j]-predValue)**2 )

        #Calculate the squared errors for the challenge instance sizes
        for size in range(threshold, len(sizes)):
            #loop over the bootstrap samples, j
            for j in range(0,len(preds[model][size])):
                predValue = preds[model][size][j]

                #calculate a lower bound on the squared error (zero if the prediction is within the inteveral)
                if bStat[0][size][j] > predValue or predValue > bStat[1][size][j]:
                    #rmseTests[k][j][0] += (statIntervals[i][1]-predValue)**2 
                    seTests[model][j][0] += min( (bStat[0][size][j]-predValue)**2, (bStat[1][size][j]-predValue)**2) 

                #Calculate the squared error for the geometric mean of the interval
                geoMean = (bStat[0][size][j]*bStat[1][size][j])**0.5
                #replace NaN with infinity. (This occurs when there are too
                #many unknown running times bounded by 0 and inf.)
                #if(math.isnan(geoMean)):
                #    geoMean = float('inf')
                seTests[model][j][1] += (geoMean-predValue)**2
                #if(math.isnan(seTests[model][j][1])):
                #    print(str(geoMean) + ' ' + str(predValue))                

                #calculate an upper bound on the squared error
                seTests[model][j][2] += max( (bStat[0][size][j]-predValue)**2, (bStat[1][size][j]-predValue)**2 )

    medianTrainRMSEGeoMean = []
    meanTrainRMSEGeoMean = []
    medianTestRMSEGeoMean = []
    meanTestRMSEGeoMean = []

    rmseTestBounds = [[-1,-1] for model in range(0,len(modelNames))]
    rmseTrainBounds = [[-1,-1] for model in range(0,len(modelNames))]

    #Divide and take the root to get the RMSE from the SEs.
    for model in range(0,len(modelNames)):
        loTrainRMSE = []
        geoMeanTrainRMSE = []
        upTrainRMSE = []
        loTestRMSE = []
        geoMeanTestRMSE = []
        upTestRMSE = []

        #Calculate the lower and upper bound RMSE for each bootstrap sample.
        #loop over the bootstrap samples, j.
        for j in range(0,len(preds[model][0])):
            #0 is the lower bound, 1 is the geometric mean (see above), 2 is the upper bound.
            loTrainRMSE.append(math.sqrt(seTrains[model][j][0]/(len(sizes) - threshold)))
            geoMeanTrainRMSE.append(math.sqrt(seTrains[model][j][1]/(len(sizes) - threshold)))
            upTrainRMSE.append(math.sqrt(seTrains[model][j][2]/(len(sizes) - threshold)))

            loTestRMSE.append(math.sqrt(seTests[model][j][0]/(len(sizes) - threshold)))
            geoMeanTestRMSE.append(math.sqrt(seTests[model][j][1]/(len(sizes) - threshold)))
            upTestRMSE.append(math.sqrt(seTests[model][j][2]/(len(sizes) - threshold)))
            #rmseTests[model][j][i] = math.sqrt(rmseTests[model][j][i]/(len(sizes) - threshold))

        #get the Q2.5 and Q97.5 for the lower and upper bounds, respectively, to get an interval
        #for the RMSE that combines the two sources of noise
        rmseTrainBounds[model][0] = summarizeRuntimes.calStatistic(loTrainRMSE, 'Q' + str(50-alpha/2.0))
        rmseTrainBounds[model][1] = summarizeRuntimes.calStatistic(upTrainRMSE, 'Q' + str(50+alpha/2.0))
        rmseTestBounds[model][0] = summarizeRuntimes.calStatistic(loTestRMSE, 'Q' + str(50-alpha/2.0))
        rmseTestBounds[model][1] = summarizeRuntimes.calStatistic(upTestRMSE, 'Q' + str(50+alpha/2.0))
        
        #Here, we calculate a statistic to be used to select the model with the best RMSE.
        #We note that we only use the lower bounds because in the event the some running
        #times are unknown, we would otherwise often result in this statistic becoming 'inf'
        #for every model. On the other hand, if all of the running times are known, then
        #the lower bound is equal to the upper bound for each bootstrap sample. This is
        #similar to how Zongxu was original handling this problem.
        medianTrainRMSEGeoMean.append(summarizeRuntimes.calStatistic(geoMeanTrainRMSE,'median'))
        meanTrainRMSEGeoMean.append(summarizeRuntimes.calStatistic(geoMeanTrainRMSE,'mean'))
        medianTestRMSEGeoMean.append(summarizeRuntimes.calStatistic(geoMeanTestRMSE,'median'))
        meanTestRMSEGeoMean.append(summarizeRuntimes.calStatistic(geoMeanTestRMSE,'mean'))


        #print('Train Interval:')
        #print(rmseTrainBounds[model])
        #print('Train Median:')
        #print(medianTrainRMSEGeoMean[model])

        #print('Test Interval:')
        #print(rmseTestBounds[model])
        #print('Test Median:')
        #print(medianTestRMSEGeoMean[model])


    return (rmseTrainBounds, rmseTestBounds, medianTrainRMSEGeoMean, meanTrainRMSEGeoMean, medianTestRMSEGeoMean, meanTestRMSEGeoMean)
    

def makeTableBootstrapModelRMSEs(rmseTrainBounds, rmseTestBounds, medianTrainRMSEGeoMean, meanTrainRMSEGeoMean, medianTestRMSEGeoMean, meanTestRMSEGeoMean, modelNames, algName):
    #Author: Yasha Pushak
    #First Created: March 21st, 2017
    #Last updated: March 21st, 2017
    
    tableName = 'table_Bootstrap-model-RMSE'

    csvHelper.genCSV( ".", tableName + ".csv", ["Model", "Median RMSE (support)", "RMSE Confidence Interval (support)", "median RMSE (challenge)", "RMSE Confidence Interval (challenge)"], \
        [ algName+" "+modelName+". Model" for modelName in modelNames ], \
        [ [medianTrainRMSEGeoMean[k], rmseTrainBounds[k], medianTestRMSEGeoMean[k], rmseTestBounds[k]] for k in range(0, len(modelNames)) ] )

    winnerSelectRule = genBootstrapModelRMSETexTable(algName, modelNames, rmseTrainBounds, rmseTestBounds, medianTrainRMSEGeoMean, meanTrainRMSEGeoMean, medianTestRMSEGeoMean, meanTestRMSEGeoMean, tableName + '.tex')

    return (tableName, winnerSelectRule)


def genBootstrapModelRMSETexTable(algName, modelNames, rmseTrainBounds, rmseTestBounds, medianTrainRMSEGeoMean, meanTrainRMSEGeoMean, medianTestRMSEGeoMean, meanTestRMSEGeoMean, texFileName="table_Bootstrap-model-RMSE.tex"):
    res = ""
    res += "\\begin{tabular}{cc|cc|cc} \n"
    res += "\\hline \n"
    res += " \multirow{2}{*}{Solver} & \multirow{2}{*}{Model} & \multicolumn{2}{c|}{Support RMSE}  & \multicolumn{2}{c}{Challenge RMSE} \\tabularnewline"
    res += " & & Median & Confidence Interval & Median & Confidence Interval \\tabularnewline"
    res += "\\hline \n"
    res += "\\hline \n"

    #Calculate the boldfaced winner
    if(math.isnan(min(medianTestRMSEGeoMean)) or min(medianTestRMSEGeoMean) == float('inf')):
        winners = []
        for i in range(0, len(modelNames)):
            if(rmseTestBounds[i][0] == min(rmseTestBounds)[0]):
                winners.append(i)
        if(min(medianTestRMSEGeoMean) == float('inf')):
            winnerSelectRule = "as per challenge RMSE lower bounds, since the medians are infinity"
        else:
            winnerSelectRule = "as per challenge RMSE lower bounds, since the medians are undefined"
    else:
        winners = []
        for i in range(0,len(modelNames)):
            if(medianTestRMSEGeoMean[i] == min(medianTestRMSEGeoMean)):
                winners.append(i)
        winnerSelectRule = "as per median challenge RMSE"

    for i in range(0, len(modelNames)):
        if i == 0:
            res += "\\multirow{%d}{*}{%s}" % (len(modelNames), latexHelper.escapeNonAlNumChars( algName ) )
        if i in winners:
            #passing 1 to genInterval makes it bold.
            res += latexHelper.prepareTableRow(" & %s." % modelNames[i], \
                [ latexHelper.bold( latexHelper.numToTex(medianTrainRMSEGeoMean[i], 5), True ), \
                latexHelper.genInterval( latexHelper.numToTex(rmseTrainBounds[i][0], 5), latexHelper.numToTex(rmseTrainBounds[i][1], 5), 1), \
                latexHelper.bold( latexHelper.numToTex(medianTestRMSEGeoMean[i], 5), True ), \
                latexHelper.genInterval( latexHelper.numToTex(rmseTestBounds[i][0], 5), latexHelper.numToTex(rmseTestBounds[i][1], 5), 1), \
                ] )
        else:
            res += latexHelper.prepareTableRow(" & %s." % modelNames[i], \
                [ "$%s$" % latexHelper.numToTex( medianTrainRMSEGeoMean[i] , 5 ), \
                "%s" % latexHelper.genInterval( latexHelper.numToTex(rmseTrainBounds[i][0], 5), latexHelper.numToTex(rmseTrainBounds[i][1], 5) ), \
                "$%s$" % latexHelper.numToTex( medianTestRMSEGeoMean[i] , 5 ), \
                "%s" % latexHelper.genInterval( latexHelper.numToTex(rmseTestBounds[i][0], 5), latexHelper.numToTex(rmseTestBounds[i][1], 5) ), \
                ] )
        #    " & $6.89157\\times10^{-4}\\text{\\ensuremath{\\times}}1.00798{}^{n}$  & 0.0008564  & 0.7600")
    res += "\\hline \n"
    res += "\end{tabular} \n"
    with open(texFileName, "w") as texFile:
        print >>texFile, res

    return winnerSelectRule


def getBootstrapTestRMSEExperimental(preds, bStat, sizes, threshold, modelNames, alpha=95):
    #Author: Yasha Pushak
    #Last updated: November 16th, 2016
    #Calculates bootstrap confidence intervals for the challenge RMSE.
    #NOTE (February 24th, 2017): This function contains several experimental
    #methods for boiling down the bounds on the RMSE from two sources of 
    #uncertainty: unknown running times, and bootstrap samples of the fitted
    #models and data. This is something that can be looked into more in the 
    #the future to improve the accuracy of the selected model. However,
    #doing so should probably make use of some extensive empirical experiments
    #to determine what method provides the most accurate results. In lieu of 
    #such a study, I (Yasha) have chosen to use the same method that Zongxu
    #did for handling the uncertaininty due to unknown running times, that is,
    #since he assumes that unkown running times are always bounded by [0,inf),
    #he always picked the model with the smallest lower bound on the RMSE.
    #Since I have modified the code to include the uncertaintiy due to 
    #bootstrap samples of the fitted models and challenge data, I am generalizing
    #his method in the most straightforward way, which is to take the mean of 
    #the lower bounds on the RMSE, a statistic which is guaranteed to always
    #exist. For simplicity, I have extracted the code to do this from my mess
    #of earlier attempts, and put it in the much cleaner function 
    #"getBootstrapTestRMSE"

    #Initialize the squared error for the test sizes to zero for all of the 
    #bootstrap models.
    rmseTests = []

    for k in range(0,len(modelNames)):
        rmseTests.append([])
        for j in range(0,len(preds[k][0])):
            rmseTests[k].append([0.0, 0.0])

           

    for k in range(0,len(modelNames)):
        for i in range(threshold, len(sizes)):
            for j in range(0,len(preds[k][i])):
                predValue = preds[k][i][j]
                #calculate a lower bound on the squared error (zero if the prediction is within the inteveral)
                if bStat[0][i][j] > predValue or predValue > bStat[1][i][j]:
                    #rmseTests[k][j][0] += (statIntervals[i][1]-predValue)**2 
                    rmseTests[k][j][0] += min( (bStat[0][i][j]-predValue)**2, (bStat[1][i][j]-predValue)**2) 
                #calculate an upper bound on the squared error
                rmseTests[k][j][1] += max( (bStat[0][i][j]-predValue)**2, (bStat[1][i][j]-predValue)**2 )

    #Divide and take the root to get the RMSE from the SEs.
    for k in range(0,len(modelNames)):
        for j in range(0,len(preds[k][0])):
            for i in [0,1]:
                rmseTests[k][j][i] = math.sqrt(rmseTests[k][j][i]/(len(sizes) - threshold))
    #Count how many times each model has the best expected RMSE
    counts = [0]*len(modelNames)
    avgRMSE = [0]*len(modelNames)
    avgRMSEList = [[] for k in range(len(modelNames))]
    for j in range(0,len(preds[0][0])):
        best = [float('inf')]*3
        argBest = []
        for k in range(0,len(modelNames)):
            #Get the expected value of the RMSE assuming a uniform
            #distribution over the bootstrap confidence interval
            #print(rmseTests)
            #print(k)
            #print(j)
            #print(rmseTests[k][j])
            RMSE = [sum(rmseTests[k][j])/2.0, rmseTests[k][j][0], rmseTests[k][j][1]]
            avgRMSE[k] += RMSE[0]
            avgRMSEList[k].append(RMSE[0])
            if(RMSE[0] < best[0]):
                best = RMSE
                argBest = [k]
            elif(best[0] == float('inf') and RMSE[0] == float('inf')):
                if(RMSE[1] < best[1]):
                    #If both of the upper bounds are inf, check which one has
                    #a smaller lower bound, and use that to break ties.
                    best = RMSE
                    argBest = [k]
                elif(RMSE[1] == best[1]):
                    #Rather than breaking ties at random, add a vote for
                    #both
                    argBest.append(k)
            elif(RMSE[0] == best[0]):
                #Rather than breaking ties uniformly at random, we simply 
                #add a vote for all tied models.
                argBest.append(k)
        for vote in argBest:
            counts[vote] += 1
    #Find which model had the most votes.
    best = -1
    argBest = []
    stats = []
    for k in range(0,len(counts)):
        #Calculate the average RMSE.
        avgRMSE[k] = avgRMSE[k]/len(rmseTests[k])
        #calculate some statistics of the average RMSEs.
        stats.append([])
        stats[k].append(summarizeRuntimes.calStatistic(avgRMSEList[k],'Q10'))
        stats[k].append(summarizeRuntimes.calStatistic(avgRMSEList[k],'Q25'))
        stats[k].append(summarizeRuntimes.calStatistic(avgRMSEList[k],'Q50'))
        stats[k].append(summarizeRuntimes.calStatistic(avgRMSEList[k],'Q75'))
        stats[k].append(summarizeRuntimes.calStatistic(avgRMSEList[k],'Q90'))
        
        if(counts[k] > best):
            best = counts[k]
            argBest = [k]
        elif(counts[k] == best):
            argBest.append(k)
     
    #break ties uniformly at random.
    winner = argBest[random.randrange(0,len(argBest))]
    print('Model Names, votes, average RMSE, RMSE bounds, Expected RMSE')
    headers = ['votes', 'average RMSE', 'RMSE bounds', 'Expected RMSE', 'average RMSE [Q10, Q25, Q50, Q75, Q90]']

    allStats = []
    for i in range(0,len(modelNames)):
        allStats.append([])

    rmseTestBounds = [[-1,-1] for i in range(0,len(modelNames))]
    expected = [-1]*len(modelNames)
    for k in range(0,len(counts)):
        loRMSE = []
        upRMSE = []
        for j in range(0,len(rmseTests[k])):
            loRMSE.append(rmseTests[k][j][0])
            upRMSE.append(rmseTests[k][j][1])
        rmseTestBounds[k][0] = summarizeRuntimes.calStatistic(loRMSE, 'Q' + str(50-alpha/2.0))
        rmseTestBounds[k][1] = summarizeRuntimes.calStatistic(upRMSE, 'Q' + str(50+alpha/2.0))
        expected[k] = sum(rmseTestBounds[k])/2

        print(modelNames[k] + ', ' + str(counts[k]) + ', ' + \
            str(avgRMSE[k]) + ', [' + str(rmseTestBounds[k][0]) + ', ' + \
            str(rmseTestBounds[k][1]) + '], ' + str(expected[k]))

        allStats[k].append(counts[k])
        allStats[k].append(avgRMSE[k])
        allStats[k].append('[' + str(rmseTestBounds[k][0]))
        allStats[k].append(str(rmseTestBounds[k][1]) + ']')
        allStats[k].append(expected[k])
        allStats[k].append('[' + str(stats[k][0]))
        allStats[k].append(stats[k][1])
        allStats[k].append(stats[k][2])
        allStats[k].append(stats[k][3])
        allStats[k].append(str(stats[k][4]) + ']')


        #print(rmseTestBounds)0
    print('Model name, average RMSE [Q10, Q25, Q50, Q75, Q90]')
    for k in range(0, len(counts)):
        print(modelNames[k] + ', [' + \
            str(stats[k][0]) + ', ' + str(stats[k][1]) + ', ' + \
            str(stats[k][2]) + ', ' + str(stats[k][3]) + ', ' + \
            str(stats[k][4]) + ']')
   
    csvHelper.genCSV(".","table_Challenge-RMSE.csv", headers, modelNames, allStats)


 
    medianMeanRMSE = []
    for i in range(0,len(avgRMSE)):
        medianMeanRMSE.append(stats[i][2])
    
    #Get the winner using the minimum median mean RMSE if possible
    if(min(medianMeanRMSE) < float('inf')):
        bestRMSE = float('inf')
        winner = []
        for k in range(0,len(counts)):
            if(medianMeanRMSE[k] < bestRMSE):
                winner = [k]
                bestRMSE = medianMeanRMSE[k]
            elif(medianMeanRMSE[k] == bestRMSE):
                winner.append(k)
    
    #break ties uniformly at random.

    #Get the winner using the expected RMSE if possible
    #if(min(expected) < float('inf')):
    #    bestRMSE = float('inf')
    #    winner = []
    #    for k in range(0,len(counts)):
    #        if(expected[k] < bestRMSE):
    #            winner = [k]
    #            bestRMSE = expected[k]
    #        elif(expected[k] == bestRMSE):
    #            winner.append(k)
 
    #Break ties uniformly at random
    winner = winner[random.randrange(0,len(winner))]
    
    #print(['Winner stats:'] + modelNames)
    #print([modelNames[winner]] + medianMeanRMSE)
    csvHelper.genCSV('.',"table_winners.csv", ['Winner stats:'] + modelNames ,['Winner'],[[modelNames[winner]] + medianMeanRMSE])
    #print([modelNames[winner]] + medianMeanRMSE)

    print('The winner is: ' + modelNames[winner])

    return (rmseTestBounds, medianMeanRMSE) 


def getRelativeRMSEsAndIntervals(testRMSE,stats,obsvLos,obsvUps,predLos,predUps,threshold,sizes,modelNames):
    #Author: Yasha Pushak
    #First Created: July 6th, 2017
    #Some additional experimental analysis to compare the size of the RMSE
    #relative to the mean challenge running time and to compare the size
    #Of the predicted and observed bootstrap intervals relative to the
    #challenge running times.

    meanStat = sum(stats[threshold:])/(len(stats[threshold:]))
    
    intervalSize = []
    meanIntervalSize = []

    
    for k in range(0,len(predLos)):
        intervalSize.append([])
        #print(modelNames[k])
        for s in range(0,len(sizes)):
            #print(str(sizes[s]) + ': ' + str(predUps[k][s]) + ' - ' + str(predLos[k][s]))
            intervalSize[k].append((predUps[k][s] - predLos[k][s])/stats[s])
        meanIntervalSize.append(sum(intervalSize[k][threshold:])/len(intervalSize[k][threshold:]))

    obsvIntSize = []
    for s in range(0,len(sizes)):
        obsvIntSize.append((obsvUps[s] - obsvLos[s])/stats[s])

    with open('table_RMSEs-and-intervals.csv','w') as f_out:
        f_out.write('#The median RMSE is across bootstrap samples. Here we are using the medianTestRMSEGeoMean. The mean observed statistic is the mean of the observed points estimates for the running times.\n')
        f_out.write('#, [median RMSE]/[mean observed statistic], mean relative interval size')
        for s in range(threshold,len(sizes)):
            f_out.write(', relative interval size n=' + str(sizes[s]))
        f_out.write('\n')
        for k in range(0,len(predLos)):
            f_out.write(modelNames[k] + ', ' + str(testRMSE[k]/meanStat) + ', ' + str(meanIntervalSize[k]))
            for s in range(threshold,len(sizes)):
                f_out.write(', ' + str(intervalSize[k][s]))
            f_out.write('\n')
        
        f_out.write('Observed data, 0, ' + str(sum(obsvIntSize[threshold:])/len(obsvIntSize[threshold:])))
        for s in range(threshold,len(sizes)):
            f_out.write(', ' + str(obsvIntSize[s]))
        f_out.write('\n')
        
