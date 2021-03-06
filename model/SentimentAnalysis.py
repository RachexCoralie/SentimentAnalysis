#!/usr/bin/env python2 
# -*- coding: utf-8 -*- 
""" 
Build sentiment analysis model, thanks to Doc2Vec model, train on sentiment tweets.
Allows to analyse opinion about a subject thank's to a pre-trained model.
 
Created on Tue Feb  7 14:09:39 2017 
@author: coralie 
""" 

from __future__ import unicode_literals 
# Library to write utf-8 text file
import codecs

import numpy 

from keras.layers.core import Dense, Dropout, Activation
from keras.layers import LSTM
from keras.models import load_model, Sequential 
 
from ..defaults import Config
from ..utils import GloveDict
from ..utils import OpinionDict
from ..utils import PreprocessTweet
from ..utils import SearchTweets

dicoGlove = GloveDict.loadGloveDicFromFile()
modelPath = Config.SENTIMENT_ANALYSIS_MODEL
batch = 500
minTweetsNb = 10


def preprocessDatasModel(): 
    """
    Preprocesses tweets corpus, in order to build a training and testing data set allowed to
    trains and tests the sentiment analysis neural network
        Return : 
            - a dictionary {label:ndarray}: 
            The label "trainX" is associated with a ndarray of training data.
            The label "trainY" is associated with a ndarray of labels associated with training data.
            The label "testX" is associated with a ndarray of testing data.
            The label "testY" is associated with a ndarray of labels associated with testing data.
    """

    fSourceTrainPos = codecs.open(Config.TRAIN_TWITTER_POS_TR_FILE, 'r', 'utf-8')
    linesTrainPos = fSourceTrainPos.readlines()
    trainDataPosNb = len(linesTrainPos) 
    fSourceTrainNeg = codecs.open(Config.TRAIN_TWITTER_NEG_TR_FILE, 'r', 'utf-8')
    linesTrainNeg = fSourceTrainNeg.readlines()
    trainDataNegNb = len(linesTrainNeg) 
    fSourceTestPos = codecs.open(Config.TEST_TWITTER_POS_TR_FILE, 'r', 'utf-8')
    linesTestPos = fSourceTestPos.readlines()
    testDataPosNb = len(linesTestPos)
    fSourceTestNeg = codecs.open(Config.TEST_TWITTER_NEG_TR_FILE, 'r', 'utf-8')
    linesTestNeg = fSourceTestNeg.readlines()
    testDataNegNb = len(linesTestNeg)
           
    dataSize=len(PreprocessTweet.tweetToVect('size', dicoGlove))
    
    # BUILD TRAINING DATASET --------------------------------------------------
     
    train_arrays = numpy.zeros((trainDataPosNb+trainDataNegNb, dataSize)) 
    train_labels = numpy.zeros(trainDataPosNb+trainDataNegNb) 
    
    # Fills training matrices with positives data and labels 1
    for i,line in enumerate(linesTrainPos):
        if i%100 == 0 : 
            print "Building the positive dataset for training : %d / %d" % (i,trainDataPosNb)
        train_arrays[i] = PreprocessTweet.tweetToVect(line, dicoGlove)
        train_labels[i] = 1 

    # Fills training matrices with negatives data and labels 0
    for i,line in enumerate(linesTrainNeg):
        if i%100 == 0 :
            print "Building  the negative dataset for training : %d / %d" % (i,trainDataNegNb)
        train_arrays[trainDataPosNb + i] = PreprocessTweet.tweetToVect(line, dicoGlove)
        train_labels[trainDataPosNb + i] = 0 

    # Shuffle data 
    shuffle_indices = numpy.random.permutation(numpy.arange(trainDataPosNb+trainDataNegNb)) 
    x_shuffled = train_arrays[shuffle_indices] 
    y_shuffled = train_labels[shuffle_indices] 
    train_arrays = x_shuffled 
    train_labels = y_shuffled 
     
    # BUILD TESTING DATASET ---------------------------------------------------
     
    test_arrays = numpy.zeros((testDataPosNb+testDataNegNb, dataSize)) 
    test_labels = numpy.zeros(testDataPosNb+testDataNegNb) 
    
    # Fills testing matrices with positives data and labels 1
    for i,line in enumerate(linesTestPos):
        if i%100 == 0 :
            print "Building the positive dataset for testing : %d / %d" % (i,testDataPosNb)
        test_arrays[i] = PreprocessTweet.tweetToVect(line, dicoGlove)
        test_labels[i] = 1 

    # Fills testing matrices with negatives data and labels 0
    for i,line in enumerate(linesTestNeg):
        if i%100 == 0 :
            print "Building  the negative dataset for testing : %d / %d" % (i,testDataNegNb)
        test_arrays[testDataPosNb + i] = PreprocessTweet.tweetToVect(line, dicoGlove)
        test_labels[testDataPosNb + i] = 0 
     
    # Shuffle data 
    shuffle_indices = numpy.random.permutation(numpy.arange(testDataPosNb+testDataNegNb)) 
    x_shuffled = test_arrays[shuffle_indices] 
    y_shuffled = test_labels[shuffle_indices] 
    test_arrays = x_shuffled 
    test_labels = y_shuffled 
    
    # RESHAPE DATASET ---------------------------------------------------------
    
    train_arrays = train_arrays.reshape(trainDataPosNb+trainDataNegNb, dataSize) 
    test_arrays = test_arrays.reshape(testDataPosNb+testDataNegNb, dataSize) 
    train_arrays = train_arrays.astype('float32') 
    test_arrays = test_arrays.astype('float32') 
    
    fSourceTrainPos.close()
    fSourceTrainNeg.close()
    fSourceTestPos.close()
    fSourceTestNeg.close()
    
    return {"trainX":train_arrays, "trainY":train_labels, "testX":test_arrays, "testY":test_labels}


    
