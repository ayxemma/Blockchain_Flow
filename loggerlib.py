#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 21 18:44:18 2019

@author: ayx
"""

import logging

def get_module_logger(mod_name):
  logger = logging.getLogger(mod_name)
  if mod_name=='__main__':
      mode_opt='w'
  else:
      mode_opt='a'
  handler=logging.FileHandler('ex_flow.log', mode=mode_opt, delay=1)
  formatter = logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
  handler.setFormatter(formatter)
  logger.addHandler(handler)
  logger.setLevel(logging.DEBUG)
  return logger