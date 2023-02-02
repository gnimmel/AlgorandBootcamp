from algosdk import transaction
from algosdk import mnemonic
from algosdk.account import generate_account, address_from_private_key
from algosdk.error import AlgodHTTPError
from algosdk.encoding import encode_address
from algosdk.atomic_transaction_composer import (
    TransactionWithSigner,
    AtomicTransactionComposer,
    AccountTransactionSigner,
)
from algosdk.v2client.algod import AlgodClient

from beaker import sandbox, consts
from beaker.client import ApplicationClient
from beaker.sandbox import SandboxAccount

from raffle_contract import Raffle
import json
import os

ROOT_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
jsonPath = (os.path.join(ROOT_DIR, 'config', 'accounts.json'))
accountsJson = json.loads(open(jsonPath).read())
for i in accountsJson['accounts']:
    print(i['mnemonic'])

app = Raffle()

###
# SANDBOX
###

# accts = sandbox.get_accounts()

# creator_acct = accts.pop()
# user_acct1 = accts.pop()
# user_acct2 = accts.pop()

# app_client = ApplicationClient(
#     client=sandbox.get_algod_client(), 
#     app=app, 
#     signer=creator_acct.signer
# )

###
# TESTNET
###

creator_private_key = mnemonic.to_private_key(accountsJson['accounts'][0]['mnemonic'])
creator_address = address_from_private_key(creator_private_key)
creator_signer = AccountTransactionSigner(creator_private_key)
creator_acct = SandboxAccount(creator_address, creator_private_key, creator_signer)

user1_private_key = mnemonic.to_private_key(accountsJson['accounts'][1]['mnemonic'])
user1_address = address_from_private_key(user1_private_key)
user1_signer = AccountTransactionSigner(user1_private_key)
user_acct1 = SandboxAccount(user1_address, user1_private_key, user1_signer)

user2_private_key = mnemonic.to_private_key(accountsJson['accounts'][2]['mnemonic'])
user2_address = address_from_private_key(user2_private_key)
user2_signer = AccountTransactionSigner(user2_private_key)
user_acct2 = SandboxAccount(user2_address, user2_private_key, user2_signer)

client = AlgodClient("", "https://testnet-api.algonode.cloud")
app_client = ApplicationClient(
    client=client, 
    app=app, 
    signer=creator_acct.signer
)

###
# DEMO
###

def demo():

    print("### INIT ### \n")
    sp = client.suggested_params()
    # Create the app on chain, set the app id for the app client
    app_id, app_addr, txid = app_client.create(price = 1 * consts.algo)
    print(f"Created App with id: {app_id} and address addr: {app_addr} in tx: {txid}")

    ticket_price = app_client.call(app.read_ticket_price)
    print(f"Ticket price is set to {ticket_price.return_value} microAlgos")

    # Fund the contract for minimum balance
    app_client.fund(100*consts.milli_algo)
    print(f"Raffle Balance: {client.account_info(app_addr).get('amount')} microAlgos \n")

#    app_client.call(app.init_raffle)

    #app_client.call(app.finalize_raffle)

    # ALICE BUYS TICKETS 
    print("### ALICE ###\n")
    
    # Set up Guest 1 application client
    app_client_alice = app_client.prepare(signer=user_acct1.signer)

    # Alice opting in and buying tickets
    print("Alice buying tickets...")
    ptxn1 = TransactionWithSigner(
            txn=transaction.PaymentTxn(user_acct1.address, sp, app_addr, 10 * consts.algo),
            signer=user_acct1.signer,
        )
    
    # Opt in to contract with event registration payment included
    app_client_alice.opt_in()

    app_client_alice.call(app.buy_tickets, payment=ptxn1, numTickets=3)

    acct_state = app_client_alice.get_account_state()
    num = acct_state["num_tickets"]
    print(f"Alice bought {num} tickets")

    
    # BOB BUYS TICKETS 
    print("\n### BOB ###\n")
    
    # Set up Guest 1 application client
    app_client_bob = app_client.prepare(signer=user_acct2.signer)

    # Bob opting in and buying tickets
    print("Bob buying tickets...")
    ptxn2 = TransactionWithSigner(
            txn=transaction.PaymentTxn(user_acct2.address, sp, app_addr, 10 * consts.algo),
            signer=user_acct2.signer,
        )
    
    # Opt in to contract with event registration payment included
    app_client_bob.opt_in()

    app_client_bob.call(app.buy_tickets, payment=ptxn2, numTickets=5)

    acct_state = app_client_bob.get_account_state()
    num = acct_state["num_tickets"]
    print(f"Bob bought {num} tickets")


    # How many tickets have been purchased?
    total = app_client.call(app.read_num_entries)
    print(f"\nTotal tickets bought: {total.return_value}")

    winner = app_client.call(app.pick_winner)
    print(f"\nWinning index: {winner.return_value}")


if __name__ == "__main__":
    demo()