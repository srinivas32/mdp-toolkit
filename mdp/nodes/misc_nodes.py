import mdp
from mdp import numx, numx_linalg, utils, Node, ClassifierNode, NodeException

import cPickle as pickle
import pickle as real_pickle

MAX_NUM = {numx.dtype('b'): 127,
           numx.dtype('h'): 32767,
           numx.dtype('i'): 2147483647,
           numx.dtype('q'): 9223372036854775807L,
           numx.dtype('f'): numx.finfo(numx.float32).max,
           numx.dtype('d'): numx.finfo(numx.float64).max}

MIN_NUM = {numx.dtype('b'): -128,
           numx.dtype('h'): -32768,
           numx.dtype('i'): -2147483648,
           numx.dtype('q'): -9223372036854775808L,
           numx.dtype('f'): numx.finfo(numx.float32).min,
           numx.dtype('d'): numx.finfo(numx.float64).min}


class IdentityNode(Node):
    """Return input data (useful in complex network layouts)"""

    @staticmethod
    def is_trainable():
        False

    def _get_supported_dtypes(self):
        """Return the list of dtypes supported by this node."""
        return (mdp.utils.get_dtypes('AllFloat') +
                mdp.utils.get_dtypes('AllInteger') +
                mdp.utils.get_dtypes('Complex'))

    def _set_input_dim(self, n):
        self._input_dim = n
        self._output_dim = n

    def _set_output_dim(self, n):
        if (self._input_dim is not None) and (self._input_dim != n):
            err = "output_dim must be equal to input_dim for indentity nodes"
            raise NodeException(err)
        self._input_dim = n
        self._output_dim = n


class OneDimensionalHitParade(object):
    """
    Class to produce hit-parades (i.e., a list of the largest
    and smallest values) out of a one-dimensional time-series.
    """
    def __init__(self, n, d, real_dtype="d", integer_dtype="l"):
        """
        Input arguments:
        n -- Number of maxima and minima to remember
        d -- Minimum gap between two hits

        real_dtype -- dtype of sequence items
        integer_dtype -- dtype of sequence indices
        Note: be careful with dtypes!
        """
        self.n = int(n)
        self.d = int(d)
        self.iM = numx.zeros((n, ), dtype=integer_dtype)
        self.im = numx.zeros((n, ), dtype=integer_dtype)
        real_dtype = numx.dtype(real_dtype)
        self.M = numx.array([MIN_NUM[real_dtype]]*n, dtype=real_dtype)
        self.m = numx.array([MAX_NUM[real_dtype]]*n, dtype=real_dtype)
        self.lM = 0
        self.lm = 0

    def update(self, inp):
        """
        Input arguments:
        inp -- tuple (time-series, time-indices)
        """
        (x, ix) = inp
        rows = len(x)
        d = self.d
        M = self.M
        m = self.m
        iM = self.iM
        im = self.im
        lM = self.lM
        lm = self.lm
        for i in xrange(rows):
            k1 = M.argmin()
            k2 = m.argmax()
            if x[i] > M[k1]:
                if ix[i]-iM[lM] <= d and x[i] > M[lM]:
                    M[lM] = x[i]
                    iM[lM] = ix[i]
                elif ix[i]-iM[lM] > d:
                    M[k1] = x[i]
                    iM[k1] = ix[i]
                    lM = k1
            if x[i] < m[k2]:
                if ix[i]-im[lm] <= d and x[i] < m[lm]:
                    m[lm] = x[i]
                    im[lm] = ix[i]
                elif ix[i]-im[lm] > d:
                    m[k2] = x[i]
                    im[k2] = ix[i]
                    lm = k2
        self.M = M
        self.m = m
        self.iM = iM
        self.im = im
        self.lM = lM
        self.lm = lm

    def get_maxima(self):
        """
        Return the tuple (maxima, time-indices).
        Maxima are sorted in descending order.
        """
        iM = self.iM
        M = self.M
        sort = M.argsort()
        return M[sort[::-1]], iM[sort[::-1]]

    def get_minima(self):
        """
        Return the tuple (minima, time-indices).
        Minima are sorted in ascending order.
        """
        im = self.im
        m = self.m
        sort = m.argsort()
        return m[sort], im[sort]


