from datetime import datetime
from decimal import Decimal
import locale
import os
import sqlite3
import json 


from flask import Flask, g, jsonify, render_template, request, make_response
from flask_cors import CORS
from flask import send_file

from ledger import Ledger, LedgerError

app = Flask(__name__)
app.config.update(dict(
	DATABASE_URL_2019=os.path.join(app.root_path, 'database.sqlite32019'),
    DATABASE_URL_2020=os.path.join(app.root_path, 'database.sqlite32020'),
	DATABASE_URL_2021=os.path.join(app.root_path, 'database.sqlite32021')
))


CORS(app) # This will enable CORS for all routes

def connect_db():
    db = sqlite3.connect(app.config['DATABASE_URL_' + '2020'])
    return db
# set g.year= 2020 and pass it in create_ledger(g.year)

def get_db():
    if not hasattr(g, 'db'):
        g.db = connect_db()
    return g.db


def create_ledger():
    return Ledger(get_db())


def get_ledger():
    if not hasattr(g, 'ledger'):
        g.ledger = create_ledger()
    return g.ledger


def init_ledger():
    get_ledger().init()


def drop_ledger():
    get_ledger().drop()


def reset_ledger():
    get_ledger().reset()


@app.cli.command('init')
def init_ledger_command():
    init_ledger()


@app.cli.command('drop')
def drop_ledger_command():
    drop_ledger()


@app.cli.command('reset')
def reset_ledger_command():
    reset_ledger()


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'db'):
        g.db.close()


def _transaction_to_jsonold(transaction):
    return {
        'date': transaction.date.strftime('%Y-%m-%d'),
        'description': transaction.description,
        'items': [
            {'account_code': item[0], 'amount': item[1]}
            for item in transaction.items
        ]
    }

def _transaction_to_json(transaction):
    return [transaction.date.strftime('%Y-%m-%d'),transaction.description,transaction.items[0][0],transaction.items[1][0],transaction.items[1][1]]



def _transactionitems_to_json(transactionitem):


	return {
        'date': transactionitem.date.strftime('%Y-%m-%d'),
        'description': transactionitem.description,
        'amount': transactionitem.amount,
        'dr': (transactionitem.amount if transactionitem.type == '2' else ''),
        'cr': (transactionitem.amount if transactionitem.type == '1' else ''),
        'balance': transactionitem.balance
     }

def _account_to_json(account, balance=None):
    result = {'code': account.code, 'name': account.name, 'type': account.type}
    if balance is not None:
        if account.type in ('equity', 'liability', 'revenue'):
            balance = -balance
        result['balance'] = balance
    return result


def _accounts_to_json(accounts_and_balances):
    return [_account_to_json(account, balance)
            for account, balance in accounts_and_balances.items()]


def _income_statement_to_json(income_statement):
    result = {
        'start_date': income_statement.start_date.strftime('%d/%m/%Y'),
        'end_date': income_statement.end_date.strftime('%d/%m/%Y'),
        'expense': _accounts_to_json(income_statement.expense),
        'revenue': _accounts_to_json(income_statement.revenue),
        'total_revenues': income_statement.total_revenues,
        'total_expenses': income_statement.total_expenses,
        'net_result': income_statement.net_result
    }
    print ('net_result',income_statement.net_result)
    if income_statement.net_result >= 0:
        result['net_income'] = income_statement.net_income
    else:
        result['net_loss'] = income_statement.net_loss
    return result


@app.template_filter('monetize')
def monetize(value):
    value = Decimal(value) / 100
    locale.setlocale(locale.LC_MONETARY, ('en_US', 'UTF-8'))
    return locale.currency(value, False, True)



@app.route('/create', methods=['GET'])
def init():
    init_ledger()
    return 'Done', 200

@app.route('/drop', methods=['GET'])
def drop():
    drop_ledger()
    return 'Done', 200

@app.route('/reset', methods=['GET'])
def reset():
    reset_ledger()
    return 'Done', 200


@app.route('/accounts/<code>', methods=['GET'])
def get_account(code):
    account = get_ledger().get_account(code)
    if account:
        return jsonify(code=account.code, name=account.name, type=account.type)
    else:
        return 'Account "{}" does not exist'.format(code), 404

@app.route('/accounts', methods=['GET'])
def get_allaccount():
    accounts = get_ledger().get_allaccount()
    if accounts:
        return jsonify({
        'accounts':  [account for account in accounts
        ]
        })
    else:
        return 'Accounts  does not exist', 404

@app.route('/accounts', methods=['POST'])
def create_account():
    if request.json is None:
        return 'Expected JSON-encoded data', 400
    if 'name' not in request.json:
        return 'Missing "name"', 400
    if 'code' not in request.json:
        return 'Missing "code"', 400
    if 'type' not in request.json:
        return 'Missing "type"', 400
    allowed_types = ('asset', 'liability', 'equity', 'revenue', 'expense')
    if request.json['type'] not in allowed_types:
        return '"type" must be one of {}'.format(', '.join(allowed_types)), 400

    try:
        get_ledger().create_account(request.json['code'], request.json['name'],
                                    request.json['type'], request.json['balance'], request.json['phone'], request.json['email'])
        return 'Created', 201
    except LedgerError as exc:
        return str(exc), 409


@app.route('/transactions/<int:id>', methods=['GET'])
def get_transaction(id):
    transaction = get_ledger().get_transaction(id)
    if transaction:
        return jsonify(_transaction_to_json(transaction))
    else:
        return 'Transaction "{}" does not exist'.format(id), 404


