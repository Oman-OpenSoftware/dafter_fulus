"""
Database models for the Bank Email Parser & Account Tracker.
"""

import enum
import logging
from datetime import datetime
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)

class TransactionType(models.TextChoices):
    """Enum for transaction types."""
    INCOME = 'income', 'Income'
    EXPENSE = 'expense', 'Expense'
    TRANSFER = 'transfer', 'Transfer'
    UNKNOWN = 'unknown', 'Unknown'

class Account(models.Model):
    """Account model representing a bank account."""
    account_number = models.CharField(max_length=50, unique=True)
    bank_name = models.CharField(max_length=100)
    account_holder = models.CharField(max_length=100, blank=True, null=True)
    balance = models.FloatField(default=0.0)
    currency = models.CharField(max_length=10, default='OMR')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"

class Transaction(models.Model):
    """Transaction model representing a financial transaction."""
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(
        max_length=10,
        choices=TransactionType.choices,
        default=TransactionType.UNKNOWN
    )
    amount = models.FloatField()
    currency = models.CharField(max_length=10, default='OMR')
    date_time = models.DateTimeField()
    description = models.TextField(blank=True, null=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)

    # Bank-specific fields
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    branch = models.CharField(max_length=200, blank=True, null=True)

    # Counterparty information
    transaction_sender = models.CharField(max_length=200, blank=True, null=True)
    transaction_receiver = models.CharField(max_length=200, blank=True, null=True)
    counterparty_name = models.CharField(max_length=200, blank=True, null=True)

    # New fields from your function
    from_party = models.CharField(max_length=200, blank=True, null=True)  # 'me' or actual name
    to_party = models.CharField(max_length=200, blank=True, null=True)    # 'me' or actual name
    transaction_details = models.CharField(max_length=500, blank=True, null=True)  # TRANSFER, Cash Dep, SALARY, etc.

    # Additional fields
    country = models.CharField(max_length=100, blank=True, null=True)

    # Email tracking
    email_id = models.CharField(max_length=100, blank=True, null=True)
    email_date = models.CharField(max_length=200, blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} {self.currency} - {self.date_time}"

class TransactionRepository:
    """Repository class for transaction operations."""

    @staticmethod
    def create_account(account_data):
        """
        Create a new account.

        Args:
            account_data (dict): Account data.

        Returns:
            Account: Created account or None if creation fails.
        """
        try:
            # Check if account already exists
            try:
                existing_account = Account.objects.get(account_number=account_data['account_number'])
                logger.info(f"Account {account_data['account_number']} already exists")
                return existing_account
            except Account.DoesNotExist:
                pass

            account = Account(
                account_number=account_data['account_number'],
                bank_name=account_data.get('bank_name', 'Unknown'),
                account_holder=account_data.get('account_holder'),
                currency=account_data.get('currency', 'OMR')
            )

            account.save()
            logger.info(f"Created account: {account.account_number}")
            return account

        except Exception as e:
            logger.error(f"Error creating account: {str(e)}")
            return None

    @staticmethod
    def create_transaction(transaction_data):
        """
        Create a new transaction.

        Args:
            transaction_data (dict): Transaction data.

        Returns:
            Transaction: Created transaction or None if creation fails.
        """
        try:
            # Get or create account
            account_number = transaction_data.get('account_number')
            if not account_number:
                logger.error("No account number provided for transaction")
                return None

            try:
                account = Account.objects.get(account_number=account_number)
            except Account.DoesNotExist:
                # Create account if it doesn't exist
                account_data = {
                    'account_number': account_number,
                    'bank_name': transaction_data.get('bank_name', 'Unknown'),
                    'currency': transaction_data.get('currency', 'OMR')
                }
                account = TransactionRepository.create_account(account_data)
                if not account:
                    return None

            # Check if transaction already exists (by transaction_id and date)
            if transaction_data.get('transaction_id'):
                try:
                    existing_transaction = Transaction.objects.get(
                        account=account,
                        transaction_id=transaction_data['transaction_id']
                    )
                    logger.info(f"Transaction {transaction_data['transaction_id']} already exists")
                    return existing_transaction
                except Transaction.DoesNotExist:
                    pass

            # Convert transaction type
            transaction_type_str = transaction_data.get('transaction_type', 'unknown').lower()
            if transaction_type_str not in [choice[0] for choice in TransactionType.choices]:
                transaction_type = TransactionType.UNKNOWN
            else:
                transaction_type = transaction_type_str

            transaction = Transaction(
                account=account,
                transaction_type=transaction_type,
                amount=transaction_data.get('amount', 0.0),
                currency=transaction_data.get('currency', 'OMR'),
                date_time=transaction_data.get('date_time', timezone.now()),
                description=transaction_data.get('description'),
                transaction_id=transaction_data.get('transaction_id'),
                bank_name=transaction_data.get('bank_name'),
                branch=transaction_data.get('branch'),
                transaction_sender=transaction_data.get('transaction_sender'),
                transaction_receiver=transaction_data.get('transaction_receiver'),
                counterparty_name=transaction_data.get('counterparty_name'),
                from_party=transaction_data.get('from_party'),
                to_party=transaction_data.get('to_party'),
                transaction_details=transaction_data.get('transaction_details'),
                country=transaction_data.get('country'),
                email_id=transaction_data.get('email_id'),
                email_date=transaction_data.get('email_date')
            )

            transaction.save()
            logger.info(f"Created transaction: {transaction.id}")
            return transaction

        except Exception as e:
            logger.error(f"Error creating transaction: {str(e)}")
            return None

    @staticmethod
    def get_account_summary(account_number):
        """
        Get account summary including balance and transaction counts.

        Args:
            account_number (str): Account number.

        Returns:
            dict: Account summary or None if not found.
        """
        try:
            try:
                account = Account.objects.get(account_number=account_number)
            except Account.DoesNotExist:
                return None

            transactions = Transaction.objects.filter(account=account)

            total_income = sum(t.amount for t in transactions if t.transaction_type == TransactionType.INCOME)
            total_expense = sum(t.amount for t in transactions if t.transaction_type == TransactionType.EXPENSE)
            total_transfer = sum(t.amount for t in transactions if t.transaction_type == TransactionType.TRANSFER)

            return {
                'account': account,
                'transaction_count': transactions.count(),
                'total_income': total_income,
                'total_expense': total_expense,
                'total_transfer': total_transfer,
                'net_balance': total_income - total_expense,
                'transactions': transactions
            }

        except Exception as e:
            logger.error(f"Error getting account summary: {str(e)}")
            return None

    @staticmethod
    def get_transactions_by_date_range(account_number, start_date, end_date):
        """
        Get transactions within a date range for an account.

        Args:
            account_number (str): Account number.
            start_date (datetime): Start date.
            end_date (datetime): End date.

        Returns:
            QuerySet: List of transactions.
        """
        try:
            try:
                account = Account.objects.get(account_number=account_number)
            except Account.DoesNotExist:
                return []

            transactions = Transaction.objects.filter(
                account=account,
                date_time__gte=start_date,
                date_time__lte=end_date
            ).order_by('-date_time')

            return transactions

        except Exception as e:
            logger.error(f"Error getting transactions by date range: {str(e)}")
            return []