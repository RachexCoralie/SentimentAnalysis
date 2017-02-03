# -*- coding: utf-8 -*-
"""
Created on Tue Jan 31 16:33:30 2017

@author: elsa
"""

#from __future__ import print_function

import numpy as np
from keras.models import Sequential
from keras.layers import Dense, Merge, BatchNormalization, Embedding, Flatten, Dropout
from keras.optimizers import SGD
from MovieProject.preprocessing import preprocess
from sklearn.cross_validation import StratifiedKFold

def createModel(textLen, genresLen):
    
    text_input_dim = 1000
    text_output_dim = 2
    genres_output_dim = 5
    
    text_branch = Sequential()
    text_branch.add(Embedding(text_input_dim, text_output_dim, input_length=textLen))
    text_branch.add(Flatten())
    
    genres_branch = Sequential()
    genres_branch.add(Dense(genres_output_dim, input_shape = (genresLen,), init='normal', activation='relu'))
    genres_branch.add(BatchNormalization())
    
#    actors_branch = Sequential()
#    actors_branch.add(Dense(10, input_shape =  (3,) , activation = 'relu'))
#    actors_branch.add(BatchNormalization())
    
#    real_branch = Sequential()
#    real_branch.add(Dense(10, input_shape =  (4,) , activation = 'relu'))
#    real_branch.add(BatchNormalization())
    
    #We merge in cascade
    
#    merge1_branch = Sequential()
#    merge1_branch.add(Merge([genres_branch, actors_branch], mode = 'concat'))
#    merge1_branch.add(Dense(1,  activation = 'sigmoid'))
    
#    merge2_branch = Sequential()
#    merge2_branch.add(Merge([real_branch, merge1_branch], mode = 'concat'))
#    merge2_branch.add(Dense(1,  activation = 'sigmoid'))  

    final_branch = Sequential()
    final_branch.add(Merge([text_branch, genres_branch], mode = 'concat'))
    
    #Here are all of our layers, the preprocessing is over
    final_branch.add(Dense(150,  activation = 'relu'))
    final_branch.add(Dropout(0.2))
    final_branch.add(Dense(130,  activation = 'relu'))
    final_branch.add(Dense(110,  activation = 'relu'))
    final_branch.add(Dense(100,  activation = 'relu'))
    final_branch.add(Dense(75,  activation = 'relu'))
    final_branch.add(Dense(50,  activation = 'relu'))
    final_branch.add(Dense(25,  activation = 'relu'))
    final_branch.add(Dense(10, activation='relu'))
    final_branch.add(Dense(3, activation='relu'))
    final_branch.add(Dropout(0.2))
    final_branch.add(Dense(1,  activation = 'sigmoid'))
    
    sgd = SGD(lr = 0.1, momentum = 0.9, decay = 0, nesterov = False)
    final_branch.compile(loss = 'binary_crossentropy', optimizer = sgd, metrics = ['accuracy'])

    return final_branch

def createTrainTestModel(textTrain, genresTrain, labelsTrain, textTest, genresTest, labelsTest):
    """
        Creates, fits and returns the specific model fitting the entries
        
        Parameters : 
            textTrain, genresTrain : the data to train on, the first one only needs embedding, the other one(s) needs dense layer before merge
            labelsTrain : the labels of the data to train
            textTest, genresTest : data to use for the test of the classifier
            labelsTest : the labels of the data to test
            
        return :
            the model is trained with the parameters
            
    """

    #Create the model
    model = createModel(len(textTrain[0]), len(genresTrain[0]))

    epoch = 5000
    batch = 500

    #Train model
    model.fit([textTrain, genresTrain], labelsTrain, batch_size = batch, nb_epoch = epoch, verbose = 1)
#    final_branch.fit([textEntries, genresEntries, actorsEntries, realEntries], classEntries, batch_size = 2000, nb_epoch = 100, verbose = 1)

    # evaluate the model
    scores = model.evaluate([textTest, genresTest],labelsTest, verbose=0)
    print("%s: %.2f%%" % (model.metrics_names[1], scores[1]*100))

    return model, scores


def createTrainModel(textTrain, genresTrain, labelsTrain, textTest, genresTest, labelsTest):
    """
        Creates, fits and returns the specific model fitting the entries
        
        Parameters : 
            textTrain, genresTrain : the data to train on, the first one only needs embedding, the other one(s) needs dense layer before merge
            labelsTrain : the labels of the data to train
            textTest, genresTest : data to use for the test of the classifier
            labelsTest : the labels of the data to test
            
        return :
            the model is trained with the parameters
            
    """

    #Create the model
    model = createModel(len(textTrain[0]), len(genresTrain[0]))

    epoch = 5000
    batch = 500

    #Train model
    model.fit([textTrain, genresTrain], labelsTrain, validation_data=([textTest, genresTest],labelsTest), batch_size = batch, nb_epoch = epoch, verbose = 1)
#    model.fit([textEntries, genresEntries, actorsEntries, realEntries], classEntries, batch_size = 2000, nb_epoch = 100, verbose = 1)

    return model


def buildModel(ids, labels):
    '''
        Builds the model that matches the movies (ids) and the like/dislike
        
        Parameters : 
            ids : the ids of the movies we want to build the model on
            labels : tells whether the movie is liked or not (binary)           
            
        return :
            the model trained on the movies
    '''
    
    T, G = preprocess(ids)

    model = createTrainModel(T, G, labels, T, G, labels)




def buildTestModel(ids, labels):
    '''
        Builds the model that matches the movies (ids) and the like/dislike
        Tests it with k-cross validation
        
        Parameters : 
            ids : the ids of the movies we want to build the model on
            labels : tells whether the movie is liked or not (binary)           
            
        return :
            the model trained on the movies
    '''
    
    T, G = preprocess(ids)
    cvscores = []

    n_folds = 2
    skf = StratifiedKFold(labels, n_folds=n_folds, shuffle=True)

    for i, (train, test) in enumerate(skf):
        print "Running Fold", i+1, "/", n_folds
        print " train, test : ", train, " ", test
        indices = np.array(train)
        tIndice = np.array(test)
        model = None # Clearing the NN.
        model, scores = createTrainTestModel(T[indices], G[indices], labels[indices], T[tIndice], G[tIndice], labels[tIndice])
        cvscores.append(scores[1] * 100)

    print("%.2f%% (+/- %.2f%%)" % (np.mean(cvscores), np.std(cvscores)))
