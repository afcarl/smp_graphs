"""smp_graphs default conf

the config is python, so we
 - import stuff we need in the config
 - put the graph config into a dict
"""

from smp_graphs.block import CountBlock2

from functools import partial

# reused variables
numsteps = 100

# graph
graph = OrderedDict([
    # a constant
    ("b1", {
        'block': CountBlock2,
        'params': {
            'id': 'b1',
            'inputs': {},
            'outputs': {'cnt': [(1,1)]},
            'debug': False,
        },
    }),
    # a random number generator, mapping const input to hi
    ("b2", {
        'block': SeqLoopBlock2,
        'params': {
            'id': 'b2',
            'idim': 6,
            'odim': 3,
            # 'lo': 0,
            # 'hi': 1,
            'outputs': {'x': [(3, 1)]},
            'debug': True,
            # 'inputs': {'lo': [0, (3, 1)], 'hi': ['b1/x']}, # , 'li': np.random.uniform(0, 1, (3,)), 'bu': {'b1/x': [0, 1]}}
            # recurrent connection
            'inputs': {'lo': ['b2/x'], 'hi': ['b1/x']}, # , 'li': np.random.uniform(0, 1, (3,)), 'bu': {'b1/x': [0, 1]}}
        },
    }),
    # plot module with blocksize = episode, fetching input from busses
    # and mapping that onto plots
    ("bplot", {
        'block': TimeseriesPlotBlock2,
        'params': {
            'id': 'bplot',
            'blocksize': numsteps,
            'idim': 6,
            'odim': 3,
            'debug': True,
            'inputs': {'d1': ['b1/cnt']}, # 'd2': ['b2/x']},
            'outputs': {'x': [(3, 1)]},
            'subplots': [
                [
                    {'input': 'd1', 'slice': (0, 3), 'plot': partial(timeseries, marker = 'o', linestyle = 'None')},
                    {'input': 'd1', 'slice': (0, 3), 'plot': histogram},
                ],
                # [
                #     {'input': 'd2', 'slice': (3, 6), 'plot': timeseries},
                #     {'input': 'd2', 'slice': (3, 6), 'plot': histogram},
                # ],
            ]
        }
    })
])