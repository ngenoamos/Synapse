// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract CathedralSBT is ERC721, AccessControl {
    bytes32 public constant ORACLE_ROLE = keccak256("ORACLE_ROLE");
    bytes32 public constant CREDIT_CONTRACT_ROLE = keccak256("CREDIT_CONTRACT_ROLE");

    struct SBTData {
        uint256 srsScore;
        uint256 lastScoringTimestamp;
        uint256 successfulRepayments;
        uint256 defaultCount;
        bool blacklisted;
        bytes32 behaviorFingerprint;
    }

    mapping(address => SBTData) public sbtData;
    
    event SBTMinted(address indexed wallet, uint256 srsScore, uint256 timestamp);
    event ScoreUpdated(address indexed wallet, uint256 oldScore, uint256 newScore, string reason);
    event RepaymentMade(address indexed wallet, uint256 loanId, uint256 newRepaymentCount);

    constructor() ERC721("Cathedral Soulbound Token", "CATH-SBT") {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ORACLE_ROLE, msg.sender);
    }

    function mintSBT(address to, uint256 srsScore, bytes32 behaviorFingerprint) 
        external 
        onlyRole(ORACLE_ROLE) 
    {
        require(balanceOf(to) == 0, "CathedralSBT: Already has SBT");
        require(srsScore >= 50, "CathedralSBT: SRS too low for minting");
        
        uint256 tokenId = uint256(uint160(to));
        _safeMint(to, tokenId);
        
        sbtData[to] = SBTData({
            srsScore: srsScore,
            lastScoringTimestamp: block.timestamp,
            successfulRepayments: 0,
            defaultCount: 0,
            blacklisted: false,
            behaviorFingerprint: behaviorFingerprint
        });
        
        emit SBTMinted(to, srsScore, block.timestamp);
    }

    function updateScore(address wallet, uint256 newScore, string calldata reason) 
        external 
    {
        require(hasRole(ORACLE_ROLE, msg.sender) || hasRole(CREDIT_CONTRACT_ROLE, msg.sender), 
                "CathedralSBT: Unauthorized");
        require(balanceOf(wallet) > 0, "CathedralSBT: No SBT for wallet");
        
        uint256 oldScore = sbtData[wallet].srsScore;
        sbtData[wallet].srsScore = newScore;
        sbtData[wallet].lastScoringTimestamp = block.timestamp;
        
        emit ScoreUpdated(wallet, oldScore, newScore, reason);
    }

    function recordRepayment(address wallet, uint256 loanId) external onlyRole(CREDIT_CONTRACT_ROLE) {
        sbtData[wallet].successfulRepayments++;
        emit RepaymentMade(wallet, loanId, sbtData[wallet].successfulRepayments);
    }

    function getCurrentSRS(address wallet) external view returns (uint256) {
        require(balanceOf(wallet) > 0, "CathedralSBT: No SBT for wallet");
        return sbtData[wallet].srsScore;
    }

    function getRepaymentHistory(address wallet) external view returns (uint256) {
        return sbtData[wallet].successfulRepayments;
    }

    function getDefaultCount(address wallet) external view returns (uint256) {
        return sbtData[wallet].defaultCount;
    }

    function isBlacklisted(address wallet) external view returns (bool) {
        return sbtData[wallet].blacklisted;
    }

    // ========== SOULBOUND PROPERTIES ==========
    
    function transferFrom(address, address, uint256) public pure override {
        revert("CathedralSBT: Soulbound token cannot be transferred");
    }

    function safeTransferFrom(address, address, uint256, bytes memory) public pure override {
        revert("CathedralSBT: Soulbound token cannot be transferred");
    }

    function approve(address, uint256) public pure override {
        revert("CathedralSBT: Soulbound token cannot be approved");
    }

    function setApprovalForAll(address, bool) public pure override {
        revert("CathedralSBT: Soulbound token cannot be approved");
    }

    function supportsInterface(bytes4 interfaceId) 
        public 
        view 
        override(ERC721, AccessControl) 
        returns (bool) 
    {
        return super.supportsInterface(interfaceId);
    }
}