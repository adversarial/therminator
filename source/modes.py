# Therminator - thermostat emulator to test functionality
# MultiStageUnit.run(stage, mode) abstracts channeler.py to modes of thermostats 
# Copyright (C) 2025 adversarial

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

from channeler import channel_manager

from uasyncio import sleep_ms as async_sleep_ms, CancelledError
from enum import Enum, Flag, auto
from source.log import log

import uasyncio

class UnitType(Enum):
    UNSPECIFIED = 0
    FURNACE = 1
    AC = 2
    HP = 3

class UnitMode(Flag):
    UNSPECIFIED = auto()
    HEATING = auto()
    AUX = auto()    # out of scope 
    COOLING = auto()

    def get_stage_types(self):
        match self:
            case UnitMode.HEATING:
                return Terminal.HEATING_STAGES.keys()
            case UnitMode.COOLING:
                return Terminal.COOLING_STAGES.keys()

class Terminal:

    class TerminalType(Flag):
        R_24V = auto()
        W = auto()
        W_2 = auto()
        W_3 = auto()
        AUX = auto()
        Y = auto()
        Y_2 = auto()
        Y_3 = auto()
        G = auto()
        O = auto()
        B = auto()
        
    class Color(Flag):
        RED = auto()
        WHITE = auto()
        GREEN = auto()
        YELLOW = auto()
        BROWN = auto()
        BLACK = auto()
        ORANGE = auto()
        BLUE = auto()
        GREY = auto()
        CUSTOM = auto()

        def to_color(self):
            return DEFAULT_TERMINAL_COLORS[self]
    
    HEATING_STAGES = { TerminalType.W: 1, TerminalType.W_2: 2, TerminalType.W_3: 3 }
    COOLING_STAGES = { TerminalType.Y: 1, TerminalType.Y_2: 2, TerminalType.Y_3: 3 }
    STAGES = HEATING_STAGES | COOLING_STAGES

    def __init__(self, color: Color,
                 type: TerminalType,
                 channel: int,
                 mode = UnitMode.UNSPECIFIED, 
                 state: bool = False):
        self.color = color
        self.ttype = type
        self.mode = mode
        self._state = state

    def __contains__(self, b):
        return b in self.ttype

    def state(self, state = None):
        if state is not None:
            self._state = state
            
        else:
            return self._state

    def to_mode(self):
        if self.ttype in self.HEATING_STAGES:
            return UnitMode.HEATING
        elif self.ttype in self.COOLING_STAGES:
            return UnitMode.COOLING
        else:
            return UnitMode.UNSPECIFIED

    def to_stage(self):
        return self.STAGES.get(self.ttype) or None

class TerminalArray:

    def __init__(self, terminals):
        self.terminals = terminals

    def __contains__(self, b):
        return b in [t.type for t in self.terminals]
    
    def __iter__(self):
        return iter(self.terminals)
    
    def get(self, ttype):
        return next(t for t in self.terminals if ttype in t) or None
    
    def get_channel(self, ttype) -> int:
        for i, t in enumerate(self.terminals):
            if ttype == t.ttype:
                return i
        raise ValueError(f'No channel of type {ttype.name} in {[t.ttype.name for t in self.terminals]} ')
        
    def set(self, ttypes, value = 1):
        for tt in ttypes:
            if (t := self.get(tt)):
                t.state(value)

    def set_channel(self, channel, value):
        self.terminals[channel].state(value)

    def get_stage_terminals(self, mode):
        raise NotImplementedError

# for testing without loading ini 
# default
two_stage_heat_terminals = TerminalArray((Terminal(Terminal.Color.RED, Terminal.TerminalType.R_24V, 0), 
                             Terminal(Terminal.Color.WHITE, Terminal.TerminalType.W, 1),
                             Terminal(Terminal.Color.BROWN, Terminal.TerminalType.W_2, 2),
                             Terminal(Terminal.Color.GREEN, Terminal.TerminalType.G, 3)))

default_terminals = two_stage_heat_terminals

class MultiStageUnit:
    
    def __init__(self, 
                 name,
                 unit_type = UnitType.UNSPECIFIED,
                 mode = UnitMode.UNSPECIFIED,
                 terminals = default_terminals, 
                 mode_cooldown_ms = 15*60*1000):
        
        self._unit_type = unit_type 
        self._mode = mode       # this should not be changed outside of init and _change_mode()
        self.name = name
        self._terminals = terminals
        self._mode_cooldown_ms = mode_cooldown_ms

        self._stage = 0
        
        #self._num_stages = self.max_stage()
        self._run_lock = uasyncio.Semaphore(1)
        self._stage_lock = uasyncio.Semaphore(1)
        self._mode_lock = uasyncio.Semaphore(1)

