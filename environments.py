# -*- coding: utf-8 -*-
"""
Created on Thu Jan 18 12:59:20 2018

@author: gamer
"""
from ale_python_interface import ALEInterface
import utils.env as utils
import numpy as np
import collections
import gym

OPTIONS = {"IMAGES_SIZE":(80,80)}
CROP = {"breakout":(32,10,8,8)}

class ALE(ALEInterface):
    
    def __init__(self,game_name, num_frames= 4, skip_frames = 2, render=True):
        
        super(ALE, self).__init__()    
        
        self.crop = CROP[game_name]
        self.num_frames = num_frames
        self.skip_frames = skip_frames
        self.load_rom(game_name,render)
        self.load_params()
    
    def load_params(self):
        
        self._actions_raw = self.getMinimalActionSet().tolist()
        self.action_space = Discrete(len(self._actions_raw))
        self.observation_space = Continuous(0,1,OPTIONS["IMAGES_SIZE"]+(self.num_frames,))
        self._memory = collections.deque([],self.num_frames)
        self._start_lives = self.lives()
        self._current_state = np.zeros(self.observation_space.shape) 
        
        while len(self._memory)<self.num_frames:
            self.capture_current_frame()
    def load_rom(self,rom_file,render):

        self.setInt(str.encode('random_seed'), 123)
        self.setFloat(str.encode('repeat_action_probability'), 0.0)        
        self.setBool(str.encode('sound'), False)
        self.setBool(str.encode('display_screen'), render)
        self.loadROM(str.encode("./roms/"+utils.game_name(rom_file)))
        
    def capture_current_frame(self):
        up,down,left,right = self.crop
        self._memory.append(utils.process_frame(
                self.getScreenRGB()[up:-down,left:-right],
                            OPTIONS["IMAGES_SIZE"])
                            )
    
    def get_current_state(self):
        
        return np.concatenate(self._memory,axis = -1)
    
    def step(self,action):
        
        
        reward = 0
        assert action in range(self.actions_n), "Action not available"
        
        for i in range(self.num_frames-1):
            reward = max(reward, self.act(self.actions_set[action]))
            
        
        state = self.get_current_state()
        
        return state, reward, self.lives() != self._start_lives

    def reset(self):
        self.reset_game()
        self.load_params()

    def clone(self):
        env = self.cloneSystemState()
        env.params()
        return env


    def act(self,action):

        res = 0
        for _ in range(self.skip_frames):
            res = max(res,super(ALE,self).act(action))

        self.capture_current_frame()

        return res

import skvideo
import skvideo.io
import skimage

class GRID(object):
    
    def __init__(self, grid_size=16, max_time=500, square_size = 2):
        

        self.grid_size = grid_size

        self.max_time = max_time
        
        self.square = square_size

        self.board = np.zeros((self.grid_size,self.grid_size))

        # recording states
        self.to_draw = np.zeros((max_time+2, self.grid_size, self.grid_size,1))
        
        
        self.action_space = Discrete(4)
        
        self.observation_space = Continuous(-1,1,(self.grid_size, self.grid_size,2))

        self.reset()
        
    def draw(self,e):
        
        video = np.zeros((len(self.to_draw),self.grid_size, self.grid_size,3)).astype('uint8')
        
        #Turns the mouse cell to red        
        video[self.to_draw[:,:,:,0]>0,0] = 255

        #Turns the cat position to white
        video[self.to_draw[:,:,:,0]<0,:] = 255

        skvideo.io.vwrite("./plays/"+str(e) + '.mp4', video,inputdict={'-r': '25'},outputdict={'-vcodec': 'libx264',
                                                                                              '-pix_fmt': 'yuv420p',
                                                                                             '-r': '25'})
    
    def draw_frame(self):
        
        skimage.io.imshow(self.to_draw[self.t])
        
    def get_frame(self):
        
        self.to_draw[int(self.t)][self.board>0,0] = 1      

        self.to_draw[int(self.t)][self.x:min(self.grid_size,self.x+self.square),self.y:min(self.grid_size,self.y+self.square),0] = -1
        
    def step(self, action):
        
        """This function returns the new state, reward and decides if the
        game ends."""

 

        reward = 0
        # clear current position

        
        if action == 0:
            if self.x == self.grid_size-1:
                self.x = self.x-1
                reward += -1 
            else:
                self.x = self.x + 1
        elif action == 1:
            if self.x == 0:
                self.x = self.x+1
                reward += -1 
            else:
                self.x = self.x-1
        elif action == 2:
            if self.y == self.grid_size - 1:
                reward += -1 
                self.y = self.y - 1
            else:
                self.y = self.y + 1
        elif action == 3:
            if self.y == 0:
                reward += -1 
                self.y = self.y + 1
            else:
                self.y = self.y - 1
        else:
            RuntimeError('Error: action not recognized')

        self.t = self.t + 1

        self.get_frame()
        
        reward = reward + np.max(self.board[self.x:min(self.grid_size,self.x+self.square),self.y:min(self.grid_size,self.y+self.square)])

        game_over = self.t > self.max_time
        
        if reward ==1:
             #game_over = True           
            self.add_mouse()

        return self.current_state(), reward, game_over

    def reset(self):

        """This function resets the game and returns the initial state"""
        
        self.start = True
        
        self.t = 0
        
        self.board *= 0
        self.to_draw *= 0
        
        self.x = self.square#np.random.randint(0, self.grid_size)
        self.y = self.square#np.random.randint(0, self.grid_size)

        self.add_mouse()

        self.get_frame()
        
        return self.current_state()
        
    def add_mouse(self):
        
        self.board*=0
        mouse_x,mouse_y = self.x,self.y
        while (mouse_x,mouse_y)==(self.x,self.y): 
            mouse_x = np.random.randint(self.square, self.grid_size-self.square)
            mouse_y = np.random.randint(self.square, self.grid_size-self.square)
            
        self.board[mouse_x:min(self.grid_size,mouse_x+self.square), mouse_y:min(self.grid_size,mouse_y+self.square)] = 1
        
    def current_state(self):
        
        return np.concatenate([self.to_draw[self.t-1],self.to_draw[self.t]],axis=-1)
    
