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
    app_id, app_addr, txid = app_client.create(price = .01 * consts.algo)
    print(f"Created App with id: {app_id} and address addr: {app_addr} in tx: {txid}")

    ticket_price = app_client.call(app.read_price)
    print(f"Ticket price is set to {ticket_price.return_value} microAlgos")

    # Fund the contract for minimum balance
    app_client.fund(100*consts.milli_algo)
    print(f"Raffle Balance: {client.account_info(app_addr).get('amount')} microAlgos \n")


if __name__ == "__main__":
    demo()