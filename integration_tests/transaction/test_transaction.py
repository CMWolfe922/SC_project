import pytest, requests

from blockchain_users.camille import private_key as camille_private_key
from common.transaction_input import TransactionInput
from common.transaction_output import TransactionOutput
from wallet.wallet import Owner, Wallet, Node, Transaction
import json


@pytest.fixture(scope="module")
def camille():
    return Owner(private_key=camille_private_key)


@pytest.fixture(scope="module")
def camille_wallet(camille):
    return Wallet(camille)


def forge_signature(transaction_data: dict):
    input_0_dict = json.loads(transaction_data["inputs"][0])
    signature, public_key = input_0_dict["unlocking_script"].split(" ")
    new_signature = signature.replace("a", "b")
    new_unlocking_script = f"{new_signature} {public_key}"
    input_0_dict["unlocking_script"] = new_unlocking_script
    new_input_0 = json.dumps(input_0_dict)
    transaction_data["inputs"][0] = new_input_0
    return transaction_data


def test_given_user_has_funds_when_process_transaction_then_transaction_is_accepted(camille_wallet):
    utxo_0 = TransactionInput(transaction_hash="5669d7971b76850a4d725c75fbbc20ea97bd1382e2cfae43c41e121ca399b660",
                              output_index=0)
    output_0 = TransactionOutput(
        public_key_hash=b"a037a093f0304f159fe1e49cfcfff769eaac7cda", amount=5)
    camille_wallet.process_transaction(inputs=[utxo_0], outputs=[output_0])


def test_given_user_has_more_funds_then_necessary_when_process_transaction_then_transaction_is_accepted(camille_wallet):
    utxo_0 = TransactionInput(transaction_hash="5669d7971b76850a4d725c75fbbc20ea97bd1382e2cfae43c41e121ca399b660",
                              output_index=0)
    output_0 = TransactionOutput(
        public_key_hash=b"a037a093f0304f159fe1e49cfcfff769eaac7cda", amount=3)
    output_1 = TransactionOutput(
        public_key_hash=b"7681c82af05a85f68a5810d967ee3a4087711867", amount=2)
    camille_wallet.process_transaction(
        inputs=[utxo_0], outputs=[output_0, output_1])


def test_given_user_points_to_non_existant_utxo_when_process_transaction_then_transaction_is_refused(camille_wallet):
    utxo_0 = TransactionInput(transaction_hash="5669d5971b76850a4d725c75fbbc20ea97bd1382e2cfae43c41e121ca399b660",
                              output_index=0)
    output_0 = TransactionOutput(
        public_key_hash=b"a037a093f0304f159fe1e49cfcfff769eaac7cda", amount=5)
    with pytest.raises(requests.exceptions.HTTPError) as error:
        camille_wallet.process_transaction(inputs=[utxo_0], outputs=[output_0])
    assert 'UTXO hash/output index combination not valid' in error.value.response.text


def test_given_user_points_to_utxo_output_index_not_pointing_to_user_when_process_transaction_then_transaction_is_refused(camille_wallet):
    utxo_0 = TransactionInput(transaction_hash="5669d5971b76850a4d725c75fbbc20ea97bd1382e2cfae43c41e121ca399b660",
                              output_index=1)
    output_0 = TransactionOutput(
        public_key_hash=b"a037a093f0304f159fe1e49cfcfff769eaac7cda", amount=5)
    with pytest.raises(requests.exceptions.HTTPError) as error:
        camille_wallet.process_transaction(inputs=[utxo_0], outputs=[output_0])
    assert 'UTXO hash/output index combination not valid' in error.value.response.text


def test_given_inputs_and_outputs_amounts_dont_match_when_process_transaction_then_transaction_is_refused(camille_wallet):
    utxo_0 = TransactionInput(transaction_hash="5669d7971b76850a4d725c75fbbc20ea97bd1382e2cfae43c41e121ca399b660",
                              output_index=0)
    output_0 = TransactionOutput(
        public_key_hash=b"a037a093f0304f159fe1e49cfcfff769eaac7cda", amount=3)
    with pytest.raises(requests.exceptions.HTTPError) as error:
        camille_wallet.process_transaction(inputs=[utxo_0], outputs=[output_0])
    assert 'Transaction inputs and outputs did not match' in error.value.response.text


def test_given_bad_signature_when_process_transaction_then_transaction_is_refused(camille):
    utxo_0 = TransactionInput(transaction_hash="5669d7971b76850a4d725c75fbbc20ea97bd1382e2cfae43c41e121ca399b660",
                              output_index=0)
    output_0 = TransactionOutput(
        public_key_hash=b"a037a093f0304f159fe1e49cfcfff769eaac7cda", amount=5)
    transaction = Transaction(camille, inputs=[utxo_0], outputs=[output_0])
    transaction.sign()
    node = Node()
    forged_transaction_data = forge_signature(transaction.transaction_data)
    with pytest.raises(requests.exceptions.HTTPError) as error:
        node.send({"transaction": forged_transaction_data})
    assert 'Transaction script validation failed' in error.value.response.text
