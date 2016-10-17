import os
import math
import numpy
import summarizeRuntimes
import modelFittingHelper
import bootstrapHelper
import csvHelper
import gnuplotHelper
import latexHelper

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

def getModels( fileDir, fileName, toModifyModelDefaultParas, sizes, stats, threshold ):
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
                modelNumParas.append( int(terms[1]) )
                modelReps.append( terms[2].strip() )
                modelDefs.append( inputModelToInternal( terms[3].strip(), True ) )
                modelGnuplotDefs.append( inputModelToInternal( terms[4].strip(), False ) )
                modelParaDefaults.append( [] )
                if toModifyModelDefaultParas and modelNames[-1].lower() == "exp" or modelNames[-1].lower() == "exponential":
                    b = ( stats[threshold]/stats[threshold-1] ) ** ( 1.0 / ( sizes[threshold]-sizes[threshold-1] ) )
                    a = stats[threshold]/(b**sizes[threshold])
                    b = 1+(b-1)/2
                    print "Replacing %s model parameters as (%f, %f)" % (modelNames[-1], a, b)
                    modelParaDefaults[-1].append( a )
                    modelParaDefaults[-1].append( b )
                elif toModifyModelDefaultParas and modelNames[-1].lower() == "rootexp" or modelNames[-1].lower() == "root-exponential":
                    b = ( stats[threshold]/stats[threshold-1] ) ** ( 1.0 / ( math.sqrt(sizes[threshold])-math.sqrt(sizes[threshold-1]) ) )
                    a = stats[threshold] / (b**math.sqrt(sizes[threshold]))
                    b = 1+(b-1)/2
                    print "Replacing %s model parameters as (%f, %f)" % (modelNames[-1], a, b)
                    modelParaDefaults[-1].append( a )
                    modelParaDefaults[-1].append( b )
                elif toModifyModelDefaultParas and modelNames[-1].lower() == "poly" or modelNames[-1].lower() == "polynomial":
                    b = ( math.log(stats[threshold]) - math.log(stats[threshold-1]) ) / ( math.log(sizes[threshold]) - math.log(sizes[threshold-1]) )
                    a = stats[threshold] / (sizes[threshold] ** b)
                    b = min(1, b/2)
                    print "Replacing %s model parameters as (%f, %f)" % (modelNames[-1], a, b)
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

