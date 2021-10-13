pragma solidity 0.6.3;

interface CommunicationOracleInterface {
    function receiveSensorValue(int256 _sensorValue, string calldata _sensorType) external;
}
