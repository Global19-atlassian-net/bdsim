# Block diagram simulation

This Python package simulates a dynamic system conceptualized in block diagram form, but represented in terms of Python class and method calls.  Unlike Simulink or LabView we write Python code rather than drawing boxes and wires.  Wires can communicate any Python type such as scalars, lists, numpy arrays, other objects, and even functions.

Consider the canonic block diagram

![block diagram](figs/bd1-sketch.png)

which we can express concisely with `bdsim` as

```python
demand = s.WAVEFORM(wave='square', freq='2', pos=(0,0))
sum = s.SUM('+-', pos=(1,0))
gain = s.GAIN(2, pos=(1.5,0))
plant = s.LTI_SISO(0.5, [1, 2], name='plant', pos=(3,0))
scope = s.SCOPE(pos=(4,0))
    
s.connect(demand, sum[0])
s.connect(plant, sum[1])
s.connect(sum, gain)
s.connect(gain, plant)
s.connect(plant, scope)
```
where the red block annotations in the diagram have become names of instances of object that represent the blocks.  

Wires can also be named, though that is less useful, since the value of a wire in uniquely determined by the output port that drives it.  In `bdsim` all wires are point to point, a *one-to-many* connection is implemented by *many* wires.

Ports are designated using Python indexing and slicing notation, for example `sum[0]`.  Whether it is an input or output port depends on context.  Blocks are connected by `connect(from, to)` so an index on the first argument refers to an output port, while on the second (or subsequent) arguments refers to an input port.  If a port has only a single port then no index is required.

A bundle of wires can be denoted using slice notation, for example `block[2:4]` refers to ports 2 and 3.  When connecting slices of ports the number of wires in each slice must be consistent.  You could even do a cross over by connecting `block1[2:4]` to `block2[5:2:-1]`.

Remember that wires can hold scalar or vector values.  The first index refers to the port. A second index, if present is used to index into a vector value on the port, eg. `block1[2,:2]` refers to the first two elements of a vector on port 2 of block1.  This notation reduces the need for multiplexer and demultiplexer blocks.

We could also write the above more compactly using implicit connections described by the assignement operator

```python
s = Simulation()
plant = s.LTI_SISO(1, [1 2], name='plant')
demand = s.WAVEFORM(type='square', freq='2')
scope = s.SCOPE()
gain = s.GAIN(value=2)

gain[0] = s.SUM('+-', demand, plant)
plant[0] = gain
scope[0] = plant
```
but note that we need to explicitly include the ports on the left-hand side of the expressions (since we cannot overload the assignment operator in Python).

Even more concisely

```python
s = Simulation()
plant = s.LTI_SISO(0.5, [1, 2], name='plant')
demand = s.WAVEFORM(type='square', freq='2')
scope = s.SCOPE()

plant[0] = s.SUM('+-', demand, plant) * s.GAIN(value=2)
scope[0] = plant
```

Whatever way we choose to express our model, and a mixture of ways is perfectly OK, the model is expressed in terms of Block and Wire objects.  The output port of a block is a set of wires connecting to input ports, and each Wire has reference to the start and end blocks. We can see this representation by

```
s.report()
```

We can also turn into something like a real block diagram using GraphViz to produce a .dot file

```python
s.dotfile('demo.dot')
```

which we can turn into a graphic using `neato`

```shell
% neato -Tpng demo.dot demo.png
```

![output of neato](figs/bd1.png)

To run the simulation and save the results 

```python
s.record(demand, plant)
out = s.run(5, dt=0.1)
```
which requests to record the outputs of the `demand` and `plant` blocks, simulate for 5s (using the default variable step RK45 solver) and output values at least every 0.1s.

The result `out` is effectively a structure with elements

- `t` the time vector: ndarray, shape=(M,)
- `x` is the state vector: ndarray, shape=(M,N)
- `xnames` is a list of the names of the states corresponding to columns of `x`, eg. "plant.x0"

In this case there are also elements due to the `record` method:

- `block0` is the output of the waveform generator: ndarray, shape=(M,)
- `plant` is the output of the plant: ndarray, shape=(M,)

Note that the names comes from the names of the blocks, because we didn't assign a name to the WAVEFORM block it gets a default name from the unique block id. 


wires can be any valid python type, scalars, lists, objects, even functions!