class HitParadeNode(Node):
    """Collect the first 'n' local maxima and minima of the training signal
    which are separated by a minimum gap 'd'.

    This is an analysis node, i.e. the data is analyzed during training
    and the results are stored internally. Use the
    'get_maxima' and 'get_minima' methods to access them.
    """

    def __init__(self, n, d=1, input_dim=None, dtype=None):
        """
        Input arguments:
        n -- Number of maxima and minima to store
        d -- Minimum gap between two maxima or two minima
        """
        super(HitParadeNode, self).__init__(input_dim, None, dtype)
        self.n = int(n)
        self.d = int(d)
        self.itype = 'int64'
        self.hit = None
        self.tlen = 0

    def _set_input_dim(self, n):
        self._input_dim = n
        self.output_dim = n

    def _get_supported_dtypes(self):
        """Return the list of dtypes supported by this node."""
        return ['b', 'h', 'i', 'q', 'f', 'd']

    def _train(self, x):
        hit = self.hit
        old_tlen = self.tlen
        if hit is None:
            hit = [OneDimensionalHitParade(self.n, self.d, self.dtype,
                                           self.itype)
                   for c in range(self.input_dim)]
        tlen = old_tlen + x.shape[0]
        indices = numx.arange(old_tlen, tlen)
        for c in range(self.input_dim):
            hit[c].update((x[:, c], indices))
        self.hit = hit
        self.tlen = tlen

    def get_maxima(self):
        """
        Return the tuple (maxima, indices).
        Maxima are sorted in descending order.

        If the training phase has not been completed yet, call
        stop_training.
        """
        self._if_training_stop_training()
        cols = self.input_dim
        n = self.n
        hit = self.hit
        iM = numx.zeros((n, cols), dtype=self.itype)
        M = numx.ones((n, cols), dtype=self.dtype)
        for c in range(cols):
            M[:, c], iM[:, c] = hit[c].get_maxima()
        return M, iM

    def get_minima(self):
        """
        Return the tuple (minima, indices).
        Minima are sorted in ascending order.

        If the training phase has not been completed yet, call
        stop_training.
        """
        self._if_training_stop_training()
        cols = self.input_dim
        n = self.n
        hit = self.hit
        im = numx.zeros((n, cols), dtype=self.itype)
        m = numx.ones((n, cols), dtype=self.dtype)
        for c in range(cols):
            m[:, c], im[:, c] = hit[c].get_minima()
        return m, im

