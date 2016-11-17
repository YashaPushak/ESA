import os
import numpy
import math
import random
import summarizeRuntimes

def doBootstrap(data, numInsts, numSamples, statistic, perInstanceStatistic):
    bStat = [[],[]]
    for j in range(0, len(data)):
        bStat[0].append( [] )
        bStat[1].append( [] )

    for i in range(0, numSamples):
        for j in range(0, len(data)):
            bTmpData = []
            size = numInsts[j]  #len(data[j])
            for k in range(0, size):
                p = random.randrange(0, size)
                if p<len(data[j]):
                    #YP: Added additional bootstrap step here
                    bTmpInstData = []
                    for l in range(0,len(data[j][p])):
                        q = random.randrange(0, len(data[j][p]))
                        bTmpInstData.append(data[j][p][q])
                    
                    bTmpData.append( summarizeRuntimes.calStatistic( bTmpInstData, perInstanceStatistic) )
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
            for line in fitsFile:
                terms = line.split(":")
                k = modelNames.index(terms[0].split()[0].strip())
                if terms[0].split()[1].strip() == "fit":
                    print >>files[k], terms[1].strip()
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
    for j in range(0,len(preds[0][0])):
        best = [float('inf')]*3
        argBest = []
        for k in range(0,len(modelNames)):
            #Get the expected value of the RMSE assuming a uniform
            #distribution over the bootstrap confidence interval
            RMSE = [sum(rmseTests[k][j])/2.0, rmseTests[k][j][0], rmseTests[k][j][1]]
            avgRMSE[k] += RMSE[0]
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
    for k in range(0,len(counts)):
        #Calculate the average RMSE.
        avgRMSE[k] = avgRMSE[k]/len(rmseTests[k])
        if(counts[k] > best):
            best = counts[k]
            argBest = [k]
        elif(counts[k] == best):
            argBest.append(k)
     
    #break ties uniformly at random.
    winner = argBest[random.randrange(0,len(argBest))]
    print('Model name, votes, average RMSE, RMSE bounds, Expected RMSE')

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
        print(modelNames[k] + ', ' + str(counts[k]) + ', ' + str(avgRMSE[k]) + ', [' + str(rmseTestBounds[k][0]) + ', ' + str(rmseTestBounds[k][1]) + '], ' + str(expected[k]))
        #print(rmseTestBounds)
    #Get the winner using the minimum RMSE if possible
    #if(min(avgRMSE) < float('inf')):
    #    bestRMSE = float('inf')
    #    winner = []
    #    for k in range(0,len(counts)):
    #        if(avgRMSE[k] < bestRMSE):
    #            winner = [k]
    #            bestRMSE = avgRMSE[k]
    #        elif(avgRMSE[k] == bestRMSE):
    #            winner.append(k)
    #break ties uniformly at random.

    #Get the winner using the expected RMSE if possible
    if(min(expected) < float('inf')):
        bestRMSE = float('inf')
        winner = []
        for k in range(0,len(counts)):
            if(expected[k] < bestRMSE):
                winner = [k]
                bestRMSE = expected[k]
            elif(expected[k] == bestRMSE):
                winner.append(k)
 
    #Break ties uniformly at random
    winner = winner[random.randrange(0,len(winner))]

    print('The winner is: ' + modelNames[winner])

    return (rmseTestBounds, expected) 
