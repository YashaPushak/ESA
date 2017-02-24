import os
import numpy
import math
import random
import summarizeRuntimes
import csvHelper

def doBootstrap(data, numInsts, numSamples, statistic, perInstanceStatistic, numSamplesPerInstance):
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
            print('Nested bootstrap samples for ' + str(size+1) + ' instance sizes made...')
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

            bStat[0][j].append( summarizeRuntimes.calStatistic( bTmpData+[ 0 for i in range(0, size-len(bTmpData)) ], statistic ) )
            bStat[1][j].append( summarizeRuntimes.calStatistic( bTmpData+[ float('inf') for i in range(0, size-len(bTmpData)) ], statistic ) )
        if(i%10 == 9):
            print(str(i+1) + " bootstrap samples made...")
    return bStat

def getBootstrapIntervals(bStat, alpha=95):
    #bStat = doBootstrap(data, numInsts, numSamples, statistic, perInstanceStatistic)
    #los = [ numpy.percentile(d, 50-alpha/2.0) for d in bStat ]
    #ups = [ numpy.percentile(d, 50+alpha/2.0) for d in bStat ]
    los = [ summarizeRuntimes.calStatistic(d, "Q%f"%(50-alpha/2.0)) for d in bStat[0] ]
    ups = [ summarizeRuntimes.calStatistic(d, "Q%f"%(50+alpha/2.0)) for d in bStat[1] ]
    return (los, ups)

def doBootstrapAnalysis(bStat, sizes, data, threshold, statistic, modelNames, modelNumParas, modelFuncs, numSamples, gnuplotPath, alpha=95):
    #bStat = doBootstrap(data, numInsts, numSamples, statistic, perInstanceStatistic)[0]
    print "bStat: %d x %d" % ( len(bStat), len(bStat[0]) )

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
        os.system(gnuplotPath + "gnuplot bootstrap-fit.plt >& /dev/null")
        
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
                raise Exception('Error, gnuplot failed to fit all of the models')
        if i%10 == 9:
            print "%d models fitted to bootstrap samples..." % (i+1)
    for file in files:
        file.close()

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


def getBootstrapTestRMSE(preds, bStat, sizes, threshold, modelNames, alpha=95):
    #Author: Yasha Pushak
    #Last updated: November 16th, 2016
    #Calculates bootstrap confidence intervals for the challenge RMSE.

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
