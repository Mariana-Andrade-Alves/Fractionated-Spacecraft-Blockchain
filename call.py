#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 15 10:28:56 2021

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
from getaddress import contract_address

pendingRequests = []
CHUNK_SIZE = 3
MAX_RETRIES = 5
currentRequest = 0
callerAddress = ""

def main(network, supervisor_address, supervisor_private_key, oracle_contract_address1,  oracle_contract_address2):

    def signal_handler(sig, frame):
        sys.exit(0)
    
    global callerAddress
    fromBlock = 0
    toBlock = 'latest'
    eventFilter = network['callerContract'].events.ValueUpdatedEvent.createFilter(fromBlock=fromBlock, toBlock=toBlock)
    eventFilter2 = network['callerContract'].events.ReceivedNewRequestIdEvent.createFilter(fromBlock=fromBlock, toBlock=toBlock)
    newEntries = eventFilter.get_all_entries()
    newEntries2 = eventFilter2.get_all_entries()
    while True:
        oldEntries = newEntries
        
        print(f'\n============== Calling the updateSensorValue() function (for first sensor)')
        nonce = network['bc'].eth.getTransactionCount(supervisor_address)
        
        update_txn = network['callerContract'].functions.updateSensorValue(oracle_contract_address1).buildTransaction({'gas': 700000, 'nonce': nonce})
        signed_txn = network['bc'].eth.account.sign_transaction(update_txn, private_key=supervisor_private_key)
        tr = network['bc'].eth.sendRawTransaction(signed_txn.rawTransaction)
        while True:
            try:        
                receipt = network['bc'].eth.get_transaction_receipt(tr)
                break
            except web3.exceptions.TransactionNotFound:
                continue
        
        print('\n============== Blockchain General Block Info')
        print(f"blockNumber: {receipt.blockNumber}")
        print(f"gasUsed: {receipt.gasUsed}")
        print(f"status: {receipt.status} (if =1, transaction was successful)")
        print(f"Supervisor account balance: {network['bc'].eth.getBalance(supervisor_address)}")
        
        oldEntries2 = newEntries2
    
        while True:
            newEntries2 = eventFilter2.get_all_entries()
            if newEntries2!=oldEntries2:
                break
        print('\n============== New ReceivedNewRequestIdEvent Emitted')
        lastEntry = newEntries2[-1]
        lastEntryArgs = lastEntry['args']
        idUpdate = lastEntryArgs['id']
        print(f"eventRequestID: {idUpdate}")
        
        print("\nStuck in infinite loop waiting for ValueUpdatedEvent (sensor1)")
        while True:
            try:
                newEntries = eventFilter.get_all_entries()
                if newEntries!=oldEntries:
                    break
            except KeyboardInterrupt:
                print("\nExiting!!!!")
                return
        print('\n============== New ValueUpdatedEvent Emitted')
        lastEntry = newEntries[-1]
        lastEntryArgs = lastEntry['args']
        updatedValue = lastEntryArgs['sensorValue']
        print(f"eventUpdatedValue: {updatedValue}")
        idUpdate = lastEntryArgs['id']
        print(f"eventRequestID: {idUpdate}")
        
        print(f'\n============== Calling the updateSensorValue() function (for second sensor)')
        nonce = network['bc'].eth.getTransactionCount(supervisor_address)
        
        update_txn = network['callerContract'].functions.updateSensorValue(oracle_contract_address2).buildTransaction({'gas': 700000, 'nonce': nonce})
        signed_txn = network['bc'].eth.account.sign_transaction(update_txn, private_key=supervisor_private_key)
        tr = network['bc'].eth.sendRawTransaction(signed_txn.rawTransaction)
        while True:
            try:        
                receipt = network['bc'].eth.get_transaction_receipt(tr)
                break
            except web3.exceptions.TransactionNotFound:
                continue
        
        print('\n============== Blockchain General Block Info')
        print(f"blockNumber: {receipt.blockNumber}")
        print(f"gasUsed: {receipt.gasUsed}")
        print(f"status: {receipt.status} (if =1, transaction was successful)")
        print(f"Supervisor account balance: {network['bc'].eth.getBalance(supervisor_address)}")
        
        oldEntries2 = newEntries2
    
        while True:
            newEntries2 = eventFilter2.get_all_entries()
            if newEntries2!=oldEntries2:
                break
        print('\n============== New ReceivedNewRequestIdEvent Emitted')
        lastEntry = newEntries2[-1]
        lastEntryArgs = lastEntry['args']
        idUpdate = lastEntryArgs['id']
        print(f"eventRequestID: {idUpdate}")
        
        oldEntries = newEntries
        
        print("\nStuck in infinite loop waiting for ValueUpdatedEvent (sensor2)")
        while True:
            try:
                newEntries = eventFilter.get_all_entries()
                if newEntries!=oldEntries:
                    break
            except KeyboardInterrupt:
                print("\nExiting!!!!")
                return
        print('\n============== New ValueUpdatedEvent Emitted')
        lastEntry = newEntries[-1]
        lastEntryArgs = lastEntry['args']
        updatedValue = lastEntryArgs['sensorValue']
        print(f"eventUpdatedValue: {updatedValue}")
        idUpdate = lastEntryArgs['id']
        print(f"eventRequestID: {idUpdate}")
    
    signal.signal(signal.SIGINT, signal_handler)
    
if __name__ == "__main__":
    
    communication_contract_address = contract_address("CommunicationOracle.json")
    caller_contract_address = contract_address("CallerContract.json")
    oracle_contract_address1 = contract_address("SymmetricSensorOracle.json")
    oracle_contract_address2 = contract_address("AsymmetricSensorOracle.json")
    
    print('============== Fetched contract addresses')
    print(f'oracle1: {oracle_contract_address1}')
    print(f'oracle2: {oracle_contract_address2}')
    print(f'caller: {caller_contract_address}')
    print(f'communication: {communication_contract_address}')

    url = 'http://localhost:'+sys.argv[1]
    network = {
        'bc': web3.Web3(web3.Web3.HTTPProvider(url))
    }

    with open(f'./build/contracts/CallerContract.json') as f:
        data = json.load(f)
    network['callerContract'] = network['bc'].eth.contract(address=network['bc'].toChecksumAddress(caller_contract_address), abi=data['abi'])

    supervisor_private_key = '0xc87509a1c067bbde78beb793e6fa76530b6382a4c0241e5e4a9ec0a0f44dc0d3'
    
    priv_key_bytes = decode_hex(supervisor_private_key)
    priv_key = keys.PrivateKey(priv_key_bytes)
    pub_key = priv_key.public_key
    supervisor_address = pub_key.to_checksum_address()
      
    main(network, supervisor_address, supervisor_private_key, oracle_contract_address1,  oracle_contract_address2)
    
    
    