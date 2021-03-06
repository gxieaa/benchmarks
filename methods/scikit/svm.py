'''
  @file svm.py
  @author Marcus Edel

  Support vector machines with scikit.
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
from sklearn import svm as ssvm

'''
This class implements the Support vector machines benchmark.
'''
class SVM(object):

  '''
  Create the Support vector machines benchmark instance.

  @param dataset - Input dataset to perform SVM on.
  @param timeout - The time until the timeout. Default no timeout.
  @param verbose - Display informational messages.
  '''
  def __init__(self, dataset, timeout=0, verbose=True):
    self.verbose = verbose
    self.dataset = dataset
    self.timeout = timeout
    self.model = None
    self.kernel = 'rbf'
    self.C = 1.0
    self.gamma = 'auto'
    self.degree = 3
    self.cache_size = 200
    self.max_iter = -1
    self.decision_function_shape = None

  '''
  Build the model for the Support vector machines.

  @param data - The train data.
  @param labels - The labels for the train set.
  @return The created model.
  '''
  def BuildModel(self, data, labels):
    # Create and train the classifier.
    svm = ssvm.SVC(kernel=self.kernel,
                   C=self.C,
                   gamma = self.gamma,
                   degree=self.degree,
                   cache_size = self.cache_size,
                   max_iter = self.max_iter,
                   decision_function_shape = self.decision_function_shape)
    svm.fit(data, labels)
    return svm

  '''
  Use the scikit libary to implement the Support vector machines.

  @param options - Extra options for the method.
  @return - Elapsed time in seconds or a negative value if the method was not
  successful.
  '''
  def SVMScikit(self, options):
    def RunSVMScikit(q):
      totalTimer = Timer()

      Log.Info("Loading dataset", self.verbose)
      trainData, labels = SplitTrainData(self.dataset)
      testData = LoadDataset(self.dataset[1])

      k = re.search("-k (\s+)", options)
      c = re.search("-c (\d+)", options)
      g = re.search("-g (\d+)", options)
      degree = re.search("--degree (\d+)", options)
      cache_size = re.search("--cache_size (\d+)", options)
      max_iter = re.search("--max_iter (\d+)", options)
      decision_function_shape = re.search("--decision_function_shape (\d+)", options)

      self.kernel = 'rbf' if not k else str(k.group(1))
      self.C = 1.0 if not c else float(c.group(1))
      self.gamma = 'auto' if not g else float(g.group(1))
      self.degree = 3 if not degree else int(degree.group(1))
      self.cache_size = 200.0 if not cache_size else float(cache_size.group(1))
      self.max_iter = -1 if not max_iter else int(max_iter.group(1))
      self.decision_function_shape = None if not decision_function_shape else str(decision_function_shape.group(1))

      try:
        with totalTimer:
          self.model = self.BuildModel(trainData, labels)
          # Run Support vector machines on the test dataset.
          self.model.predict(testData)
      except Exception as e:
        Log.Debug(str(e))
        q.put(-1)
        return -1

      time = totalTimer.ElapsedTime()
      q.put(time)

      return time

    return timeout(RunSVMScikit, self.timeout)

  '''
  Perform the Support vector machines. If the method has been
  successfully completed return the elapsed time in seconds.

  @param options - Extra options for the method.
  @return - Elapsed time in seconds or a negative value if the method was not
  successful.
  '''
  def RunMetrics(self, options):
    Log.Info("Perform SVM.", self.verbose)

    results = None
    if len(self.dataset) >= 2:
      results = self.SVMScikit(options)

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

