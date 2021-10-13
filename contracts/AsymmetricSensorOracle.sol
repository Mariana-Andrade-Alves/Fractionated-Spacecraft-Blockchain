pragma solidity 0.6.3;
import "./Roles.sol";
import "./SafeMath.sol";
import "./CallerContractInterface.sol";
import "./CallerContract.sol";
import "./SensorValueOracleInterface.sol";

contract AsymmetricSensorOracle is SensorValueOracleInterface {
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
    struct Response {
        address oracleAddress;
        address callerAddress;
        int256 sensorValue;
    }

    mapping(uint256 => Response[]) public requestIdToResponse;
    event GetLatestSensorValueEvent(address callerAddress, uint256 id);
    event SetLatestSensorValueEvent(int256 sensorValue, address callerAddress);
    event AddOracleEvent(address oracleAddress);
    event RemoveOracleEvent(address oracleAddress, string reason);
    event SetThresholdEvent(uint256 threshold);
    event VariationSurpassedEvent(
        address oracleAddress,
        int256 computedSensorValue,
        int256 sensorValue
    );
    mapping(int256 => int256) counting;

    constructor(address _owner) public {
        oracles.add(_owner);
        ReputationRecord[_owner] = 0;
        numOracles++;
    }

    function addOracle(address _oracle) public {
        require(oracles.has(msg.sender), "Not an oracle, cannot add oracles!");
        require(!oracles.has(_oracle), "Already an oracle!");
        oracles.add(_oracle);
        ReputationRecord[_oracle] = 0;
        numOracles++;
    }

    function removeOracle(address _oracle, string memory _reason) private {
        require(oracles.has(_oracle), "Not an oracle!");
        oracles.remove(_oracle);
        delete ReputationRecord[_oracle];
        numOracles--;
        emit RemoveOracleEvent(_oracle, _reason);
    }

    function autoDestructOracle() public {
        removeOracle(msg.sender, "Sensor is self-removing from the subsystem!");
    }

    function updateOracleSensorsList(uint256 _id, int256 _computedSensorValue)
        private
    {
        int256 max = _computedSensorValue + MaxVARIATION;
        int256 min = _computedSensorValue - MaxVARIATION;
        for (uint256 f = 0; f < requestIdToResponse[_id].length; f++) {
            address oracle = requestIdToResponse[_id][f].oracleAddress;
            // Update Reputation Record
            if (
                (requestIdToResponse[_id][f].sensorValue > max) ||
                (requestIdToResponse[_id][f].sensorValue < min)
            ) {
                ReputationRecord[oracle] = ReputationRecord[oracle] + 1;
                emit VariationSurpassedEvent(
                    oracle,
                    _computedSensorValue,
                    requestIdToResponse[_id][f].sensorValue
                );
            }
            // Update OracleSensorsList
            if (ReputationRecord[oracle] > RepTHRESHOLD) {
                removeOracle(oracle, "Sensor surpassed reputation threshold!");
            }
        }
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

    function getLatestSensorValue() public override returns (uint256) {
        randNonce++;
        uint256 id = uint256(
            keccak256(abi.encodePacked(now, msg.sender, randNonce))
        ) % modulus;
        pendingRequests[id] = true;
        emit GetLatestSensorValueEvent(msg.sender, id);
        return id;
    }

    function setLatestSensorValue(
        int256 _sensorValue,
        address _callerAddress,
        uint256 _id,
        int256[] memory _relativeSensorValues
    ) public {
        require(oracles.has(msg.sender), "Not an oracle!");
        require(
            pendingRequests[_id],
            "This request is not in my pending list."
        );
        // Computing the absolute position of the system's center
        int256 center = 0;
        for (uint256 f = 0; f < numOracles; f++) {
            center = center + _relativeSensorValues[f];
        }
        center =
            center /
            int256(_relativeSensorValues.length) +
            _sensorValue;
        Response memory resp;
        resp = Response(msg.sender, _callerAddress, center);

        requestIdToResponse[_id].push(resp);
        uint256 numResponses = requestIdToResponse[_id].length;
        if (numResponses == THRESHOLD) {
            int256 computedSensorValue = requestIdToResponse[_id][0]
                .sensorValue;
            for (uint256 f = 0; f < requestIdToResponse[_id].length; f++) {
                counting[requestIdToResponse[_id][f].sensorValue] = 0;
            }
            //Calculating the mode
            for (uint256 f = 0; f < requestIdToResponse[_id].length; f++) {
                counting[requestIdToResponse[_id][f].sensorValue] =
                    counting[requestIdToResponse[_id][f].sensorValue] +
                    1;
                if (
                    counting[requestIdToResponse[_id][f].sensorValue] >
                    counting[computedSensorValue]
                ) {
                    computedSensorValue = requestIdToResponse[_id][f]
                        .sensorValue;
                }
            }
            updateOracleSensorsList(_id, computedSensorValue);
            delete pendingRequests[_id];
            delete requestIdToResponse[_id];
            CallerContractInterface callerContractInstance;
            callerContractInstance = CallerContractInterface(_callerAddress);
            callerContractInstance.callback(
                computedSensorValue,
                _id,
                "position"
            );
        }
    }
}
