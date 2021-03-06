import sys,os
import numpy as np
import keras.backend as K
from keras.engine.topology import Layer
from keras.initializers import RandomUniform, Initializer, Constant
import tensorflow as tf
import keras
from utils.console import Progbar
from nn import patchlayer

sys.path.append(os.path.dirname(os.getcwd()))

# =============================================================================
# Base structure for Neural structure
# =============================================================================

def pseudo_rbf(x):
    return (1+tf.cos(2*tf.atan(x)))/2

class InitCentersRandom(Initializer):
    """ Initializer for initialization of centers of RBF network
        as random samples from the given data set.
    # Arguments
        X: matrix, dataset to choose the centers from (random rows 
          are taken as centers)
    """
    def __init__(self, X):
        self.X = X 

    def __call__(self, shape, dtype=None):
        assert shape[1] == self.X.shape[1]
        idx = np.random.randint(self.X.shape[0], size=shape[0])
        return self.X[idx,:]

        
class RBFLayer(Layer):
    """ Layer of Gaussian RBF units. 
    # Example
 
    ```python
        model = Sequential()
        model.add(RBFLayer(10,
                           initializer=InitCentersRandom(X), 
                           betas=1.0,
                           input_shape=(1,)))
        model.add(Dense(1))
    ```
    
    # Arguments
        output_dim: number of hidden units (i.e. number of outputs of the layer)
        initializer: instance of initiliazer to initialize centers
        betas: float, initial value for betas 
    """
    def __init__(self, output_dim, initializer=None, betas=1.0, **kwargs):
        self.output_dim = output_dim
        self.init_betas = betas 
        if not initializer:
            self.initializer = RandomUniform(0.0, 1.0)
            #self.initializer = Orthogonal()
        else:
            self.initializer = initializer 
        super(RBFLayer, self).__init__(**kwargs)

    def build(self, input_shape):
        
        self.centers = self.add_weight(name='centers', 
                                       shape=(self.output_dim, input_shape[1]),
                                       initializer=self.initializer,
                                       trainable=True)
        self.betas = self.add_weight(name='betas',
                                     shape=(input_shape[1],self.output_dim),
                                     initializer=Constant(value=self.init_betas),
                                     #initializer='ones',
                                     trainable=True)
            
        super(RBFLayer, self).build(input_shape)
        
        self.trainable_weights=[self.centers, self.betas]

    def call(self, inputs):

        C = K.expand_dims(self.centers)
        H = K.transpose(C-K.transpose(inputs))
        return pseudo_rbf(-K.sum(self.betas*H**2, axis=1))

    def compute_output_shape(self, input_shape):
        return (input_shape[0], self.output_dim)


    def get_config(self):
        # have to define get_config to be able to use model_from_json
        config = {
            'output_dim': self.output_dim
        }
        base_config = super(RBFLayer, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))