class TimeFramesNode(Node):
    """Copy delayed version of the input signal on the space dimensions.

    For example, for time_frames=3 and gap=2:

    [ X(1) Y(1)        [ X(1) Y(1) X(3) Y(3) X(5) Y(5)
      X(2) Y(2)          X(2) Y(2) X(4) Y(4) X(6) Y(6)
      X(3) Y(3)   -->    X(3) Y(3) X(5) Y(5) X(7) Y(7)
      X(4) Y(4)          X(4) Y(4) X(6) Y(6) X(8) Y(8)
      X(5) Y(5)          ...  ...  ...  ...  ...  ... ]
      X(6) Y(6)
      X(7) Y(7)
      X(8) Y(8)
      ...  ...  ]

    It is not always possible to invert this transformation (the
    transformation is not surjective. However, the 'pseudo_inverse'
    method does the correct thing when it is indeed possible.
    """

    def __init__(self, time_frames, gap=1, input_dim=None, dtype=None):
        """
        Input arguments:
        time_frames -- Number of delayed copies
        gap -- Time delay between the copies
        """
        self.time_frames = time_frames
        super(TimeFramesNode, self).__init__(input_dim, None, dtype)
        self.gap = gap

    def _get_supported_dtypes(self):
        """Return the list of dtypes supported by this node."""
        return ['int8', 'int16', 'int32', 'int64', 'float32', 'float64']

    @staticmethod
    def is_trainable():
        return False

    @staticmethod
    def is_invertible():
        return False

    def _set_input_dim(self, n):
        self._input_dim = n
        self._output_dim = n*self.time_frames

    def _set_output_dim(self, n):
        msg = 'Output dim can not be explicitly set!'
        raise NodeException(msg)

    def _execute(self, x):
        gap = self.gap
        tf = x.shape[0] - (self.time_frames-1)*gap
        rows = self.input_dim
        cols = self.output_dim
        y = numx.zeros((tf, cols), dtype=self.dtype)
        for frame in range(self.time_frames):
            y[:, frame*rows:(frame+1)*rows] = x[gap*frame:gap*frame+tf, :]
        return y

    def pseudo_inverse(self, y):
        """This function returns a pseudo-inverse of the execute frame.
        y == execute(x) only if y belongs to the domain of execute and
        has been computed with a sufficently large x.
        If gap > 1 some of the last rows will be filled with zeros.
        """

        self._if_training_stop_training()

        # set the output dimension if necessary
        if not self.output_dim:
            # if the input_dim is not defined, raise an exception
            if not self.input_dim:
                errstr = ("Number of input dimensions undefined. Inversion"
                          "not possible.")
                raise NodeException(errstr)
            self.outputdim = self.input_dim

        # control the dimension of y
        self._check_output(y)
        # cast
        y = self._refcast(y)

        gap = self.gap
        exp_length = y.shape[0]
        cols = self.input_dim
        rest = (self.time_frames-1)*gap
        rows = exp_length + rest
        x = numx.zeros((rows, cols), dtype=self.dtype)
        x[:exp_length, :] = y[:, :cols]
        count = 1
        # Note that if gap > 1 some of the last rows will be filled with zeros!
        block_sz = min(gap, exp_length)
        for row in range(max(exp_length, gap), rows, gap):
            x[row:row+block_sz, :] = y[-block_sz:, count*cols:(count+1)*cols]
            count += 1
        return x


class EtaComputerNode(Node):
    """Compute the eta values of the normalized training data.

    The delta value of a signal is a measure of its temporal
    variation, and is defined as the mean of the derivative squared,
    i.e. delta(x) = mean(dx/dt(t)^2).  delta(x) is zero if
    x is a constant signal, and increases if the temporal variation
    of the signal is bigger.

    The eta value is a more intuitive measure of temporal variation,
    defined as
       eta(x) = T/(2*pi) * sqrt(delta(x))
    If x is a signal of length T which consists of a sine function
    that accomplishes exactly N oscillations, then eta(x)=N.

    EtaComputerNode normalizes the training data to have unit
    variance, such that it is possible to compare the temporal
    variation of two signals independently from their scaling.

    Reference: Wiskott, L. and Sejnowski, T.J. (2002).
    Slow Feature Analysis: Unsupervised Learning of Invariances,
    Neural Computation, 14(4):715-770.

    Important: if a data chunk is tlen data points long, this node is
    going to consider only the first tlen-1 points together with their
    derivatives. This means in particular that the variance of the
    signal is not computed on all data points. This behavior is
    compatible with that of SFANode.

    This is an analysis node, i.e. the data is analyzed during training
    and the results are stored internally.  Use the functions
    'get_eta' to access them.
    """

    def __init__(self, input_dim=None, dtype=None):
        super(EtaComputerNode, self).__init__(input_dim, None, dtype)
        self._initialized = 0

    def _set_input_dim(self, n):
        self._input_dim = n
        self.output_dim = n

    def _get_supported_dtypes(self):
        """Return the list of dtypes supported by this node."""
        return ['float32', 'float64']

    def _init_internals(self):
        input_dim = self.input_dim
        self._mean = numx.zeros((input_dim,), dtype='d')
        self._var = numx.zeros((input_dim,), dtype='d')
        self._tlen = 0
        self._diff2 = numx.zeros((input_dim,), dtype='d')
        self._initialized = 1

    def _train(self, data):
        # here SignalNode.train makes an automatic refcast
        if not self._initialized:
            self._init_internals()

        rdata = data[:-1]
        self._mean += rdata.sum(axis=0)
        self._var += (rdata*rdata).sum(axis=0)
        self._tlen += rdata.shape[0]
        td_data = utils.timediff(data)
        self._diff2 += (td_data*td_data).sum(axis=0)

    def _stop_training(self):
        var_tlen = self._tlen-1
        # unbiased
        var = (self._var - self._mean*self._mean/self._tlen)/var_tlen

        # biased
        #var = (self._var - self._mean*self._mean/self._tlen)/self._tlen

        # old formula: wrong! is neither biased nor unbiased
        #var = (self._var/var_tlen) - (self._mean/self._tlen)**2

        self._var = var
        delta = (self._diff2/self._tlen)/var
        self._delta = delta
        self._eta = numx.sqrt(delta)/(2*numx.pi)

    def get_eta(self, t=1):
        """Return the eta values of the data received during the training
        phase. If the training phase has not been completed yet, call
        stop_training.

        Input arguments:
        t -- Sampling frequency in Hz
             The original definition in (Wiskott and Sejnowski, 2002)
             is obtained for t=self._tlen, while for t=1 (default),
             this corresponds to the beta-value defined in
             (Berkes and Wiskott, 2005).
        """
        self._if_training_stop_training()
        return self._refcast(self._eta*t)


