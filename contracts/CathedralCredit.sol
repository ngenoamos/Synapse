// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "./CathedralSBT.sol";

contract CathedralCredit is AccessControl {
    CathedralSBT public sbtContract;
    IERC20 public lusdToken;
    
    struct Loan {
        address borrower;
        uint256 amount;
        uint256 startTime;
        uint256 endTime;
        bool repaid;
        bool defaulted;
    }
    
    mapping(uint256 => Loan) public loans;
    uint256 public loanCounter;
    mapping(address => uint256) public outstandingLoans;
    uint256 public treasuryBalance;
    uint256 public treasuryCapPercent = 80;
    uint256 public minSRSForLoan = 60;
    uint256 public baseCreditLimit = 100 * 1e18;
    
    event LoanRequested(uint256 indexed loanId, address indexed borrower, uint256 amount, uint256 duration);
    event LoanRepaid(uint256 indexed loanId, address indexed borrower);
    event LoanDefaulted(uint256 indexed loanId, address indexed borrower);

    constructor(address _sbtContract, address _lusdToken) {
        require(_sbtContract != address(0), "CathedralCredit: Invalid SBT contract");
        require(_lusdToken != address(0), "CathedralCredit: Invalid LUSD token");
        
        sbtContract = CathedralSBT(_sbtContract);
        lusdToken = IERC20(_lusdToken);
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
    }

    function creditLimit(address wallet) public view returns (uint256) {
        if (sbtContract.balanceOf(wallet) == 0) return 0;
        if (sbtContract.getCurrentSRS(wallet) < minSRSForLoan) return 0;
        
        uint256 repaymentCount = sbtContract.getRepaymentHistory(wallet);
        uint256 limit = baseCreditLimit + (repaymentCount * 10 * 1e18);
        
        return limit;
    }

    function requestLoan(uint256 amount, uint256 duration) external {
        require(amount > 0, "CathedralCredit: Amount must be > 0");
        require(duration >= 7 days && duration <= 180 days, "CathedralCredit: Invalid duration");
        require(sbtContract.balanceOf(msg.sender) > 0, "CathedralCredit: No SBT");
        require(sbtContract.getCurrentSRS(msg.sender) >= minSRSForLoan, "CathedralCredit: SRS too low");
        require(amount <= creditLimit(msg.sender), "CathedralCredit: Exceeds credit limit");
        
        uint256 totalOutstanding = getTotalOutstandingLoans();
        uint256 treasuryCap = (treasuryBalance * treasuryCapPercent) / 100;
        require(totalOutstanding + amount <= treasuryCap, "CathedralCredit: Treasury cap reached");
        require(lusdToken.balanceOf(address(this)) >= amount, "CathedralCredit: Insufficient treasury");
        
        uint256 loanId = loanCounter++;
        loans[loanId] = Loan({
            borrower: msg.sender,
            amount: amount,
            startTime: block.timestamp,
            endTime: block.timestamp + duration,
            repaid: false,
            defaulted: false
        });
        
        outstandingLoans[msg.sender] += amount;
        require(lusdToken.transfer(msg.sender, amount), "CathedralCredit: LUSD transfer failed");
        
        emit LoanRequested(loanId, msg.sender, amount, duration);
    }

    function repayLoan(uint256 loanId) external {
        Loan storage loan = loans[loanId];
        require(loan.borrower == msg.sender, "CathedralCredit: Not your loan");
        require(!loan.repaid, "CathedralCredit: Loan already repaid");
        require(!loan.defaulted, "CathedralCredit: Loan already defaulted");
        require(block.timestamp <= loan.endTime, "CathedralCredit: Loan overdue");
        
        require(lusdToken.transferFrom(msg.sender, address(this), loan.amount), "CathedralCredit: Repayment failed");
        
        loan.repaid = true;
        outstandingLoans[msg.sender] -= loan.amount;
        sbtContract.recordRepayment(msg.sender, loanId);
        
        uint256 newSRS = sbtContract.getCurrentSRS(msg.sender) + 5;
        if (newSRS > 100) newSRS = 100;
        sbtContract.updateScore(msg.sender, newSRS, "repayment");
        
        emit LoanRepaid(loanId, msg.sender);
    }

    function getTotalOutstandingLoans() public view returns (uint256) {
        uint256 total = 0;
        for (uint256 i = 0; i < loanCounter; i++) {
            if (!loans[i].repaid && !loans[i].defaulted) {
                total += loans[i].amount;
            }
        }
        return total;
    }

    function depositTreasury(uint256 amount) external {
        require(lusdToken.transferFrom(msg.sender, address(this), amount), "CathedralCredit: Deposit failed");
        treasuryBalance += amount;
    }

    function withdrawTreasury(uint256 amount) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(treasuryBalance >= amount, "CathedralCredit: Insufficient treasury");
        require(lusdToken.transfer(msg.sender, amount), "CathedralCredit: Withdrawal failed");
        treasuryBalance -= amount;
    }
}