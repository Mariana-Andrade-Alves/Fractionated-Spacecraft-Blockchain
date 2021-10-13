#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 28 14:04:37 2021

@author: rsx02
"""

import secrets

def generateKeys(keyFile, number):
    for i in range(number):
        private_key = secrets.token_hex(32)
        private_key = "0x"+private_key
        with open(keyFile, "a") as filout:
            filout.write("{}\n".format(private_key))
    