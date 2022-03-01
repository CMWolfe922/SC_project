import binascii, json
from signal import signal
import base58
from Crypto.Hash import SHA256, SHA3_256, SHA3_512
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
import requests
from wallet.utils import generate_transaction_data, convert_transaction_data_to_bytes, calculate_hash
from common.transaction_inputs import TransactionInput
from common.transaction_outputs import TransactionOutput

class Owner:
    def __init__(self, private_key: RSA.RsaKey, public_key: bytes, bitcoin_address: bytes):
        self.private_key = private_key
        self.public_key = public_key
        self.bitcoin_address = bitcoin_address


def initialize_wallet():
    private_key = RSA.generate(2048)
    public_key = private_key.publickey().export_key()
    hash_1 = calculate_hash(public_key, hash_function="sha256")
    hash_2 = calculate_hash(hash_1, hash_function="ripemd160")
    bitcoin_address = base58.b58encode(hash_2)
    return Owner(private_key, public_key, bitcoin_address)


class Transaction:

    def __init__(self, owner: Owner, inputs: list(TransactionInput),
    outputs: list(TransactionOutput)):
        self.owner = owner
        self.inputs = inputs
        self.outputs = outputs

    def sign_transaction_data(self):
        transaction_dict = {
            "inputs": [tx_input.to_json(with_signature_and_public_key=False) for tx_input in self.inputs],
            "outputs": [tx_output.to_json() for tx_output in self.outputs]
        }
        transaction_bytes = json.dumps(transaction_dict, indent=2).encode("utf-8")
        hash_object = SHA256.new(transaction_bytes)
        signature = pkcs1_15.new(self.owner.private_key).sign(hash_object)
        return signature

    def generate_data(self) -> bytes:
        transaction_data = generate_transaction_data(self.owner.bitcoin_address, self.receiver_bitcoin_address, self.amount)
        return convert_transaction_data_to_bytes(transaction_data)

    def sign(self):
       signature_hex = binascii.hexlify(self.sign_transaction_data()).decode("utf-8")
       for transaction_input in self.inputs:
           transaction_input.signature = signature_hex
           transaction_input.public_key = self.owner.public_key_hex

    def send_to_nodes(self):
        return {
            "inputs": [i.to_json() for i in self.inputs],
            "outputs": [i.to_json() for i in self.outputs]
        }


class Node:

    def __init__(self):
        ip = "127.0.0.1"
        port = 5000
        self.base_url = f"http://{ip}:{port}/"

    def send(self, transaction_data: dict) -> requests.Response:

        url = f"{self.base_url}transactions"
        req_return = requests.post(url, json=transaction_data)
        req_return.raise_for_status()
        return req_return


class Wallet:

    def __init__(self, owner: Owner):
        self.owner = owner
        self.node = Node()

    def process_transaction(self, inputs: list(TransactionInput), outputs: list(TransactionOutput)) -> requests.Response:
        transaction = Transaction(self.owner, inputs, outputs)
        transaction.sign()
        return self.node.send({"transaction":transaction.transaction_data})


# # Send a transaction:
# utxo_0 = TransactionInput(transaction_hash="whatever_hash", output_index=0)
# output_0 = TransactionOutput(public_key_hash=b"whatever_public_key", amount=5)
# your_wallet.process_transaction(inputs=list(utxo_0), outputs=list(output_0))
