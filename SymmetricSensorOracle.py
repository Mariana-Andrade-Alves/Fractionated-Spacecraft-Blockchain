#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 14 13:45:52 2021

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

pendingRequests = []
CHUNK_SIZE = 3
MAX_RETRIES = 5
currentRequest = 0
supervisor_private_key = sys.argv[1]
sensorFile = sys.argv[3]

def main(network, supervisor_address):
    
    def signal_handler(sig, frame):
        try:
            FilterEvents.join()
            CheckOracleState.join()
            CheckOracleVariations.join()
            print('\n============== Joined filterEvents and checkOracleState and checkOracleVariations threads')
        except:
            print("Unable to join filterEvents and checkOracleState thread")
        gracefullyExit(network)    
        sys.exit(0)
    
    try:
        FilterEvents = threading.Thread(target=filterEvents,args=(network,))
        CheckOracleState = threading.Thread(target=checkOracleState,args=(network, supervisor_address))
        CheckOracleVariations = threading.Thread(target=checkOracleVariations,args=(network, supervisor_address))
        print('\n============== Creating filterEvents and checkOracleState and checkOracleVariations threads')
    except:
        print("Error: unable to create filterEvents and checkOracleState and checkOracleVariations threads")
      
    try:
        FilterEvents.start()
        CheckOracleState.start()
        CheckOracleVariations.start()
        print('\n============== Running filterEvents and checkOracleState and checkOracleVariations threads') 
    except:
        print("Error: unable to start filterEvents and checkOracleState and checkOracleVariations threads")
    
    print('\n============== Running processQueue function') 
    processQueue(network,caller_contract_address, supervisor_address)
    
    signal.signal(signal.SIGINT, signal_handler)

def checkOracleVariations(network, supervisor_address):
    fromBlock = 0
    toBlock = 'latest'
    eventFilterVariations = network['contract'].events.VariationSurpassedEvent.createFilter(fromBlock=fromBlock, toBlock=toBlock)
    while True:    
        while True:
            newEntries = eventFilterVariations.get_new_entries()
            if newEntries!=[]:
                break
        
        for i in newEntries:
            args = i['args']
            if (args['oracleAddress'] == supervisor_address):
                print('\n============== New VariationSurpassedEvent Emitted for Me')
                print(f"eventOracleAddress: {args['oracleAddress'] }")
                print(f"eventComputedValue: {args['computedSensorValue']}")
                print(f"eventSensorValue: {args['sensorValue']}")
    print("Exiting!!!")
    print("Unable to join FilterEvents and checkOracleVariations threads")
    gracefullyExit(network)
    os._exit(1)
    
def checkOracleState(network, supervisor_address):
    fromBlock = 0
    toBlock = 'latest'
    eventFilter = network['contract'].events.RemoveOracleEvent.createFilter(fromBlock=fromBlock, toBlock=toBlock)
    while True:    
        while True:
            newEntries = eventFilter.get_new_entries()
            if newEntries!=[]:
                break
        
        for i in newEntries:
            args = i['args']
            if (args['oracleAddress'] == supervisor_address):
                print('\n============== RemoveOracleEvent Emitted for Me')
                print(f"eventOracleAddress: {args['oracleAddress'] }")
                print(f"eventReason: {args['reason']}")
                print("Exiting!!!")
                print("Unable to join FilterEvents and checkOracleVariations threads")
                os._exit(1)
             
    print("Exiting!!!")
    print("Unable to join FilterEvents and checkOracleVariations threads")
    gracefullyExit(network)
    os._exit(1)        
        
        
def processQueue(network,caller_contract_address, supervisor_address):
    global pendingRequests
    global CHUNK_SIZE
    global MAX_RETRIES
    while True:
        processedRequests = 0
        while (len(pendingRequests) > 0 & processedRequests < CHUNK_SIZE):
            idRequest = int(pendingRequests.pop())
            print(f"\n============== Handle request: {idRequest}")
            processRequest(network, caller_contract_address, supervisor_address, idRequest)
            processedRequests+=1
            
        try:
            sleep(5)
        except KeyboardInterrupt:
            print("Exiting!!!")
            print("Unable to join FilterEvents and CheckOracleState and checkOracleVariations threads")
            gracefullyExit(network)
            os._exit(1)
    
        
