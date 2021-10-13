pragma solidity 0.6.3;

interface SensorValueOracleInterface {
    function getLatestSensorValue() external returns (uint256);
}