def reshapeData3D(data):
    """
    Rashape data : 2D -> 3D
        Parameters : 
            - data : ndarray 2D of training data
        Return : 
            - ndarray 3D of training data
    """
    # reshape input to be [samples, time steps, features]
    dataReshape = numpy.reshape(data, (data.shape[0], 1, data.shape[1]))
    
    return dataReshape

    

def LSTMModelRN(trainX ,trainY, testX, testY):
    """
    Build a LSTM + 2 layer fully connected neural network
    > On IMDB : Dense(50), nb_epoch=3, batch_size=32 : Acc:0.86
    > On Twitter : Dense(50), nb_epoch=10, batch_size=32 : Acc:0.72 -> 0.80
        Parameters : 
            - trainX : ndarray of training data
            - trainY : ndarray of labels associated with training data
            - testX : ndarray of testing data
            - testY : ndarray of labels associated with testing data
        Return : 
            - the model trained
    """
    # Reshape data matrices before LSTM layer
    trainX = reshapeData3D(trainX)
    testX = reshapeData3D(testX)
    
    dataSize = trainX.shape[2]
    
    model = Sequential()
    model.add(LSTM(50, input_dim=dataSize))
        
    # We add a vanilla hidden layer:
    model.add(Dense(25))
    model.add(Dropout(0.2))
    model.add(Activation('relu'))
    
    # We project onto a single unit output layer, and squash it with a sigmoid:
    model.add(Dense(1))
    model.add(Activation('sigmoid'))

    #model.compile(loss='mean_squared_error', optimizer='adam')
    model.compile(loss='binary_crossentropy',optimizer='adam', metrics=['accuracy'])
    model.fit(trainX, trainY, nb_epoch=10, batch_size=100, verbose=1, validation_data=(testX, testY))   
    
    return model
    
    
    
def fullyConnectedRN(trainX, trainY) :
    """
    Build a simple 3 layer fully connected neural network
    > On IMDB : Dense(output_dim=50, input_dim=100, init='normal', activation='relu'), Dropout(0.2), Dense(output_dim=10, input_dim=50, init='normal', activation='softmax'), nb_epoch=4, batch_size=32 : Acc:0.86
        Parameters : 
            - trainX : ndarray of training data
            - trainY : ndarray of labels associated with training data
        Return : 
            - the model trained
    """
    model = Sequential() 
    model.add(Dense(output_dim=25, input_dim=50, init='normal', activation='relu'))
    model.add(Dropout(0.2))
    model.add(Dense(output_dim=10, input_dim=25, init='normal', activation='softmax'))
    
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=["accuracy"]) 
    model.fit(trainX, trainY, batch_size=32, nb_epoch=4, verbose=1) 
    
    return model
    
    
    