def run(fileDir, fileName="runtimes.csv", algName="Algorithm", instName="the problem instances", modelFileName="models.txt", threshold=0, alpha=95, numBootstrapSamples=100, statistic="median", toModifyModelDefaultParas=False, tableDetailsSupportFileName="table_Details-dataset-support", tableDetailsChallengeFileName="table_Details-dataset-challenge", tableFittedModelsFileName="table_Fitted-models", tableBootstrapIntervalsParaFileName="table_Bootstrap-intervals-of-parameters", tableBootstrapIntervalsSupportFileName="table_Bootstrap-intervals_support", tableBootstrapIntervalsChallengeFileName="table_Bootstrap-intervals_challenge", figureCdfsFileName="cdfs", figureFittedModelsFileName="fittedModels", figureFittedResiduesFileName="fittedResidues", latexTemplate = "template-AutoScaling.tex", modelPlotTemplate = "template_plotModels.plt", residuePlotTemplate = "template_plotResidues.plt", gnuplotPath = '', numRunsPerInstance = 0, perInstanceStatistic="median"):
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

    #   prepare template files
    if not os.path.exists( fileDir+"/"+modelFileName ):
        os.system( "cp models.txt %s" % (fileDir+"/"+modelFileName) )
    if not os.path.exists( fileDir+"/"+latexTemplate ):
        os.system( "cp template-AutoScaling.tex %s" % (fileDir+"/"+latexTemplate) )
    if not os.path.exists( fileDir+"/"+modelPlotTemplate ):
        os.system( "cp template_plotModels.plt %s" % (fileDir+"/"+modelPlotTemplate) )
    if not os.path.exists( fileDir+"/"+residuePlotTemplate ):
        os.system( "cp template_plotResidues.plt %s" % (fileDir+"/"+residuePlotTemplate) )
    #   move the pdflatex input file
    if not os.path.exists( fileDir+"/pdflatex_input.txt" ):
        os.system( "cp pdflatex_input.txt " + fileDir +"/pdflatex_input.txt" )    
    #print(numRunsPerInstance)
    #   read in runtimes and summarize
    (sizes, runtimes, numInsts) = summarizeRuntimes.getRuntimesFromFile( fileDir, fileName, numRunsPerInstance )

    cwd = os.getcwd()
    os.chdir( fileDir )
    (counts, stats, statIntervals, threshold) = summarizeRuntimes.summarizeRuntimes( sizes, runtimes, numInsts, algName, ".", statistic, perInstanceStatistic, threshold )
    # stats = [ summarizeRuntimes.calStatistic( runtimes[i], statistic ) for i in range(0, len(sizes)) ]

    #   read in model names and definitions
    (modelNames, modelNumParas, modelOriReps, modelDefs, modelGnuplotDefs, modelParaDefaults, modelFuncs) = getModels( '.', modelFileName, toModifyModelDefaultParas, sizes, stats, threshold )
    modelReps = replaceRepsForOutput( modelOriReps )

    #   prepare gnuplot scripts
    gnuplotHelper.genGnuplotScripts( modelNames, modelGnuplotDefs, modelNumParas, modelParaDefaults, '.', sizes, modelPlotTemplate, residuePlotTemplate )
    

    #YP: Refactored code to only create bootstrap samples once to save time.
    bStat = bootstrapHelper.doBootstrap(runtimes, numInsts, numBootstrapSamples, statistic,     perInstanceStatistic)


    #   calculate confidence intervals of observed data
    (obsvLos, obsvUps) = bootstrapHelper.getBootstrapIntervals( bStat )

    #   fit models
    modelFittingHelper.fitModels( algName, modelNames, modelNumParas, modelReps, modelFuncs, sizes, stats, statIntervals, threshold, gnuplotPath, modelFileName)


    #   calculate bootstrap intervals of fitted models
    (paras, preds) = bootstrapHelper.doBootstrapAnalysis(bStat[0], sizes, runtimes, threshold, statistic, modelNames, modelNumParas, modelFuncs, numBootstrapSamples, gnuplotPath )
    (paraLos, paraUps) = bootstrapHelper.getLoUps( modelNames, paras )
    csvHelper.genCSV( ".", "table_Bootstrap-intervals-of-parameters.csv", [ ("Confidence intervals of p%d" % i) for i in range(0, max(modelNumParas)) ], [ algName+" "+modelName+". model" for modelName in modelNames ], getIntervals(paraLos, paraUps))
    latexHelper.genTexTableBootstrapParas( algName, modelNames, modelNumParas, paraLos, paraUps )

    (predLos, predUps) = bootstrapHelper.getLoUps( modelNames, preds )
    csvHelper.genCSV( ".", "table_Bootstrap-intervals.csv", [algName for i in range(threshold, len(sizes))], ["n"] + [modelName+". model confidence intervals" for modelName in modelNames ] + ["observed point estimates", "observed confidence intervals"], [sizes[threshold:]] + getIntervals([predLos[k][threshold:] for k in range(0, len(modelNames))], [predUps[k][threshold:] for k in range(0, len(modelNames))]) + [stats[threshold:]] + getIntervals([obsvLos[threshold:]], [obsvUps[threshold:]]) )
    latexHelper.genTexTableBootstrap( algName, modelNames, sizes, 0, threshold, predLos, predUps, statIntervals, obsvLos, obsvUps, tableBootstrapIntervalsSupportFileName+".tex" )
    latexHelper.genTexTableBootstrap( algName, modelNames, sizes, threshold, len(sizes), predLos, predUps, statIntervals, obsvLos, obsvUps, tableBootstrapIntervalsChallengeFileName+".tex" )

    #   add above data into gnuplot files
    gnuplotHelper.genGnuplotFiles( fileDir, sizes, stats, statIntervals, obsvLos, obsvUps, predLos, predUps, threshold, statistic )

    #   generate plots
    #YP: Added gnuplotPath
    #YP: Instead of directing output to /dev/null I'm sending it to a log file and checking for the beginning of an error message in the gnuplot file. If there is one, we print a message and save the output file.
    os.system(gnuplotPath + "gnuplot plotModels.plt >& plotModels.log")
    os.system(gnuplotPath + "gnuplot plotResidues.plt >& plotResidues.log")
    logFiles = ['plotModels', 'plotResidues']
    for logFile in logFiles:
        with open(logFile + '.log') as f_log:
            logText = f_log.read()
            if('"' + logFile + '.plt", line' in logText):
                print('[Warning]: There may have been an error in ' + logFile + '.plt. If you encounter any problems, please try running it manually and checking the corresponding gnuplot template file you used. The output was saved in ' + logFile + '.log')
            else: 
                os.system('rm -f ' + logFile + '.log')

    #   generate files
    latexHelper.genTexFile( fileDir, algName, instName, sizes, counts, numInsts, threshold, modelNames, modelOriReps, modelNumParas, numBootstrapSamples, statistic, tableDetailsSupportFileName, tableDetailsChallengeFileName, tableFittedModelsFileName, tableBootstrapIntervalsParaFileName, tableBootstrapIntervalsSupportFileName, tableBootstrapIntervalsChallengeFileName, figureCdfsFileName, figureFittedModelsFileName, figureFittedResiduesFileName, evaluateModels( modelNames, threshold, statIntervals, predLos, predUps ), latexTemplate )
    os.system( "pdflatex 'scaling_%s.tex' >& /dev/null < pdflatex_input.txt" % latexHelper.removeSubstrs( algName, '/' ) )
    os.system( "bibtex 'scaling_%s' >& /dev/null < pdflatex_input.txt" %       latexHelper.removeSubstrs( algName, '/' ) )
    os.system( "pdflatex 'scaling_%s.tex' >& /dev/null < pdflatex_input.txt" % latexHelper.removeSubstrs( algName, '/' ) )
    os.system( "pdflatex 'scaling_%s.tex' >& /dev/null < pdflatex_input.txt" % latexHelper.removeSubstrs( algName, '/' ) )

    #YP: Added a check for the pdf file and error message
    if(not os.path.isfile('scaling_' + algName + '.pdf')):
        print('[Error]: scaling_' + algName + '.pdf was not successfully created. This may be due to a tex complication error. If you are not sure why, please try compiling scaling_' + algName + '.tex manually to check for errors.')

    #   wrap up
    os.chdir( cwd )

