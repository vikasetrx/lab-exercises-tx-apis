from fastapi import FastAPI, Query, Path, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import random

app = FastAPI(title="Bank API", 
              description="API for retrieving bank account details and transactions",
              version="1.0.0")

# Define account types
ACCOUNT_TYPES = ["Transactional", "Credit Card", "Loan"]

# Define models with Pydantic
class BankAccount(BaseModel):
    id: int
    account_name: str
    account_type: str
    available_balance: float
    total_balance: float

class Transaction(BaseModel):
    id: int
    transaction_reference: str
    transaction_amount: float
    transaction_type: str  # "debit" or "credit"
    transaction_date: str

class AccountsResponse(BaseModel):
    accounts: List[BankAccount]
    total_count: int

class TransactionsResponse(BaseModel):
    account_id: int
    transactions: List[Transaction]
    total_count: int

class MultiAccountTransactionsResponse(BaseModel):
    accounts: Dict[str, List[Transaction]]
    total_transactions: int
    
# Generate sample account data
def generate_accounts(count=20):
    accounts = []
    
    # Common account name prefixes
    name_prefixes = ["Main", "Joint", "Personal", "Business", "Savings", "Holiday", 
                     "Emergency", "Investment", "Everyday", "Bonus", "Mortgage", "Auto"]
    
    for i in range(1, count + 1):
        # Generate random account details
        account_type = random.choice(ACCOUNT_TYPES)
        
        # Logic for balances based on account type
        if account_type == "Transactional":
            total_balance = round(random.uniform(1000, 50000), 2)
            # Available might be less than total due to pending transactions
            available_balance = round(total_balance - random.uniform(0, 500), 2)
            name_suffix = "Account"
        elif account_type == "Credit Card":
            # Credit limit between $1,000 and $20,000
            credit_limit = round(random.uniform(1000, 20000), 2)
            # Some amount has been used
            used_amount = round(random.uniform(0, credit_limit * 0.8), 2)
            total_balance = -used_amount  # Negative because it's money owed
            available_balance = credit_limit - used_amount
            name_suffix = "Card"
        else:  # Loan
            # Loan amount between $5,000 and $500,000
            original_loan = round(random.uniform(5000, 500000), 2)
            # Some amount has been repaid
            repaid_amount = round(random.uniform(0, original_loan * 0.5), 2)
            total_balance = -(original_loan - repaid_amount)  # Negative because it's money owed
            available_balance = 0  # Typically loans don't have available balance
            name_suffix = "Loan"
        
        # Generate account name
        account_name = f"{random.choice(name_prefixes)} {name_suffix}"
        
        account = BankAccount(
            id=i,
            account_name=account_name,
            account_type=account_type,
            available_balance=available_balance,
            total_balance=total_balance
        )
        accounts.append(account)
    
    return accounts

# Generate transactions for a specific account
def generate_transactions_for_account(account_id, count=5):
    transactions = []
    
    # Sample transaction references based on common banking transactions
    debit_references = [
        "PAYMENT: Online Purchase", 
        "ATM WITHDRAWAL", 
        "POS PURCHASE: Grocery Store",
        "BILL PAYMENT: Utility",
        "TRANSFER TO: Savings Account",
        "SUBSCRIPTION: Streaming Service",
        "RESTAURANT PAYMENT",
        "MOBILE PAYMENT",
        "INSURANCE PREMIUM",
        "LOAN REPAYMENT"
    ]
    
    credit_references = [
        "SALARY DEPOSIT",
        "TRANSFER FROM: Checking Account",
        "REFUND: Online Store",
        "INTEREST PAYMENT",
        "TAX REFUND",
        "DIVIDEND PAYMENT",
        "CASH DEPOSIT",
        "PAYMENT RECEIVED",
        "REIMBURSEMENT",
        "GOVERNMENT PAYMENT"
    ]
    
    for i in range(1, count + 1):
        # Generate random date within the last 14 days
        days_ago = random.randint(0, 14)
        trans_date = datetime.now() - timedelta(days=days_ago)
        date_str = trans_date.strftime("%Y-%m-%d")
        
        # Determine if debit or credit
        is_debit = random.choice([True, False])
        transaction_type = "debit" if is_debit else "credit"
        
        # Generate amount between $5 and $1000
        amount = round(random.uniform(5, 1000), 2)
        
        # Choose appropriate reference
        if is_debit:
            reference = random.choice(debit_references)
        else:
            reference = random.choice(credit_references)
        
        transaction = Transaction(
            id=account_id * 100 + i,  # Create unique transaction ID
            transaction_reference=reference,
            transaction_amount=amount,
            transaction_type=transaction_type,
            transaction_date=date_str
        )
        transactions.append(transaction)
    
    # Sort transactions by date (most recent first)
    transactions.sort(key=lambda x: x.transaction_date, reverse=True)
    
    return transactions

