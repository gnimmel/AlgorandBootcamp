from algosdk import account, mnemonic
from algosdk.v2client import algod
from algosdk.future.transaction import AssetConfigTxn, wait_for_confirmation, AssetTransferTxn, AssetFreezeTxn
import logging
import json

BOOL_GENERATE_WALLET = False
OWNER_PRIVATE_KEY = 'EYB7ek2HbuqRK/trQvc5rU7DSCfoRkE2aiy4YqUNW3DTE1o0bHkqHT/IT/7NYC/qj9wGYNgeTaCtG8dbY5rCxQ=='
OWNER_ADDRESS = '2MJVUNDMPEVB2P6IJ77M2YBP5KH5YBTA3APE3IFNDPDVWY42YLCVAS66EA'

OPTIN_PRIVATE_KEY = 'qqr7zQlJ0hkAkX2/D8aqO5shgu4BtGSysgkc6mlkyTD4DHPSkIkcinVoBhGuYw2zSkcm6XV1HoGVb8a4NLfR+g=='
OPTIN_ADDRESS = '7AGHHUUQREOIU5LIAYI24YYNWNFEOJXJOV2R5AMVN7DLQNFX2H5MCZXCCE'

ALGOD_ADDRESS  = 'https://testnet-api.algonode.cloud'
ALGOD_CLIENT = algod.AlgodClient("", ALGOD_ADDRESS)
SUGGESTED_PARAMS = ALGOD_CLIENT.suggested_params()

logging.basicConfig(level=logging.DEBUG)

#
# Generate an account
# returns: a tuple (private key, public address) 
# notes: This just adds logging to the generate call
#
def generate_algorand_keypair():
    private_key, address = account.generate_account()
    logging.info(f"private_key: {private_key}")
    logging.info(f"address: {address}")
    logging.info(f"passphrase: {mnemonic.from_private_key(private_key)}")
    
    return private_key, address

