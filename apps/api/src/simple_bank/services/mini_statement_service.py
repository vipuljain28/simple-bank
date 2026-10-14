"""Mini statement service for retrieving account transaction history."""
from decimal import Decimal
from typing import Literal

from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from simple_bank.domain.account_numbers import mask_account_number
from simple_bank.domain.errors import NotFound
from simple_bank.domain.timestamps import to_ist_iso8601
from simple_bank.persistence.models import Account, Transaction
from simple_bank.api.schemas.mini_statement_schema import (
    TransactionDetail,
    MiniStatementResponse,
)


class MiniStatementService:
    """Service for retrieving mini statement (last 10 transactions)."""
    
    def __init__(self, db: Session):
        """Initialize service with database session.
        
        Args:
            db: SQLAlchemy ORM session for database access.
        """
        self.db = db
    
    def get_mini_statement(
        self,
        account_number: str,
        authenticated_user_id: str
    ) -> MiniStatementResponse:
        """Retrieve mini statement for an account.
        
        Args:
            account_number: The account number to retrieve statement for.
            authenticated_user_id: The authenticated user's ID (from JWT).
            
        Returns:
            MiniStatementResponse with account info and last 10 transactions.
            
        Raises:
            Unauthorized: If user is not the account owner.
            NotFound: If account does not exist (indistinguishable from unauthorized).
        """
        # Query account with its transactions, ordered by newest first
        account = self.db.execute(
            select(Account).where(Account.account_number == account_number)
        ).scalar_one_or_none()
        
        if account is None:
            # Return 404 without distinguishing between "not found" and "unauthorized"
            # to prevent account enumeration attacks
            raise NotFound(f"Account not found")
        
        # Check if authenticated user owns this account
        if account.user_id != authenticated_user_id:
            # Return 404 even if unauthorized to prevent enumeration
            raise NotFound(f"Account not found")
        
        # Get last 10 transfers for this account (newest first)
        transfers = self.db.execute(
            select(Transaction)
            .where(
                (Transaction.from_account == account_number) |
                (Transaction.to_account == account_number)
            )
            .order_by(desc(Transaction.created_at))
            .limit(10)
        ).scalars().all()
        
        # Convert to transaction details
        transactions = []
        for transfer in transfers:
            # Determine if this is a DEBIT or CREDIT for this account
            if transfer.from_account == account_number:
                txn_type: Literal["DEBIT", "CREDIT"] = "DEBIT"
                amount = transfer.amount  # Money going out
            else:  # to_account == account_number
                txn_type = "CREDIT"
                amount = transfer.amount  # Money coming in
            
            # Build transaction description with masked account number
            if transfer.from_account == account_number:
                # This account sent money
                other_account = mask_account_number(transfer.to_account)
                description = f"Transfer to {other_account}"
            else:
                # This account received money
                other_account = mask_account_number(transfer.from_account)
                description = f"Transfer from {other_account}"
            
            # Get balance after this transaction
            # For each transaction, we need to calculate what the balance was
            # after that transaction occurred
            balance_after = self._calculate_balance_after_transfer(
                account_number,
                transfer
            )
            
            transaction = TransactionDetail(
                timestamp=to_ist_iso8601(transfer.created_at),
                type=txn_type,
                amount=f"{amount:.2f}",
                balance_after=f"{balance_after:.2f}",
                description=description
            )
            transactions.append(transaction)
        
        # Return mini statement response
        masked_account = mask_account_number(account_number)
        current_balance = Decimal(str(account.balance))
        
        return MiniStatementResponse(
            account_number=masked_account,
            current_balance=f"{current_balance:.2f}",
            transactions=transactions
        )
    
    def _calculate_balance_after_transfer(
        self,
        account_number: str,
        transfer: Transfer
    ) -> Decimal:
        """Calculate account balance immediately after a specific transfer.
        
        Args:
            account_number: The account to calculate balance for.
            transfer: The transfer event.
            
        Returns:
            Balance after the transfer occurred.
        """
        # Get current balance
        current_balance = self.db.execute(
            select(Account).where(Account.account_number == account_number)
        ).scalar_one().balance
        
        current_balance = Decimal(str(current_balance))
        transfer_amount = Decimal(str(transfer.amount))
        
        # Walk backwards through all transfers to calculate balance at this point
        # Get all transfers after this one (newer)
        newer_transfers = self.db.execute(
            select(Transaction)
            .where(
                ((Transaction.from_account == account_number) |
                 (Transaction.to_account == account_number)) &
                (Transaction.created_at > transfer.created_at)
            )
        ).scalars().all()
        
        balance_at_transfer = current_balance
        for t in newer_transfers:
            if t.from_account == account_number:
                # Money went out, so add it back
                balance_at_transfer += Decimal(str(t.amount))
            else:
                # Money came in, so subtract it
                balance_at_transfer -= Decimal(str(t.amount))
        
        return balance_at_transfer
