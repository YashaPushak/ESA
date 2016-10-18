import sys
import os
import math
import csvHelper
import latexHelper

def fillModelRepsWValues( modelRep, valueTuple ):
    while modelRep.find("@@") > -1:
        stIdx = modelRep.find("@@")
        edIdx = modelRep.find("@@", stIdx+2)+2
        if edIdx<2:
            break
        elif edIdx!=stIdx+5:
            print modelRep
            raise Exception
        id = modelRep[stIdx+2]
        modelRep = modelRep[0:stIdx] + valueTuple[ord(id)-ord('a')] + modelRep[edIdx:]
    return modelRep

def genFittedModelsTexTable(algName, modelNames, modelNumParas, modelReps, sizes, threshold, para, seTrains, seTests, texFileName="table_Fitted-models.tex"):
    res = ""
    res += "\\begin{tabular}{ccccc} \n"
    res += "\\hline \n"
    res += " &  & \multirow{2}{*}{Model} & RMSE  & RMSE\\tabularnewline \n"
    res += " &  &  & (support)  & (challenge)\\tabularnewline \n"
    res += "\\hline \n"
    res += "\\hline \n"
    for i in range(0, len(modelNames)):
        if i == 0:
            res += "\\multirow{%d}{*}{%s}" % (len(modelNames), latexHelper.escapeNonAlNumChars( algName ) )
        if seTests[i][0] == min(seTests)[0]:
            modelParasTuple = ()
            for k in range(0, modelNumParas[i]):
                modelParasTuple += ( latexHelper.numToTex(para[i][k], 5), )
            res += latexHelper.prepareTableRow(" & %s. Model" % modelNames[i], \
                [ latexHelper.bold( fillModelRepsWValues( modelReps[i], modelParasTuple ), True ), \
                latexHelper.bold( latexHelper.numToTex(math.sqrt( seTrains[i]/threshold ), 5), True ), \
                latexHelper.bold( latexHelper.numToTex(math.sqrt( seTests[i][0]/(len(sizes)-threshold)), 5), True ) if seTests[i][0]==seTests[i][1] else latexHelper.genInterval( latexHelper.numToTex(math.sqrt( seTests[i][0]/(len(sizes)-threshold)), 5), latexHelper.numToTex(math.sqrt( seTests[i][1]/(len(sizes)-threshold)), 5), 1) ] ) 
        else:
            modelParasTuple = ()
            for k in range(0, modelNumParas[i]):
                modelParasTuple += ( latexHelper.numToTex(para[i][k], 5) ,)
            res += latexHelper.prepareTableRow(" & %s. Model" % modelNames[i], \
                [ "$%s$" % fillModelRepsWValues( modelReps[i], modelParasTuple ), \
                "$%s$" % latexHelper.numToTex( math.sqrt( seTrains[i]/threshold ), 5 ), \
                "$%s$" % latexHelper.numToTex( math.sqrt( seTests[i][0]/(len(sizes)-threshold) ), 5 ) if seTests[i][0]==seTests[i][1] else latexHelper.genInterval( latexHelper.numToTex(math.sqrt( seTests[i][0]/(len(sizes)-threshold)), 5), latexHelper.numToTex(math.sqrt( seTests[i][1]/(len(sizes)-threshold)), 5) ) ] )
        #    " & $6.89157\\times10^{-4}\\text{\\ensuremath{\\times}}1.00798{}^{n}$  & 0.0008564  & 0.7600")
    res += "\\hline \n"
    res += "\end{tabular} \n"
    with open(texFileName, "w") as texFile:
        print >>texFile, res

def fitModels( algName, modelNames, modelNumParas, modelReps, modelFuncs, sizes, medians, medianIntervals, threshold, gnuplotPath, modelFileName ):
    #YP: added some extra exception handling and error checking in case
    #gnuplot is unavailable
    os.system(gnuplotPath + "gnuplot fitModels.plt >& fit.log")
    with open('fit.log') as f_fit:
        if('No such file or directory' in f_fit.read()):
            print('[ERROR]: Unable to run gnuplot.')
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
        print "[ERROR]: Model fitting failed! Please check to make sure gnuplot is installed correctly, or try specifying the directory containing gnuplot configurations.txt using the gnuplotPath variable. (see fit.log for more details about the error message.)"
        sys.exit(1)

    #YP: fixed check to ensure that all of the models were fit correctly and updated the error
    #message to include information about which model failed to fit and how to fix it.
    for k in range(0, len(modelNames)):
        if len(para[k]) == 0:
            print "[ERROR]: Model fitting failed for the " + modelNames[k] + " model!"
            print "[ERROR]: Please try updating the initial values for the " + modelNames[k] + " model parameters in " + modelFileName + "."
            print "[ERROR]: Ideally these values should be within one order of magnitude of their fitted values."
            sys.exit(1)
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
        # if modelNames[k] == "Poly":
        #     for i in range(0, threshold):
        #         seTrains[k] += (po(para[k], sizes[i]) - medians[i])**2 
        #     for i in range(threshold, len(sizes)):
        #         seTests[k] = (po(para[k], sizes[i]) - medians[i])**2 
    csvHelper.genCSV( ".", "table_Fitted-models.csv", ["Model", "RMSE (support)", "RMSE (challenge)"], \
        [ algName+" "+modelName+". Model" for modelName in modelNames ], \
        [ [ para[k], math.sqrt( seTrains[k]/threshold ), [math.sqrt( seTests[k][i]/(len(sizes)-threshold) ) for i in range(0,2)] ] for k in range(0, len(modelNames)) ] )
    genFittedModelsTexTable(algName, modelNames, modelNumParas, modelReps, sizes, threshold, para, seTrains, seTests)

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