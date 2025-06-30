"""
Views for the Money Tracker app.
"""

import os
import logging
from datetime import datetime
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

# Import path_setup to add the parent directory to the Python path
from . import path_setup

from .forms import EmailContentForm, EmailFetchForm
from .models import TransactionRepository
from money_tracker.services.parser_service import TransactionParser
from money_tracker.services.email_service import EmailService

# Setup logging
logger = logging.getLogger(__name__)

# Initialize services
parser = TransactionParser()
email_service = EmailService()

def index(request):
    """Home page with options to input email data."""
    email_content_form = EmailContentForm()
    email_fetch_form = EmailFetchForm()
    return render(request, 'index.html', {
        'email_content_form': email_content_form,
        'email_fetch_form': email_fetch_form
    })

def parse_email(request):
    """Parse email data from various sources."""
    if request.method != 'POST':
        return redirect('index')

    form = EmailContentForm(request.POST, request.FILES)
    if not form.is_valid():
        messages.error(request, 'Please correct the errors in the form.')
        return redirect('index')

    email_data = {}
    source = form.cleaned_data['source']

    if source == 'paste':
        # Handle pasted email content
        email_content = form.cleaned_data['email_content']
        if not email_content:
            messages.error(request, 'Please paste email content')
            return redirect('index')

        email_data = {
            'id': f'manual_{datetime.now().strftime("%Y%m%d%H%M%S")}',
            'subject': form.cleaned_data.get('subject', 'Manual Entry'),
            'from': form.cleaned_data.get('from_email', 'manual@example.com'),
            'date': datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z'),
            'body': email_content
        }

    elif source == 'upload':
        # Handle uploaded email file
        email_file = form.cleaned_data.get('email_file')
        if not email_file:
            messages.error(request, 'No file selected')
            return redirect('index')

        try:
            # Save the file temporarily
            file_path = default_storage.save(
                os.path.join(settings.UPLOAD_FOLDER, email_file.name),
                ContentFile(email_file.read())
            )

            # Read the file content
            with default_storage.open(file_path) as f:
                email_content = f.read().decode('utf-8')

            email_data = {
                'id': f'upload_{datetime.now().strftime("%Y%m%d%H%M%S")}',
                'subject': email_file.name,
                'from': form.cleaned_data.get('from_email', 'upload@example.com'),
                'date': datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z'),
                'body': email_content
            }

            # Clean up the uploaded file
            default_storage.delete(file_path)
        except Exception as e:
            logger.error(f"Error reading uploaded file: {str(e)}")
            messages.error(request, f'Error reading file: {str(e)}')
            return redirect('index')

    else:
        messages.error(request, 'Invalid source')
        return redirect('index')

    # Parse the email data
    transaction_data = parser.parse_email(email_data)

    if not transaction_data:
        messages.error(request, 'Failed to parse email content. Make sure it contains valid transaction data.')
        return redirect('index')

    # Store the transaction data in session for display
    request.session['transaction_data'] = transaction_data

    # Optionally save to database if requested
    save_to_db = form.cleaned_data.get('save_to_db', False)
    if save_to_db:
        try:
            transaction = TransactionRepository.create_transaction(transaction_data)
            if transaction:
                messages.success(request, 'Transaction saved to database')
            else:
                messages.error(request, 'Failed to save transaction to database')
        except Exception as e:
            logger.error(f"Error saving transaction to database: {str(e)}")
            messages.error(request, f'Error saving to database: {str(e)}')

    return redirect('results')

def results(request):
    """Display the parsed transaction data."""
    transaction_data = request.session.get('transaction_data')
    if not transaction_data:
        messages.error(request, 'No transaction data available')
        return redirect('index')

    return render(request, 'results.html', {'transaction': transaction_data})

def accounts(request):
    """Display all accounts and their summaries."""
    try:
        from .models import Account
        accounts = Account.objects.all()

        summaries = []
        for account in accounts:
            summary = TransactionRepository.get_account_summary(account.account_number)
            if summary:
                summaries.append(summary)

        return render(request, 'accounts.html', {'summaries': summaries})
    except Exception as e:
        logger.error(f"Error getting account summaries: {str(e)}")
        messages.error(request, f'Error getting account summaries: {str(e)}')
        return redirect('index')

def account_details(request, account_number):
    """Display details for a specific account."""
    try:
        from .models import Account, Transaction

        try:
            account = Account.objects.get(account_number=account_number)
        except Account.DoesNotExist:
            messages.error(request, f'Account {account_number} not found')
            return redirect('accounts')

        transactions = Transaction.objects.filter(account=account).order_by('-date_time')
        summary = TransactionRepository.get_account_summary(account_number)

        return render(request, 'account_details.html', {
            'account': account,
            'transactions': transactions,
            'summary': summary
        })
    except Exception as e:
        logger.error(f"Error getting account details: {str(e)}")
        messages.error(request, f'Error getting account details: {str(e)}')
        return redirect('accounts')

def fetch_emails(request):
    """Fetch emails directly from the email account."""
    if request.method != 'POST':
        return redirect('index')

    form = EmailFetchForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Please correct the errors in the form.')
        return redirect('index')

    try:
        # Get email settings from form
        email_host = form.cleaned_data['email_host']
        email_port = form.cleaned_data['email_port']
        email_username = form.cleaned_data['email_username']
        email_password = form.cleaned_data['email_password']
        email_use_ssl = form.cleaned_data['email_use_ssl']
        bank_email_addresses = form.cleaned_data['bank_email_addresses']
        bank_email_subjects = form.cleaned_data['bank_email_subjects']

        # Create a custom email service with user-provided settings
        custom_email_service = EmailService(
            host=email_host,
            port=email_port,
            username=email_username,
            password=email_password,
            use_ssl=email_use_ssl,
            bank_email_addresses=bank_email_addresses.split(','),
            bank_email_subjects=bank_email_subjects.split(',')
        )

        # Connect to email
        if not custom_email_service.connect():
            messages.error(request, 'Failed to connect to email server. Check your email settings.')
            return redirect('index')

        # Get bank emails
        folder = form.cleaned_data['folder']
        unread_only = form.cleaned_data['unread_only']

        emails = custom_email_service.get_bank_emails(folder=folder, unread_only=unread_only)

        if not emails:
            messages.info(request, 'No bank emails found')
            return redirect('index')

        # Parse each email and store results
        parsed_emails = []
        for email_data in emails:
            transaction_data = parser.parse_email(email_data)
            if transaction_data:
                parsed_emails.append({
                    'email': email_data,
                    'transaction': transaction_data
                })

        if not parsed_emails:
            messages.info(request, 'No transaction data found in the emails')
            return redirect('index')

        # Store the first transaction in session for display
        request.session['transaction_data'] = parsed_emails[0]['transaction']

        # Optionally save to database if requested
        save_to_db = form.cleaned_data['save_to_db']
        if save_to_db:
            try:
                saved_count = 0
                for parsed_email in parsed_emails:
                    transaction = TransactionRepository.create_transaction(parsed_email['transaction'])
                    if transaction:
                        saved_count += 1

                if saved_count > 0:
                    messages.success(request, f'Saved {saved_count} transactions to database')
                else:
                    messages.error(request, 'Failed to save transactions to database')
            except Exception as e:
                logger.error(f"Error saving transactions to database: {str(e)}")
                messages.error(request, f'Error saving to database: {str(e)}')

        # Disconnect from email
        custom_email_service.disconnect()

        return redirect('results')
    except Exception as e:
        logger.error(f"Error fetching emails: {str(e)}")
        messages.error(request, f'Error fetching emails: {str(e)}')
        return redirect('index')