@app.route('/transactions', methods=['GET'])
def get_transactions():
    transactions = get_ledger().get_transactions()
    return jsonify({
        'transactions': [
            _transaction_to_json(transaction) for transaction in transactions
        ]
    })

@app.route('/ledger/<code>', methods=['GET'])
def get_accountledger(code):
    transactionitems = get_ledger().get_accountledger(code)
    itemslist = [_transactionitems_to_json(transactionitem) for transactionitem in transactionitems]
    return jsonify({
        'transactionitems': itemslist
    })

@app.route('/excel', methods=['GET'])
def readExcel():
    get_ledger().upload_account()
    return 'Read Data'.format(id), 202

@app.route('/bill', methods=['GET'])
def billExcel():
    get_ledger().monthly_bills()
    return 'Add bill Data'.format(id), 202

@app.route('/payments', methods=['GET'])
def paymentExcel():
    get_ledger().bills_payment()
    return 'Add payment Data'.format(id), 202

@app.route('/transactions/<sheetname>', methods=['POST'])
def add_transaction(sheetname):
    get_ledger().add_transaction(sheetname)
    return 'Add Transaction Data'.format(id), 202


@app.route('/transactions', methods=['POST'])
def record_transaction():
    if 'date' not in request.json:
        return 'Missing "date"', 400
    if 'description' not in request.json:
        return 'Missing "description"', 400
    if 'items' not in request.json:
        return 'Missing "items"', 400
    if not request.json['items']:
        return 'Cannot record an empty transaction', 400
    if any('account_code' not in item for item in request.json['items']):
        return 'All items must contain "account_code"', 400
    if any('amount' not in item for item in request.json['items']):
        return 'All items must contain "amount"', 400

    try:
        date = datetime.strptime(request.json['date'], '%Y-%m-%d').date()
        transaction_id = get_ledger().record_transaction(
            date,
            request.json['description'],
            [[item['account_code'], item['amount']]
             for item in request.json['items']]
        )
        return str(transaction_id), 201
    except (ValueError, LedgerError) as exc:
        return str(exc), 400




@app.route('/balance-sheets/<date>.json', methods=['GET'])
def get_json_balance_sheet(date):
    date = datetime.strptime(date, '%Y-%m-%d').date()
    balance_sheet = get_ledger().get_balance_sheet(date)
    return jsonify(
        date=balance_sheet.date.strftime('%d/%m/%Y'),
        asset=_accounts_to_json(balance_sheet.asset),
        liability=_accounts_to_json(balance_sheet.liability),
        equity=_accounts_to_json(balance_sheet.equity),
        retained_earnings=balance_sheet.retained_earnings,
        total_assets=sum(balance_sheet.asset.values()),
        total_liabilities=-sum(balance_sheet.liability.values()),
        total_equity=-sum(balance_sheet.equity.values()) + balance_sheet.retained_earnings
    )


@app.route('/balance-sheets/<date>.html', methods=['GET'])
def get_html_balance_sheet(date):
    date = datetime.strptime(date, '%Y-%m-%d').date()
    return render_template('balance_sheet.html',
                           balance_sheet=get_ledger().get_balance_sheet(date))


@app.route('/income-statements/<start_date>-to-<end_date>.json',
           methods=['GET'])
def get_json_income_statement(start_date, end_date):
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    income_statement = get_ledger().get_income_statement(start_date, end_date)
    return jsonify(
            **_income_statement_to_json(income_statement)
    )


@app.route('/income-statements/<start_date>-to-<end_date>.html',
           methods=['GET'])
def get_html_income_statement(start_date, end_date):
    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    return render_template(
        'income_statement.html',
        income_statement=get_ledger().get_income_statement(start_date, end_date)
    )


@app.route('/bills',
           methods=['POST'])
def save_bills():
	json_object =json.dumps(request.json, indent = 4) 
	print(json_object)
	get_ledger().save_bills(json_object)
	return 'All items must contain "amount"', 200

@app.route('/bills',
           methods=['GET'])
def read_bills():
	columns = get_ledger().read_bills()
	return jsonify({
        'columns':  [col for col in columns
        ]
        })

@app.route('/bills/generate',
           methods=['POST'])
def generate_bills():
	print('DAte ' + request.json['date'])
	date = datetime.strptime(request.json['date'], '%Y-%m-%d').date()
	filename = get_ledger().generate_bills_excel(date)
	return send_file(filename,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     attachment_filename=filename,
                     as_attachment=True)


@app.route('/bills/generate/pdf',
           methods=['POST'])
def generate_bills_pdf():
	print('Date ' + request.json['date'])
	date = datetime.strptime(request.json['date'], '%Y-%m-%d').date()
	filename = get_ledger().generate_bills_pdf(date)
	return send_file(filename,
                     mimetype='application/pdf',
                     attachment_filename=filename,
                     as_attachment=True)



@app.route('/bills/upload', methods = ['POST'])  
def success():  
    if request.method == 'POST':  
        f = request.files['file']  
        f.save(f.filename)  
        get_ledger().monthly_bills(f.filename)
        return 'Upload sucessfully', 200


@app.route('/transactions/upload', methods = ['POST'])  
def paybills():  
    if request.method == 'POST':  
        f = request.files['file']  
        f.save(f.filename)  
        get_ledger().bills_payment(f.filename)
        return 'Upload sucessfully', 200


def _build_cors_prelight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add('Access-Control-Allow-Headers', "*")
    response.headers.add('Access-Control-Allow-Methods', "*")
    return response

def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response
if __name__ == '__main__':
    app.run()
