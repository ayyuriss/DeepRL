#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 20 17:28:08 2018

@author: thinkpad
"""

class FCNet(trc.nn.Module):

    def __init__(self):
        super(Net, self).__init__()
        
        self.layer1 = nn.Conv2d(1,10,5)
        self.layer2 = nn.Conv2d(10,20,5)
        
        # an affine operation: y = Wx + b
        self.fc1 = nn.Linear(20 * 4 * 4, 120)
        self.fc2 = nn.Linear(120, 80)
        self.fc3 = nn.Linear(80, 10)

    def forward(self, x):
        # Max pooling over a (2, 2) window
        x = F.max_pool2d(F.relu(self.layer1(x)), (2, 2))
        # If the size is a square you can only specify a single number
        x = F.max_pool2d(F.relu(self.layer2(x)), 2)
        
        x = x.view(-1, self.num_flat_features(x))
        x = F.softplus(self.fc1(x))
        x = F.softplus(self.fc2(x))
        x = self.fc3(x)
        return x

    def num_flat_features(self, x):
        size = x.size()[1:]  # all dimensions except the batch dimension
        num_features = 1
        for s in size:
            num_features *= s
        return num_features