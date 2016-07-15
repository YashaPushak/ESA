import os
import numpy
import random
import summarizeRuntimes

def doBootstrap(data, numInsts, numSamples, statistic):
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
                    bTmpData.append( data[j][p] )
            bStat[0][j].append( summarizeRuntimes.calStatistic( bTmpData+[ 0 for i in range(0, size-len(bTmpData)) ], statistic ) )
            bStat[1][j].append( summarizeRuntimes.calStatistic( bTmpData+[ float('inf') for i in range(0, size-len(bTmpData)) ], statistic ) )
    return bStat

def getBootstrapIntervals(data, numInsts, numSamples, statistic, alpha=95):
    bStat = doBootstrap(data, numInsts, numSamples, statistic)
    #los = [ numpy.percentile(d, 50-alpha/2.0) for d in bStat ]
    #ups = [ numpy.percentile(d, 50+alpha/2.0) for d in bStat ]
    los = [ summarizeRuntimes.calStatistic(d, "Q%f"%(50-alpha/2.0)) for d in bStat[0] ]
    ups = [ summarizeRuntimes.calStatistic(d, "Q%f"%(50+alpha/2.0)) for d in bStat[1] ]
    return (los, ups)

def doBootstrapAnalysis(sizes, data, numInsts, threshold, statistic, modelNames, modelNumParas, modelFuncs, numSamples, gnuplotPath, alpha=95):
    bStat = doBootstrap(data, numInsts, numSamples, statistic)[0]
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
        os.system(gnuplotPath + "/gnuplot bootstrap-fit.plt >& /dev/null")
        
        with open("fit-models.log") as fitsFile:
            for line in fitsFile:
                terms = line.split(":")
                k = modelNames.index(terms[0].split()[0].strip())
                if terms[0].split()[1].strip() == "fit":
                    print >>files[k], terms[1].strip()
        if i%10 == 9:
            print "%d bootstrap done..." % (i+1)
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
