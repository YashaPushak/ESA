#Author: YP
#Created: 2019-01-03
#Last updated: 2019-01-03

#This file can be used as both a template and an example of how to create
#your own user-defined models. To support a new model, you need to define
#a name as a string, e.g., "my model" (or a set of names, see below), and 
#support that model in each of three functions: fitModelLS, evalModel, 
#and getResiduals.

import numpy as np

def evalModel(x,a,modelName):
    #Author: YP
    #Created: 2019-01-03
    #Evaluates the model named modelName with parameters
    #a on the numpy array of instance sizes x.

    if(modelName.lower() in ['poly','poly.','polynomial']):
        return poly(a,x)
    elif(modelName.lower() in ['exp','exp.','exponential']):
        return exp(a,x)
    elif(modelName.lower() in ['lin','lin.','linear']):
        return linear(a,x)
    elif(modelName.lower() in ['sqrtexp','sqrtexp.','sqrt-exp','rootexp','rootexp.','root-exp','square-root exponential','root exponential']):
        return sqrtexp(a,x)
    elif(modelName.lower() in ['polylog']):
        return polylog(a,x)


def fitModelLS(x,y,modelName,weights=None,a0=None):
    #Author: YP
    #Create: 2019-01-03
    #Fit the specified model to the numpy array data
    #x and y. If weights are specified, you must 
    #perform weight least squares regression.
    #When this function is called iteratively, the
    #previous itereations parameter values will be
    #passed in as a0. However, no default values 
    #are provided for the first iteration. 
    #You can use any least squares regression procedure
    #that you like, and you can even modify the
    #the optimization problem to make it more tractable
    #for your model, as we do for most of ours by fitting
    #the logarithm of the model predictions to the  
    #logarithm of the observations. Since this distorts
    #the error terms, we are heuristically multiplying by
    #the predicted running times from the previous 
    #iteration's fitted model to further weight our 
    #residuals. 

    if(modelName.lower() in ['poly','poly.','polynomial','exp','exp.','exponential','sqrtexp','sqrtexp.','sqrt-exp','rootexp','rootexp.','root-exp','square-root exponential','root exponential','polylog']):
        #If we have no weights, then treat all weights as 1.
        if(weights is None):
            weights = np.ones(len(y))
        #We also use the previous iteration's fitted model
        #to heuristically increase the weights for instances
        #that are predicted to have larger running times. 
        #If we do not have the previous model's parameter values
        #a0, then it is because we are currently performing the
        #first iteration. The first iteration's fit is done using
        #the observed statistics (rather than the fulling running
        #time data set), so we just use them to weight the
        #problem. 
        #We can't use the raw running times to weight the problem
        #because we need all instances of a particular size to 
        #be weighted equally, otherwise the optimization problem
        #becomes biased vertically, instead of just horizontally. 
        if(a0 is None):
            W = np.diag(weights*y)
        else:
            W = np.diag(weights*evalModel(x,a0,modelName))

        if(modelName.lower() in ['poly','poly.','polynomial']):        
            #Note that we have to modify x to obtain X differently
            #depending on what model we have. 
            X = np.transpose([np.log(x),np.ones(len(x))])
            y = np.transpose(np.log(y))
            #Solve the optimization problem in closed form. 
            AAinv = np.linalg.pinv(np.linalg.multi_dot([np.transpose(X),W,X]))
            w = np.linalg.multi_dot([AAinv,np.transpose(X),W,y])
            #we also need to make similar but different reverse 
            #transformations here
            b = w[0]
            a = np.exp(w[1])
        elif(modelName.lower() in ['exp','exp.','exponential']):
            X = np.transpose([np.array(x),np.ones(len(x))])
            y = np.transpose(np.log(y))
            AAinv = np.linalg.pinv(np.linalg.multi_dot([np.transpose(X),W,X]))
            w = np.linalg.multi_dot([AAinv,np.transpose(X),W,y])
            b = np.exp(w[0])
            a = np.exp(w[1]) 
        elif(modelName.lower() in ['sqrtexp','sqrtexp.','sqrt-exp','rootexp','rootexp.','root-exp','square-root exponential','root exponential']):
            X = np.transpose([np.sqrt(x),np.ones(len(x))])
            y = np.transpose(np.log(y))
            AAinv = np.linalg.pinv(np.linalg.multi_dot([np.transpose(X),W,X]))
            w = np.linalg.multi_dot([AAinv,np.transpose(X),W,y])
            b = np.exp(w[0])
            a = np.exp(w[1])
        elif(modelName.lower() in ['polylog']):
            X = np.transpose([np.log(x),np.ones(len(x))])
            y = np.transpose(np.log(y) - np.log(np.log(x)))
            AAinv = np.linalg.pinv(np.linalg.multi_dot([np.transpose(X),W,X]))
            w = np.linalg.multi_dot([AAinv,np.transpose(X),W,y])
            b = w[0]
            a = np.exp(w[1])
        a = [a,b]
    elif(modelName.lower() in ['lin','lin.','linear']):
        if(weights is not None):
            W = np.diag(weights)
        else:
            W = np.diag(np.ones(len(y)))

        X = np.transpose([x,np.ones(len(x))])
        y = np.transpose(y)
        AAinv = np.linalg.pinv(np.linalg.multi_dot([np.transpose(X),W,X]))
        w = np.linalg.multi_dot([AAinv,np.transpose(X),W,y])
        a = w[0]
        b = w[1]
        a = [a,b]

    return a


def getResiduals(x,y,a,modelName):
    #Author: YP
    #Created: 2019-01-03
    #Evaluates the model named modelName with parameters
    #a on the numpy array of instance sizes x and returns
    #the residuals in the form observation - prediction.
    #NOTE: You are allowed to approximate the least 
    #squares regression problem with an easier one (for
    #example by taking the log of the running times and
    #and the model predictions, as we have done). If you
    #do this, then this function must return the residuals
    #of the modified objective function. 
    #NOTE: If you flip the sign of the residuals, it won't
    #change anything for symmetric objective functions, like
    #the mean or median. However, any other quantile will be
    #flipped, e.g., the 95th quantile will become the 5th.

    if(modelName.lower() in ['poly','poly.','polynomial']):
        return np.log(y) - np.log(poly(a,x))
    elif(modelName.lower() in ['exp','exp.','exponential']):
        return np.log(y) - np.log(exp(a,x))
    elif(modelName.lower() in ['lin','lin.','linear']):
        #NOTE: This is the only example we have where we are
        #not modifying the objective function to simplify the
        #regression problem, so we do not modify the residuals
        #here. 
        return y - linear(a,x)
    elif(modelName.lower() in ['sqrtexp','sqrtexp.','sqrt-exp','rootexp','rootexp.','root-exp','square-root exponential','root exponential']):
        return np.log(y) - np.log(sqrtexp(a,x))
    elif(modelName.lower() in ['polylog']):
        return np.log(y) - np.log(polylog(a,x))





def linear(a,x):
    return a[0]*x + a[1]

def poly(a,x):
    return a[0]*x**a[1]

def exp(a,x):
    return a[0]*a[1]**x

def sqrtexp(a,x):
    return a[0]*a[1]**(x**0.5)

def polylog(a,x):
    return a[0]*(x**a[1])*np.log(x)


