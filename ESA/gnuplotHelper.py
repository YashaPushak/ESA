import os
import numpy as np
import summarizeRuntimes
import copy
import userDefinitions as ud


def addModelNameToP( md, mn ):
    idx = md.find( 'p', 0 )
    while idx>-1:
        if idx+1<len(md) and md[idx+1].isdigit():
            md = md[0:idx] + mn + "_" + md[idx:]
        idx = md.find( 'p', idx+len(mn)+2)
    return md
    
def printModel(modelDef,a):
    #Author: YP
    #Created: 2019-01-08
    for i in range(0,len(a)):
        modelDef = modelDef.replace('p' + str(i),str(a[i]))
    return modelDef


def getModelOrder(fittedModels, modelNames, size):
    #Author: YP
    #Created: 2019-01-09
    #Calculates the order of the models so that the legend
    #can be printed in the correct order.
  
    predictions = []

    for i in range(0,len(modelNames)):
        predictions.append(ud.evalModel(size, fittedModels[i], modelNames[i]))

    order = list(np.argsort(predictions)+1)
    order.reverse()
    return order


def genGnuplotScripts(logger, algName, modelNames, fittedModels, statistic, sizes, sizeThreshold, flattenedRuntimesTrain, flattenedRuntimesTest, modelGnuplotDefs, cutoff, alpha):
    flattenedRuntimesTrain = np.array(flattenedRuntimesTrain)
    flattenedRuntimesTest = np.array(flattenedRuntimesTest)

    subs = {}
    subs['stat'] = statistic
    #subs['cutoff'] = int(cutoff)
    subs['thresholdSize'] = int(sizeThreshold)
    subs['minSize'] = int(min(sizes))
    subs['maxSize'] = int(max(sizes))
    subs['algName'] = algName
    subs['maxTime'] = float(max([max(flattenedRuntimesTrain),max(flattenedRuntimesTest)]))
    subs['minTime'] = float(min([min(flattenedRuntimesTrain),min(flattenedRuntimesTest)]))

    modelOrder = getModelOrder(fittedModels, modelNames, int(max(sizes)))

    #print(modelOrder)

    intervalTemplate = "'@@file@@' using 1:@@low@@:@@up@@ with filledcurves lc @@color@@ notitle,  \\"
    intervalKey = "'' using (0):(0):(0) with filledcurves lc 'grey' title '" + str(alpha) + "% Confidence Interval'"
    modelTemplate = "@@printedModel@@ lc @@color@@ title '@@model@@', \\"
    residueTemplate = "'@@file@@' using 1:@@ind@@ lc @@color@@ smooth unique title '@@model@@', \\"

    colors = ['"blue"','"magenta"','"cyan"', '"orange"', '"purple"', '"yellow"','"red"','"green"','"black"','"brown"',]

    plotModelText = '''plot 'gnuplotTrainFile.txt' using 1:2 pt 1 lc "dark-grey" ps 1 title 'Support Data', \\
'gnuplotTestFile.txt' using 1:2 pt 1 lc "light-grey" ps 1 title 'Challenge Data', \\
'''

    if(subs['maxTime'] >= cutoff):
        plotModelText += "x*0 + " + str(cutoff) + " lw 2 dt 2 lc 'black' title 'Running Time Cutoff', \\\n"

    plotResidueText = '''plot '''


    models = ['Obsv']
    models.extend(modelNames)

    templates = ['plotModels','plotResidues']
    for template in templates:
        with open('template-' + template + '.plt') as f_in:
          with open(template + '.plt','w') as f_out:
            text = f_in.read()
            for key in subs.keys():
                text = text.replace("@@" + key + "@@", str(subs[key]))
            f_out.write(text)

            f_out.write('set output "fitted' + template[4:] + '.pdf"\n')

            if(template == 'plotModels'):
                f_out.write(plotModelText)

                order = [0]
                order.extend(modelOrder)

                for temp in [intervalTemplate, modelTemplate]:
                    for i in order:
                        text = copy.copy(temp)

                        subsCopy = copy.copy(subs)
                        if(models[i].lower() == 'obsv'):
                            subsCopy['model'] = 'Observed ' + statistic.capitalize() + ' Scaling'
                        else:
                            subsCopy['model'] = models[i].capitalize() + ' Model'
                        subsCopy['color'] = colors[i]
                        subsCopy['low'] = str((i+1)*2+1)
                        subsCopy['up'] = str((i+1)*2+2)
                        subsCopy['file'] = 'gnuplotDataFile.txt'
                        if(models[i] == 'Obsv'):
                            subsCopy['printedModel'] = "'gnuplotDataFile.txt' using 1:2 smooth unique"
                        else:
                            subsCopy['printedModel'] = printModel(modelGnuplotDefs[i-1],fittedModels[i-1])

                        for key in subsCopy.keys():
                            text = text.replace("@@" + key + "@@", str(subsCopy[key]))

                        f_out.write(text + '\n')
                f_out.write(intervalKey)

            if(template == 'plotResidues'):
                f_out.write(plotResidueText)

                order = copy.copy(modelOrder)
                order.reverse()

                for temp in [intervalTemplate, residueTemplate]:
                    for i in order:
                        text = copy.copy(temp)

                        subsCopy = copy.copy(subs)
                        subsCopy['model'] = models[i].capitalize()
                        subsCopy['color'] = colors[i]
                        subsCopy['ind'] = str((i-1)*3+2)
                        subsCopy['low'] = str((i-1)*3+3)
                        subsCopy['up'] = str((i-1)*3+4)
                        subsCopy['file'] = 'gnuplotResidueFile.txt'

                        for key in subsCopy.keys():
                            text = text.replace("@@" + key + "@@", str(subsCopy[key]))

                        f_out.write(text + '\n')
                f_out.write(intervalKey)





