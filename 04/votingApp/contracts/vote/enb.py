from pyteal import *
from algosdk import account, mnemonic
from algosdk.v2client import algod
from algosdk.future.transaction import AssetConfigTxn, wait_for_confirmation, AssetTransferTxn, AssetFreezeTxn
import json


OWNER_PRIVATE_KEY = 'EYB7ek2HbuqRK/trQvc5rU7DSCfoRkE2aiy4YqUNW3DTE1o0bHkqHT/IT/7NYC/qj9wGYNgeTaCtG8dbY5rCxQ=='
OWNER_ADDRESS = '2MJVUNDMPEVB2P6IJ77M2YBP5KH5YBTA3APE3IFNDPDVWY42YLCVAS66EA'

ALGOD_ADDRESS  = 'https://testnet-api.algonode.cloud'
ALGOD_CLIENT = algod.AlgodClient("", ALGOD_ADDRESS)
SUGGESTED_PARAMS = ALGOD_CLIENT.suggested_params()

#
# Create ENB ASA
#
def create_enb_asa():
    txn = AssetConfigTxn(
        sender=         OWNER_ADDRESS,
        sp=             SUGGESTED_PARAMS,
        total=          1000000,
        default_frozen= False,
        unit_name=      "ENB",
        asset_name=     "Eat Nuts and Berries",
        manager=        OWNER_ADDRESS,
        reserve=        OWNER_ADDRESS,
        freeze=         OWNER_ADDRESS,
        clawback=       OWNER_ADDRESS,
        decimals=       0
    )

    signedTxn = txn.sign(OWNER_PRIVATE_KEY)

    response = send_txn(signedTxn, ALGOD_CLIENT, True)
    assetID = response['asset-index']
    print(f"Asset Index: {assetID}")  
    
    return assetID

#
# Send Transaction
#
def send_txn(_signedTxn, _algodClient, boolJsonDump):
    try:
        txnId = _algodClient.send_transaction(_signedTxn)
        print(f"Transaction sent with ID: {txnId}")
        txnResponse = wait_for_confirmation(_algodClient, txnId, 4)
        print(f"Txn confirmed in block: {txnResponse['confirmed-round']}")      
    except Exception as e:
        print(f"Error: {e}")

    if boolJsonDump:
        print(f"Transaction information: {json.dumps(txnResponse, indent=4)}")

    return txnResponse

#
# Contract
# 
ENB_ID = create_enb_asa()

def approval():
    # globals
    global_enb_id = Bytes("enbId")

    on_creation = Seq(
        [
            App.globalPut(Bytes("Owner"), Txn.sender()),
            Assert(Txn.application_args.length() == Int(2)),
            App.globalPut(Bytes("enbId"), Btoi(Txn.application_args[1])),
            Return(Int(1))
        ]
    )

    is_owner = Txn.sender() == App.globalGet(Bytes("Owner"))

    program = Cond(
        [Txn.application_id() == Int(0), on_creation],
        [Txn.on_completion() == OnComplete.DeleteApplication, Return(is_owner)],
        [Txn.on_completion() == OnComplete.UpdateApplication, Return(is_owner)]
    )

    return program


def clear():
    Return(Int(1))


if __name__ == "__main__":

    with open("../build/enb_approval.teal", "w") as f:
        compiled = compileTeal(approval(), mode=Mode.Application) # Should thius be Mode.Signature ???
        f.write(compiled)

    with open("../build/enb_clear_state.teal", "w") as f:
        compiled = compileTeal(clear(), mode=Mode.Application)  # Should thius be Mode.Signature ???
        f.write(compiled)