from typing import *
from pyteal import *
from beaker import *
import logging

class Raffle(Application):

    ###
    # Constants
    ###

    # Max number of tickets that can be purchased
    MAX_NUM_TICKETS = 100

    # Max number of tickets that can be purchased per user
    MAX_NUM_TICKETS_PER_ACCOUNT = 10

    # Price per ticket. Default price is 1 Algo
    PRICE_PER_TICKET = 1000000 

    # Randomness Beacon app IDs
    BEACON_ID_TESTNET = 110096026
    BEACON_ID_MAINNET = 947957720

    ###
    # Application state values 
    ###

    beacon_app_id: Final[ApplicationStateValue] = ApplicationStateValue(
        TealType.uint64,
        default=Int(BEACON_ID_TESTNET),
        descr="App ID of the randomness beacon",
        static=True
    )

    commitment_round: Final[ApplicationStateValue] = ApplicationStateValue(
        TealType.uint64,
        descr="Round committed for randomness beacon",
    )

    # Might be unnecessary... currently using Global.creator_address() where owner could be used instead
    # OR keep it in case we want to transfer ownership later?
    owner: Final[ApplicationStateValue] = ApplicationStateValue(
        stack_type=TealType.bytes, 
        default=Global.creator_address(),
        descr="Creator of the Raffle"
    )

    ticket_price: Final[ApplicationStateValue] = ApplicationStateValue(
        stack_type=abi.Uint64,
        default=PRICE_PER_TICKET,
        descr="Price per ticket"
    )

    entries: Final[ApplicationStateValue] = ApplicationStateValue(
        stack_type=abi.StaticArray(abi.Address, MAX_NUM_TICKETS),
        descr="Array of account addresses that have purchased tickets"
    )

    num_entries: Final[ApplicationStateValue] = ApplicationStateValue(
        stack_type=TealType.uint64,
        default=Int(0),
        descr="Number of tickets purchsed (aka entries.length)"
    )

    ###
    # Account state values 
    ###

    # TODO: likely unnecessary. Unless user has to claim their winnings
    is_winner: Final[AccountStateValue] = AccountStateValue(
        stack_type=abi.Bool,
        default=False,
        descr="Whether or not you won!!"
    )

    # TODO: likely unnecessary
    num_tickets: Final[AccountStateValue] = AccountStateValue(
        stack_type=abi.Uint64,
        default=0,
        descr="Number of tickets you hold"
    )

    ###
    # Externals
    ###


    ###
    # Internals
    ###

    @ internal(TealType.bytes)
    def get_randomness(self, acct_round: Expr):
        """get random from beacon for requested round"""
        return Seq(
            # Prep arguments
            (round := abi.Uint64()).set(acct_round),
            (user_data := abi.make(abi.DynamicArray[abi.Byte])).set([]),
            
            InnerTxnBuilder.ExecuteMethodCall(
                app_id=self.beacon_app_id,
                method_signature="must_get(uint64,byte[])byte[]",
                args=[round, user_data],
            ),
            # Remove first 4 bytes (ABI return prefix)
            # and return the rest
            Suffix(InnerTxn.last_log(), Int(4)),
        )

    ###
    # App lifecycle
    ###

    @create
    def create(self, price: abi.Uint64):
        """Deploy contract and initialze the app states"""
        return Seq(
            self.initialize_application_state(),
            self.ticket_price.set(price.get()),
        )

    @ opt_in
    def opt_in(self):
        return Approve()

    @ update(authorize=Authorize.only(Global.creator_address()))
    def update(self):
        return Approve()

    # HOW DOES ARRAY MANIPULATION WORK???? deletion etc... if at all
    @ clear_state
    def clear_state(self):
        return Seq(
            # Did sender buy any tickets?
            If(self.num_tickets[Txn.sender()] > Int(0)).Then(
                # TODO: Remove entries from array (if even possible???)
                # OR check that winning addr is still opted in on pick_winner
            ),
            Approve(),
        )

    @ close_out
    def close_out(self):
        return Seq(
            # Did sender buy any tickets?
            If(self.num_tickets[Txn.sender()] > Int(0)).Then(
                # TODO: Remove entries from array (if even possible???)
                # OR check that winning addr is still opted in on pick_winner
            ),
            Approve(),
        )