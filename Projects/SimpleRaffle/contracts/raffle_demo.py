from algosdk import transaction
from algosdk.error import AlgodHTTPError
from algosdk.atomic_transaction_composer import (
    TransactionWithSigner,
)

from beaker import sandbox, consts
from beaker.client import ApplicationClient

from raffle_contract import Raffle

client = sandbox.get_algod_client()
accts = sandbox.get_accounts()

creator_acct = accts.pop()
user_acct1 = accts.pop()
user_acct2 = accts.pop()

app = Raffle()

app_client = ApplicationClient(client, app, signer=creator_acct.signer)

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
    print("### BOB ###\n")
    
    # Set up Guest 1 application client
    app_client_bob = app_client.prepare(signer=user_acct2.signer)

    # Alice opting in and buying tickets
    print("Alice buying tickets...")
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
    print(f"Total tickets bought: {total.return_value}")


if __name__ == "__main__":
    demo()