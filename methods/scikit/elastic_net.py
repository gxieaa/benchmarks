'''
  @file elastic_net.py
  @author Marcus Edel

  Elastic Net Classifier with scikit.
'''

import os
import sys
import inspect

# Import the util path, this method even works if the path contains symlinks to
# modules.
cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(
  os.path.split(inspect.getfile(inspect.currentframe()))[0], "../../util")))
if cmd_subfolder not in sys.path:
  sys.path.insert(0, cmd_subfolder)

#Import the metrics definitions path.
metrics_folder = os.path.realpath(os.path.abspath(os.path.join(
  os.path.split(inspect.getfile(inspect.currentframe()))[0], "../metrics")))
if metrics_folder not in sys.path:
  sys.path.insert(0, metrics_folder)

from log import *
from timer import *
from definitions import *
from misc import *

import numpy as np
from sklearn.linear_model import ElasticNet as SElasticNet

'''
This class implements the Elastic Net Classifier benchmark.
'''
class ElasticNet(object):

  '''
  Create the Elastic Net Classifier benchmark instance.

  @param dataset - Input dataset to perform ElasticNet on.
  @param timeout - The time until the timeout. Default no timeout.
  @param verbose - Display informational messages.
  '''
  def __init__(self, dataset, timeout=0, verbose=True):
    self.verbose = verbose
    self.dataset = dataset
    self.timeout = timeout
    self.model = None
    self.rho = 1.0
    self.alpha = 0.5
    self.fit_intercept = True
    self.normalize = False
    self.precompute = False
    self.max_iter = 1000
    self.copy_X = True
    self.tol = 0.0001
    self.warm_start = False
    self.positive = False
    self.selection = 'cyclic'


  '''
  Build the model for the Elastic Net Classifier.

  @param data - The train data.
  @param labels - The labels for the train set.
  @return The created model.
  '''
  def BuildModel(self, data, labels):
    # Create and train the classifier.
    elasticNet = SElasticNet(alpha=self.rho,
                             l1_ratio=self.alpha,
                             fit_intercept = self.fit_intercept,
                             normalize = self.normalize,
                             precompute = self.precompute,
                             max_iter = self.max_iter,
                             copy_X = self.copy_X,
                             tol = self.tol,
                             warm_start = self.warm_start,
                             positive = self.positive,
                             selection = self.selection)
    elasticNet.fit(data, labels)
    return elasticNet

  '''
  Use the scikit libary to implement the Elastic Net Classifier.

  @param options - Extra options for the method.
  @return - Elapsed time in seconds or a negative value if the method was not
  successful.
  '''
  def ElasticNetScikit(self, options):
    def RunElasticNetScikit(q):
      totalTimer = Timer()

      Log.Info("Loading dataset", self.verbose)
      trainData, labels = SplitTrainData(self.dataset)
      testData = LoadDataset(self.dataset[1])

      r = re.search("-r (\d+)", options)
      a = re.search("-a (\d+)", options)
      max_iter = re.search("--max_iter (\d+)", options)
      tol = re.search("--tol (\d+)", options)
      selection = re.search("--selection (\s+)", options)

      self.rho = 1.0 if not r else int(r.group(1))
      self.alpha = 0.5 if not r else int(a.group(1))
      self.max_iter = 1000 if not max_iter else int(max_iter.group(1))
      self.tol = 0.0001 if not tol else float(tol.group(1))
      self.selection = 'cyclic' if not selection else str(selection.group(1))
      if self.selection not in ['cyclic','random']:
          Log.Fatal("Invalid selection: " + str(selection.group(1)) 
                    + ". Must be either cyclic or random")
          q.put(-1)
          return -1

      try:
        with totalTimer:
          self.model = self.BuildModel(trainData, labels)
          # Run Elastic Net Classifier on the test dataset.
          self.model.predict(testData)
      except Exception as e:
        Log.Debug(str(e))
        q.put(-1)
        return -1

      time = totalTimer.ElapsedTime()
      q.put(time)

      return time

    return timeout(RunElasticNetScikit, self.timeout)

  '''
  Perform the Elastic Net Classifier. If the method has been
  successfully completed return the elapsed time in seconds.

  @param options - Extra options for the method.
  @return - Elapsed time in seconds or a negative value if the method was not
  successful.
  '''
  def RunMetrics(self, options):
    Log.Info("Perform Elastic Net.", self.verbose)

    results = None
    if len(self.dataset) >= 2:
      results = self.ElasticNetScikit(options)

      if results < 0:
        return results
    else:
      Log.Fatal("This method requires two datasets.")


    # Datastructure to store the results.
    metrics = {'Runtime' : results}

    if len(self.dataset) >= 3:

      # Check if we need to create a model.
      if not self.model:
        trainData, labels = SplitTrainData(self.dataset)
        self.model = self.BuildModel(trainData, labels)

      testData = LoadDataset(self.dataset[1])
      truelabels = LoadDataset(self.dataset[2])
      predictedlabels = self.model.predict(testData)

      confusionMatrix = Metrics.ConfusionMatrix(truelabels, predictedlabels)
      metrics['ACC'] = Metrics.AverageAccuracy(confusionMatrix)
      metrics['MCC'] = Metrics.MCCMultiClass(confusionMatrix)
      metrics['Precision'] = Metrics.AvgPrecision(confusionMatrix)
      metrics['Recall'] = Metrics.AvgRecall(confusionMatrix)
      metrics['MSE'] = Metrics.SimpleMeanSquaredError(truelabels, predictedlabels)

    return metrics