def genGnuplotFiles(modelNames, statxTrain, statxTest, statyTrain, statyTest, statyTrainBounds, statyTestBounds, predTrainLos, predTrainUps, predTestLos, predTestUps, sizesTrain, flattenedRuntimesTrain, sizesTest, flattenedRuntimesTest, residuesTrain, residuesTest, iresiduesTrain, iresiduesTest):
    #Author: ZM, YP
    #Last updated: 2019-01-08
    with open("gnuplotDataFile.txt", 'w') as gnuplotFile:
        gnuplotFileLine = "#n observed-statistic observed-lower-bound observed-upper-bound "
        for modelName in modelNames:
            gnuplotFileLine += modelName.replace(' ','-') + '-lower-bound ' + modelName.replace(' ','-') + '-upper-bound '
        print >>gnuplotFile, gnuplotFileLine
        for i in range(0, len(statxTrain)):
            gnuplotFileLine = "%d %f %f %f" % (statxTrain[i], statyTrain[i], statyTrainBounds[i][0], statyTrainBounds[i][1])
            for j in range(0, len(predTrainLos)):
                gnuplotFileLine += " %f %f" % (predTrainLos[j][i], predTrainUps[j][i])
            print >>gnuplotFile, gnuplotFileLine
        for i in range(0, len(statxTest)):
            #We put statyTest[i] here three times because in the case of unknown running times (which is no longer supported),
            #we used to have the best guess estimate first, and then the upper and lower bounds second and third respectively.
            gnuplotFileLine = "%d %f %f %f" % (statxTest[i], statyTest[i], statyTestBounds[i][0], statyTestBounds[i][1])
            for j in range(0, len(predTestLos)):
                gnuplotFileLine += " %f %f" % (predTestLos[j][i], predTestUps[j][i])
            print >>gnuplotFile, gnuplotFileLine


    with open("gnuplotTrainFile.txt",'w') as gnuplotFile:
        gnuplotFileLine = "#n running-time"
        print >>gnuplotFile, gnuplotFileLine
        for i in range(0,len(sizesTrain)):
            gnuplotFileLine = "%d %f" % (sizesTrain[i], flattenedRuntimesTrain[i])
            print >>gnuplotFile, gnuplotFileLine

    with open("gnuplotTestFile.txt",'w') as gnuplotFile:
        gnuplotFileLine = "#n running-time"
        print >>gnuplotFile, gnuplotFileLine
        for i in range(0,len(sizesTest)):
            gnuplotFileLine = "%d %f" % (sizesTest[i], flattenedRuntimesTest[i])
            print >>gnuplotFile, gnuplotFileLine

    with open("gnuplotResidueFile.txt",'w') as gnuplotFile:
        gnuplotFileLine = "#n"
        for modelName in modelNames:
            gnuplotFileLine += " " + modelName + "-observed 95%-lower-bound 95%-upper-bound"
        print >>gnuplotFile, gnuplotFileLine
        for i in range(0,len(statxTrain)):
            gnuplotFileLine = str(statxTrain[i])
            for j in range(0,len(modelNames)):
                gnuplotFileLine += " " + str(residuesTrain[j][i])
                gnuplotFileLine += " " + str(iresiduesTrain[j][0][i])
                gnuplotFileLine += " " + str(iresiduesTrain[j][1][i])
            print >>gnuplotFile, gnuplotFileLine
        for i in range(0,len(statxTest)):
            gnuplotFileLine = str(statxTest[i])
            for j in range(0,len(modelNames)):
                gnuplotFileLine += " " + str(residuesTest[j][i])
                gnuplotFileLine += " " + str(iresiduesTest[j][0][i])
                gnuplotFileLine += " " + str(iresiduesTest[j][1][i])
            print >>gnuplotFile, gnuplotFileLine
            



