def processRequest(network, caller_contract_address, supervisor_address, idRequest):
    global supervisor_private_key
    retries = 0
    print('\n============== Calling the setLatestSensorValue function')
    while (retries <= MAX_RETRIES) :
        try:
            sensorValue = retrieveLatestSensorValue()
            print(f"\nNew Sensor Value: {sensorValue}")
            break
        except KeyboardInterrupt:
            print("Exiting!!!")
            print("Unable to join FilterEvents and CheckOracleState and checkOracleVariations threads")
            gracefullyExit(network)
            os._exit(1)
        except:
            print(f"\n Error number {retries} for retrieveLatestSensorValue function.")
            retries+=1
    while (retries <= MAX_RETRIES) :
        try:
            #FUNCTION setLatestSensorValue
            nonce = network['bc'].eth.getTransactionCount(supervisor_address)
            update_txn = network['contract'].functions.setLatestSensorValue(sensorValue, caller_contract_address, idRequest).buildTransaction({ 'gas': 700000, 'nonce': nonce})
            signed_txn = network['bc'].eth.account.sign_transaction(update_txn, private_key=supervisor_private_key)
            tr = network['bc'].eth.sendRawTransaction(signed_txn.rawTransaction)
            print("Stuck in infinite loop waiting for receipt of transaction setLatestSensorValue")
            printReceipt(tr, network, supervisor_address, 'setLatestSensorValue')
            break
        except KeyboardInterrupt:
            print("Exiting!!!")
            print("Unable to join FilterEvents and CheckOracleState and checkOracleVariations threads")
            gracefullyExit(network)
            os._exit(1)
        except:
            print(f"\n Error number {retries+1} for setLatestSensorValue function.")
            retries+=1
            sleep(2)

def retrieveLatestSensorValue():
    global currentRequest
    sensorFile
    #get sensor value on a textfile
    with open(sensorFile, "r") as filin:
        line = filin.readlines()
    lastValue = int(line[currentRequest])
    currentRequest+=1
    return lastValue
        
def filterEvents(network):
    global pendingRequests
    fromBlock = 0
    toBlock = 'latest'
    eventFilter = network['contract'].events.GetLatestSensorValueEvent.createFilter(fromBlock=fromBlock, toBlock=toBlock)
    newEntries = eventFilter.get_all_entries()
    while True:
        oldEntries = newEntries  
    
        while True:
            newEntries = eventFilter.get_all_entries()
            if newEntries!=oldEntries:
                break
        print('\n============== New GetLatestSensorValueEvent Emitted')
        lastEntry = newEntries[-1]
        lastEntryArgs = lastEntry['args']
        #FUNCTION addRequestToQueue(event)
        print(f"eventContractAddress: {lastEntry['address']}")
        callerAddress = lastEntryArgs['callerAddress']
        print(f"eventCallerAddress: {callerAddress}")
        idRequest = lastEntryArgs['id']
        print(f"eventID: {idRequest}")
        pendingRequests.append(idRequest)
        print(f"\n============== Pending Requests: {pendingRequests}")        
        
        try:
            sleep(2)
        except KeyboardInterrupt:
            print("Exiting!!!")
            print("Unable to join main and CheckOracleState and checkOracleVariations threads")
            gracefullyExit(network)
            os._exit(1)
    print("Exiting!!!")
    print("Unable to join main and CheckOracleState and checkOracleVariations threads")
    gracefullyExit(network)
    os._exit(1)

def gracefullyExit(network):
    print('\n============== Calling the autoDestructOracle function')
    nonce = network['bc'].eth.getTransactionCount(supervisor_address)  
    update_txn = network['contract'].functions.autoDestructOracle().buildTransaction({'gas': 700000, 'nonce': nonce})
    signed_txn = network['bc'].eth.account.sign_transaction(update_txn, private_key=supervisor_private_key)
    tr = network['bc'].eth.sendRawTransaction(signed_txn.rawTransaction)
    printReceipt(tr, network, supervisor_address, 'autoDestructOracle')

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
    
    caller_contract_address = contract_address("CallerContract.json")
    oracle_contract_address = contract_address("SymmetricSensorOracle.json")

    print('============== Fetched contract addresses')
    print(f'oracle: {oracle_contract_address}')
    print(f'caller: {caller_contract_address}')

    
    url='http://localhost:'+sys.argv[2]
    network = {
        'bc': web3.Web3(web3.Web3.HTTPProvider(url))
    }
    symmetric_oracle_abi = abi('SymmetricSensorOracle.json')
    network['contract'] = network['bc'].eth.contract(address=network['bc'].toChecksumAddress(oracle_contract_address), abi=symmetric_oracle_abi)
    
    priv_key_bytes = decode_hex(supervisor_private_key)
    priv_key = keys.PrivateKey(priv_key_bytes)
    pub_key = priv_key.public_key
    supervisor_address = pub_key.to_checksum_address()

    main(network, supervisor_address)