class Discrete(object):
    
    def __init__(self,n):        
        self.n = n
        self.shape = (n,)
        self.dtype = np.int64

    def sample(self):
        return np.random.randint(self.n)
    
    def __repr__(self):
        return "Discrete(%d)" % self.n
        
    def __eq__(self,m):
        return self.n ==m

class Continuous(object):
    def __init__(self,low=None, high = None, shape=None, dtype = np.float32):
        
        self.shape = shape
        self.dtype = dtype
        
        self.low = low + np.zeros(shape)
        self.high = high + np.zeros(shape)
        
    def sample(self):
        np.random.uniform(low = self.low, high = self.high)
    
    def __repr__(self):
        return "Continuous" +str(self.shape)
    
class OpenAI(gym.Wrapper):
    
    def __init__(self,name):
        super(OpenAI,self).__init__(gym.make(name))
    
    def load_params(self):
        
        self._actions_raw = self.getMinimalActionSet().tolist()
        self.action_space = Discrete(len(self._actions_raw))
        self.observation_space = Continuous(0,1,OPTIONS["IMAGES_SIZE"]+(self.num_frames,))
        self._memory = collections.deque([],self.num_frames)
        self._start_lives = self.lives()
        self._current_state = np.zeros(self.observation_space.shape) 
        
        while len(self._memory)<self.num_frames:
            self.capture_current_frame()
    def load_rom(self,rom_file,render):

        self.setInt(str.encode('random_seed'), 123)
        self.setFloat(str.encode('repeat_action_probability'), 0.0)        
        self.setBool(str.encode('sound'), False)
        self.setBool(str.encode('display_screen'), render)
        self.loadROM(str.encode("./roms/"+utils.game_name(rom_file)))
        
    def capture_current_frame(self):
        up,down,left,right = self.crop
        self._memory.append(utils.process_frame(
                self.getScreenRGB()[up:-down,left:-right],
                            OPTIONS["IMAGES_SIZE"])
                            )
    
    def get_current_state(self):
        
        return np.concatenate(self._memory,axis = -1)
    
    def step(self,action):
        
        
        reward = 0
        assert action in range(self.actions_n), "Action not available"
        
        for i in range(self.num_frames-1):
            reward = max(reward, self.act(self.actions_set[action]))
            
        
        state = self.get_current_state()
        
        return state, reward, self.lives() != self._start_lives

    def reset(self):
        self.reset_game()
        self.load_params()

    def clone(self):
        env = self.cloneSystemState()
        env.params()
        return env


    def act(self,action):

        res = 0
        for _ in range(self.skip_frames):
            res = max(res,super(ALE,self).act(action))

        self.capture_current_frame()

        return res