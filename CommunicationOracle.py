
"""
Created on Mon Jun 14 13:45:52 2021

@author: Mariana Alves & Justine VEIRIER D'AIGUEBONNE
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
responseFile = sys.argv[3]


def main(network, supervisor_address, caller_contract_address):

    def signal_handler(sig, frame):
        try:
            FilterEvents.join()
            ReceivingCommands.join()
            CheckOracleState.join()
            print('\n============== Joined filterEvents and receivingCommands and checkOracleState threads')
        except:
            print("Unable to join filterEvents and receivingCommands threads")
        gracefullyExit(network)    
        sys.exit(0)
    
    try:
        FilterEvents = threading.Thread(target=filterEvents,args=(network,))
        ReceivingCommands = threading.Thread(target=receivingCommands,args=(network, supervisor_address, caller_contract_address))
        CheckOracleState = threading.Thread(target=checkOracleState,args=(network, supervisor_address))
        print('\n============== Creating filterEvents and receivingCommands and checkOracleState threads')
    except:
        print("Error: unable to create filterEvents and receivingCommands threads")
        
    try:
        FilterEvents.start()
        ReceivingCommands.start()
        CheckOracleState.start()
        print('\n============== Running filterEvents and receivingCommands and checkOracleState threads') 
    except:
        print("Unable to run filterEvents and receivingCommands threads")
    
    print('\n============== Running processQueue function') 
    processQueue(network,caller_contract_address, supervisor_address)
    
    signal.signal(signal.SIGINT, signal_handler)

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
                print("Unable to join FilterEvents and receivingCommands threads")
                os._exit(1)
             
    print("Exiting!!!")
    print("Unable to join FilterEvents and receivingCommands threads")
    gracefullyExit(network)
    os._exit(1)    
        
def processQueue(network, caller_contract_address, supervisor_address):
    global pendingRequests
    global CHUNK_SIZE
    global MAX_RETRIES
    while True:
        processedRequests = 0
        while (len(pendingRequests) > 0 & processedRequests < CHUNK_SIZE):
            lastRequest = pendingRequests.pop()
            idRequest = lastRequest[0]
            messageToSend = lastRequest[1]
            print(f"\n============== Handle request: {idRequest}")
            print(f"\n============== Message : {messageToSend}")
            processRequest(network, caller_contract_address, supervisor_address, idRequest, messageToSend)
            processedRequests+=1
            
        try:
            sleep(5)
        except KeyboardInterrupt:
            print("Exiting!!!")
            print("Unable to join filterEvents and receivingCommands threads")
            gracefullyExit(network)
            os._exit(1)
            
        
def processRequest(network, caller_contract_address, supervisor_address, idRequest, messageToSend):
    global supervisor_private_key
    retries = 0
    #print('\n============== Calling the verifyMessageSending function')
    while (retries <= MAX_RETRIES) :
        try:
            status = sendMessageToAntenna(messageToSend)
            print(f"\nNew Status: {status}")
            
#            nonce = network['bc'].eth.getTransactionCount(supervisor_address)
#            
#            update_txn = network['contract'].functions.verifyMessageSending(messageToSend, status).buildTransaction({'gas': 700000, 'nonce': nonce})
#            signed_txn = network['bc'].eth.account.sign_transaction(update_txn, private_key=supervisor_private_key)
#            tr = network['bc'].eth.sendRawTransaction(signed_txn.rawTransaction)
#            while True:
#                try:        
#                    receipt = network['bc'].eth.get_transaction_receipt(tr)
#                    print("TRANSACTION SHOULD BE DONE")
#                    break
#                except web3.exceptions.TransactionNotFound:
#                    continue
#            print('\n============== Blockchain General Block Info (verifyMessageSending Transaction)')
#            print(f"blockNumber: {receipt.blockNumber}")
#            print(f"gasUsed: {receipt.gasUsed}")
#            print(f"status: {receipt.status} (if =1, transaction was successful)")
#            print(f"Supervisor account balance: {network['bc'].eth.getBalance(supervisor_address)}")
            
            
            
            break
        except KeyboardInterrupt:
            print("Exiting!!!")
            print("Unable to join filterEvents and receivingCommands threads")
            gracefullyExit(network)
            os._exit(1)
        except:
            print(f"\n Error number {retries} for verifyMessageSending function.")
            retries+=1
            sleep(2)
   

#first part : send a message
#write in a file the message
#return a status 0 = fail / 1 = sending
def sendMessageToAntenna(message):
    status = 0
    with open(responseFile, "a") as filout:
        filout.write("{}\n".format(message))
        status = 1
    print(f"\nWriting done")
    return status

        
def filterEvents(network):
    global pendingRequests
    fromBlock = 0
    toBlock = 'latest'
    eventFilter = network['contract'].events.SendMessageToAntennaEvent.createFilter(fromBlock=fromBlock, toBlock=toBlock)
    while True:
        newEntries = eventFilter.get_new_entries()
        for lastEntry in newEntries:
             lastEntryArgs = lastEntry['args']
             senderAddress = lastEntryArgs['sender']
             if (senderAddress == supervisor_address):
                    print('\n============== New SendMessageToAntennaEvent Emitted for ME')
                    print(f"eventSenderAddress: {senderAddress}")
                    callerAddress = lastEntryArgs['callerAddress']
                    print(f"eventContractAddress: {lastEntry['address']}")
                    print(f"eventCallerAddress: {callerAddress}")
                    idRequest = lastEntryArgs['id']
                    print(f"eventID: {idRequest}")

                    #get message from the event
                    messageToSend = lastEntryArgs['messageToSend']
                    print(f"message: {messageToSend}")
                    pendingRequests.append([idRequest, messageToSend])
                    print(f"\n============== Pending Requests: {pendingRequests}")        
        try:
            sleep(2)
        except KeyboardInterrupt:
            print("Exiting!!!")
            print("Unable to join receivingCommands threads")
            gracefullyExit(network)
            os._exit(1)
    
    gracefullyExit(network)
    os._exit(1)


#second part : receive a message
def receivingCommands(network, supervisor_address, caller_contract_address):
    global supervisor_private_key
    retries = 0
    commands = receiveMessageFromAntenna()
    print(f"\n============== commands : {commands}")
    
    fromBlock = 0
    toBlock = 'latest'
    eventFilter = network['contract'].events.NewSensorRequest.createFilter(fromBlock=fromBlock, toBlock=toBlock)
    eventFilterDelete = network['contract'].events.DeleteSensorRequest.createFilter(fromBlock=fromBlock, toBlock=toBlock)
    newEntries = eventFilter.get_all_entries()
    newEntriesDelete = eventFilterDelete.get_all_entries()
    for i in range(len(commands)):
        print(f"\n============== commands[i] : {commands[i]}")
        
        if (commands[i].startswith('sensorValue')):
            request = commands[i].split(':')[1]
            print(f"request : {request}")
            
            oldEntries = newEntries 
            oldEntriesDelete = newEntriesDelete
            
            retries = 0
            print('\n============== receive part : Calling the askSensorValue function')
            while (retries <= MAX_RETRIES) :
                try:
                    nonce = network['bc'].eth.getTransactionCount(supervisor_address)
            
                    if (request.startswith('temperature')):
                        update_txn = network['contract'].functions.askSensorValue(caller_contract_address, symmetric_sensor_contract_address).buildTransaction({'gas': 700000, 'nonce': nonce})
                    else:
                        update_txn = network['contract'].functions.askSensorValue(caller_contract_address, asymmetric_sensor_contract_address).buildTransaction({'gas': 700000, 'nonce': nonce})
             
                    signed_txn = network['bc'].eth.account.sign_transaction(update_txn, private_key=supervisor_private_key)
                    tr = network['bc'].eth.sendRawTransaction(signed_txn.rawTransaction)
                    status = printReceipt(tr, network, supervisor_address, 'askSensorValue')
                    if (status!=1):
                        print(f"\n Error number {retries+1} for askSensorValue function.")
                        print(f"Previous request has not been handled.")
                        retries+=1
                        continue
                    break
                except KeyboardInterrupt:
                    print("Exiting!!!")
                    print("Unable to join FilterEvents and CheckOracleState and checkOracleVariations threads")
                    gracefullyExit(network)
                    os._exit(1)
                except:
                    print(f"\n Error number {retries+1} for askSensorValue function.")
                    retries+=1
                    sleep(2)
                    
            while True:
                newEntries = eventFilter.get_all_entries()
                if newEntries!=oldEntries:
                    while True:
                        lastEntry = newEntries[-1]
                        lastEntryArgs = lastEntry['args']
                        sender = lastEntryArgs['sender']
                        if (sender == supervisor_address):
                            break
                        else:
                            newEntries = newEntries[:len(newEntries)-2]
                            if (len(newEntries) == 0):
                                break
                    break
        
            print('\n============== New NewSensorRequest Emitted for ME')
            print(f"eventOracleContractAddress: {lastEntryArgs['oracle']}")
            print(f"eventSenderAddress: {sender}")
            print(f"eventNumberofRequests: {lastEntryArgs['num']}")
            
            while True:
                newEntriesDelete = eventFilterDelete.get_all_entries()
                if (newEntriesDelete != oldEntriesDelete):
                    break
            news = newEntriesDelete[len(oldEntriesDelete)-1:]
            for lastEntry in news:
                lastEntryArgs = lastEntry['args']
                senderAddress = lastEntryArgs['sender']
                if (senderAddress == supervisor_address):
                    print('\n============== New DeleteSensorRequest Emitted for ME')
                    print(f"eventSenderAddress: {senderAddress}")
                    break
            
            
        elif (commands[i].startswith('send me')) :            
            message = commands[i].split('"')[1]
            print(f"message : {message}")
            
            nonce = network['bc'].eth.getTransactionCount(supervisor_address)
            print('\n============== receive part : Calling the sendMessageToAntenna function')
            update_txn = network['contract'].functions.sendMessageToAntenna(message).buildTransaction({'gas': 700000, 'nonce': nonce})
            signed_txn = network['bc'].eth.account.sign_transaction(update_txn, private_key=supervisor_private_key)
            tr = network['bc'].eth.sendRawTransaction(signed_txn.rawTransaction)
            printReceipt(tr, network, supervisor_address, 'sendMessageToAntenna')
        
        else:
            continue
        
        
#read commands in a file
def receiveMessageFromAntenna():
    commands = sys.argv[4]
    with open(commands, "r") as filin:
        commands = filin.readlines() 
    return commands

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
    return receipt.status    

if __name__ == "__main__":
    
    communication_contract_address = contract_address("CommunicationOracle.json")
    caller_contract_address = contract_address("CallerContract.json")
    symmetric_sensor_contract_address = contract_address("SymmetricSensorOracle.json")
    asymmetric_sensor_contract_address = contract_address("AsymmetricSensorOracle.json")

    print('============== Fetched contract addresses')
    print(f'communication: {communication_contract_address}')
    print(f'caller: {caller_contract_address}')
    print(f'symmetric sensor: {symmetric_sensor_contract_address}')
    print(f'asymmetric sensor: {asymmetric_sensor_contract_address}')
    
    url='http://localhost:'+sys.argv[2]
    network = {
        'bc': web3.Web3(web3.Web3.HTTPProvider(url))
    }
    communication_abi = abi('CommunicationOracle.json')
    network['contract'] = network['bc'].eth.contract(address=network['bc'].toChecksumAddress(communication_contract_address), abi=communication_abi)
    
    priv_key_bytes = decode_hex(supervisor_private_key)
    priv_key = keys.PrivateKey(priv_key_bytes)
    pub_key = priv_key.public_key
    supervisor_address = pub_key.to_checksum_address()
    
    main(network, supervisor_address, caller_contract_address)
