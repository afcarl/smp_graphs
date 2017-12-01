"""**Model blocks**: blocks that contain a model

.. moduleauthor:: Oswald Berthold 2012-2017

Most often models are adaptive models which are trained with data like
a neural network, a kernel machine, mixture models, and so on. More
generally models are things like coders, hand-crafted or learned
representations; predictors or inference engines; associative memory
modules, etc. In a deeper sense, almost everything can be seen as a
model but the full story is kept for *smp-graphs-ng*.

Here are some more examples of model types and contexts in which they are used:
 - *raw models* doing fit/predict, X/Y style training and prediction
 - *sensorimotor (sm) models* are embedded in the sensorimotor context of an agent
 - *developmental (dvl) models* are collections of raw models,
   sm-models, and additional operators that describe and control the
   developmental sequence of an agent

The model design is in progress. The current approach is to have a
general Block wrapper for all models. Particular models are of class
model and actual model functions are implemented by lightewight init()
and step() function-only definitions. This works but has some
drawbacks, like deeper class hierarchy, limited reusability, ...

**Available models**

Obtained with `git grep -i \^def\\ step smp_graphs/block_models.py | grep -v \\# | sed -e 's/smp_graphs\/block_models.py:def step_//' | sed -e 's/(.*$//'`.

musig (:func:`init_musig`, :func:`step_musig`), res (:func:`init_res`, :func:`step_res`), polyexp (:func:`init_polyexp`, :func:`step_polyexp`), random_lookup (:func:`init_random_lookup`, :func:`step_random_lookup`), random_uniform (:func:`init_random_uniform`, :func:`step_random_uniform`), random_uniform_pi_2 (:func:`init_random_uniform_pi_2`, :func:`step_random_uniform_pi_2`), budget (:func:`init_budget`, :func:`step_budget`), random_uniform_modulated (:func:`init_random_uniform_modulated`, :func:`step_random_uniform_modulated`), alternating_sign (:func:`init_alternating_sign`, :func:`step_alternating_sign`), actinf (:func:`init_actinf`, :func:`step_actinf`), actinf_2 (:func:`init_actinf_2`, :func:`step_actinf_2`), homeokinesis (:func:`init_homeokinesis`, :func:`step_homeokinesis`), sklearn (:func:`init_sklearn`, :func:`step_sklearn`), e2p (:func:`init_e2p`, :func:`step_e2p`), imol (:func:`init_imol`, :func:`step_imol`), eh (:func:`init_eh`, :func:`step_eh`), 

.. exec::
    import json
    from smp_graphs.block_models import model
    modeldict = dict([(k, '') for k, v in model.models.items()])
    json_obj = json.dumps(modeldict, sort_keys=True, indent=4)
    print ".. code-block:: JavaScript\\n\\n    models = {0}\\n    \\n".format(json_obj)
    pass


Things
 - FIXME: A modelblock's :attr:`models` config dict is interpreted as a loop spec generating a block for each of the models (syntactic sugar).
 - FIXME: Consolidate model names by 'function'
 - FIXME: Next approach is to convert all model definitions from function-only style to class-style with some model specific wrappers.
 - FIXME: clean up and enable list of models in ModelBlock2, self.models has name, conf(model, in, out), model-instance, model.mdl-instance(s)
"""

from os import path as ospath
from functools import partial

# pickling and storing of models
import pickle, joblib

import numpy as np

from smp_base.common import get_module_logger

from smp_graphs.block        import decInit, decStep, Block2, PrimBlock2
from smp_graphs.common       import code_compile_and_run, get_input
from smp_graphs.funcs_models import model
from smp_graphs.graph        import nxgraph_node_by_id_recursive

from logging import DEBUG as LOGLEVEL
logger = get_module_logger(modulename = 'block_models', loglevel = LOGLEVEL - 0)

class CodingBlock2(PrimBlock2):
    """CodingBlock2

    mean-variance-residual coding block, recursive estimate of input's mu and sigma
    """
    @decInit()
    def __init__(self, conf = {}, paren = None, top = None):
        
        PrimBlock2.__init__(self, conf = conf, paren = paren, top = top)
        
        for ink, inv in self.inputs.items():
            print inv
            for outk in ["mu", "sig", "std"]:
                if outk.endswith("sig"):
                    setattr(self, "%s_%s" % (ink, outk), np.ones(inv['shape']))
                else:
                    setattr(self, "%s_%s" % (ink, outk), np.zeros(inv['shape']))
        
    @decStep()
    def step(self, x = None):
        self.debug_print("%s.step:\n\tx = %s,\n\tbus = %s,\n\tinputs = %s,\n\toutputs = %s",
                         (self.__class__.__name__,self.outputs.keys(), self.bus, self.inputs, self.outputs))

        # FIXME: relation rate / blocksize, remember cnt from last step, check difference > rate etc
        
        if self.cnt % self.blocksize == 0:
            for ink, inv in self.inputs.items():
                for outk_ in ["mu", "sig", "std"]:
                    outk = "%s_%s" % (ink, outk_)
                    outv_ = getattr(self, outk)

                    if outk.endswith("mu"):
                        setattr(self, outk, 0.99 * outv_ + 0.01 * inv['val'])
                    elif outk.endswith("sig"):
                        setattr(self, outk, 0.99 * outv_ + 0.01 * np.sqrt(np.square(inv['val'] - getattr(self, ink + "_mu"))))
                    elif outk.endswith("std"):
                        mu = getattr(self, 'x_mu')
                        sig = getattr(self, 'x_sig')
                        setattr(self, outk, (inv['val'] - mu) / sig)

