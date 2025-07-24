from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Mock data for the bank CRM system
customers = [
    {
        'id': 1,
        'name': 'Rajesh Kumar Sharma',
        'email': 'rajesh.sharma@email.com',
        'phone': '+91-9876543210',
        'account_number': 'GTB001',
        'balance': 1575000.50,
        'account_type': 'Savings',
        'status': 'Active',
        'join_date': '2023-01-15',
        'last_transaction': '2024-06-08',
        'city': 'Mumbai',
        'aadhar': '1234-XXXX-XXXX',
        'pan': 'ABCDXXXXX',
        'crm_ref': 'GTBCRM230115001'
    },    {
        'id': 2,
        'name': 'Priya Gupta',
        'email': 'priya.gupta@email.com',
        'phone': '+91-9876543211',
        'account_number': 'GTB002',
        'balance': 2895000.75,
        'account_type': 'Current',
        'status': 'Active',
        'join_date': '2023-03-22',
        'last_transaction': '2024-06-10',
        'city': 'Delhi',
        'aadhar': '2345-XXXX-XXXX',
        'pan': 'BCDEXXXXX',
        'crm_ref': 'GTBCRM230322002'
    },    {
        'id': 3,
        'name': 'Arjun Singh Rajput',
        'email': 'arjun.rajput@email.com',
        'phone': '+91-9876543212',
        'account_number': 'GTB003',
        'balance': 520000.25,
        'account_type': 'Savings',
        'status': 'Active',
        'join_date': '2023-05-10',
        'last_transaction': '2024-06-09',
        'city': 'Jaipur',
        'aadhar': '1234-XXXX-XXXX',
        'pan': 'ABCDXXXXX',
        'crm_ref': 'GTBCRM230510003'
    },    {
        'id': 4,
        'name': 'Sneha Patel',
        'email': 'sneha.patel@email.com',
        'phone': '+91-9876543213',
        'account_number': 'GTB004',
        'balance': 4210000.00,
        'account_type': 'Premium',
        'status': 'Active',
        'join_date': '2022-12-08',
        'last_transaction': '2024-06-11',
        'city': 'Ahmedabad',
        'aadhar': '1234-XXXX-XXXX',
        'pan': 'ABCDXXXXX',
        'crm_ref': 'GTBCRM221208004'
    },    {
        'id': 5,
        'name': 'Vikram Reddy',
        'email': 'vikram.reddy@email.com',
        'phone': '+91-9876543214',
        'account_number': 'GTB005',
        'balance': 125000.80,
        'account_type': 'Current',
        'status': 'Inactive',
        'join_date': '2023-08-18',
        'last_transaction': '2024-05-20',
        'city': 'Hyderabad',
       'aadhar': '1234-XXXX-XXXX',
        'pan': 'ABCDXXXXX',
        'crm_ref': 'GTBCRM230818005'
    },    {
        'id': 6,
        'name': 'Anita Desai',
        'email': 'anita.desai@email.com',
        'phone': '+91-9876543215',
        'account_number': 'GTB006',
        'balance': 3250000.00,
        'account_type': 'Premium',
        'status': 'Active',
        'join_date': '2022-09-12',
        'last_transaction': '2024-06-12',
        'city': 'Pune',
       'aadhar': '1234-XXXX-XXXX',
        'pan': 'ABCDXXXXX',
        'crm_ref': 'GTBCRM220912006'
    }
]

transactions = [
    {
        'id': 1,
        'customer_id': 1,
        'type': 'Deposit',
        'amount': 50000.00,
        'date': '2024-06-08',
        'description': 'Salary credit from TCS Ltd',
        'ref_number': 'GTBK24160782341',
        'utr_number': 'GTBK2416087234'
    },
    {
        'id': 2,
        'customer_id': 2,
        'type': 'Withdrawal',
        'amount': 20000.00,
        'date': '2024-06-10',
        'description': 'ATM withdrawal - Connaught Place',
        'ref_number': 'GTBK24162345678',
        'utr_number': 'GTBK2416234567'
    },
    {
        'id': 3,
        'customer_id': 3,
        'type': 'Transfer',
        'amount': 100000.00,
        'date': '2024-06-09',
        'description': 'NEFT to GTB002 - House rent',
        'ref_number': 'GTBK24161876543',
        'utr_number': 'GTBK2416187654'
    },
    {
        'id': 4,
        'customer_id': 4,
        'type': 'Deposit',
        'amount': 250000.00,
        'date': '2024-06-11',
        'description': 'Business profit transfer',
        'ref_number': 'GTBK24163456789',
        'utr_number': 'GTBK2416345678'
    },
    {
        'id': 5,
        'customer_id': 1,
        'type': 'EMI',
        'amount': 25000.00,
        'date': '2024-06-05',
        'description': 'Home loan EMI payment',
        'ref_number': 'GTBK24156789012',
        'utr_number': 'GTBK2415678901'
    },
    {
        'id': 6,
        'customer_id': 4,
        'type': 'EMI',
        'amount': 15000.00,
        'date': '2024-06-03',
        'description': 'Car loan EMI payment',
        'ref_number': 'GTBK24154567890',
        'utr_number': 'GTBK2415456789'
    }
]

