
# Table of Contents

1.  [smp\_graphs](#org08e9199)
    1.  [smp what?](#org6ef7e63)
    2.  [Installation](#org1e8d782)
    3.  [Examples](#orga1cc7a0)
    4.  [Design considerations](#orga94b695)
        1.  [Read/write: integrate input from and output to ROS, OSC, &#x2026;](#org060b17d)
        2.  [Base block](#org6bdf688)
    5.  [Notes](#orgda21f47)
2.  [API documentation](#org53e36e7)



<a id="org08e9199"></a>

# smp\_graphs


<a id="org6ef7e63"></a>

## smp what?

This is an experimental framework for specifying sensorimotor learning
experiments as a computation graph. The nodes represent functions
which consume and produce signals which are the function's inputs and
outputs and are represented as edges in the graph. This approach
reflects the necessity of identifying design patterns in such
experiments and capturing them in such a way that they can be reused
across many different experiments. This idea is not new and smp\_graphs
simply represents the commitment to my own characteristic
decompositions of the problems into reusable elements and patterns of
arrangement. Of course there is no fundamental intrinsic restriction
to sensorimotor learning so the framework can be used for any kind of
computation flow. There are many examples of similar environments out
there some of which I have used extensively and which acted as
inspiration to my own design here. These are for example mdp,
pylearn2, blocks, procgraph, keras, supercollider, puredata,
gstreamer, gnuradio, and simulink / labview.

The framework exists inside the larger sensorimotor primitives (smp)
ecosystem and it implements only (mostly) framework specific functions
of graph handling, manipulation, and execution. The actual algorithms
are kept separately in a library called [smp\_base](https://github.com/x75/smp_base). Specific block
implementations make use of other *smp\_\** libs, such as [smp\_sys](https://github.com/x75/smp_sys)
(robots &isin; systems) and other 3rd party python libs, see
dependencies.

An experiment's graph is specified in a configuration file written
down as a Python dictionary. The configuration is then loaded by the
general experimental shell 'experiment.py'. The assignment of values
to a node's inputs is part of the graph configuration and is either a
constant computed at configuration time or another block's output
provided on a globally shared bus structure. Every block writes it's
outputs to that bus, where it can be picked up and used by any other
block, including the block itself, allowing recurrent connections.

The graph-based representation provides good separation of the
experiment's algorithm and the implementation. The project is
work-in-progress and stilll moving. In principle the configuration is
independent of this specific implementation and could also be used
to generate or assemble an implementation in another language or
particular hardware etc. The most important drawback right now is the
verbosity of the configuration dictionary but clearly this can also be
optimized to allow very terse formulations.


<a id="org1e8d782"></a>

## Installation

Depends on 

-   External: numpy, scipy, networkx, pandas, matplotlib, sklearn, seaborn, rlspy, jpype/infodynamics.jar, mdp/Oger, ros, pyunicorn, hyperopt, cma
-   smp world: smp\_base, smp\_sys

smp stuff is 'installed' by cloning the repositories and setting the PYTHONPATH to include the relevant directories like

    export PYTHONPATH=/path/to/smp_base:/path/to/smp_graphs:$PYTHONPATH

Simulators and robots

-   stdr simulator (FIXME: fetch config from smq)
-   lpzrobots
-   sphero\_ros
-   MORSE

TODO

-   prepare requirements.txt: numpy, scipy, sklearn scikit-learn,
    seaborn, fix: rlspy from git, jpype = jpypex, link infodynamics,
    mdp = MDP, fix Oger from git, cma is cma, add: colorcet, pyunicorn
    deps: weave, igraph/jgraph
-   clean path for running without ROS


<a id="orga1cc7a0"></a>

## Examples

Go into smp\_graphs/experiments directory where experiments are run from

    cd smp_graph/experiments

Run some example configurations like

    # example_default2.py, test most basic functionality with const and random blocks
    python experiment.py --conf conf/example_default2.py

    # example_loop.py, test the graph modifying loop block
    python experiment.py --conf conf/example_loop.py

    # example_hierarchical.py, test hierarchical composition loading a subblock from
    #                             an existing configuration
    python experiment.py --conf conf/example_hierarchical.py

    # example_loop_seq.py, test dynamic loop instantiating the loopblock
    #                         for every loop iteration
    python experiment.py --conf conf/example_loop_seq.py

and so on. Have a look at the files in the 'experiments/conf/'
directory.

\FIXME Provide the data for the examples as a .zip file on osf


<a id="orga94b695"></a>

## Design considerations

This is a dynamic list which I use both to sketch (TODO) and document
(DONE) the requirements and issues of the framework. Items that are
already implemented should trickle down to the bottom as they
consolidate, while the hottest items are at the top. Otherwise the
order of items is random.

-   misc stuff: immediate or small
    -   expansion: mean/var coding, log coding, res expansion, mdp nonlin expansion (mdp block containing entire flow?)
    -   systems: add real systems with async exec foo: stdr, puppy, sphero
    -   fix infth, xcorr, RecurrencePlot normalization via parameter switch
    -   fix parameters for infth embeddings and RecurrencePlot embedding
        the image can be analyzed further as an image
    -   make recurrenceanalysis separate block, independent of plotting so
    -   general clean up / function refactoring
    -   x fix table attribute storage: pandas silently replaces the table object on reallocation, metadata does not propagate. store attributes at the end of experiment
    -   x dump exec configuration
    -   x dump plain config: as file, as log table vlarray string
    -   x fix config dump via nxgraph
    -   x separate header/footer for full config file to remove code
        replication and clutter

-   power blocks, the real stuff
    -   block\_expand: expansion blocks: random non-linear expansion (mdp), reservoir expansion, soft-body expansion
    -   block\_repr: representation learning, unsupervised learning, input decomposition
    -   block\_func: function approximation blocks
    -   x block\_meas: measurement / analysis blocks

-   documentation
    -   make more documentation for all existing smp\_graphs configs
    -   do the documentation
    -   doc: all the logic
    -   doc: inputs spec, outputs spec, slicespec, plotinput spec, mixed blocksizes?

-   predictive processing
    -   prediction
    -   can we map top down - bottom up flow nicely into the graph? think
        yes.
    -   make pp mapping explicit: single sm-interface struct with 3
        layers [raw input, error, prediction], see
        <doc/img/agent-world-interface-sm.pdf>

-   scheduling / phases
    -   be able to prescribe definite or variable-dependent sequences of
        development
    -   cache results of each stage by augmenting the log with computed
        results

-   don't need to copy outputs of subgraph because the bus is global,
    FIXME consider making hierarchical bus identifiers or assert all
    keys and subkeys uniq

-   loop block
    -   test looping over more complex blocks to evaluate / grid\_search /
        hpo real hyper params
    -   special hierarchical block with additional spec about how often
        and with which variations to iterate the subgraph
    -   x sequential loop for running block variations e.g hyperopt or evo,
        for now assert blocksize = numloops, one loop iteration returns
        one data point
    -   x parallel loop within graph, modify graph. this is different
        from dynamic containment

-   sync / async block execution
    -   x research: rate/blocksize/ibuf/obuf,
    -   sequencing (sequential execution) of subgraphs, aka execution phases
    -   run multiple topblocks and pass around the data
    -   execution timing:
        -   blocksize = rate, at which point during counting should the block be executed
        -   input shape: input buffer expected by the block, step wrapper takes care of collecting incoming data which is faster than the block's rate
        -   output shape: output buffer at every execution step: arbitrary but fixed
    -   async process / worker thread spawning
    -   spawn/fork threads as worker cloud, can be sequential loop or
        custom parallel version
    -   ros style callback inputs as usual simple buffer to local var copy

-   dynamic growth
    -   grow the acutal execution graph, take care of logging, timebase
        for block step indexing

-   models, learning, fitting, representing, decomposing, expanding
    -   models
    -   make learners / models and robots
    -   think of it as layers: model learners, expansions,
        representations, predictive residual layer (e.g. mean/var layer)
    -   glue: mean/var coder, log coder, nonlin exp coder, res exp coder
        (build smp\_recurrence\_plot via res exp + som)

-   analysis
    -   check normalization in infth comp and correlation (switching argument)
    -   x RecurrencePlot: fix rp examples
    -   x cross-correlation
    -   x mutual information / information distance
    -   x transfer entropy / conditional transfer entropy
    -   x multivariate vs. uni-/bivariate

-   graph issues
    -   flat execution graph for running + plotting vs. structured configuration graph for readability and preservation of groupings
    -   graph: lazy init with dirty flag that loops until all dependencies are satisfied
    -   graph: execution: sequencing / timeline / phases
    -   graph: finite episode is the wrong model, switch to infinite
        realtime process, turn on/off logging etc, only preallocate
        runtime buffers
    -   graph: "sparse" logging
    -   graph: run multiple topblocks and pass around the data
    -   graph / subgraph similarity search and reuse
        -   graph: store graph search results to save comp. time
        -   x graph: fix recursive node search in graph with subgraphs (nxgraph\_node\_by\_id\_&#x2026;)
    -   / graph: proper bus structure with change notifications and multidim
        signalling (tensor foo) depends:mdb
    -   introduced dict based Bus class which can do it in the future
    -   x graph: multi-dimensional busses (mdb)
    -   x graph: execution: sliding window analysis mode with automatic, depends:mdb,ipl
        subplot / dimstack routing,
    -   x graph: input / output specs need to be dicts (positional indexing gets over my head)
    -   x two-pass init: complete by putting input init into second pass

-   / step, blocksize, ibuf
    -   min blocksize after pass 1
    -   how to optimize if min(bs) > 1?
    -   x kinesis rate param for blocks = blocksize: introduced 'rate' parameter
    -   x make prim blocks blocksize aware
    -   x check if logging still works properly
    -   x basic blocksize handling

-   / networkx
    -   fix hierarchical graph connection drawing
    -   / put entire runtime graph into nx.graph with proper edges etc
    -   x standalone networkx graph from final config
    -   x graphviz
    -   x visualization

-   / plotting
    -   properly label plots
    -   put fileblock's input file into plot title / better plottitle in
        general
    -   proper normalization
    -   proper ax labels, ticks, and scales
    -   x dimstack: was easy, kinda ;)
    -   x display graph + bus ion
    -   x saveplots
    -   x dimstack plot vs. subplots, depends:mdp
    -   x interactive plotting (ipl): pyqtgraph / in step decorator?
        -   works out of the box when using small exec blocksize in plot block

-   x hierarchical composition
    -   x changed that: hierarchical from file, from dict and loopblocks all
        get their own nxgraph member constructed an loop their children on step()
    -   x two ways of handling subgraphs: 1) insert into flattened
        topgraph, 2) keep hierarchical graph structure: for now going
        with 1)
    -   x think about these issues: outer vs. inner numsteps and blocksizes,
        how to get data in and out in a subgraph independent way: global
        bus solves i/o, scaling to be seen
    -   x for now: assert inner numsteps <= outer numsteps, could either
        enforce 1 or equality: flattening of graph enforces std graph
        rule bs\_earlier\_lt\_bs\_later
    -   x use blocks that contain other graphs (example\_hierarchical.py)

-   x logging
    -   x graph: windowed computation coupled with rate, slow estimates sparse logging, bus value just remains unchanged
    -   x block: shape, rate, dt as logging table attributes
    -   x std logging OK
    -   x include git revision, initial and final config in log
    -   x profiling: logging: make logging internal blocksize

-   dict printing for dynamic reconf inspection
    -   fix OrderedDict in reconstructed config dicts
    -   x print\_dict print compilable python code?
    -   x basic formatted dict printing. issues: different needs in
        different contexts, runtime version vs. init version. disregard
        runtime version in logging and storage

-   experiments to build
    -   expr: use cte curve for EH and others, concise embedding
    -   expr: windowed audio fingerprinting
    -   expr: fm beattrack
    -   expr: make full puppy analysis with motordiff
    -   expr: make target frequency sweep during force learning and do sliding window analysis on shifted mi/te
    -   expr: map an sm manifold from logdata via scattermatrix or dimstack, sort the axes by pairwise MI/infodist
    -   x expr: puppy scatter with proper delay: done for m:angle/s:angvel
    -   x expr: make windowed infth analysis: manifold\_timespread\_windowed.py


<a id="org060b17d"></a>

### Read/write: integrate input from and output to ROS, OSC, &#x2026;

-   x basic simulated robots: pointmass, simplearm, bha
-   x ros systems: STDRCircular, LPZBarrel
-   OSC in/out?


<a id="org6bdf688"></a>

### Base block

The basic block class is Block2. Blocks come in two fundamental
flavours, composite blocks and primitive blocks. Composite ones are
composed of other composite or primitive blocks. An experiment
consists at the top level of a single block with a 'graph' attribute
that contains all subordinate blocks. When the experiment is run, we
just iterate over the range from 1 up to the top level 'numsteps'
parameter and call the .step function of the top block, which in turn
walks the graph and calls each node's step function.

Composite blocks are Block2, LoopBlock2, and SeqLoopBlock2. Block2 can
be used to include an entire static subgraph specified either as a
dict directly in the configuration, or as a filename that points to
any other configuration file. At init time, the configuration
dictionary is converted into the execution graph, which as a networkx
graph, and whose nodes' attributes contain the original configuration
plus the runtime block instance.


<a id="orgda21f47"></a>

## Notes

This is approximately my 5th attempt at defining a framework for
computational sensorimotor learning experiments. Earlier attempts
include

-   **smp\_experiments**: define configuration as name-value pairs and
    some wrapping with python code, enabling the reuse of singular
    experiments defined elsewhere in an outer loop doing variations
    experiment variations for statistics or optimization
-   **smpblocks**: first attempt at using plain python config files
    containing a dictionary that specifies a graph of computation nodes
    (blocks) and their connections. granularity was too small and
    specifying connections was too complicated
-   **smq**: in [smq](https://github.com/x75/smq) I tried to be more high-level, introducing three specific and
    fixed modules 'world', 'robot', 'brain'. Alas it turned out that
    left us too inflexible and obviosuly couldn't accomodate any
    experiments deviating from that schema. Is where we are ;)


<a id="org53e36e7"></a>

# API documentation