# change stage with small delay in increases (board will interpet simultaneously connected terminals as 1->long delay->2)
    async def _change_stage(self, stage, cooldown_ms = 750):
        try:
            async with self._stage_lock:
                if stage == 0:
                    self._terminals.set(Terminal.STAGES.keys(), 0)
                    return 
                elif stage == self._stage:
                    log(f'Stage request is same as current stage {stage}.')
                    return

                applicable_stages = Terminal.HEATING_STAGES if self._mode == UnitMode.HEATING else Terminal.COOLING_STAGES if self._mode == UnitMode.COOLING else None
                stage_terminals = sorted([s for s in self._terminals if s.ttype in applicable_stages], 
                                         key = lambda s: s.to_stage())
                # for each stage in 1 .. stage, check there is an existing terminal
                if not all(any([s == t.to_stage() for t in stage_terminals]) for s in range(1, stage)):
                    raise ValueError(f'Invalid stage {stage} provided. Available stages: {[s.ttype for s in stage_terminals]}')
                
                # stage_terminals is 0-indexed list of available stages
                # increasing all stages below, requires small cooldown
                # ie from stage 1 to stage 3:
                if stage > self._stage:
                    for i in range(self._stage, stage): # [1, 2] stage_terminals[1] = stage 2, stage_terminals[2] = s3
                        stage_terminals[i].state(1)
                        await async_sleep_ms(cooldown_ms)
                # disable all stages above
                # ie from s3 to 0 (off):
                # indices = [2, 1, 0] -> term[2] = s3, term[1] = s2, term[0] = s1 
                elif stage < self._stage:
                    for i in reversed(range(stage, self._stage)):
                        stage_terminals[i].state(0)

                self._stage = stage
                return True
        except CancelledError as e:
            log(f'Stage change from {self._stage} to {stage} cancelled.')
            raise e

# init off current mode, wait for cooldown if not already off, change to desired mode and stage  
    async def _change_mode(self, mode, initial_stage = 0, cooldown_ms = None):
        try:
            async with self._mode_lock:
                match mode:
                    case self._mode:
                        log('Mode change: matches current mode.')
                        return mode
                    case UnitMode.HEATING | UnitMode.COOLING | UnitMode.AUX:
                        pass
                    case _:
                        raise ValueError('Mode change: invalid mode given.')
                # current mode off
                await self._change_stage(0)
                # if starting from off then no need to wait
                if self._mode != UnitMode.UNSPECIFIED:
                    await async_sleep_ms(cooldown_ms or self._mode_cooldown_ms)
                # start new mode
                self._mode = mode
                await self._change_stage(initial_stage)
        except CancelledError as e:
            log(f'Mode change from {self._mode.name} to {mode.name} cancelled.')
            raise e

# public function to control device
    async def run(self, stage, mode = UnitMode.UNSPECIFIED):

        async with self._run_lock:
            if mode == UnitMode.UNSPECIFIED:
                if self._mode == UnitMode.UNSPECIFIED:
                    raise ValueError(f'No mode has been set for this MultiStageUnit.')
                else:
                    mode = self._mode
            await self._change_mode(mode, stage)

    def has_stage(self, stage, mode = UnitMode.UNSPECIFIED):
        raise NotImplementedError
    
    def max_stage(self, mode = UnitMode.UNSPECIFIED):
        for t in self._terminals:
            max_stage = max(t.ttype.to_stage(), max_stage or 0)
        return max_stage

    def get_type(self):
        return self._unit_type

DEFAULT_TERMINAL_COLORS = {
    Terminal.Color.RED: '#E3170D',
    Terminal.Color.WHITE: '#FFF8DC', 
    Terminal.Color.GREEN: '#32CD32',
    Terminal.Color.YELLOW: '#FFFF4d',
    Terminal.Color.BROWN: '#B98A5B',
    Terminal.Color.BLACK: '#000000',
    Terminal.Color.ORANGE: '#FF8000',
    Terminal.Color.BLUE: '#0000FF',
    Terminal.Color.GREY: '#C9C9C9',
    Terminal.Color.CUSTOM: '#68f9d8'
}