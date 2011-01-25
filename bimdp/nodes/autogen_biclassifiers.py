"""
AUTOMATICALLY GENERATED CODE, DO NOT MODIFY!

Edit and run autogen.py instead to overwrite this module.
"""

import mdp.nodes
from bimdp import BiClassifier

class SignumBiClassifier(BiClassifier, mdp.nodes.SignumClassifier):
    """Automatically created BiClassifier version of SignumClassifier."""
    def __init__(self, input_dim=None, output_dim=None, dtype=None, node_id=None, stop_result=None):
        """If the input dimension and the output dimension are
        unspecified, they will be set when the 'train' or 'execute'
        method is called for the first time.
        If dtype is unspecified, it will be inherited from the data
        it receives at the first call of 'train' or 'execute'.

        Every subclass must take care of up- or down-casting the internal
        structures to match this argument (use _refcast private
        method when possible).
        """
        super(SignumBiClassifier, self).__init__(input_dim=input_dim, output_dim=output_dim, dtype=dtype, node_id=node_id, stop_result=stop_result)

class PerceptronBiClassifier(BiClassifier, mdp.nodes.PerceptronClassifier):
    """Automatically created BiClassifier version of PerceptronClassifier."""
    def __init__(self, input_dim=None, dtype=None, node_id=None, stop_result=None):
        super(PerceptronBiClassifier, self).__init__(input_dim=input_dim, dtype=dtype, node_id=node_id, stop_result=stop_result)

class SimpleMarkovBiClassifier(BiClassifier, mdp.nodes.SimpleMarkovClassifier):
    """Automatically created BiClassifier version of SimpleMarkovClassifier."""
    def __init__(self, input_dim=None, dtype=None, node_id=None, stop_result=None):
        super(SimpleMarkovBiClassifier, self).__init__(input_dim=input_dim, dtype=dtype, node_id=node_id, stop_result=stop_result)

class DiscreteHopfieldBiClassifier(BiClassifier, mdp.nodes.DiscreteHopfieldClassifier):
    """Automatically created BiClassifier version of DiscreteHopfieldClassifier."""
    def __init__(self, input_dim=None, node_id=None, stop_result=None):
        super(DiscreteHopfieldBiClassifier, self).__init__(input_dim=input_dim, node_id=node_id, stop_result=stop_result)

class KMeansBiClassifier(BiClassifier, mdp.nodes.KMeansClassifier):
    """Automatically created BiClassifier version of KMeansClassifier."""
    def __init__(self, num_clusters, max_iter=10000, input_dim=None, dtype=None, node_id=None, stop_result=None):
        """Employs K-Means Clustering for a given number of centroids.
        
        num_clusters -- number of centroids to use = number of clusters
        max_iter     -- if the algorithm does not reach convergence (for some
                        numerical reason), stop after max_iter iterations
        """
        super(KMeansBiClassifier, self).__init__(num_clusters=num_clusters, max_iter=max_iter, input_dim=input_dim, dtype=dtype, node_id=node_id, stop_result=stop_result)
