#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Components of the simulation system, namely blocks, wires and plugs.
"""

import numpy as np


                
class Wire:
    """
    A Wire object connects two block ports.  A Wire has a reference to the
    start and end ports.
    """
                
                
    def __init__(self, start=None, end=None, name=None):
        self.name = name
        self.id = None
        self.start = Plug(start)
        self.end = Plug(end)
        self.value = None
        self.type = None

    @property
    def info(self):
        print("block:")
        for k,v in self.__dict__.items():
            print("  {:8s}{:s}".format(k+":", str(v)))
            
    def __repr__(self):
        
        # def range(x):
        #     if isinstance(x,slice):
        #         return "{:d}:{:d}".format(x.start, x.stop)
        #     else:
        #         return "{:d}".format(x)
        # if self.id is None:
        #     sid = ""
        # else:
        #     sid = "-{:d}".format(self.id)            
        # s = "wire{:s}: {:s}[{:s}] --> {:s}[{:s}]".format(sid, type(self.start.block).__name__, range(self.start.port), type(self.end.block).__name__, range(self.end.port))
        

        return str(self) + ": " + self.str2
    
    @property
    def str2(self):
        return "{:s}[{:d}] --> {:s}[{:d}]".format(str(self.start.block), self.start.port, str(self.end.block), self.end.port)
    
    def __str__(self):
        s = "wire."
        if self.name is not None:
            s += self.name
        elif self.id is not None:
            s += str(self.id)
        else:
            s += '??'
        return s

# ------------------------------------------------------------------------- # 

class Plug:
    """
    Plugs are on the end of each wire, and connect a Wire to a specific port on
    a Block.
    """
    def __init__(self, bp):
        self.block = bp[0]
        self.port = bp[1]
        self.dir = ''
        
    def __mul__(left, right):
        pass
        # plug * plug
        # plug * block
        # make connection, return a plug
        
    def __repr(self):
        return self.block + "[" + self.port + "]"
    
# ------------------------------------------------------------------------- # 

class Block:
    """
    A block object is the superclass of all blocks in the simulation environment.
    """
    
    def __init__(self, blockclass=None, name=None, pos=None, **kwargs):
        #print('Block constructor'
        self.name = name
        self.pos = pos
        self.id = None
        self.out = []
        self.inputs = None
        self.updated = False
        self.shape = 'block' # for box
        self.blockclass = blockclass
        
        # self.passthru
        

    @property
    def info(self):
        print("block: " + type(self).__name__)
        for k,v in self.__dict__.items():
            print("  {:8s}{:s}".format(k+":", str(v)))

        
    def __getitem__(self, port):
        return (self, port)
    
    def __setitem__(self, i, port):
        pass
    
    def __mul__(left, right):
        pass
        # block * block
        # block * plug
        # make connection, return a plug
        
    def __str__(self):
        s = self.type + '.'
        if self.name is not None:
            s += self.name
        elif self.id is not None:
            s += 'block' + str(self.id)
        else:
            s += '??'
        return s
    
    def __repr__(self):
        return self.fullname
    
    @property
    def fullname(self):
        return self.blockclass + "." + str(self)
    
    def reset(self):
        if self.nin > 0:
            self.inputs = [None] * self.nin
        self.updated = False
        
    def add_out(self, w):
        self.out.append(w)
    
    def setinput(self, wire, val):
        """
        Receive input from a wire
        
        :param wire: Incoming wire
        :type wire: Wire
        :param val: Incoming value
        :type val: any
        :return: If all inputs have been received
        :rtype: bool

        """

        # stash it away
        self.inputs[wire.end.port] = val

        # check if all inputs have been assigned
        if all([x is not None for x in self.inputs]):
            self.updated = True
            #self.update()
        return self.updated
    
    def start(self, **kwargs):  # begin of a simulation
        pass
    

    def check(self):  # check validity of block parameters at start
        pass
    
    def done(self, **kwargs):  # end of simulation
        pass
    
    def step(self):  # valid
        pass
        
class Sink(Block):
    """
    A Sink is a subclass of Block that represents a block that has inputs
    but no outputs. Typically used to save data to a variable, file or 
    graphics.
    """
    
    blockclass = "sink"
    
    def __init__(self, **kwargs):
        #print('Sink constructor')
        super().__init__(blockclass='sink', **kwargs)
        self.nin = 1
        self.nout = 0
        self.nstates = 0


class Source(Block):
    """
    A Source is a subclass of Block that represents a block that has outputs
    but no inputs.  Its output is a function of parameters and time.
    """
    blockclass = "source"
    
    def __init__(self, **kwargs):
        #print('Source constructor')
        super().__init__(blockclass='source', **kwargs)
        self.nin = 0
        self.nout = 1
        self.nstates = 0
        
class Transfer(Block):
    """
    A Transfer is a subclass of Block that represents a block with inputs
    outputs and states. Typically used to describe a continuous time dynamic
    system, either linear or nonlinear.
    """
    blockclass = "transfer"
    
    def __init__(self, **kwargs):
        #print('Transfer constructor')
        super().__init__(blockclass='transfer', **kwargs)
        
    def reset(self):
        super().reset()
        self.x = self.x0
        return self.x
    
    def setstate(self, x):
        self.x = x[:self.nstates] # take as much state vector as we need
        return x[self.nstates:]   # return the rest
    
    def getstate(self):
        return self.x0
    
    def check(self):
        assert len(self.x0) == self.nstates, 'incorrect length for initial state'
                
    

class Function(Block):
    """
    A Function is a subclass of Block that represents a block that has inputs
    and outputs but no state variables.  Typically used to describe operations
    such as gain, summation or various mappings.
    """
    blockclass = "function"
    
    def __init__(self, **kwargs):
        super().__init__(blockclass='function', **kwargs)
        self.nstates = 0