# Loan data
loans = [
    {
        'id': 1,
        'customer_id': 1,
        'loan_type': 'Home Loan',
        'principal_amount': 2500000.00,
        'outstanding_amount': 1875000.00,
        'interest_rate': 8.5,
        'tenure_months': 240,
        'emi_amount': 25000.00,
        'start_date': '2022-06-01',
        'status': 'Active',
        'next_due_date': '2024-07-05',
        'loan_ref': 'GTBL2022450871',
        'sanction_ref': 'GTBSANC220601001'
    },
    {
        'id': 2,
        'customer_id': 4,
        'loan_type': 'Car Loan',
        'principal_amount': 800000.00,
        'outstanding_amount': 450000.00,
        'interest_rate': 9.2,
        'tenure_months': 60,
        'emi_amount': 15000.00,
        'start_date': '2023-01-15',
        'status': 'Active',
        'next_due_date': '2024-07-03',
        'loan_ref': 'GTBL2023298456',
        'sanction_ref': 'GTBSANC230115004'
    },
    {
        'id': 3,
        'customer_id': 2,
        'loan_type': 'Personal Loan',
        'principal_amount': 300000.00,
        'outstanding_amount': 180000.00,
        'interest_rate': 12.5,
        'tenure_months': 36,
        'emi_amount': 10500.00,
        'start_date': '2023-08-10',
        'status': 'Active',
        'next_due_date': '2024-07-10',
        'loan_ref': 'GTBL2023675432',
        'sanction_ref': 'GTBSANC230810002'
    },
    {
        'id': 4,
        'customer_id': 6,
        'loan_type': 'Business Loan',
        'principal_amount': 5000000.00,
        'outstanding_amount': 3750000.00,
        'interest_rate': 11.0,
        'tenure_months': 84,
        'emi_amount': 75000.00,
        'start_date': '2022-12-01',
        'status': 'Active',
        'next_due_date': '2024-07-01',
        'loan_ref': 'GTBL2022987654',
        'sanction_ref': 'GTBSANC221201006'
    }
]

# Login credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = '123'

@app.route('/')
def index():
    if 'logged_in' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['logged_in'] = True
        flash('Login successful!', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid credentials!', 'error')
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'logged_in' not in session:
        return redirect(url_for('index'))
    
    # Calculate dashboard statistics
    total_customers = len(customers)
    active_customers = len([c for c in customers if c['status'] == 'Active'])
    total_balance = sum(c['balance'] for c in customers)
    total_loans = sum(loan['outstanding_amount'] for loan in loans)
    recent_transactions = sorted(transactions, key=lambda x: x['date'], reverse=True)[:5]
    
    return render_template('dashboard.html', 
                         total_customers=total_customers,
                         active_customers=active_customers,
                         total_balance=total_balance,
                         total_loans=total_loans,
                         recent_transactions=recent_transactions)

@app.route('/customers')
def customer_list():
    if 'logged_in' not in session:
        return redirect(url_for('index'))
    return render_template('customers.html', customers=customers)

@app.route('/customer/<int:customer_id>')
def customer_detail(customer_id):
    if 'logged_in' not in session:
        return redirect(url_for('index'))
    
    customer = next((c for c in customers if c['id'] == customer_id), None)
    if not customer:
        flash('Customer not found!', 'error')
        return redirect(url_for('customer_list'))
    
    customer_transactions = [t for t in transactions if t['customer_id'] == customer_id]
    customer_loans = [l for l in loans if l['customer_id'] == customer_id]
    return render_template('customer_detail.html', customer=customer, transactions=customer_transactions, loans=customer_loans)

@app.route('/transactions')
def transaction_list():
    if 'logged_in' not in session:
        return redirect(url_for('index'))
    
    # Get customer names for transactions
    transactions_with_names = []
    for transaction in transactions:
        customer = next((c for c in customers if c['id'] == transaction['customer_id']), None)
        transaction_copy = transaction.copy()
        transaction_copy['customer_name'] = customer['name'] if customer else 'Unknown'
        transactions_with_names.append(transaction_copy)
    
    return render_template('transactions.html', transactions=transactions_with_names)

@app.route('/add_customer')
def add_customer_form():
    if 'logged_in' not in session:
        return redirect(url_for('index'))
    return render_template('add_customer.html')

@app.route('/add_customer', methods=['POST'])
def add_customer():
    if 'logged_in' not in session:
        return redirect(url_for('index'))
    
    new_customer = {
        'id': len(customers) + 1,
        'name': request.form['name'],
        'email': request.form['email'],
        'phone': request.form['phone'],
        'account_number': f"GTB{len(customers) + 1:03d}",
        'balance': float(request.form['balance']),
        'account_type': request.form['account_type'],
        'status': 'Active',        'join_date': datetime.now().strftime('%Y-%m-%d'),
        'last_transaction': datetime.now().strftime('%Y-%m-%d'),
        'city': request.form.get('city', ''),
        'aadhar': request.form.get('aadhar', ''),
        'pan': request.form.get('pan', ''),
        'crm_ref': f"GTBCRM{datetime.now().strftime('%y%m%d')}{len(customers) + 1:03d}"
    }
    
    customers.append(new_customer)
    flash('Customer added successfully!', 'success')
    return redirect(url_for('customer_list'))

@app.route('/loans')
def loan_list():
    if 'logged_in' not in session:
        return redirect(url_for('index'))
    
    # Get customer names for loans
    loans_with_names = []
    for loan in loans:
        customer = next((c for c in customers if c['id'] == loan['customer_id']), None)
        loan_copy = loan.copy()
        loan_copy['customer_name'] = customer['name'] if customer else 'Unknown'
        loans_with_names.append(loan_copy)
    
    return render_template('loans.html', loans=loans_with_names)

# API endpoints for AJAX requests
@app.route('/api/customers')
def api_customers():
    if 'logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(customers)

@app.route('/api/transactions')
def api_transactions():
    if 'logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(transactions)

if __name__ == '__main__':
    app.run(debug=True)
