pragma solidity 0.6.3;

interface CallerContractInterface {
    function callback(
        int256 _sensorValue,
        uint256 id,
        string calldata _sensorType
    ) external;

    function updateSensorValue(address _oracleInstanceAddress) external;
}
