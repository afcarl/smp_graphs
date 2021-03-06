"""expr0110 pointmass 1D with delay open loop xcorr scan
"""

from smp_graphs.utils_conf import get_systemblock
from smp_graphs.utils_conf_meas import make_input_matrix_ndim
from smp_graphs.block_meas import XCorrBlock2

from numpy import arange

numsteps = 2000

robot1 = get_systemblock['pm'](dim_s0 = 1)
robot1['params']['transfer'] = 0 # 4 # cosine
dim_s0 = robot1['params']['dims']['s0']['dim']
dim_m0 = robot1['params']['dims']['m0']['dim']
m_mins = np.array([robot1['params']['m_mins']]).T
m_maxs = np.array([robot1['params']['m_maxs']]).T

# scan parameters
scanstart = -10
scanstop = 0
scanlen = scanstop - scanstart

outputs = {'latex': {'type': 'latex'}}

desc = """The same configuration as in the previous experiment is now
run for {0} time steps as \TODO{{sufficient statistics}}. A
cross-correlation scan is then performed on the motor variables $m$
versus the sensor variables $s_0$. The scan consists of computing the
Pearson correlation coefficient of $m_i$ and $s_i$ for a set of preset
temporal offsets.  The output is generated by incrementally shifting
the destination variable in the pair by one time step into the past
and then computing the correlation coefficient. The scanning range of
temporal offsets in this example is going from {1} to {2}. The output
of the scan correctly determines a delay of 2 time steps, which is the
maximum correlation over all possible shifts. A shift of zero is not
included as a minimum motor-sensor delay of one time step is assumed
by the underlying representation of time and causality.""".format(
numsteps, scanstart, scanstop)

graph = OrderedDict([
    # point mass system
    ('robot1', robot1),
    
    # noise
    ('pre_l0', {
        'block': ModelBlock2,
        'params': {
            'blocksize': 1,
            'blockphase': [0],
            'inputs': {                        
                'lo': {'val': m_mins, 'shape': (dim_s0, 1)},
                'hi': {'val': m_maxs, 'shape': (dim_s0, 1)},
                },
            'outputs': {'pre': {'shape': (dim_m0, 1)}},
            'models': {
                'goal': {'type': 'random_uniform'}
                },
            'rate': 5,
            },
        }),

    # measurement
    ('meas_l0', {
        'block': PlotBlock2,
        'params': {
            'blocksize': numsteps,
            'saveplot': saveplot, 'savetype': 'pdf',
            'inputs': {
                's0': {'bus': 'robot1/s0', 'shape': (dim_s0, numsteps)},
                's0p': {'bus': 'pre_l0/pre', 'shape': (dim_m0, numsteps)},
            },
            'subplots': [
                [
                    {
                        'input': ['s0p', 's0'], 'plot': [partial(timeseries, marker = 'o')] * 2,
                    },
                ],
            ],
        },
    }),
    
    # cross-correlation scan
    ('xcorr', {
        'block': XCorrBlock2,
        'params': {
            # 'debug': True,
            'blocksize': numsteps,
            'inputs': {'y': {'bus': 'pre_l0/pre', 'shape': (dim_s0, numsteps)}, 'x': {'bus': 'robot1/s0', 'shape': (dim_s0, numsteps)}},
            'shift': (scanstart, scanstop),
            'outputs': {'xcorr': {'shape': (dim_m0, dim_s0, scanlen)}},
        }
    }),
    
    # cross-correlation plot
    ('xcorr_plot', {
        'block': ImgPlotBlock2,
        'params': {
            'logging': False,
            'saveplot': saveplot,
            'debug': False,
            'blocksize': numsteps,
            # 'inputs': make_input_matrix(xdim = dim_m0, ydim = dim_s0, with_t = True),
            'inputs': make_input_matrix_ndim(xdim = dim_m0, ydim = dim_s0, with_t = True, scan = (scanstart, scanstop)),
            'outputs': {}, #'x': {'shape': (3, 1)}},
            'wspace': 0.5,
            'hspace': 0.5,
            'subplots': [
                # [{'input': ['d3'], 'ndslice': (i, j, ), 'xslice': (0, scanlen), 'xaxis': 't',
                #   'plot': partial(timeseries, linestyle="none", marker=".")} for j in range(dim_m0)]
                # for i in range(dim_s0)],
                [
                    {
                        'input': ['d3'], 'ndslice': (slice(scanlen), i, j),
                        'shape': (1, scanlen), 'cmap': 'RdGy', 'title': 'xcorrs',
                        'vmin': -1.0, 'vmax': 1.0, 'vaxis': 'cols',
                        'yticks': False, 'yticklabels': None, 'ylabel': None,
                        'xticks': (arange(scanlen) + 0.5).tolist(),
                        'xticklabels': range(scanstart, scanstop),
                        'colorbar': True,
                    } for j in range(dim_m0)] # 'seismic'
            for i in range(dim_s0)],
        },
    }),
    
])
