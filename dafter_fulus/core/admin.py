"""
Admin configuration for the Money Tracker app.
"""

from django.contrib import admin
from .models import Account, Transaction

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    """Admin configuration for the Account model."""
    list_display = ('account_number', 'bank_name', 'account_holder', 'balance', 'currency')
    search_fields = ('account_number', 'bank_name', 'account_holder')
    list_filter = ('bank_name', 'currency')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin configuration for the Transaction model."""
    list_display = ('transaction_id', 'account', 'transaction_type', 'amount', 'currency', 'date_time')
    search_fields = ('transaction_id', 'description', 'account__account_number')
    list_filter = ('transaction_type', 'currency', 'bank_name')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'date_time'