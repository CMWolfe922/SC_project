import binascii, json

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15

from node.block import Block
from transaction_inputs import TransactionInput
from transaction_outputs import TransactionOutput

class NodeTransaction:

    def __init__(self, blockchain: Block):
        self.blockchain = blockchain
        self.transaction_data = ""
        self.signature = ""

    def validate_signature(self):
        transaction_data = copy.deepcopy(self.transaction_data)
        for count, tx_input in enumerate(transaction_data["inputs"]):
            tx_input_dict = json.loads(tx_input)
            public_key = tx_input_dict.pop("public_key")
            signature = tx_input_dict.pop("signature")
            transaction_data["inputs"][count] = json.dumps(tx_input_dict)
            signature_decoded = binascii.unhexlify(signature.encode("utf-8"))
            public_key_bytes = public_key.encode("utf-8")
            public_key_object = RSA.import_key(binascii.unhexlify(public_key_bytes))
            transaction_bytes = json.dumps(transaction_data, indent=2).encode('utf-8')
            transaction_hash = SHA256.new(transaction_bytes)

    def validate_funds(self, sender_address: bytes, amount: int) -> bool:
        sender_balance = 0
        current_block = self.blockchain
        while current_block:
            if current_block.transaction_data["sender"] == sender_address:
                sender_balance = sender_balance - current_block.transaction_data["amount"]
            if current_block.transaction_data["receiver"] == sender_address:
                sender_balance = sender_balance + current_block.transaction_data["amount"]
            current_block = current_block.previous_block
        if amount <= sender_balance:
            return True
        else:
            return False

    def validate(self):
        self.validate_signature()
        self.validate_funds_are_owned_by_sender()
        self.validate_funds()

pkcs1_15.new(public_key_object).verify(transaction_hash, signature_decoded)