class NoiseNode(Node):
    """Inject multiplicative or additive noise into the input data.

    Original code contributed by Mathias Franzius.

    Note that due to the noise_func attribute this node cannot be pickled.
    """

    def __init__(self, noise_func = mdp.numx_rand.normal, noise_args = (0, 1),
                 noise_type = 'additive', input_dim = None, dtype = None):
        """
        Add noise to input signals.

        Input signal:
        'noise_func' -- A function that generates noise. It must
                        take a 'size' keyword argument and return
                        a random array of that size. Default is normal noise.

        'noise_args' -- Tuple of additional arguments passed to noise_func.
                        Default is (0,1) for (mean, standard deviation)
                        of the normal distribution.

        'noise_type' -- Either 'additive' or 'multiplicative':
                         'additive' returns x + noise
                         'multiplicative' returns x * (1 + noise)
                        Default is 'additive'.
        """
        super(NoiseNode, self).__init__(input_dim=input_dim,
                                        output_dim=input_dim,
                                        dtype=dtype)
        self.noise_func = noise_func
        self.noise_args = noise_args
        valid_noise_types = ['additive', 'multiplicative']
        if noise_type not in valid_noise_types:
            err_str = '%s is not a valid noise type' % str(noise_type)
            raise NodeException(err_str)
        else:
            self.noise_type = noise_type

    def _get_supported_dtypes(self):
        """Return the list of dtypes supported by this node."""
        return (mdp.utils.get_dtypes('AllFloat') +
                mdp.utils.get_dtypes('AllInteger'))

    @staticmethod
    def is_trainable():
        return False

    @staticmethod
    def is_invertible():
        return False

    def _execute(self, x):
        noise_mat = self._refcast(self.noise_func(*self.noise_args,
                                                  **{'size': x.shape}))
        if self.noise_type == 'additive':
            return x+noise_mat
        elif self.noise_type == 'multiplicative':
            return x*(1.+noise_mat)

    def save(self, filename, protocol = -1):
        """Save a pickled serialization of the node to 'filename'.
        If 'filename' is None, return a string.

        Note: the pickled Node is not guaranteed to be upward or
        backward compatible."""
        if filename is None:
            return real_pickle.dumps(self, protocol)
        else:
            # if protocol != 0 open the file in binary mode
            if protocol != 0:
                mode = 'wb'
            else:
                mode = 'w'
            flh = open(filename, mode)
            real_pickle.dump(self, flh, protocol)
            flh.close()


    def copy(self, protocol = -1):
        """Return a deep copy of the node.
        Protocol is the pickle protocol."""
        as_str = real_pickle.dumps(self, protocol)
        return real_pickle.loads(as_str)


