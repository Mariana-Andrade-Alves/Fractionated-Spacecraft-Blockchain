#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 17 16:10:36 2021

@author: rsx02
"""

import sys
import json
import math
import signal
import web3 as web3
import threading

from constants import *
from time import sleep
from cfonts import render, say
from yaspin import yaspin
from yaspin.spinners import Spinners
from eth_keys import keys
from eth_utils import decode_hex

import getaddress
from getaddress import contract_address, abi
from generateKeys import generateKeys

def main(network, supervisor_address, supervisor_private_key, symmetric_oracle_contract_address ,  asymmetric_oracle_contract_address, communication_contract_address):

    def signal_handler(sig, frame):
        sys.exit(0)
        
    print('\n===============================================================================================')
    print('===============================================================================================')  
    print('========================================= SYSTEM SETUP ========================================')
    print('===============================================================================================')  
    print('===============================================================================================')  
    
    print('\n===============================================================================================')
    print('============== Saving all Sensor Subsystem Contract Addresses in Caller Contract ==============')
    print('===============================================================================================')    
    
    print('\n============== Calling the addOracleInstanceAddress function (for symmetric sensor subsystem contract)')
    nonce = network['bc'].eth.getTransactionCount(supervisor_address)  
    update_txn = network['callerContract'].functions.addOracleInstanceAddress(symmetric_oracle_contract_address).buildTransaction({'gas': 700000, 'nonce': nonce})
    signed_txn = network['bc'].eth.account.sign_transaction(update_txn, private_key=supervisor_private_key)
    tr = network['bc'].eth.sendRawTransaction(signed_txn.rawTransaction)
    printReceipt(tr, network, supervisor_address, "addOracleInstanceAddress")

    print('\n============== Calling the addOracleInstanceAddress function (for asymmetric sensor subsystem contract)')
    nonce = network['bc'].eth.getTransactionCount(supervisor_address)  
    update_txn = network['callerContract'].functions.addOracleInstanceAddress(asymmetric_oracle_contract_address).buildTransaction({'gas': 700000, 'nonce': nonce})
    signed_txn = network['bc'].eth.account.sign_transaction(update_txn, private_key=supervisor_private_key)
    tr = network['bc'].eth.sendRawTransaction(signed_txn.rawTransaction)
    printReceipt(tr, network, supervisor_address, "addOracleInstanceAddress")

    print('\n============== Calling the setCommunicationOracleInstanceAddress function (for communication subsystem contract)')
    nonce = network['bc'].eth.getTransactionCount(supervisor_address) 
    update_txn = network['callerContract'].functions.setCommunicationOracleInstanceAddress(communication_contract_address).buildTransaction({'gas': 700000, 'nonce': nonce})
    signed_txn = network['bc'].eth.account.sign_transaction(update_txn, private_key=supervisor_private_key)
    tr = network['bc'].eth.sendRawTransaction(signed_txn.rawTransaction)
    printReceipt(tr, network, supervisor_address, "setCommunicationOracleInstanceAddress")
    
    print('\n===============================================================================================')
    print('=============== Defining all Sensor Subsystem Contracts Performance Parameters ================')
    print('===============================================================================================')
    
    threshold = 3
    
    print('\n============== Calling the setThreshold function  (for symmetric sensor subsystem contract)')
    nonce = network['bc'].eth.getTransactionCount(supervisor_address)
    update_txn = network['symmetricSensorContract'].functions.setThreshold(threshold).buildTransaction({'gas': 700000, 'nonce': nonce})
    signed_txn = network['bc'].eth.account.sign_transaction(update_txn, private_key=supervisor_private_key)
    tr = network['bc'].eth.sendRawTransaction(signed_txn.rawTransaction)
    printReceipt(tr, network, supervisor_address, "setThreshold")
    
    print('\n============== Calling the setThreshold function  (for asymmetric sensor subsystem contract)')
    nonce = network['bc'].eth.getTransactionCount(supervisor_address)   
    update_txn = network['asymmetricSensorContract'].functions.setThreshold(threshold).buildTransaction({'gas': 700000, 'nonce': nonce})
    signed_txn = network['bc'].eth.account.sign_transaction(update_txn, private_key=supervisor_private_key)
    tr = network['bc'].eth.sendRawTransaction(signed_txn.rawTransaction)
    printReceipt(tr, network, supervisor_address, "setThreshold")
    
    print('\n============== Calling the setThreshold function  (for communication sensor subsystem contract)')
    nonce = network['bc'].eth.getTransactionCount(supervisor_address)  
    update_txn = network['communicationContract'].functions.setThreshold(threshold).buildTransaction({'gas': 700000, 'nonce': nonce})
    signed_txn = network['bc'].eth.account.sign_transaction(update_txn, private_key=supervisor_private_key)
    tr = network['bc'].eth.sendRawTransaction(signed_txn.rawTransaction)
    printReceipt(tr, network, supervisor_address, "setThreshold")
    
    repThreshold = 2
    maxVariation = 615
    
    print('\n============== Calling the setReputationParameters function (for symmetric sensor subsystem contract)')
    nonce = network['bc'].eth.getTransactionCount(supervisor_address)
    update_txn = network['symmetricSensorContract'].functions.setReputationParameters(repThreshold,maxVariation).buildTransaction({'gas': 700000, 'nonce': nonce})
    signed_txn = network['bc'].eth.account.sign_transaction(update_txn, private_key=supervisor_private_key)
    tr = network['bc'].eth.sendRawTransaction(signed_txn.rawTransaction)
    printReceipt(tr, network, supervisor_address, "setReputationParameters")
    
    print('\n============== Calling the setReputationParameters function (for asymmetric sensor subsystem contract)')
    nonce = network['bc'].eth.getTransactionCount(supervisor_address)
    update_txn = network['asymmetricSensorContract'].functions.setReputationParameters(repThreshold,maxVariation).buildTransaction({'gas': 700000, 'nonce': nonce})
    signed_txn = network['bc'].eth.account.sign_transaction(update_txn, private_key=supervisor_private_key)
    tr = network['bc'].eth.sendRawTransaction(signed_txn.rawTransaction)
    printReceipt(tr, network, supervisor_address, "setReputationParameters")

#    print('\n===============================================================================================')
#    print('========================== Generating all Approved Subsystem Sensors ==========================')
#    print('===============================================================================================')
#
#    generateKeys("Files/keys/approvedPrivateKeysSymmetric.txt", threshold-1)
#    print("Created Symmetric Subsystem Keys\n")
#    generateKeys("Files/keys/approvedPrivateKeysAsymmetric.txt", threshold-1)
#    print("Created Asymmetric Subsystem Keys\n")
#    generateKeys("Files/keys/approvedPrivateKeysCommunication.txt", threshold-1)
#    print("Created Communication Subsystem Keys\n")

    print('\n===============================================================================================')
    print('============================ Adding all Approved Subsystem Sensors ============================')
    print('===============================================================================================')

    with open("Files/keys/approvedPrivateKeysSymmetric.txt", "r") as filin:
        lines = filin.readlines()
    for line in lines:
        priv_key_bytes = decode_hex(line.strip())
        priv_key = keys.PrivateKey(priv_key_bytes)
        pub_key = priv_key.public_key
        oracle_address = pub_key.to_checksum_address()
        print('\n============== Calling the addOracle function (for symmetric sensor subsystem contract)')
        nonce = network['bc'].eth.getTransactionCount(supervisor_address)  
        update_txn = network['symmetricSensorContract'].functions.addOracle(oracle_address).buildTransaction({'gas': 700000, 'nonce': nonce})
        signed_txn = network['bc'].eth.account.sign_transaction(update_txn, private_key=supervisor_private_key)
        tr = network['bc'].eth.sendRawTransaction(signed_txn.rawTransaction)
        printReceipt(tr, network, supervisor_address, 'addOracle')
    
    with open("Files/keys/approvedPrivateKeysAsymmetric.txt", "r") as filin:
        lines = filin.readlines()
    for line in lines:
        priv_key_bytes = decode_hex(line.strip())
        priv_key = keys.PrivateKey(priv_key_bytes)
        pub_key = priv_key.public_key
        oracle_address = pub_key.to_checksum_address()
        print('\n============== Calling the addOracle function (for asymmetric sensor subsystem contract)')
        nonce = network['bc'].eth.getTransactionCount(supervisor_address)  
        update_txn = network['asymmetricSensorContract'].functions.addOracle(oracle_address).buildTransaction({'gas': 700000, 'nonce': nonce})
        signed_txn = network['bc'].eth.account.sign_transaction(update_txn, private_key=supervisor_private_key)
        tr = network['bc'].eth.sendRawTransaction(signed_txn.rawTransaction)
        printReceipt(tr, network, supervisor_address, 'addOracle')
        
    with open("Files/keys/approvedPrivateKeysCommunication.txt", "r") as filin:
        lines = filin.readlines()
    for line in lines:
        priv_key_bytes = decode_hex(line.strip())
        priv_key = keys.PrivateKey(priv_key_bytes)
        pub_key = priv_key.public_key
        oracle_address = pub_key.to_checksum_address()
        print('\n============== Calling the addOracle function (for communication sensor subsystem contract)')
        nonce = network['bc'].eth.getTransactionCount(supervisor_address)  
        update_txn = network['communicationContract'].functions.addOracle(oracle_address).buildTransaction({'gas': 700000, 'nonce': nonce})
        signed_txn = network['bc'].eth.account.sign_transaction(update_txn, private_key=supervisor_private_key)
        tr = network['bc'].eth.sendRawTransaction(signed_txn.rawTransaction)
        printReceipt(tr, network, supervisor_address, 'addOracle')
    
    signal.signal(signal.SIGINT, signal_handler)

def printReceipt(tr, network, supervisor_address, transaction):
    while True:
        try:        
            receipt = network['bc'].eth.get_transaction_receipt(tr)
            break
        except web3.exceptions.TransactionNotFound:
            continue
    
    print(f'\n============== Blockchain General Block Info ({transaction} Transaction)')
    print(f"blockNumber: {receipt.blockNumber}")
    print(f"gasUsed: {receipt.gasUsed}")
    print(f"status: {receipt.status} (if =1, transaction was successful)")
    print(f"Supervisor account balance: {network['bc'].eth.getBalance(supervisor_address)}")

if __name__ == "__main__":
    
    communication_contract_address = contract_address("CommunicationOracle.json")
    caller_contract_address = contract_address("CallerContract.json")
    symmetric_oracle_contract_address = contract_address("SymmetricSensorOracle.json")
    asymmetric_oracle_contract_address = contract_address("AsymmetricSensorOracle.json")

    
    print('============== Fetched contract addresses')
    print(f'Symmetric Sensor Subsystem Oracle: {symmetric_oracle_contract_address}')
    print(f'Asymmetric Sensor Subsystem Oracle: {asymmetric_oracle_contract_address}')
    print(f'Caller Contract: {caller_contract_address}')
    print(f'Communication Subsystem Oracle: {communication_contract_address}')

    url = 'http://localhost:'+sys.argv[1]
    network = {
        'bc': web3.Web3(web3.Web3.HTTPProvider(url))
    }

    caller_abi = abi('CallerContract.json')
    network['callerContract'] = network['bc'].eth.contract(address=network['bc'].toChecksumAddress(caller_contract_address), abi=caller_abi)

    symmetric_oracle_abi = abi('SymmetricSensorOracle.json')
    network['symmetricSensorContract'] = network['bc'].eth.contract(address=network['bc'].toChecksumAddress(symmetric_oracle_contract_address), abi=symmetric_oracle_abi)

    asymmetric_oracle_abi = abi('AsymmetricSensorOracle.json')
    network['asymmetricSensorContract'] = network['bc'].eth.contract(address=network['bc'].toChecksumAddress(asymmetric_oracle_contract_address), abi=asymmetric_oracle_abi)

    communication_abi = abi('CommunicationOracle.json')
    network['communicationContract'] = network['bc'].eth.contract(address=network['bc'].toChecksumAddress(communication_contract_address), abi=communication_abi)
    
    # This is the genesis oracle which will add all the oracles to all the subsystems
    supervisor_private_key = '0xae6ae8e5ccbfb04590405997ee2d52d2b330726137b875053c36d94e974d162f'    
    priv_key_bytes = decode_hex(supervisor_private_key)
    priv_key = keys.PrivateKey(priv_key_bytes)
    pub_key = priv_key.public_key
    supervisor_address = pub_key.to_checksum_address()
    
    main(network, supervisor_address, supervisor_private_key, symmetric_oracle_contract_address ,  asymmetric_oracle_contract_address, communication_contract_address)
    
    
    