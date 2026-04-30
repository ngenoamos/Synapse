const { ethers } = require("hardhat");

async function main() {
  console.log("Deploying Cathedral contracts...");
  
  const [deployer] = await ethers.getSigners();
  console.log("Deploying with account:", deployer.address);
  console.log("Balance:", (await deployer.provider.getBalance(deployer.address)).toString());

  // Deploy SBT
  const CathedralSBT = await ethers.getContractFactory("CathedralSBT");
  const sbt = await CathedralSBT.deploy();
  await sbt.waitForDeployment();
  console.log("✅ CathedralSBT deployed to:", await sbt.getAddress());

  // Deploy Oracle
  const BACKEND_SIGNER = process.env.BACKEND_SIGNER || deployer.address;
  const CathedralOracle = await ethers.getContractFactory("CathedralOracle");
  const oracle = await CathedralOracle.deploy(await sbt.getAddress(), BACKEND_SIGNER);
  await oracle.waitForDeployment();
  console.log("✅ CathedralOracle deployed to:", await oracle.getAddress());

  // Grant oracle role to SBT
  const ORACLE_ROLE = await sbt.ORACLE_ROLE();
  await sbt.grantRole(ORACLE_ROLE, await oracle.getAddress());
  console.log("✅ Oracle role granted");

  // Deploy Credit Contract
  // LUSD on Arbitrum Sepolia: 0x5f98805A4E8be255a32880FDeC7F6728C6568bA0
  // For local testing, use a placeholder address
  const LUSD_ADDRESS = "0x5f98805A4E8be255a32880FDeC7F6728C6568bA0";
  const CathedralCredit = await ethers.getContractFactory("CathedralCredit");
  const credit = await CathedralCredit.deploy(await sbt.getAddress(), LUSD_ADDRESS);
  await credit.waitForDeployment();
  console.log("✅ CathedralCredit deployed to:", await credit.getAddress());

  // Grant credit role to SBT
  const CREDIT_CONTRACT_ROLE = await sbt.CREDIT_CONTRACT_ROLE();
  await sbt.grantRole(CREDIT_CONTRACT_ROLE, await credit.getAddress());
  console.log("✅ Credit role granted");

  console.log("\n🎉 All contracts deployed successfully!");
  console.log("========================================");
  console.log("CathedralSBT:", await sbt.getAddress());
  console.log("CathedralOracle:", await oracle.getAddress());
  console.log("CathedralCredit:", await credit.getAddress());
  console.log("========================================");
}

main().catch(console.error);