# Writing your own block

Your block must belong to one of these categories which are subclasses of the `Block` superclass.

- a **Source** which has no inputs, and creates a signal as a function of simulation time
- a **Sink** which has no outputs, and performs some display or recording function
- a **Function** which has inputs *and* outputs but has no internal state variables.  The output is a direct function of the input.
- a **Transfer** which has inputs and outputs and some internal state variables.  The output is not a direct function of the input, that is, it is a *proper* transfer function or a statespace system where D=0.

All blocks are described by classes defined in Python modules residing in the `blocks` folder. Suitably named classes defined in any module are dynamically added as methods of the `Simulation` class. For example a 
class called `_MyBlock` will be available as a method called `MYBLOCK` which invokes the object constructor.

Each class:

- has a name that begins with an underscore.  The corresponding method is capitalized and without the underscore.
- must subclass one of `Source`, `Sink`, `Function` or `Transfer`.
- must provide a constructor that handles keyword arguments passed from the call to `s.MYBLOCK()` where `s` is an instance of the `Simulation` class.  You need to ensure that argument names don't clash with those already in use by the superclasses.
- constructor must call the superclass constructor with keyword arguments
- constructor must implement certain other methods depending on which category it belongs to.
- can add attributes to the instance to enable the operation of your block.  You need to ensure that attribute names don't clash with those already in use by the superclasses.

To create your own block create a file `blocks/myblock.py` and adapt one of the templates below.  Methods in your class have access to useful attributes including:


|  attribute  |  purpose  |
|-------------|-----------|
|nin          | number of input ports to the block  |
|nout         | number of output ports from the block  |
|nstates      | number of state variables in the block  |
|sim          | reference to Simulation instance  |
|sim.T        | maximum simulation time  |
|sim.t        | current simulation time  |
|sim.graphics | graphics enabled (bool)  |

## Source


```
from bdsim.blocks import *

class _MyBlock(Source):
	
	def __init__(self, param1=defautl1, param2=default2, **kwargs):
		super().__init__(**kwargs)
		
		self.param1 = param1
		self.param2 = param2

	def output(self, t):
		# return a list with self.nout elements representing the output ports 
		# of the block. This is a function of the passed time `t` and 
		# the parameters passed to the constructor.	
		
	def start(self):
		# simulation is beginning, open files etc.
		
	def done(self):
		# simulation is complete, close files etc.
```


## Sink


```
from bdsim.blocks import *

class _MyBlock(Sink):
	
	def __init__(self, param1=defautl1, param2=default2, **kwargs):
		super().__init__(**kwargs)
		
		self.param1 = param1
		self.param2 = param2

	def step(self):
		# the values of the inputs to the block are available in the list
		# self.inputs which has self.nin elements.
		
	def start(self):
		# simulation is beginning, open files etc.
		
	def done(self):
		# simulation is complete, close files etc.
		
```
If a sink performs graphics it should respect the boolean `self.sim.graphics`.


## Function


```
from bdsim.blocks import *

class _MyBlock(Function):
	
	def __init__(self, param1=defautl1, param2=default2, **kwargs):
		super().__init__(**kwargs)
		
		self.param1 = param1
		self.param2 = param2
		
	def output(self, t):
		# return a list with self.nout elements representing the output ports 
		# of the block. This is a function of the passed time `t`, the 
		# parameters passed to the constructor, and the inputs to the block 
		# which are available in the list self.inputs which has self.nin elements.
	
	def start(self):
		# simulation is beginning
			
	def done(self):
		# simulation is complete
		
```

## Transfer


```
from bdsim.blocks import *

class _MyBlock(Transfer):
	
	def __init__(self, param1=defautl1, param2=default2, **kwargs):
		super().__init__(**kwargs)
		
		self.param1 = param1
		self.param2 = param2
		
	def output(self, t):
		# return a list with self.nout elements representing the output ports 
		# of the block. This is a function of the state self.x
	
	def deriv(self):
		# return an ndarray with self.nstate elements containing the derivative,
		# computed as a function of the current state self.x and current inputs
		# in self.inputs
	
	def start(self):
		# simulation is beginning
			
	def done(self):
		# simulation is complete
		
	def update(self):
		# the values of the inputs attribute are valid
		# inputs is list representing the input ports to the block
```