class NormalNoiseNode(mdp.Node):
    """Special version of NoiseNode for Gaussian additive noise.

    Unlike NoiseNode it does not store a noise function reference but simply
    uses numx_rand.normal. This has the advantage that the node can be pickled
    (which does not work for a normal NoiseNode).
    """

    def __init__(self, noise_args=(0, 1), input_dim=None, dtype=None):
        """Set the noise parameters.

        noise_args -- Tuple of (mean, standard deviation) for the normal
            distribution, default is (0,1).
        """
        super(NormalNoiseNode, self).__init__(input_dim=input_dim,
                                              output_dim=input_dim,
                                              dtype=dtype)
        self.noise_args = noise_args

    @staticmethod
    def is_trainable():
        return False

    @staticmethod
    def is_invertible():
        return False

    def _get_supported_dtypes(self):
        return mdp.utils.get_dtypes('AllFloat')

    def _execute(self, x):
        noise = self._refcast(mdp.numx_rand.normal(size=x.shape) * self.noise_args[1]
                              + self.noise_args[0])
        return x + noise


class GaussianClassifierNode(ClassifierNode):
    """Perform a supervised Gaussian classification.

    Given a set of labelled data, the node fits a gaussian distribution
    to each class. Note that it is written as an analysis node (i.e., the
    execute function is the identity function). To perform classification,
    use the 'label' method. If instead you need the posterior
    probability of the classes given the data use the 'class_probabilities'
    method.
    """
    def __init__(self, input_dim=None, dtype=None):
        super(GaussianClassifierNode, self).__init__(input_dim, None, dtype)
        self.cov_objs = {}

    def _set_input_dim(self, n):
        self._input_dim = n
        self._output_dim = n

    def _set_output_dim(self, n):
        msg = "Output dim cannot be set explicitly!"
        raise mdp.NodeException(msg)

    def _get_supported_dtypes(self):
        """Return the list of dtypes supported by this node."""
        return ['float32', 'float64']

    @staticmethod
    def is_invertible():
        return False

    def _check_train_args(self, x, labels):
        if isinstance(labels, (list, tuple, numx.ndarray)) and (
            len(labels) != x.shape[0]):
            msg = ("The number of labels should be equal to the number of "
                   "datapoints (%d != %d)" % (len(labels), x.shape[0]))
            raise mdp.TrainingException(msg)

    def _update_covs(self, x, lbl):
        if lbl not in self.cov_objs:
            self.cov_objs[lbl] = utils.CovarianceMatrix(dtype=self.dtype)
        self.cov_objs[lbl].update(x)

    def _train(self, x, labels):
        """
        Additional input arguments:
        labels -- Can be a list, tuple or array of labels (one for each data point)
                  or a single label, in which case all input data is assigned to
                  the same class.
        """
         # if labels is a number, all x's belong to the same class
        if isinstance(labels, (list, tuple, numx.ndarray)):
            labels_ = numx.asarray(labels)
            # get all classes from cl
            for lbl in set(labels_):
                x_lbl = numx.compress(labels_==lbl, x, axis=0)
                self._update_covs(x_lbl, lbl)
        else:
            self._update_covs(x, labels)

    def _stop_training(self):
        self.labels = self.cov_objs.keys()
        self.labels.sort()

        # we are going to store the inverse of the covariance matrices
        # since only those are useful to compute the probabilities
        self.inv_covs = []
        self.means = []
        self.p = []
        # this list contains the square root of the determinant of the
        # corresponding covariance matrix
        self._sqrt_def_covs = []
        nitems = 0

        for lbl in self.labels:
            cov, mean, p = self.cov_objs[lbl].fix()
            nitems += p
            self._sqrt_def_covs.append(numx.sqrt(numx_linalg.det(cov)))
            self.means.append(mean)
            self.p.append(p)
            self.inv_covs.append(utils.inv(cov))

        for i in range(len(self.p)):
            self.p[i] /= float(nitems)

        del self.cov_objs

    def _gaussian_prob(self, x, lbl_idx):
        """Return the probability of the data points x with respect to a
        gaussian.

        Input arguments:
        x -- Input data
        S -- Covariance matrix
        mn -- Mean
        """
        x = self._refcast(x)

        dim = self.input_dim
        sqrt_detS = self._sqrt_def_covs[lbl_idx]
        invS = self.inv_covs[lbl_idx]
        # subtract the mean
        x_mn = x - self.means[lbl_idx][numx.newaxis, :]
        # exponent
        exponent = -0.5 * (utils.mult(x_mn, invS)*x_mn).sum(axis=1)
        # constant
        constant = (2.*numx.pi)**-(dim/2.)/sqrt_detS
        # probability
        return constant * numx.exp(exponent)

    def class_probabilities(self, x):
        """Return the posterior probability of each class given the input."""
        self._pre_execution_checks(x)

        # compute the probability for each class
        tmp_prob = numx.zeros((x.shape[0], len(self.labels)),
                              dtype=self.dtype)
        for i in range(len(self.labels)):
            tmp_prob[:, i] = self._gaussian_prob(x, i)
            tmp_prob[:, i] *= self.p[i]

        # normalize to probability 1
        # (not necessary, but sometimes useful)
        tmp_tot = tmp_prob.sum(axis=1)
        tmp_tot = tmp_tot[:, numx.newaxis]
        return tmp_prob/tmp_tot

    def _prob(self, x):
        """Return the posterior probability of each class given the input in a dict."""

        class_prob = self.class_probabilities(x)
        return [dict(zip(self.labels, prob)) for prob in class_prob]

    def _label(self, x):
        """Classify the input data using Maximum A-Posteriori."""

        class_prob = self.class_probabilities(x)
        winner = class_prob.argmax(axis=-1)
        return [self.labels[winner[i]] for i in range(len(winner))]


