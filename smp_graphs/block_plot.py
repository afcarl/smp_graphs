
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from smp_graphs.block import decStep, decInit
from smp_graphs.block import PrimBlock2

from smp_base.plot import makefig, timeseries, histogram

################################################################################
# Plotting blocks

class PlotBlock2(PrimBlock2):
    """!@brief Basic plotting block

params
 - blocksize: usually numsteps (meaning plot all data created by that episode/experiment)
 - subplots: array of arrays, each cell of that matrix hold on subplot configuration dict
  - subplotconf: dict with inputs: list of input keys, plot: plotting function pointer
"""
    @decInit()
    def __init__(self, conf = {}, paren = None, top = None):
        PrimBlock2.__init__(self, conf = conf, paren = paren, top = top)

        # configure figure and plot axes
        self.fig_rows = len(self.subplots)
        self.fig_cols = len(self.subplots[0])
        # create figure
        self.fig = makefig(rows = self.fig_rows, cols = self.fig_cols)
        # self.debug_print("fig.axes = %s", (self.fig.axes, ))
        
    @decStep()
    def step(self, x = None):
        # have inputs at all?
        if len(self.inputs) < 1: return

        # make sure that data can have been generated
        if self.cnt > 0 and (self.cnt % self.blocksize) == 0: # (self.blocksize - 1):
            # self.debug_print("step ibuf = %s, in(%s).shape = %s", (self.ibuf, ink, inv[0]))

            plots = self.plot_subplots()
            
            # set figure title and show the fig
            self.fig.suptitle("%s" % (self.top.id,))
            self.fig.show()
        else:
            self.debug_print("%s.step", (self.__class__.__name__,))
            
    def plot_subplots(self):
        """loop over configured subplot and plot the data according to config"""
        if True:
            for i, subplot in enumerate(self.subplots):
                for j, subplotconf in enumerate(subplot):
                    idx = (i*self.fig_cols)+j
                    self.debug_print("%s.step idx = %d, conf = %s, data = %s", (
                        self.__class__.__name__, idx,
                        subplotconf, subplotconf['input']))
                    # self.inputs[subplotconf['input']][0]))

                    # configure x axis
                    if subplotconf.has_key('xaxis'):
                        t = self.inputs[subplotconf['xaxis']][0].T
                    else:
                        t = np.linspace(0, self.blocksize-1, self.blocksize)

                    # assert input an array 
                    if type(subplotconf['input']) is str:
                        subplotconf['input'] = [subplotconf['input']]

                    # plotdata = self.inputs[subplotconf['input']][0].T
                    # elif type(subplotconf['input']) is list:
                    # plotdata = self.inputs[subplotconf['input'][1]][0].T
                    plotdata = {}
                    plotvar = ""
                    for k, ink in enumerate(subplotconf['input']):
                        plotdata[ink] = self.inputs[ink][0].T
                        # fix nans
                        plotdata[ink][np.isnan(plotdata[ink])] = -1.0
                        plotvar += "%s, " % (self.inputs[ink][2],)
                    # different 
                    if subplotconf.has_key('mode'):
                        ivecs = tuple(self.inputs[ink][0].T for k, ink in enumerate(subplotconf['input']))
                        for item in ivecs:
                            print "ive.shape", item.shape
                        plotdata = {}
                        if subplotconf['mode'] in ['stack', 'combine', 'concat']:
                            plotdata['all'] = np.hstack(ivecs)
                        
                    if hasattr(subplotconf['plot'], 'func_name'):
                        # plain function
                        plottype = subplotconf['plot'].func_name
                    elif hasattr(subplotconf['plot'], 'func'):
                        # partial'ized func
                        plottype = subplotconf['plot'].func.func_name
                    else:
                        # unknown func type
                        plottype = "unk type"

                    # if type(subplotconf['input']) is list:
                    if subplotconf.has_key('xaxis'):
                        plotvar += " over %s" % (self.inputs[subplotconf['xaxis']][2], )
                        # plotvar = ""
                        # # FIXME: if len == 2 it is x over y, if len > 2 concatenation
                        # for k, inputvar in enumerate(subplotconf['input']):
                        #     tmpinput = self.inputs[inputvar][2]
                        #     plotvar += str(tmpinput)
                        #     if k != (len(subplotconf['input']) - 1):
                        #         plotvar += " revo "
                    # else:
                    # plotvar = self.inputs[subplotconf['input'][0]][2]
                        
                    print "plotvar", plotvar
                        
                    # plot the plotdata
                    for ink, inv in plotdata.items():
                        subplotconf['plot'](
                            self.fig.axes[idx],
                            data = inv, ordinate = t)
                        # metadata
                    self.fig.axes[idx].set_title("%s of %s" % (plottype, plotvar, ), fontsize=8)
                    # [subplotconf['slice'][0]:subplotconf['slice'][1]].T)


class SnsMatrixPlotBlock2(PrimBlock2):
    """!@brief Plotting block doing seaborn pairwaise matrix plots: e.g. scatter, hexbin, ...

params
 - blocksize: usually numsteps (meaning plot all data created by that episode/experiment)
 - f_plot_diag: diagonal cells
 - f_plot_matrix: off diagonal cells
 - numpy matrix of data, plot iterates over all pairs with given function
"""
    @decInit()
    def __init__(self, conf = {}, paren = None, top = None):
        PrimBlock2.__init__(self, conf = conf, paren = paren, top = top)

    @decStep()
    def step(self, x = None):
        print "%s.step inputs: %s"  % (self.cname, self.inputs.keys())

        subplotconf = self.subplots[0][0]
        
        # different 
        if subplotconf.has_key('mode'):
            ivecs = tuple(self.inputs[ink][0].T for k, ink in enumerate(subplotconf['input']))
            for ivec in ivecs:
                print "ivec.shape", ivec.shape
            plotdata = {}
            if subplotconf['mode'] in ['stack', 'combine', 'concat']:
                plotdata['all'] = np.hstack(ivecs)

        data = plotdata['all']

        print "SnsPlotBlock2:", data.shape
        scatter_data_raw  = data
        scatter_data_cols = ["x_%d" % (i,) for i in range(data.shape[1])]

        # prepare dataframe
        df = pd.DataFrame(scatter_data_raw, columns=scatter_data_cols)
        
        g = sns.PairGrid(df)
        g.map_diag(plt.hist)
        # g.map_diag(sns.kdeplot)
        g.map_offdiag(plt.hexbin, cmap="gray", gridsize=20, bins="log");
        # g.map_offdiag(plt.plot, linestyle = "None", marker = "o", alpha = 0.5) # , bins="log");

        # print "dir(g)", dir(g)
        # print g.diag_axes
        # print g.axes
    
        # for i in range(data.shape[1]):
        #     for j in range(data.shape[1]): # 1, 2; 0, 2; 0, 1
        #         if i == j:
        #             continue
        #         # column gives x axis, row gives y axis, thus need to reverse the selection for plotting goal
        #         # g.axes[i,j].plot(df["%s%d" % (self.cols_goal_base, j)], df["%s%d" % (self.cols_goal_base, i)], "ro", alpha=0.5)
        #         g.axes[i,j].plot(df["x_%d" % (j,)], df["x_%d" % (i,)], "ro", alpha=0.5)

        # plt.show()
        