class ModelBlock2(PrimBlock2):
    """Basic Model block

    This is a template block with a member params[\"models\"]. A model
    is loaded on init by evaluating an init_MODEL and step_MODEL
    function with a common interface. This way we don't need to define
    a block for every model variant but can just write it down
    compactly as init and step functions.

     - FIXME: obvisouly merge with funcblock, a model is a more
       general func, with memory, see morphism
     - FIXME: not sure if this is a good final repr for models and their scope
    """
    defaults = {
        'debug': False,
        'model_numelem': 1001,
        'models': {
            'uniform': {
                'type': 'random_uniform',
                
            },
        },
        'inputs': {
            'lo': {'val': -np.ones((1,1))},
            'hi': {'val':  np.ones((1,1))},
        },
        'outputs': {
            'pre': {'shape': (1,1)},
        },
    }
    @decInit()
    def __init__(self, conf = {}, paren = None, top = None):
        """ModelBlock2 init
        """

        # get configuration from parent.defaults stack
        params = {}
        params.update(Block2.defaults)
        params.update(PrimBlock2.defaults)
        params.update(self.defaults)
        params.update(conf['params'])

        # write back to orig conf
        conf['params'].update(params)

        # pre-configure some self attributes
        self.conf = conf
        self.top = top
        self.logger = logger
        self.loglevel = params['loglevel']
        self.debug = params['debug']
        # self.lag = 1

        # s_ = super(ModelBlock2, self)
        # self.logger.info('super = %s, %s', type(s_), s_.__class__.__name__)

        def rewrite_model_to_block(conf, mkey, mconf, rewritekeys = ['inputs', 'outputs'], nummodels = 1):
            # for k, v in mconf.items():
            #     if k not in rewritekeys: continue
            for k in rewritekeys:
                conf_ = mconf
                mconf_k = True
                
                if not mconf.has_key(k):
                    mconf_k = False
                    conf_ = conf
                    mconf[k] = {}
                    
                v = conf_[k]
                
                for ck, cv in v.items():
                    if nummodels > 1:
                        ck_ = '%s/%s' % (mkey, ck)
                        # rewrite entry
                        mconf[k][ck_] = cv
                        # delete original entry
                        if mconf_k:
                            mconf[k].pop(ck)
                    else:
                        mconf[k][ck] = cv
            return mconf
        
        # initialize model
        # FIXME: need to associate inputs / outputs with a model for arrays of models
        mconf_io = {'inputs': {}, 'outputs': {}}
        nummodels = len(params['models'])
        for mk, mv in params['models'].items():
            # generate model inputs/outputs configuration
            # 1 if model brings its own i/o conf, unroll / copy that into block outputs
            # if mv.has_key('inputs'):
            #     print "have inputs, great"
            #     mconf_inputs = rewrite_model_to_block(params['id'], mv, ['inputs'])
            #     self.logger.debug("conf_ = %s" % (conf_, ))
            # else:
            # if v.has_key('outputs'):
            #     print "have outputs, great"
            #     mconf_outputs = rewrite_model_to_block(params['id'], v, ['outputs'])

            # rewrite conf
            mconf = rewrite_model_to_block(params, mk, mv, ['inputs', 'outputs'], nummodels)

            # self.logger.debug("mkey = %s, mconf = %s", mk, mconf)
            
            # update conf
            for iok in ['inputs', 'outputs']:
                mconf_io[iok].update(mconf[iok])

        # self.logger.debug("mconf_io = %s", mconf_io)
            
        # 1.1 update block conf
        # 2   if model does not bring its own i/o conf, generate block/mdl i/o from block i/o * mdl-key
        # 3   remove block i/o template conf

        # update conf
        for iok in ['inputs', 'outputs']:
            # replace all block level configuration
            conf['params'][iok].update(mconf_io[iok])
            # params[iok] = mconf_io[iok]

        self.logger.debug("conf['params']['inputs'] = %s", conf['params']['inputs'])
        self.logger.debug("conf['params']['outputs'] = %s", conf['params']['outputs'])
        
        # init models
        for mk, mv in params['models'].items():
            mv['inst_'] = model(ref = self, conf = conf, mref = mk, mconf = mv)
            params['models'][mk].update(mv)

        # FIXME: legacy iodim at block level
        for k in ['idim', 'odim']:
            if mv.has_key(k):
                setattr(self, k, mv[k])
            
        # print "\n params.models = %s" % (params['models'], )
        # print "top", top.id

        PrimBlock2.__init__(self, conf = conf, paren = paren, top = top)

        # print "\n self.models = %s" % (self.models, )
        for mk, mv in self.models.items():
            mref = mv['inst_']
            mref.init_modelfilename(self)
            mref.load(self)

    def save(self):
        """Dump the model into a file
        """
        for k, v in self.models.items():
            mdl_inst = v['inst_']
            # if hasattr(self, 'saveable') and self.saveable:
            mdl_inst.save(ref = self)
        
    @decStep()
    def step(self, x = None):
        """ModelBlock2 step"""
        # print "%s-%s.step %d" % (self.cname, self.id, self.cnt,)
        # self.debug_print("%s.step:\n\tx = %s,\n\tbus = %s,\n\tinputs = %s,\n\toutputs = %s",
        #     (self.__class__.__name__, self.outputs.keys(), self.bus,
        #          self.inputs, self.outputs))

        # FIXME: relation rate / blocksize, remember cnt from last step, check difference > rate etc
        # FIXME: if block_is_scheduled
        # FIXME: if output_is_scheduled
        
        if self.cnt % self.blocksize == 0:
            for mk, mv in self.models.items():
                mv['inst_'].predict(self)

            # copy output from model to block

        if self.block_is_finished():
            self.save()
            
        # if rospy.is_shutdown():
        #     sys.exit()