# Used to generate the account we funded with testAlgo from the faucet -> https://bank.testnet.algorand.network/    
if BOOL_GENERATE_WALLET:
    generate_algorand_keypair()


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
# Create Encodium ASA
#
def create_encodium_asa():
    txn = AssetConfigTxn(
        sender=         OWNER_ADDRESS,
        sp=             SUGGESTED_PARAMS,
        total=          1000,
        default_frozen= False,
        unit_name=      "NCD",
        asset_name=     "Encodium",
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
# Modify ASA with asset config txn
#
def modify_asset_manager(_assetId, _newManagerAddr):
    txn = AssetConfigTxn(
        sender=     OWNER_ADDRESS,
        sp=         SUGGESTED_PARAMS,
        index=      _assetId, 
        manager=    _newManagerAddr,
        reserve=    OWNER_ADDRESS,
        freeze=     OWNER_ADDRESS,
        clawback=   OWNER_ADDRESS)

    signedTxn = txn.sign(OWNER_PRIVATE_KEY)

    send_txn(signedTxn, ALGOD_CLIENT, True)


#
# Opt-in ASA -> AssetTransferTxn
#
def optin_asset(_assetId, _addr, _sk):
    #private_key, address = account.generate_account()
    accountInfo = ALGOD_CLIENT.account_info(_addr)
    holding = None
    idx = 0

    for item in accountInfo['assets']:
        theAsset = accountInfo['assets'][idx]
        idx = idx + 1 
        if (theAsset['asset-id'] == _assetId):
            holding = True
            break
    
    #
    # TODO: Try this with non-zero amount .. what happens?
    # shouldn't the sender be the owner of the asset ???
    #
    if not holding:
        txn = AssetTransferTxn(
            sender=     _addr,
            sp=         SUGGESTED_PARAMS,
            receiver=   _addr,
            amt=        0,
            index=      _assetId)

        signedTxn = txn.sign(_sk)

        send_txn(signedTxn, ALGOD_CLIENT, False)


#
# Transfer ASA
#
def transfer_asset(_amnt, _assetId, _toAddr):
    #private_key, address = account.generate_account()
    txn = AssetTransferTxn(
        sender=     OWNER_ADDRESS,
        sp=         SUGGESTED_PARAMS,
        receiver=   _toAddr,
        amt=        _amnt,
        index=      _assetId)

    signedTxn = txn.sign(OWNER_PRIVATE_KEY)

    response = send_txn(signedTxn, ALGOD_CLIENT, False)

    return response

    #log_asset_holding(ALGOD_CLIENT, address, _assetId)


#
# Freeze ASA
#
def freeze_asset(_assetId, _addr):
    txn = AssetFreezeTxn(
        sender=             OWNER_ADDRESS,
        sp=                 SUGGESTED_PARAMS,
        index=              _assetId,
        target=             _addr,
        new_freeze_state=   True   
        )
    
    signedTxn = txn.sign(OWNER_PRIVATE_KEY)
    
    send_txn(signedTxn, ALGOD_CLIENT, False)


#
# Revoke ASA
#
def revoke_asset(_assetID, _amnt, _targetAddr):
    txn = AssetTransferTxn(
        sender=             OWNER_ADDRESS,
        sp=                 SUGGESTED_PARAMS,
        receiver=           OWNER_ADDRESS,
        amt=                _amnt,
        index=              _assetID,
        revocation_target=  _targetAddr
        )

    signedTxn = txn.sign(OWNER_PRIVATE_KEY)

    send_txn(signedTxn, ALGOD_CLIENT, False)


#
# Revoke ASA
#
def destroy_asset(_assetID, _managerAddr, _managerPrivateKey):
    txn = AssetConfigTxn(
        sender=                     _managerAddr,
        sp=                         SUGGESTED_PARAMS,
        index=                      _assetID,
        strict_empty_address_check= False
        )
    
    signedTxn = txn.sign(_managerPrivateKey)

    send_txn(signedTxn, ALGOD_CLIENT, False)


#
# Print ASA Information Utility funcs
#
def print_created_asset(_client, _addr, _assetid):
    accountInfo = _client.account_info(_addr)
    idx = 0
    for info in accountInfo['created-assets']:
        theAsset = accountInfo['created-assets'][idx]
        idx = idx + 1       
        if (theAsset['index'] == _assetid):
            print(f"Asset ID: {theAsset['index']}")
            print(json.dumps(info['params'], indent=4))
            break

def print_asset_holding(_client, _addr, _assetid):
    accountInfo = _client.account_info(_addr)
    idx = 0
    for info in accountInfo['assets']:
        theAsset = accountInfo['assets'][idx]
        idx = idx + 1        
        if (theAsset['asset-id'] == _assetid):
            print(f"Asset ID: {theAsset['asset-id']}")
            print(json.dumps(theAsset, indent=4))
            break


def main():
    #create the asset
    ASSET_ID = create_encodium_asa()
    
    print_created_asset(ALGOD_CLIENT, OWNER_ADDRESS, ASSET_ID)
    print_asset_holding(ALGOD_CLIENT, OWNER_ADDRESS, ASSET_ID)

    # Funded alt test account
    alt_private_key = OPTIN_PRIVATE_KEY
    alt_address = OPTIN_ADDRESS

    logging.info("MODIFY MANAGER")
    modify_asset_manager(ASSET_ID, alt_address)
    # manager should be different
    print_created_asset(ALGOD_CLIENT, OWNER_ADDRESS, ASSET_ID)

    logging.info("OPT IN TO ASSET")
    optin_asset(ASSET_ID, alt_address, alt_private_key)
    print_asset_holding(ALGOD_CLIENT, alt_address, ASSET_ID)

    logging.info("TRANSFER 10")
    transfer_asset(10, ASSET_ID, alt_address)
    print_asset_holding(ALGOD_CLIENT, alt_address, ASSET_ID)

    logging.info("FREEZE ASSET")
    freeze_asset(ASSET_ID, alt_address)
    print_asset_holding(ALGOD_CLIENT, alt_address, ASSET_ID)

    logging.info("REVOKE ASSET -> balance should be 0 now")
    revoke_asset(ASSET_ID, 10, alt_address)
    print_asset_holding(ALGOD_CLIENT, alt_address, ASSET_ID)

    logging.info("DESTROY ASSET -> nothing should print")
    destroy_asset(ASSET_ID, alt_address, alt_private_key)
    try:
        print_created_asset(ALGOD_CLIENT, OWNER_ADDRESS, ASSET_ID)
        print_asset_holding(ALGOD_CLIENT, OWNER_ADDRESS, ASSET_ID)
    except Exception as e:
        logging.error(e)


if __name__=="__main__":
    main()