def evaluateLSTM(model, testX, testY) :
    """ 
    Evaluate model performance
        Parameters :
            - model : the model created by Keras to test
            - testX : ndarray of testing data
            - testY : ndarray of labels associated with testing data
        Return :
            - the model score (loss, accuracy)
            
    """ 
    # Reshape data matrices before LSTM layer
    testX = reshapeData3D(testX)
    
    score = model.evaluate(testX, testY, verbose=0) 
    print('Loss on tests:', score[0]) 
    print('Accuracy on test:', score[1])   
    
    return score
    
    
    
def saveModel(model, filename):
    """
    Save a Keras model into a single HDF5 file which will contain all that we need to re-create this model
        Parameters:
            - model : keras model to store
            - filename : the filename of the HDF5 file (.h5)
    """
    # creates a HDF5 file
    model.save(filename)  
    # deletes the existing model
    del model
 
    
    
def createModel():
    """
    Create model based on LSTM neuronal network
    """
        
    data = preprocessDatasModel()
    trainX = data["trainX"]
    trainY = data["trainY"]
    testX = data["testX"]
    testY = data["testY"]

    # LSTM RN
    model = LSTMModelRN(trainX ,trainY, testX, testY)
    print(model.summary())
    evaluateLSTM(model, testX, testY)
    
    model.save(modelPath)

def sentimentAnalysis(tweet, model, dico): 
    '''
    Predicts the sentiment class of the tweet according to the model
        parameters : 
            - tweet : string of the unpreprocess tweet
            - model : the model used by the prediction
            - dico : dictionnary of opinion words
        returns : 
            - The opinion score on Twitter (between 0 & 1 : the more the score is close to 1, the more the opinion is favorable, the closer the score is to 0, the more the opinion is unfavorable).
            - Returns -1 if the tweet could not be parsed
    '''    
    
    # Tweet preprocessing thank's to glove dictionnary
    tweet = PreprocessTweet.preprocessTweet(tweet,dico)
    
    # Predict opinion classe probability
    if tweet :
        # Infer tweet vector
        tweet = PreprocessTweet.tweetToVect(tweet, dicoGlove)
        # Reshape
        tweet = tweet.reshape(1, tweet.shape[0])
        tweet = tweet.astype('float32')    
        # Reshape if the model is LSTM or Convolutional    
        tweet = tweet.reshape(tweet.shape[0], 1, tweet.shape[1])
        # Return  the opinion classe probability
        return model.predict_proba(tweet, batch_size=batch, verbose=0)
    return  -1
    
def opinionAnalysisOnTwitter(topic):
    """
    Analyzes public opinion on Twitter related to a topic
        parameters :
            - topic : string[] of topic and filters to select the most relevant tweets
        returns :
            - tweetsNb : The tweets number
            - score : The opinion score of these tweets (between 0 & 1 or -1 if we can not find any tweet on the subject. The more the score is close to 1, the more the opinion is favorable, the closer the score is to 0, the more the opinion is unfavorable)
    """
    model = load_model(modelPath)
    dico = OpinionDict.extractOpinionWords()

    samplesAverage = []
    publicOpinion = 0.0
    tweetSelectedNb = 0
    score = -1

    print "> Processing for subject : %s" %(topic)
    tweets = SearchTweets.SearchOnTwitter(topic,'en')

    for i,tweet in enumerate(tweets) :
        score = sentimentAnalysis(tweet, model, dico)
        if score != -1 :
            tweetSelectedNb += 1
            publicOpinion += score
        if tweetSelectedNb == minTweetsNb :
            # Computation of a samples average
            samplesAverage.append(publicOpinion / tweetSelectedNb)
            publicOpinion = 0.0
            tweetSelectedNb = 0

    if samplesAverage :
        score = sum(samplesAverage) / len(samplesAverage)

    return {"tweetsNb": len(tweets), "score": score}    
    
    