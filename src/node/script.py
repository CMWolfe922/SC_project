import json, binascii
from Crypto.Hash import RSA
from utils import calculate_hash
# Since I am building a blockchain with python I can't use
# the script language, so I have to build one. To do that
# I have to first create a simple stack.

class Stack:
    def __init__(self):
        self.elements = []

    def push(self, element):
        self.elements.append(element)

    def pop(self):
        self.elements.pop()

# Then build another class called StackScript that inherits
# from Stack. It will contain methods that correspond to
# the methods in Stack

class StackScript(Stack):

    def __init__(self, transaction_data: dict):
        super().__init__()
        for count, tx_input in enumerate(transaction_data["inputs"]):
            tx_input_dict = json.loads(tx_input)
            tx_input_dict.pop("unlocking_script")
            transaction_data["inputs"][count] = json.dumps(tx_input_dict)
            self.transaction_data = transaction_data

    # This method duplicates the top most element of the stack
    # which is the public key
    def op_dup(self):
        public_key = self.pop()
        self.push(public_key)
        self.push(public_key)

    # This method hashes the last element of the stack (the public key) twice
    def op_hash160(self):
        public_key = self.pop()
        self.push(calculate_hash(calculate_hash(public_key, hash_function="sha256"), hash_function="ripemd160"))

    # This method validates that the last two elements of the stack
    # are equal to each other
    def op_equalverify(self):
        last_element_1 = self.pop()
        last_element_2 = self.pop()
        assert last_element_1 == last_element_2

    # The last one is op_check_sig that validates that the signature
    # from the unlocking script is valid.
    def op_checksig(self, transaction_data: dict):
        public_key = self.pop()
        signature = self.pop()
        signature_decoded = binascii.unhexlify(signature.encode("utf-8"))
        public_key_bytes = public_key.encode("utf-8")
        public_key_object = RSA.import_key(binascii.unhexlify(public_key_bytes))
        transaction_bytes = json.dumps(self.transaction_data, indent = 2).encode("utf-8")

# For Script Execution: The node looks inside of the unlocking scripts
# and locking scripts and executing the methods provided blindly.
# I will implement those execution methods in my NodeTransaction class.