class CutoffNode(mdp.Node):
    """Node to cut off values at specified bounds.

    Works similar to numpy.clip, but also works when only a lower or upper
    bound is specified.
    """

    def __init__(self, lower_bound=None, upper_bound=None,
                 input_dim=None, dtype=None):
        """Initialize node.

        lower_bound -- Data values below this are cut to the lower_bound value.
            If lower_bound is None no cutoff is performed.
        upper_bound -- Works like lower_bound.
        """
        super(CutoffNode, self).__init__(input_dim=input_dim,
                                         output_dim=input_dim,
                                         dtype=dtype)
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    @staticmethod
    def is_trainable():
        return False

    @staticmethod
    def is_invertible():
        return False

    def _get_supported_dtypes(self):
        return (mdp.utils.get_dtypes('AllFloat') +
                mdp.utils.get_dtypes('AllInteger'))

    def _execute(self, x):
        """Return the clipped data."""
        # n.clip() does not work, since it does not accept None for one bound
        if self.lower_bound is not None:
            x = numx.where(x >= self.lower_bound, x, self.lower_bound)
        if self.upper_bound is not None:
            x = numx.where(x <= self.upper_bound, x, self.upper_bound)
        return x


class HistogramNode(mdp.Node):
    """Node which stores a history of the data during its training phase.

    The data history is stored in self.data_hist and can also be deleted to
    free memory. Alternatively it can be automatically pickled to disk.

    Note that data is only stored during training.
    """

    def __init__(self, hist_fraction=1.0, hist_filename=None,
                 input_dim=None, dtype=None):
        """Initialize the node.

        hist_fraction -- Defines the fraction of the data that is stored
            randomly.
        hist_filename -- Filename for the file to which the data history will
            be pickled after training. The data is pickled when stop_training
            is called and data_hist is then cleared (to free memory).
            If filename is None (default value) then data_hist is not cleared
            and can be directly used after training.
        """
        super(HistogramNode, self).__init__(input_dim=input_dim,
                                            output_dim=input_dim,
                                            dtype=dtype)
        self._hist_filename = hist_filename
        self.hist_fraction = hist_fraction
        self.data_hist = None  # stores the data history

    def _get_supported_dtypes(self):
        return (mdp.utils.get_dtypes('AllFloat') +
                mdp.utils.get_dtypes('AllInteger'))

    def _train(self, x):
        """Store the history data."""
        if self.hist_fraction < 1.0:
            x = x[numx.random.random(len(x)) < self.hist_fraction]
        if self.data_hist is not None:
            self.data_hist = numx.concatenate([self.data_hist, x])
        else:
            self.data_hist = x

    def _stop_training(self):
        """Pickle the histogram data to file and clear it if required."""
        super(HistogramNode, self)._stop_training()
        if self._hist_filename:
            pickle_file = open(self._hist_filename, "wb")
            try:
                pickle.dump(self.data_hist, pickle_file, protocol=-1)
            finally:
                pickle_file.close( )
            self.data_hist = None