class TopDummy(object):
    """Dummy top block

    Can be used for testing Block2s which require 'top' argument and
    rely on some top properties for internal operation.
    """
    def __init__(self):
        from smp_graphs.block import Bus
        
        self.blocksize_min = np.inf
        self.bus = Bus()
        self.cnt = 0
        self.docache = False
        self.inputs = {}
        self.numsteps = 100
        self.saveplot = False
        self.topblock = True

if __name__ == '__main__':
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec

    # dummy top block
    top = TopDummy()
    # setattr(top, 'numsteps', 100)
    
    # test model: random_lookup
    dim_s_proprio = 1
    default_conf = {
        'block': ModelBlock2,
        'params': {
            'id': 'bla',
            'debug': True,
            'logging': False,
            'models': {
                'infodistgen': {
                    'type': 'random_lookup',
                    'd': 0.9,
                }
            },
            'inputs': {
                'x': {'bus': 'robot1/s_proprio', 'shape': (dim_s_proprio, 1)},
            },
            'outputs': {
                'y': {'shape': (dim_s_proprio, 1)},
            },
        }
    }

    top.bus['robot1/s_proprio'] = np.random.uniform(-1, 1, (dim_s_proprio, 1))

    block = ModelBlock2(conf = default_conf, paren = top, top = top)

    print "bus\n", top.bus.astable()

    print "block", block.id

    # for i in range(10):
    #     top.bus['robot1/s_proprio'] = np.random.uniform(-1, 1, (dim_s_proprio, 1))
    #     block.inputs['x']['val'] = top.bus['robot1/s_proprio']
    #     block.step()
        
    # params = conf['params']
    # params['numelem'] = 1001
    # inshape = params['inputs']['x']['shape']    
    # ref.h_lin = np.linspace(-1, 1, params['numelem']) # .reshape(1, params['numelem'])
    # mconf['d']

    conf = {
        'params': {
            'inputs': {
                'x': {'shape': (1, 1)},
            },
            'nesting_indent': 4,
        },
        'd': 0.9,
    }

    top.inputs['x'] = conf['params']['inputs']['x']
    top.inputs['x']['val'] = np.random.uniform(-1, 1, (1,1))
    
    init_random_lookup(top, conf, conf)

    xs = np.zeros((dim_s_proprio, 101))
    ys = np.zeros((dim_s_proprio, 101))
    
    for i,x in enumerate(np.linspace(-1, 1, 101)):
        # top.inputs['x']['val'] = np.random.uniform(-1, 1, (dim_s_proprio, 1))
        top.inputs['x']['val'] = np.ones((1,1)) * x
        top.cnt += 1
        step_random_lookup(top)
        # print "y", top.x, top.y
        xs[...,[i]] = top.x
        ys[...,[i]] = top.y

    print "xs", xs
    print "ys", ys
    fig = plt.figure()
    gs = GridSpec(2,1)
    ax1 = fig.add_subplot(gs[0])
    ax1.set_title('transfer functions')
    ax1.plot(top.h_lin, 'ko', alpha = 0.3, label = 'lin')
    ax1.plot(top.h_noise, 'ro', alpha = 0.3, label = 'gaussian')
    ax1.legend()
    ax2 = fig.add_subplot(gs[1])
    ax2.set_title('y over x as y = h(binidx(x))')
    ax2.plot(xs.T, ys.T, 'ko', label = 'y = h(x)')
    ax2.legend()
    fig.show()
    plt.show()
