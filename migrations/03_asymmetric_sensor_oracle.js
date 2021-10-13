const AsymmetricSensorOracle = artifacts.require("AsymmetricSensorOracle");
const owner = "0xf17f52151EbEF6C7334FAD080c5704D77216b732";

module.exports = function(deployer) {
	deployer.deploy(AsymmetricSensorOracle, owner);
};
