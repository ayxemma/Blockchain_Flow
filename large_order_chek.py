#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 21 13:07:36 2019

@author: ayx
"""
from loggerlib import get_module_logger
logger = get_module_logger(__name__)
from get_exchange_flow import get_freq_trans
logger.debug('Started')
get_freq_trans()
logger.debug('Finished')