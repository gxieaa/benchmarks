'''
  @file LSHForest.py

  Approximate Nearest Neighbors using LSHForest with scikit.
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

from sklearn.neighbors import LSHForest

'''
This class implements the Approximate Nearest Neighbors benchmark.
'''
class ANN(object):

  '''
  Create the Approximate Nearest Neighbors benchmark instance.

  @param dataset - Input dataset to perform ANN on.
  @param timeout - The time until the timeout. Default no timeout.
  @param verbose - Display informational messages.
  '''
  def __init__(self, dataset, timeout=0, verbose=True):
    self.verbose = verbose
    self.dataset = dataset
    self.timeout = timeout
    self.model = None
    self.n_estimators = 10
    self.n_neighbors = 5

  '''
  Build the model for the Approximate Nearest Neighbors.

  @param data - The train data.
  @param labels - The labels for the train set.
  @return The created model.
  '''
  def BuildModel(self, data, labels):
    # Create and train the classifier.
    lshf = LSHForest(n_estimators = self.n_estimators,
                     min_hash_match = self.min_hash_match,
                     n_candidates = self.n_candidates,
                     radius_cutoff_ratio = self.radius_cutoff_ratio,
                     radius = self.radius,
                     n_neighbors = self.n_neighbors)
    lshf.fit(data)
    return lshf

  '''
  Use the scikit libary to implement Approximate Nearest Neighbors.

  @param options - Extra options for the method.
  @return - Elapsed time in seconds or a negative value if the method was not
  successful.
  '''
  def AnnScikit(self, options):
    def RunAnnScikit(q):
      totalTimer = Timer()

      Log.Info("Loading dataset", self.verbose)
      trainData, labels = SplitTrainData(self.dataset)
      testData = LoadDataset(self.dataset[1])
      #Number of trees in the LSH Forest.
      n_estimators = re.search("-n (\d+)", options)
      #Number of neighbors to be returned from the query function.
      n_neighbors = re.search("-k (\d+)", options)
      #Lowest hash length to be searched when candidate selection is performed.
      min_hash_match = re.search("-H (\d+)", options)
      #Minimum number of candidates evaluated per estimator.
      n_candidates = re.search("--n_candidates (\d+)", options)
      #Radius from data point to its neighbors.
      radius = re.search("--radius (\d+)", options)
      #A value ranges from 0 to 1.
      radius_cutoff_ratio = re.search("--radius_cutoff_ratio (\d+)", options)
      self.n_estimators = 10 if not n_estimators else int(n_estimators.group(1))
      self.n_neighbors = 5 if not n_neighbors else int(n_neighbors.group(1))
      self.min_hash_match = 4 if not min_hash_match else int(min_hash_match.group(1))
      self.n_candidates = 10 if not n_candidates else int(n_candidates.group(1))
      self.radius = 1.0 if not radius else float(radius.group(1))
      self.radius_cutoff_ratio = 0.9 if not radius_cutoff_ratio else float(radius_cutoff_ratio.group(1))
      try:
        with totalTimer:
          self.model = self.BuildModel(trainData, labels)
          # Run Approximate on the test dataset.
          distances,indices = self.model.kneighbors(testData,
                                                    n_neighbors = self.n_neighbors)
      except Exception as e:
        Log.Debug(str(e))
        q.put(-1)
        return -1

      time = totalTimer.ElapsedTime()
      q.put(time)

      return time

    return timeout(RunAnnScikit, self.timeout)

  '''
  Perform Approximate Nearest Neighbors. If the method has been successfully
  completed return the elapsed time in seconds.

  @param options - Extra options for the method.
  @return - Elapsed time in seconds or a negative value if the method was not
  successful.
  '''
  def RunMetrics(self, options):
    Log.Info("Perform ANN.", self.verbose)

    results = None
    if len(self.dataset) >= 2:
      results = self.AnnScikit(options)

      if results < 0:
        return results
    else:
      Log.Fatal("This method requires two datasets.")

    # Datastructure to store the results.
    metrics = {'Runtime' : results}
    
    return metrics