class AdaptiveCutoffNode(HistogramNode):
    """Node which uses the data history during training to learn cutoff values.

    As opposed to the simple CutoffNode, a different cutoff value is learned
    for each data coordinate. For example if an upper cutoff fraction of
    0.05 is specified, then the upper cutoff bound is set so that the upper
    5% of the training data would have been clipped (in each dimension).
    The cutoff bounds are then applied during execution.
    This Node also works as a HistogramNode, so the histogram data is stored.

    When stop_training is called the cutoff values for each coordinate are
    calculated based on the collected histogram data.
    """

    def __init__(self, lower_cutoff_fraction=None, upper_cutoff_fraction=None,
                 hist_fraction=1.0, hist_filename=None,
                 input_dim=None, dtype=None):
        """Initialize the node.

        lower_cutoff_fraction -- Fraction of data that will be cut off after
            the training phase (assuming the data distribution does not
            change). If set to None (default value) no cutoff is performed.
        upper_cutoff_fraction -- Works like lower_cutoff_fraction.
        hist_fraction -- Defines the fraction of the data that is stored for the
            histogram.
        hist_filename -- Filename for the file to which the data history will
            be pickled after training. The data is pickled when stop_training
            is called and data_hist is then cleared (to free memory).
            If filename is None (default value) then data_hist is not cleared
            and can be directly used after training.
        """
        super(AdaptiveCutoffNode, self).__init__(hist_fraction=hist_fraction,
                                                 hist_filename=hist_filename,
                                                 input_dim=input_dim,
                                                 dtype=dtype)
        self.lower_cutoff_fraction = lower_cutoff_fraction
        self.upper_cutoff_fraction = upper_cutoff_fraction
        self.lower_bounds = None
        self.upper_bounds = None

    def _stop_training(self):
        """Calculate the cutoff bounds based on collected histogram data."""
        if self.lower_cutoff_fraction or self.upper_cutoff_fraction:
            sorted_data = self.data_hist.copy()
            sorted_data.sort(axis=0)
            if self.lower_cutoff_fraction:
                index = self.lower_cutoff_fraction * len(sorted_data)
                self.lower_bounds = sorted_data[index]
            if self.upper_cutoff_fraction:
                index = (len(sorted_data) -
                         self.upper_cutoff_fraction * len(sorted_data))
                self.upper_bounds = sorted_data[index]
        super(AdaptiveCutoffNode, self)._stop_training()

    def _execute(self, x):
        """Return the clipped data."""
        if self.lower_bounds is not None:
            x = numx.where(x >= self.lower_bounds, x, self.lower_bounds)
        if self.upper_bounds is not None:
            x = numx.where(x <= self.upper_bounds, x, self.upper_bounds)
        return x
