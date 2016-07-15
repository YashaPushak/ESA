import math
import numpy
import os
import sys
import csvHelper
import latexHelper

def calStatistic( list, statistic ):
    if statistic == "mean":
        return numpy.mean( list )
    if statistic[0] == "q" or statistic[0] == "Q":
        percent = float( statistic[1:] )
        if percent<1:
            percent *= 100
#       return numpy.percentile( list, percent )
        return sorted(list)[ int(len(list)*percent/100)-1 ]
#   return numpy.median( list )
    return sorted(list)[ (len(list))/2-1 ]

def calStatisticIntervals( list, statistic, numInsts ):
    if statistic == "mean" or len(list) == numInsts:
        return [ calStatistic( list, statistic ) for i in range(0,2) ]
    else:
        return [ calStatistic( list+[ 0 for i in range(0, numInsts-len(list)) ], statistic ), calStatistic( list+[ float('inf') for i in range(0, numInsts-len(list)) ], statistic ) ]

def getRuntimesFromFile(dirName, filename):
    sizes = []
    runtimes = []
    numInsts = []
    sizeRuntimes = {}
    sizeNumInsts = {}
    header = True
    with open(dirName+"/"+filename, 'r') as runtimesFile:
        for line in runtimesFile:
            if line.strip()[0] == '#':
                if line.strip()[1:10] == 'instances':#YP: I suspect that this entire if statement (and the following one I marked) are not used in practice, but where originally intended for debugging purposes...
                    terms = line.split(",")
                    sizeNumInsts[ int(terms[1]) ] = int(terms[2])
                continue
            terms = line.split(",")
            #YP: added float() before int() for terms[1] in three spots that follow
            if int(float(terms[1])) not in sizeRuntimes:
                sizeRuntimes[ int(float(terms[1])) ] = []
            try:
                runtime = float(terms[2])
            except:
                runtime = float('inf')
            if runtime < 0:
                runtime = float('inf')
            sizeRuntimes[ int(float(terms[1])) ].append( runtime )
    for size in sorted( sizeRuntimes ):
        sizes.append(size)
        runtimes.append( sizeRuntimes[size] )
        numInsts.append( len( sizeRuntimes[size] ) )
        if size in sizeNumInsts.keys():#YP: See comment above.
            numInsts[-1] = sizeNumInsts[size]
#            if header == True:
#                terms = line.split(",")
#                for term in terms:
#                    sizes.append( int(term) )
#                    runtimes.append( [] )
#                header = False
#            else:
#                stIdx = 0
#                terms = line.split(",")
#                if len(terms) == len(sizes)+1:
#                    stIdx = 1
#                for i in range(stIdx, len(terms)):
#                    if terms[i].strip() == "":
#                        continue
#                    runtimes[ i-stIdx ].append( float(terms[i]) )
    return (sizes, runtimes, numInsts)

def prepareRuntimesTexTable(st, ed, sizes, counts, numInsts, means, coeffVars, q10s, q25s, medians, q75s, q90s):
    res = ""
    res += "\\begin{tabular}{c|" + "c"*len(sizes[st:ed]) + "} \n"
    res += "\\hline \n"
    res += latexHelper.prepareTableRow("$n$", sizes[st:ed])
    res += "\\hline \n"
    res += latexHelper.prepareTableRow("\\# instances", numInsts[st:ed])
    res += latexHelper.prepareTableRow("\\# running times", counts[st:ed])
    res += latexHelper.prepareTableRow("mean", [ ("$%s$" % latexHelper.numToTex(means[i], 4) if counts[i]==numInsts[i] else "N/A" ) for i in range(st,ed) ] )
    res += latexHelper.prepareTableRow("coefficient of variation", [ ("$%s$" % latexHelper.numToTex(coeffVars[i], 4) if counts[i]==numInsts[i] else "N/A" ) for i in range(st,ed) ] )
    res += latexHelper.prepareTableRow("Q(0.1)",  [ ( "$%s$" % latexHelper.numToTex(v[0],4) if v[0]==v[1] else latexHelper.genInterval(latexHelper.numToTex(v[0], 3), latexHelper.numToTex(v[1], 4) ) ) for v in q10s[st:ed] ])
    res += latexHelper.prepareTableRow("Q(0.25)", [ ( "$%s$" % latexHelper.numToTex(v[0],4) if v[0]==v[1] else latexHelper.genInterval(latexHelper.numToTex(v[0], 3), latexHelper.numToTex(v[1], 4) ) ) for v in q25s[st:ed] ])
    res += latexHelper.prepareTableRow("median",  [ ( "$%s$" % latexHelper.numToTex(v[0],4) if v[0]==v[1] else latexHelper.genInterval(latexHelper.numToTex(v[0], 3), latexHelper.numToTex(v[1], 4) ) ) for v in medians[st: ed]])
    res += latexHelper.prepareTableRow("Q(0.75)", [ ( "$%s$" % latexHelper.numToTex(v[0],4) if v[0]==v[1] else latexHelper.genInterval(latexHelper.numToTex(v[0], 3), latexHelper.numToTex(v[1], 4) ) ) for v in q75s[st:ed] ])
    res += latexHelper.prepareTableRow("Q(0.9)",  [ ( "$%s$" % latexHelper.numToTex(v[0],4) if v[0]==v[1] else latexHelper.genInterval(latexHelper.numToTex(v[0], 3), latexHelper.numToTex(v[1], 4) ) ) for v in q90s[st:ed] ])
    res += "\\hline \n"
    res += "\\end{tabular} \n"
    res += "\\medskip{} \n"
    return res

