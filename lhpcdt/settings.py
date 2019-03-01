#!/bin/env python


from .singleton import *

@Singleton
class LaunchSettings:

    def __init__(self):
        self.args = None
