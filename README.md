# BUILDING MY BLOCKCHAIN WITH PYTHON:
---
> I didn't start taking notes from the tutorial until part 5, so I will need to go back and add the notes I need from parts 1-4. This way I know the purpose of each function and method created as well as the role they play overall. It will also, give me notes to reference while developing a plan to evolve the implementation.

## TRANSACTION SCRIPTS:
> Basically, up until this point validating transactions was done by using cryptography to spend some of the unspent transaction outputs. To do this, I would present proof that the amount was correct/valid using a signature. **BUT** *to allow for this type of transaction as well as much more complex ones to take place, I need to create a "transaction script" like bitcoin and other cryptocurrencies use*. The scripts are used to define the contract between sender and receiver.

    - Other currencies like bitcoin have their own language for building transaction scripts. Here, I will have to create my own 'script' using classes and methods.

This is the definition of Transaction Scripts on Bitcoin's wiki:
    - **A _transaction_ script is a list of instructions recorded with each transaction that describe how the next person wanting to spend the Bitcoins being transferred can gain access to them.**

- Transaction Scripts are made out of two sections, an unlocking script and a locking script and those are part of each transaction. This is what a typical bitcoin transaction looks like:
```json
{
    'inputs': [
        {"transaction_hash": "a26d9501f3fa92ffa9991cf05a72f8b9ca2d66e31e6221cecb66973671a81898", "output_index": 0,
         "unlocking_script": "<sender signature> <sender public key>"}],
    'outputs': [
        {"amount": 10,
         "locking_script": "OP_DUP OP_HASH160 <receiver public key hash> OP_EQUAL_VERIFY OP_CHECKSIG"}]
}
```

> This shows that each transaction input now contains 3 fields: the UTXO hash, the UTXO output index and an unlocking script. The unlocking script is the key to spend the amount from the specified UTXO. For a typical bitcoin transaction, the unlocking script looks like this:

`<sig> <pubKey>`

- **Each ***transaction output*** contains two fields**:
1. The amount
2. The locking script

- The locking script encumbers the output with the receiver address. For a typical bitcoin transaction, the locking script will look like this:
`OP_DUP OP_HASH160 <pubKeyHash> OP_EQUAL_VERIY OP_CHECKSIG`

> The scripting language used inside of bitcoin to conduct these transactions is called **Script** and it was developed specifically for bitcoin. Both the locking and unlocking scripts are written in this language.

- This is a quote from _Mastering Bitcoin_:
> _Transaction outputs associate a specific amount to a specific encumbrance or locking script that defines the condition that must be met to spend that amount. In most cases, the locking script will lock the output to a specific bitcoin address, thereby transferring ownership of that amount to the new owner. When Alice paid Bob’s Cafe for a cup of coffee, her transaction created a 0.015 bitcoin output encumbered or locked to the cafe’s bitcoin address. That 0.015 bitcoin output was recorded on the blockchain and became part of the Unspent Transaction Output set, meaning it showed in Bob’s wallet as part of the available balance. When Bob chooses to spend that amount, his transaction will release the encumbrance, unlocking the output by providing an unlocking script containing a signature from Bob’s private key._

- For each transaction, nodes will combine the unlocking script from the transaction's input to the locking script associated with the UTXO stored on the blockchain and compute the script. If the script passes, the transaction is valid, and if it fails, it's invalid.

##### Unlocking Script: (scriptSig)
`<sig> <PubK>`
-> Unlock Script (scriptSig) is provided by the user to resolve the encumbrance.

##### Locking Script: (scriptPubKey)`
`DUP HASH160 <PubKHash> EQUALVERIFY CHECKSIG`
-> Lock Script (scriptPubKey) is found in a transaction output and is the encumbrance that must be fulfilled to spend the output

### Script Execution:
---
One of the most common examples to this is the validations used for checking the hash signatures.

- Example:
    1. Person 1 wants to send funds to person 2 and wants only Person 2 to be able to make transactions with those funds in the future. The locking script for this transaction would look like this:
    `OP_DUP OP_HASH160 <pubKeyHash> OP_EQUAL_VERIFY OP_CHECKSIG`

    2. *where `<pubKeyHash>` is Person 2's public key hash. Now when Person 2 wants to make a transaction to Person 3, he or she will use the UTXO received from the first transaction and he or she will provide the unlocking script associated to this transaction. This unlocking script will look like This:*
    - `<sig> <pubKey>`

    3. Now when the node receives the transaction, it will look at the inputs' UTXO and it will retrieve the locking script associated with it from the blockchain. It will then combine those teo together (it's just a simple concatenation)
    - `<sig> <pubKey> OP_DUP OP_HASH160 <pubKeyHash> OP_EQUAL_VERIFY OP_CHECKSIG`

> So each operation above that I just laid out is an operation done to a stack. The node will create an empty stack and will execute the operations of this script in the same order as they come. So if I wrote the script out, it would look like this:

    1. Push the Signature
    2. Push the public key
    3. Complete the OP_DUP operation
    4. Complete the OP_HASH160 operation
    5. Push the public key hash
    6. Complete the OP_EQUAL_VERIFY operation
    7. Complete the OP_CHECKSIG operation

