// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "./CathedralSBT.sol";

contract CathedralOracle is AccessControl {
    bytes32 public constant SIGNER_ROLE = keccak256("SIGNER_ROLE");
    
    CathedralSBT public sbtContract;
    mapping(bytes32 => bool) public usedSignatures;
    address public backendSigner;
    
    event SBTMintedViaOracle(address indexed wallet, uint256 srsScore);

    constructor(address _sbtContract, address _backendSigner) {
        sbtContract = CathedralSBT(_sbtContract);
        backendSigner = _backendSigner;
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(SIGNER_ROLE, _backendSigner);
    }

    function mintSBT(
        address wallet,
        uint256 srsScore,
        bytes32 behaviorFingerprint,
        uint256 timestamp,
        bytes memory signature
    ) external {
        require(block.timestamp <= timestamp + 5 minutes, "Signature expired");
        
        bytes32 messageHash = keccak256(abi.encodePacked(wallet, srsScore, behaviorFingerprint, timestamp));
        require(!usedSignatures[messageHash], "Signature already used");
        
        // Manual Ethereum signed message prefix (compatible with older ethers)
        bytes32 prefixedHash = keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32", messageHash));
        address signer = ECDSA.recover(prefixedHash, signature);
        require(signer == backendSigner, "Invalid signature");
        
        usedSignatures[messageHash] = true;
        sbtContract.mintSBT(wallet, srsScore, behaviorFingerprint);
        
        emit SBTMintedViaOracle(wallet, srsScore);
    }
}