def prepareRuntimesTexTables(sizes, runtimes, numInsts, threshold, dirName, supportTexFileName="table_Details-dataset-support.tex", challengeTexFileName="table_Details-dataset-challenge.tex"):
    counts = []
    means = []
    coeffVars = []
    q10s = []
    q25s = []
    medians = []
    q75s = []
    q90s = []
    for i in range(0, len(sizes)):
        counts.append( len(runtimes[i]) )
        means.append( calStatistic(runtimes[i], "mean") )
        coeffVars.append( numpy.std(runtimes[i])/means[i] )
        medians.append( calStatisticIntervals( runtimes[i], "median", numInsts[i] ) )
        q10s.append(    calStatisticIntervals( runtimes[i], "q10"   , numInsts[i] ) )
        q25s.append(    calStatisticIntervals( runtimes[i], "q25"   , numInsts[i] ) )
        q75s.append(    calStatisticIntervals( runtimes[i], "q75"   , numInsts[i] ) )
        q90s.append(    calStatisticIntervals( runtimes[i], "q90"   , numInsts[i] ) )
    csvHelper.genCSV(".", "table_Details-dataset.csv", sizes, ["# instances", "# running times", "mean", "coefficient of variation", "Q(0.1)", "Q(0.25)", "median", "Q(0.75)", "Q(0.9)"], [numInsts, counts, means, coeffVars, q10s, q25s, medians, q75s, q90s])

    maxColsPerTable = 4
    with open(dirName+"/"+supportTexFileName, "w") as texFile:
        numTables = (threshold+maxColsPerTable-1)/maxColsPerTable
        numCols = (threshold+numTables-1)/numTables
        for i in range(0, numTables):
            print >>texFile, prepareRuntimesTexTable(i*numCols, min((i+1)*numCols, threshold), sizes, counts, numInsts, means, coeffVars, q10s, q25s, medians, q75s, q90s)
    with open(dirName+"/"+challengeTexFileName, "w") as texFile:
        numTables = (len(sizes)-threshold+maxColsPerTable-1)/maxColsPerTable
        numCols = (len(sizes)-threshold+numTables-1)/numTables
        for i in range(0, numTables):
            print >>texFile, prepareRuntimesTexTable(threshold+i*numCols, min(threshold+(i+1)*numCols, len(sizes)), sizes, counts, numInsts, means, coeffVars, q10s, q25s, medians, q75s, q90s)
    return counts
    
def genGnuplotFiles(dirName, sizes, stats, threshold, statistic):
    dirName = "."
    with open(dirName+"/gnuplotTrainFile.txt", 'w') as gnuplotFile: 
        for i in range(0, threshold):
            print >>gnuplotFile, "%d %f" % (sizes[i], stats[i])
    with open(dirName+"/gnuplotTestFile.txt", 'w') as gnuplotFile: 
        for i in range(threshold, len(sizes)):
            print >>gnuplotFile, "%d %f" % (sizes[i], stats[i])

def summarizeRuntimes(sizes, runtimes, numInsts, algName, dirName, statistic, threshold=0):
    #YP: Removed what I believe were old debugging messages.
    #print len(runtimes)
    #print len(runtimes[0])
    if threshold<=0 or threshold>=len(sizes):
        threshold = (3*len(sizes)+2)/5
    counts = prepareRuntimesTexTables( sizes, runtimes, numInsts, threshold, dirName )
    stats = [ calStatistic( runtimes[i], statistic ) for i in range(0, len(sizes)) ]
    statIntervals = [ calStatisticIntervals( runtimes[i], statistic, numInsts[i] ) for i in range(0, len(sizes)) ]
    genGnuplotFiles( dirName, sizes, stats, threshold, statistic )
    return (counts, stats, statIntervals, threshold)