**[+] Definitions for those operations:**
- `OP_DUP` --> Duplicates the top stack item (`<pubKey>`)
- `OP_HASH_160` --> The top stack item (`<pubKey>`) is hashed twice, first with SHA-256 and then with RIPEMD-160
- `OP_EQUAL_VERIFY` --> Fails if the last 2 items in the stack don't match (`<pubKey>` and `<pubKeyHash>`)
- `OP_CHECK_SIG` --> The entire transaction's outputs, inputs, and script are hashed. The signature `<sig>` is validated against this hash.

> ABOVE IS A VERY BASIC TYPE OF SCRIPT. THERE ARE MUCH MORE COMPLEX TYPES OF SCRIPTS THAT I NOTE FURTHER DOWN.

### Script Implementation
---
To iimplement the script I have to update the transaction input and output data structures to reflect the dact that they now contain scripts.

- So for `transaction_inputs.py`:
```python
class TransactionInput:
    def __init__(self, transaction_hash: str, output_index: int, unlocking_script: str = ""):
        self.transaction_hash = transaction_hash
        self.output_index = output_index
        self.unlocking_script = unlocking_script

    def to_json(self, with_unlocking_script: bool = True) -> str:
        if with_unlocking_script:
            return json.dumps({
                "transaction_hash": self.transaction_hash,
                "output_index": self.output_index,
                "unlocking_script": self.unlocking_script
            })
        else:
            return json.dumps({
                "transaction_hash": self.transaction_hash,
                "output_index": self.output_index
            })

```
- `transaction_ouputs.py`
```python
import json


class TransactionOutput:
    def __init__(self, public_key_hash: bytes, amount: int):
        self.amount = amount
        self.locking_script = f"OP_DUP OP_HASH160 {public_key_hash} OP_EQUAL_VERIFY OP_CHECKSIG"

    def to_json(self) -> str:
        return json.dumps({
            "amount": self.amount,
            "locking_script": self.locking_script
        })
```

> Since this is written in python like discussed above, I can't use the script language so the code below will be influenced by it and it will start with a simple stack:

```python
# node/script.pyclass Stack:
    def __init__(self):
        self.elements = []

    def push(self, element):
        self.elements.append(element)

    def pop(self):
        return self.elements.pop()
```

> We create a new class `StackScript` that inherits from the `Stack` class. This new class contains methods that correspond to the operations shown above. It also has an `__init__` that will store the current transaction data. This information will be used later by the `op_check_sig` method.

```python
# node/script.pyclass StackScript(Stack):
    def __init__(self, transaction_data: dict):
        super().__init__()
        for count, tx_input in enumerate(transaction_data["inputs"]):
            tx_input_dict = json.loads(tx_input)
            tx_input_dict.pop("unlocking_script")
            transaction_data["inputs"][count] = json.dumps(tx_input_dict)
        self.transaction_data = transaction_data    def op_dup(self):
        pass

    def op_hash160(self):
        pass

    def op_equalverify(self):
        pass

    def op_checksig(self, transaction_data: dict):
        pass
```

##### Details about above methods:
> The first is `op_dup` and simply duplicates the top most element of the stack, which is the public key.
```python
def op_dup(self):
    public_key = self.pop()
    self.push(public_key)
    self.push(public_key)
```

> The next is `op_hash_160` that hashes the last element from the stack (the public key) twice.
```python
def op_hash160(self):
    public_key = self.pop()
    self.push(calculate_hash(calculate_hash(public_key, hash_function="sha256"), hash_function="ripemd160"))
```

> The next is `op_equalverify` that validates that the last 2 elements from the stack are equal.
```python
def op_equalverify(self):
    last_element_1 = self.pop()
    last_element_2 = self.pop()
    assert last_element_1 == last_element_2
```

> The last one is `op_check_sig` that validates that the signature from the unlocking script is valid.
```python
def op_checksig(self):
    public_key = self.pop()
    signature = self.pop()
    signature_decoded = binascii.unhexlify(signature.encode("utf-8"))
    public_key_bytes = public_key.encode("utf-8")
    public_key_object = RSA.import_key(binascii.unhexlify(public_key_bytes))
    transaction_bytes = json.dumps(self.transaction_data, indent=2).encode('utf-8')
    transaction_hash = SHA256.new(transaction_bytes)
    pkcs1_15.new(public_key_object).verify(transaction_hash, signature_decoded)
```

### BACK TO SCRIPT EXECUTION:
---
> The node looks inside of the unlocking scripts and locking scripts and executes the methods provided blindly. Those execution steps will be implemented in `NodeTransaction` class in the `node.py` file:

```python
from node.script import StackScriptclass NodeTransaction:

    def execute_script(self, unlocking_script, locking_script):
        unlocking_script_list = unlocking_script.split(" ")
        locking_script_list = locking_script.split(" ")
        stack_script = StackScript(self.transaction_data)
        for element in unlocking_script_list:
            if element.startswith("OP"):
                class_method = getattr(StackScript, element.lower())
                class_method(stack_script)
            else:
                stack_script.push(element)
        for element in locking_script_list:
            if element.startswith("OP"):
                class_method = getattr(StackScript, element.lower())
                class_method(stack_script)
            else:
                stack_script.push(element)
```
