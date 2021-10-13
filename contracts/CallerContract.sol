pragma solidity 0.6.3;
import "./SensorValueOracleInterface.sol";
import "./CallerContractInterface.sol";
import "./CommunicationOracleInterface.sol";

contract CallerContract is CallerContractInterface {
    int256 private sensorValue;
    address private communicationOracleAddress;
    CommunicationOracleInterface communicationInstance;

    mapping(address => SensorValueOracleInterface) private oracleInstance;
    mapping(address => bool) private oracleAddress;
    mapping(uint256 => bool) myRequests;

    event newOracleAddressEvent(address oracleAddress);
    event ReceivedNewRequestIdEvent(uint256 id);
    event ValueUpdatedEvent(int256 sensorValue, uint256 id);

    function addOracleInstanceAddress(address _oracleInstanceAddress) public {
        require(
            !oracleAddress[_oracleInstanceAddress],
            "This contract is already saved."
        );
        oracleAddress[_oracleInstanceAddress] = true;
        oracleInstance[_oracleInstanceAddress] = SensorValueOracleInterface(
            _oracleInstanceAddress
        );
    }

    function setCommunicationOracleInstanceAddress(
        address _communicationOracleAddress
    ) public {
        communicationOracleAddress = _communicationOracleAddress;
        communicationInstance = CommunicationOracleInterface(
            communicationOracleAddress
        );
    }

    function updateSensorValue(address _oracleInstanceAddress) public override {
        require(msg.sender == communicationOracleAddress,"You are not authorized to call this function.");
        uint256 id = oracleInstance[_oracleInstanceAddress]
            .getLatestSensorValue();
        myRequests[id] = true;
        emit ReceivedNewRequestIdEvent(id);
    }

    function callback(
        int256 _sensorValue,
        uint256 _id,
        string memory _sensorType
    ) public override onlyOracle {
        require(myRequests[_id], "This request is not in my pending list.");
        sensorValue = _sensorValue;
        delete myRequests[_id];
        emit ValueUpdatedEvent(_sensorValue, _id);
        communicationInstance.receiveSensorValue(sensorValue, _sensorType);
    }

    modifier onlyOracle() {
        require(
            oracleAddress[msg.sender],
            "You are not authorized to call this function."
        );
        _;
    }
}
