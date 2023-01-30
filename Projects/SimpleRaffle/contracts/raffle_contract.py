from typing import *
from pyteal import *
from beaker import *
import logging

# TODO: 
# Reset / start new raffle
# Raffle asset manager
# Auto pick winner when tickets sold out 


class Raffle(Application):

    ###
    # Constants
    ###

    # Max number of tickets that can be purchased
    # TODO: Make this configurable
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
        #static=True
    )

    commitment_round: Final[ApplicationStateValue] = ApplicationStateValue(
        TealType.uint64,
        default=Int(0),
        descr="Round committed for randomness beacon",
    )

    # Might be unnecessary... currently using Global.creator_address() where 'owner' could be used instead
    # OR keep it in case we want to transfer ownership later?
    owner: Final[ApplicationStateValue] = ApplicationStateValue(
        stack_type=TealType.bytes, 
        default=Global.creator_address(),
        descr="Creator of the Raffle"
    )

    ticket_price: Final[ApplicationStateValue] = ApplicationStateValue(
        stack_type=TealType.uint64,
        default=Int(PRICE_PER_TICKET),
        descr="Price per ticket"
    )

    # HMMMM: This is not doable 
    # How do I store ticket holders??

    # entries: Final[ApplicationStateValue] = ApplicationStateValue(
    #     stack_type=abi.StaticArray(abi.Address, MAX_NUM_TICKETS),
    #     descr="Array of account addresses that have purchased tickets"
    # )

    entriesArrayLength: Final[ApplicationStateValue] = ApplicationStateValue(
        stack_type=TealType.uint64,
        default=Int(0),
        descr="Number of tickets purchsed (aka entries.length)"
    )

    ###
    # Account state values 
    ###

    # TODO: likely unnecessary. Unless user has to claim their winnings
    is_winner: Final[AccountStateValue] = AccountStateValue(
        stack_type=TealType.uint64,
        default=Int(0),
        descr="Whether or not you won!!"
    )

    # TODO: likely unnecessary
    num_tickets: Final[AccountStateValue] = AccountStateValue(
        stack_type=TealType.uint64,
        default=Int(0),
        descr="Number of tickets you hold"
    )

    ###
    # Externals
    ###

    @external(authorize=Authorize.only(Global.creator_address()))
    def finalize_raffle(self):
        return Seq(
            Assert(self.entriesArrayLength.get() > Int(0)), # Did anyone buy tickets?

            Approve()
        )

        # return Seq(
        #     (indx := abi.Uint64()).set(self.get_random_int(self.entriesArrayLength)),
        # )
        #indx = self.get_random_int()

        # check that winning addr is still opted in
        # use indx to extract winning address
        # set is_winner flag
        # send prize
        # end raffle

    @external(authorize=Authorize.opted_in(Global.current_application_id())) 
    def buy_tickets(self, payment: abi.PaymentTransaction, numTickets: abi.Uint64):
    
        return Seq(
            Assert(payment.get().amount() > self.ticket_price.get()),

            #numTickets.set(payment.get().amount() / self.ticket_price.get()),
            self.num_tickets.set(numTickets.get()),
            #self.entriesArrayLength.get(),
            
            Approve()
        )
        # assign tickets to user
        # push user account to entries array
        # update entryArrayLength

    @external(authorize=Authorize.only(Global.creator_address()))
    def init_raffle(self, prize: abi.Asset, price: abi.Uint64):
        return Seq(
            Assert(self.entriesArrayLength.get() == Int(0)),

            Approve()
        )
        # confirm there are no raffles running -> 
        # update ticket price

    ###
    # Internals
    ###

    @internal(TealType.uint64)
    def get_random_int(
        self, 
        max: abi.Uint64, 
        #*, 
        #output: abi.Uint64
        ):
        """Use randomness beacon to select an index from the entries array"""
        #won = abi.Uint64()

        return Seq(
            # # Get the randomness
            (randomness := abi.DynamicBytes()).decode(
                self.get_randomness(self.commitment_round.get())
            ),
            # # take the modulo of the random number and the length of the entries array to get a value within the array
            #won.set(randomness.get() % max),
            # won.set(ExtractUint64(randomness.get(), Int(0)) % max),
            # If(won.get()).Then(
            #     output.set(won)
            # ).Else(
            #     output.set(0)
            # )
            ExtractUint64(randomness.get(), Int(0)) % max
        )

    @internal(TealType.bytes)
    def get_randomness(self):
        """get random from beacon"""
        return Seq(
            # Prep arguments
            (round := abi.Uint64()).set(self.commitment_round.get()),
            (user_data := abi.make(abi.DynamicArray[abi.Byte])).set([]), # Should entropy be something else? 
            
            InnerTxnBuilder.ExecuteMethodCall(
                app_id=self.beacon_app_id.get(),
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

            (round := ScratchVar()).store(Global.round() + Int(3)),
            self.commitment_round.set(round.load()),
        )

    @opt_in
    def opt_in(self):
        return Approve()

    @update(authorize=Authorize.only(Global.creator_address()))
    def update(self):
        return Approve()

    # HOW DOES ARRAY MANIPULATION WORK???? deletion etc... if at all
    @clear_state
    def clear_state(self):
        return Approve()
        # return Seq(
        #     # Did sender buy any tickets?
        #     If(self.num_tickets[Txn.sender()] > Int(0)).Then(
        #         # TODO: Remove entries from array (if even possible???)
        #         # OR check that winning addr is still opted in on pick_winner
        #     ),
        #     Approve(),
        # )

    @close_out
    def close_out(self):
        return Approve()
        # return Seq(
        #     # Did sender buy any tickets?
        #     If(self.num_tickets[Txn.sender()] > Int(0)).Then(
        #         # TODO: Remove entries from array (if even possible???)
        #         # OR check that winning addr is still opted in on pick_winner
        #     ),
        #     Approve(),
        # )

    ###
    # Read Only
    ###
    
    @external(read_only=True, authorize=Authorize.only(Global.creator_address()))
    def read_num_entries(self, *, output: abi.Uint64):
        """Read total number of entries. Only callable by Creator."""
        return output.set(self.entriesArrayLength)
    
    @external(read_only=True)
    def read_ticket_price(self, *, output: abi.Uint64):
        """Read price per ticket. Only callable by Creator."""
        return output.set(self.ticket_price)


if __name__ == "__main__":
    import os
    import json

    path = os.path.dirname(os.path.abspath(__file__))

    raffle_app = Raffle()

    # Dump out the contract as json that can be read in by any of the SDKs
    with open(os.path.join(path, "contract.json"), "w") as f:
        f.write(json.dumps(raffle_app.application_spec(), indent=2))

    # Write out the approval and clear programs
    with open(os.path.join(path, "approval.teal"), "w") as f:
        f.write(raffle_app.approval_program)

    with open(os.path.join(path, "clear.teal"), "w") as f:
        f.write(raffle_app.clear_program)
