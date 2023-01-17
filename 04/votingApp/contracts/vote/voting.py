from pyteal import *


def approval():
    on_creation = Seq(
        [
            App.globalPut(Bytes("Creator"), Txn.sender()),
            Assert(Txn.application_args.length() == Int(5)),
            App.globalPut(Bytes("RegBegin"), Btoi(Txn.application_args[0])),
            App.globalPut(Bytes("RegEnd"), Btoi(Txn.application_args[1])),
            App.globalPut(Bytes("VoteBegin"), Btoi(Txn.application_args[2])),
            App.globalPut(Bytes("VoteEnd"), Btoi(Txn.application_args[3])),
            Return(Int(1)),
        ]
    )

    is_creator = Txn.sender() == App.globalGet(Bytes("Creator"))

    get_vote_of_sender = App.localGetEx(Int(0), App.id(), Bytes("voted"))

    enb_id = App.globalGetEx(Txn.applications[1], Bytes("enbId"))
    enb_balance = AssetHolding.balance(Txn.sender(), (enb_id.value())) # Int(enb_id) or Bytes(enb_id) ???
    
    on_closeout = Seq(
        [
            get_vote_of_sender,
            enb_balance,
            If(
                And(
                    Global.round() <= App.globalGet(Bytes("VoteEnd")),
                    get_vote_of_sender.hasValue(),
                ),
                App.globalPut(
                    get_vote_of_sender.value(),
#                    App.globalGet(get_vote_of_sender.value()) - (enb_balance.value()),
                ),
            ),
            Return(Int(1)),
        ]
    )

    on_register = Return(
        And(
            Global.round() >= App.globalGet(Bytes("RegBegin")),
            Global.round() <= App.globalGet(Bytes("RegEnd")),
        )
    )

    choice = Txn.application_args[1]
    choice_tally = App.globalGet(choice)

    on_vote = Seq(
        [
            Assert(
                And(
                    Global.round() >= App.globalGet(Bytes("VoteBegin")),
                    Global.round() <= App.globalGet(Bytes("VoteEnd")),
                )
            ),
            get_vote_of_sender,
            If(get_vote_of_sender.hasValue(), Return(Int(0))), # User already voted
            enb_balance,
            Assert(enb_balance.hasValue()),
            Ge(enb_balance.value(), Int(1000)),
            Assert(
                Or(
                    choice == Bytes("yes"),
                    choice == Bytes("no"),
                    choice == Bytes("abstain")
                )
            ),
            App.globalPut(choice, choice_tally + (enb_balance.value())),
            App.localPut(Int(0), Bytes("voted"), choice),
            Return(Int(1)),
        ]
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_creation],
        [Txn.on_completion() == OnComplete.DeleteApplication, Return(is_creator)],
        [Txn.on_completion() == OnComplete.UpdateApplication, Return(is_creator)],
        [Txn.on_completion() == OnComplete.CloseOut, on_closeout],
        [Txn.on_completion() == OnComplete.OptIn, on_register],
        [Txn.application_args[0] == Bytes("vote"), on_vote],
    )

    return program


def clear():
    get_vote_of_sender = App.localGetEx(Int(0), App.id(), Bytes("voted"))
    enb_id = App.globalGetEx(Txn.applications[1], Bytes("enbId"))
    enb_balance = AssetHolding.balance(Txn.sender(), (enb_id.value())) # Int(enb_id) or Bytes(enb_id) ???

    program = Seq(
        [
            get_vote_of_sender,
            enb_balance,
            If(
                And(
                    Global.round() <= App.globalGet(Bytes("VoteEnd")),
                    get_vote_of_sender.hasValue(),
                    enb_balance.hasValue(),
                ),
                App.globalPut(
                    get_vote_of_sender.value(),
#                    App.globalGet(get_vote_of_sender.value()) - (enb_balance.value()),
                ),
            ),
            Return(Int(1)),1
        ]
    )

    return program


if __name__ == "__main__":
    with open("../../build/vote_approval.teal", "w") as f:
        compiled = compileTeal(approval(), mode=Mode.Application)
        f.write(compiled)

    with open("../../build/vote_clear_state.teal", "w") as f:
        compiled = compileTeal(clear(), mode=Mode.Application)
        f.write(compiled)