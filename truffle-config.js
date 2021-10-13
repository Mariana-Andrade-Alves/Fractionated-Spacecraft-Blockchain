const PrivateKeyProvider = require("@truffle/hdwallet-provider");
// Oracle Private Key 
const privateKey = ["0xae6ae8e5ccbfb04590405997ee2d52d2b330726137b875053c36d94e974d162f"];
const privateKeyProvider = new PrivateKeyProvider(privateKey, "http://localhost:9545");

module.exports = {
	networks: {
		besuWallet: {
			provider: privateKeyProvider,
			network_id: "*",
			gasPrice: 0,
			//gas: '0x1ffffffffffffe'
			gas: "0x47b760"
		}
	},
	compilers: {
		solc: {
			version: "0.6.3"
		}
	}
};