@app.get("/")
def read_root():
    return {"message": "Welcome to the Bank API. Go to /docs for documentation."}

@app.get("/api/accounts", response_model=AccountsResponse, 
         summary="Get bank accounts",
         description="Retrieve a list of bank accounts with optional filtering")
def get_accounts(
    limit: int = Query(20, description="Number of accounts to return (max 20)"),
    account_type: Optional[str] = Query(None, description="Filter by account type (Transactional, Credit Card, or Loan)")
):
    # Ensure limit doesn't exceed 20
    limit = min(limit, 20)
    
    # Generate accounts
    all_accounts = generate_accounts(20)
    
    # Apply account type filter if provided
    if account_type and account_type in ACCOUNT_TYPES:
        all_accounts = [a for a in all_accounts if a.account_type == account_type]
    
    # Apply limit
    accounts = all_accounts[:limit]
    
    return {
        "accounts": accounts,
        "total_count": len(accounts)
    }

@app.get("/api/accounts/{account_id}/transactions", response_model=TransactionsResponse,
         summary="Get account transactions",
         description="Retrieve recent transactions for a specific account")
def get_account_transactions(
    account_id: int = Path(..., description="The ID of the account to retrieve transactions for"),
    limit: int = Query(5, description="Number of transactions to return (max 5)")
):
    # Ensure limit doesn't exceed 5
    limit = min(limit, 5)
    
    # Check if account exists (in a real API, you'd query a database)
    all_accounts = generate_accounts(20)
    account_ids = [account.id for account in all_accounts]
    
    if account_id not in account_ids:
        raise HTTPException(status_code=404, detail=f"Account with ID {account_id} not found")
    
    # Generate transactions for the account
    transactions = generate_transactions_for_account(account_id, count=limit)
    
    return {
        "account_id": account_id,
        "transactions": transactions,
        "total_count": len(transactions)
    }

@app.get("/api/transactions", response_model=MultiAccountTransactionsResponse,
         summary="Get transactions for multiple accounts",
         description="Retrieve recent transactions for multiple accounts at once")
def get_multiple_account_transactions(
    account_ids: str = Query(..., description="Comma-separated list of account IDs (e.g., '1,3,5')"),
    transactions_per_account: int = Query(5, description="Number of transactions per account (max 5)")
):
    # Parse account IDs from the query string
    try:
        id_list = [int(aid.strip()) for aid in account_ids.split(",") if aid.strip()]
        if not id_list:
            raise HTTPException(status_code=400, detail="No valid account IDs provided")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid account ID format. Use comma-separated integers.")
    
    # Ensure limit doesn't exceed 5
    transactions_per_account = min(transactions_per_account, 5)
    
    # Check if accounts exist (in a real API, you'd query a database)
    all_accounts = generate_accounts(20)
    valid_account_ids = [account.id for account in all_accounts]
    
    # Filter to valid account IDs only
    valid_ids = [aid for aid in id_list if aid in valid_account_ids]
    invalid_ids = [aid for aid in id_list if aid not in valid_account_ids]
    
    if not valid_ids:
        raise HTTPException(status_code=404, detail="None of the provided account IDs were found")
    
    # Generate transactions for each valid account
    account_transactions = {}
    total_transactions = 0
    
    for account_id in valid_ids:
        transactions = generate_transactions_for_account(account_id, count=transactions_per_account)
        account_transactions[str(account_id)] = transactions
        total_transactions += len(transactions)
    
    # Add warning about invalid IDs if any
    result = {
        "accounts": account_transactions,
        "total_transactions": total_transactions
    }
    
    if invalid_ids:
        result["warnings"] = f"Account IDs not found: {', '.join(map(str, invalid_ids))}"
    
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)