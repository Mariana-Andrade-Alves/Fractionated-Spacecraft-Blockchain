#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 17 12:02:31 2021

@author: rsx09
"""
import json

def contract_address(file):
    path = 'build/contracts/'+file
    with open(path) as json_data:
        data_dict = json.load(json_data)
    
    networks = data_dict["networks"]
    dossier = networks["1337"]
    contract_address = dossier["address"]
    return contract_address

def abi(file):
    path = 'build/contracts/'+file
    with open(path) as json_data:
        data_dict = json.load(json_data)

    return data_dict['abi']
