pragma solidity 0.6.3;
import "./Roles.sol";
import "./SafeMath.sol";
import "./CallerContractInterface.sol";
import "./CommunicationOracleInterface.sol";

contract CommunicationOracle is CommunicationOracleInterface {
    using Roles for Roles.Role;
    Roles.Role private owners;
    Roles.Role private oracles;
    using SafeMath for uint256;
    uint256 private randNonce = 0;
    uint256 private modulus = 1000;
    uint256 private numOracles = 0;
    uint256 private THRESHOLD = 0;

    uint256 private RepTHRESHOLD = 0;
    mapping(address => uint256) private ReputationRecord;
    int256 private MaxVARIATION = 0;

    mapping(uint256 => bool) pendingRequests;

    struct Request {
        address oracleAddress;
        address otherAddress;
    }
    mapping(address => Request[]) public requestSensorToRequest;
    mapping(address => bool) public pendingSensorRequests;

    //variable to randomly choose oracle to respond to ground station
    address[] oraclesStored;

    event SendMessageToAntennaEvent(
        address sender,
        address callerAddress,
        uint256 id,
        string messageToSend
    );
    //event SetLatestSensorValueEvent(uint256 sensorValue, address callerAddress);
    event AddOracleEvent(address oracleAddress);
    event RemoveOracleEvent(address oracleAddress, string reason);
    event SetThresholdEvent(uint256 threshold);

    event DeleteSensorRequest(address sender, address oracle, string flag);
    event NewSensorRequest(address sender, address oracle, uint num);

    event VariationSurpassedEvent(
        address oracleAddress,
        int256 computedSensorValue,
        int256 sensorValue
    );

    constructor(address _owner) public {
        oracles.add(_owner);
        ReputationRecord[_owner] = 0;
        numOracles++;
    }

    function addOracle(address _oracle) public {
        require(oracles.has(msg.sender), "Not an oracle, cannot add oracles!");
        require(!oracles.has(_oracle), "Already an oracle!");
        oracles.add(_oracle);
        oraclesStored.push(_oracle);
        ReputationRecord[_oracle] = 0;
        numOracles++;
    }

    function removeOracle(address _oracle, string memory _reason) private {
        require(oracles.has(_oracle), "Not an oracle!");
        oracles.remove(_oracle);

        //delete oracle for stored list
        for (uint i=0; i < oraclesStored.length; i++) {
            if (oraclesStored[i] == _oracle) {
                for (uint j=i; i < oraclesStored.length-1; j++) {
                    oraclesStored[i] = oraclesStored[i+1];
                }
                oraclesStored.pop();
                break;
            }
        }

        delete ReputationRecord[_oracle];
        delete pendingSensorRequests[_oracle];

        numOracles--;
        emit RemoveOracleEvent(_oracle, _reason);
    }

    function autoDestructOracle() public {
        removeOracle(msg.sender, "Sensor is self-removing from the subsystem!");
    }

    function setThreshold(uint256 _threshold) public {
        require(oracles.has(msg.sender), "Not an oracle, cannot set parameters!");
        THRESHOLD = _threshold;
    }

    function setReputationParameters(
        uint256 _RepThreshold,
        int256 _MaxVariation
    ) public {
        require(oracles.has(msg.sender), "Not an oracle, cannot set parameters!");
        RepTHRESHOLD = _RepThreshold;
        MaxVARIATION = _MaxVariation;
    }

    //emit event listened by python
    function sendMessageToAntenna(string memory message)
        public
        returns (uint256)
    {
        // Generate random sender
        randNonce++;
        uint256 senderId = uint256(
            keccak256(abi.encodePacked(now, msg.sender, randNonce))
        ) % oraclesStored.length;
        address sender = oraclesStored[senderId];
        randNonce++;
        uint256 id = uint256(
            keccak256(abi.encodePacked(now, msg.sender, randNonce))
        ) % modulus;
        pendingRequests[id] = true;
        emit SendMessageToAntennaEvent(sender,msg.sender, id, message);
        return id;
    }

    //verify message sending
    function verifyMessageSending(string memory message, uint256 status)
        public
    {
        //to complete with cryptographic verification
    }

    //asking sensorValue and send to antenna
    function askSensorValue(
        address _callerAddress,
        address _sensor_oracle_address
    ) public {
        require(oracles.has(msg.sender), "Not an oracle!");
        require(
            !pendingSensorRequests[msg.sender],
            "Previous request has not yet been processed!"
        );
        //Signaling that a request has been made
        pendingSensorRequests[msg.sender] = true;

        //Saving request
        Request memory satRequest = Request(msg.sender, _callerAddress);
        requestSensorToRequest[_sensor_oracle_address].push(satRequest);
        uint256 numRequests = requestSensorToRequest[_sensor_oracle_address]
            .length;
        emit NewSensorRequest(msg.sender, _sensor_oracle_address, numRequests);

        if (numRequests == THRESHOLD) {
            //ask for a measure
            CallerContractInterface callerContractInstance;
            callerContractInstance = CallerContractInterface(_callerAddress);
            callerContractInstance.updateSensorValue(_sensor_oracle_address);

            //Deleting pending request attached to sensor
            satRequest.otherAddress = _sensor_oracle_address;
            for (uint256 i = 0; i < numRequests; i++) {
                emit DeleteSensorRequest(
                    requestSensorToRequest[_sensor_oracle_address][i]
                        .oracleAddress,
                    _sensor_oracle_address,
                    "Deleting pendingRequests"
                );
                delete pendingSensorRequests[requestSensorToRequest[_sensor_oracle_address][i]
                    .oracleAddress];
            }
            //Deleting requests from pending list
            delete requestSensorToRequest[_sensor_oracle_address];

        }
    }

    //receiving the value
    function receiveSensorValue(int256 _sensorValue, string memory _sensorType)
        public
        override
    {
        string memory value = strConcat(
            " updated value = ",
            int2str(_sensorValue)
        );
        value = strConcat(_sensorType, value);
        sendMessageToAntenna(value);
    }

    function int2str(int256 i) internal pure returns (string memory) {
        if (i == 0) return "0";
        bool negative = i < 0;
        uint256 j = uint256(negative ? -i : i);
        uint256 l = j; // Keep an unsigned copy
        uint256 len;
        while (j != 0) {
            len++;
            j /= 10;
        }
        if (negative) ++len; // Make room for '-' sign
        bytes memory bstr = new bytes(len);
        uint256 k = len - 1;
        while (l != 0) {
            bstr[k--] = bytes1(uint8(48 + (l % 10)));
            l /= 10;
        }
        if (negative) {
            // Prepend '-'
            bstr[0] = "-";
        }
        return string(bstr);
    }

    function strConcat(string memory _a, string memory _b)
        internal
        pure
        returns (string memory)
    {
        bytes memory _ba = bytes(_a);
        bytes memory _bb = bytes(_b);
        string memory ab = new string(_ba.length + _bb.length);
        bytes memory bab = bytes(ab);
        uint256 k = 0;
        for (uint256 i = 0; i < _ba.length; i++) bab[k++] = _ba[i];
        for (uint256 i = 0; i < _bb.length; i++) bab[k++] = _bb[i];
        return string(bab);
    }
}
