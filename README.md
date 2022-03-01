# BUILDING MY BLOCKCHAIN WITH PYTHON:
---
> I didn't start taking notes from the tutorial until part 5, so I will need to go back and add the notes I need from parts 1-4. This way I know the purpose of each function and method created as well as the role they play overall. It will also, give me notes to reference while developing a plan to evolve the implementation.

## DOUBLE ENTRY BOOKKEPING AND UTXO's:
> This section will deep dive into how transactions are actually stored on the blockchain (which is via double entry bookkeeping). And while doing this it will cover the subject of Unspent Transaction Outputs (UTXO's)
---

- This is the wikipedia definition:
*__Double-entry bookkeeping__, in accounting, is a system of book keeping where every entry to an account requires a corresponding and opposite entry to a different account. The double-entry system has two equal and corresponding sides known as debit and credit. The left-hand side is debit and the right-hand side is credit.*

- The reason this makes sense is because there really are two different effects for every transaction. An example of this would be; if you are buying a car. You give money and you receive a car. Those are two distinct things that will affect your business differently. Now if we look at the only equation in accounting (shown below), buying a $1,000 car here will increase both your __assets__ and your __liabilities__ (accounts payable) by $1000 and both sides of the accounting equation remain the same:
    - Assets = Liabilities + Equity

Most businesses use double-entry bbookkeeping for their accounting needs mainly because it makes it more simple to keep track of assets and liabilities.

__Double Entry Bookkeping In Blockchain__
Up to now I have used single entry in the blockchain I built (i.e. one entry per transaction). Our entries looked something like "sender, receiver, amount". But double-entry bookkeeping is useful, so how can it relate to the transactions in the blockchain?

- Quote from 'Mastering Bitcoin':
> In simple terms, each transaction contains one or more “inputs,” which are debits against a bitcoin account. On the other side of the transaction, there are one or more “outputs,” which are credits added to a bitcoin account.

- This would now make the transactions contain two sections: inputs and outputs. So if I used the example; Camille has 15 and she wants to send 5 to Albert, *This would be 1 input and 2 outputs*:

    - Inputs: _Input #1_ __Address__: Camille __Amount__: 15
    - Outputs: _Output #1_ __Address__: Albert __Amount__: 5
    - Outputs: _Output #2_ __Address__: Camille __Amount__: 10

---
##### Transaction Forms:
This new format will allow my transactions to have any number of inputs and outputs, and these are some common forms:

- __Common Transaction (1 input, 2 outputs):__ This is what I just showed above where Person 1 sends money to Person 2 and there's change.

- __Aggregation Transaction (N inputs, 1 output):__ If person 1 has received money through multiple transactions and he want to simplify his assets, he might want to aggregate them (just like you would exchange your pocket change against a 20$ bill).

- __Distributing Transactions (1 input, N outputs):__ If person 1 wants to send money to all of his friends for example, he would use a distributing transaction.


##### Unspent Transaction Outputs (UTXO):
This will complicate things. But lets consider that inputs for transactions are a collection of previously unspent transaction outputs (UTXO). This is easy to commpare with real cash: _Person 1 gives you $10, Person 2 gives you $20 and you want to buy a t-shirt for $25, You would have to use your two unspent transaction outputs (your two bills) to produce a new transaction to the t-shirt shop. At this point you will give your $20 bill and your $10 bill to the shop and you will get a $5 bill in change. This is the same as what happened with Albert, Bertrand and Camille.

> So this means that transaction inputs contain a past transaction's hash and the output index corresponding to the UTXO. So to apply this to my python code, I have to create two new classes that will help me form my transactions. And the first one is for `transaction_inputs.py`

```python
class TransactionInput:
    def __init__(self, transaction_hash: str, output_index: int, public_key: str = "", signature: str = ""):
        self.transaction_hash = transaction_hash
        self.output_index = output_index
        self.public_key = public_key
        self.signature = signature

    def to_json(self, with_signature_and_public_key: bool = True) -> str:
        if with_signature_and_public_key:
            return json.dumps({
                "transaction_hash": self.transaction_hash,
                "output_index": self.output_index,
                "public_key": self.public_key,
                "signature": self.signature
            })
        else:
            return json.dumps({
                "transaction_hash": self.transaction_hash,
                "output_index": self.output_index
            })
```

> And the second one it for `transaction_ouputs.py`

```python
class TransactionOutput:
    def __init__(self, public_key_hash: str, amount: int):
        self.amount = amount
        self.public_key_hash = public_key_hash

    def to_json(self) -> str:
        return json.dumps({
            "amount": self.amount,
            "public_key_hash": self.public_key_hash
        })
```

- Now I have to update these methods inside my wallet's `Transaction` class to reflect these changes:

```python
import json

from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15

from transaction.transaction_input import TransactionInput
from transaction.transaction_output import TransactionOutputclass Transaction:
    def __init__(self, owner: Owner, inputs: [TransactionInput], outputs: [TransactionOutput]):
        self.owner = owner
        self.inputs = inputs
        self.outputs = outputs

    def sign_transaction_data(self):
        transaction_dict = {
            "inputs": [tx_input.to_json(with_signature_and_public_key=False) for tx_input in self.inputs],
            "outputs": [tx_output.to_json() for tx_output in self.outputs]
        }
        transaction_bytes = json.dumps(transaction_dict, indent=2).encode('utf-8')
        hash_object = SHA256.new(transaction_bytes)
        signature = pkcs1_15.new(self.owner.private_key).sign(hash_object)
        return signature

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
```

> So now lets say that Camille wants to send 5 to Bertrand, here is how her wallet would do it:

```python
utxo_0 = TransactionInput(transaction_hash=blockchain.transaction_hash, output_index=0)
output_0 = TransactionOutput(public_key_hash=bertrand_wallet.public_key_hash, amount=5)
transaction = Transaction(camille_wallet, inputs=[utxo_0], outputs=[output_0])
transaction.sign()
```



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

> After `execute_script`, I am going to create an empty stack, scroll through each element of each script and apply the methods to the stack.

    - Also, modify the `validate` method so that the `execute_script` method is called for every transaction input.

```python
def validate(self):
        for tx_input in self.inputs:
            input_dict = json.loads(tx_input)
            locking_script = self.get_locking_script_from_utxo(input_dict["transaction_hash"], input_dict["output_index"])
            self.execute_script(input_dict["unlocking_script"], locking_script)
```

- for each input, the locking script is retrieved from the UTXO. To do so, we created a new method called `get_locking_script_from_utx`. This method scrolls through the blockchain until it finds the UTXO and returns its locking script.

```python
def get_locking_script_from_utxo(self, utxo_hash: str, utxo_index: int):
        transaction_data = self.get_transaction_from_utxo(utxo_hash)
        return json.loads(transaction_data["outputs"][utxo_index])["locking_script"]
```

#### Other Transaction Scripts
---
> Transaction scripts are at the core of every blockchain transaction. They allow secure validation of transactions and provide a framework to create complex transaction contracts. Validating transactions with the use of scripts allows for a variety of different transaction types to exist. *Below is a list of examples:*

- **Pay-to-Public-Key-Hash (P2PKH)**: This is the most common execution script and it is the one used as an example above.

```Script
Unlocking script: <sig> <pubKey>
Locking script: OP_DUP OP_HASH160 <Cafe Public Key Hash> OP_EQUAL OP_CHECKSIG
```

- **Pay-to-Public-Key (P2PK):** This is similar to P2PKH but it takes a whole lot more space because you have to know the whole public key of the person you want to send money to.

```Script
Unlocking script: <sig>
Locking script: <pubKey> OP_CHECKSIG
```

- **Multi-signature:** These exist for when you need multiple people to approve a transaction. At least M out of N of those must provide signatures to unlock funds.

```Script
Unlocking script: OP_0 <Signature 1> <Signature 2>
Locking script: M <Public Key 1> <Public Key 2> … <Public Key N> N CHECKMULTISIG
```

- **Pay-to-script-hash (P2SH):** This allows you to accept money from a client and only use the money if 'M out of N' partners approve the use of the funds. So kind of like a vote to use the funds. The locking script the client would have to use would be very long and complex. P2SH scripts are around to simplify complex transactions by hashing those complex scripts.

```Script
Unlocking script: Sig1 Sig2 redeem script
Locking script: OP_HASH160 <Hash of redeem script> OP_EQUAL
```
---
Now that The transaction scripts have been covered and the blockchain can validate transactions, it still isn't decentralized. If I turned my computer off it wouldn't work. The next section will go over decentralizing the network and creating a network that consists of multiple nodes that can communicate with each other via TCP/IP. Each node will store a copy of the blockchain and is responsible of validating transactions and broadcasting them to other nodes.

---

## THE NETWORK:
---
So far I have built three things: a blockchain, a node, and a wallet. The blockchain contains blocks and each block contains transaction data, a timestamp and a hash of the previous block. The node stores the blockchain and validates new transactions. The wallet builds new transactions and is capable of sending those to the node. As of now, all of that code is central. So only my computer can make transactions.

- So this is where it begins to get more complicated. In this section, the code will begin broadcasting transactions to the network.

### The Blockchain Network:
---
In bitcoin, satoshi nakomoto defines a transaction like this:
1. New transactions are broadcast to all nodes.
2. Each node collects new transactions into a block.
3. Each node works on finding a difficult proof-of-work for its block.
4. When a node finds a proof-of-work, it broadcasts the block to all nodes.
5. Nodes accept the block only if all transactions in it are valid and not already spent.
6. Nodes express their acceptance of the block by working on creating the next block in the chain, using the hash of the accepted block as the previous hash.

- So instead of storing the ledger centrally, their is a network of nodes that store a copy of the blockchain. They work with each other in a competitive manner to process transactions and ultimately maintain the ledger.

##### Transaction Validation:
Validating the transaction is the first step in the transaction process. These transactions are sent by the wallet and received by the nodes that validate they're valid.

- first, I need to make adjustments to my code to accomodate remote transaction validation. I will start with modifying the wallet code to allow it to **send** HTTP requests to a node. *So create two new classes in the wallet file*:

```python
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
```

> **Note:** I am adding a new library requirement `requests` which helps form and send HTTP requests. As a user of those classes you would create and send a transaction like so:
---
```python
utxo_0 = TransactionInput(transaction_hash="whatever_hash",
                          output_index=0)
output_0 = TransactionOutput(public_key_hash=b"whatever_public_key", amount=5)
your_wallet.process_transaction(inputs=[utxo_0], outputs=[output_0])
```
---
- I also need to modify my node's code so that it can receive HTTP requests (i.e. I need the node to have an API). To do this easily, I am going to use the Flask framework to build a restful API. [Click here for quick Flask tutorial](https://flask.palletsprojects.com/en/2.0.x/quickstart/)

- Create a `main.py` file that takes care of accepting HTTP requests and routing them to the correct methods. SO for each POST to the `/transactions` endpoint, I will have a method called `validate_transaction` that will be executed. Inside of that method, I will use the "node's" `validate` and `validate_funds` methods.
- Then if there is an _error_ then __status code 400__ will show up, IF __there is no__ _error then status code 200_ will show.

    -Code for flask app:

```python
from flask import Flask, request

from node.node import NodeTransaction, TransactionException
from initialize_blockchain import blockchain

app = Flask(__name__)

blockchain_base = blockchain()

@app.route("/transactions", methods=['POST'])
def validate_transaction():
    content = request.json
    try:
        node = NodeTransaction(blockchain_base)
        node.receive(transaction=content["transaction"])
        node.validate()
        node.validate_funds()
        node.broadcast()
    except TransactionException as transaction_exception:
        return f"{transaction_exception}", 400
    return "Transaction Success!", 200

```

> __To start the flask app, go to terminal and run this:__

`set FLASK_APP=src/main.py`
`flask run`

_Note that you can change the HTTP port that your flask app listens on by adding the `—- port` option to `flask run` command. Example: `flask run —-port 5002`_

    - This can also enable you to create multiple instances of the app on your laptop if each has a different port.

--> After the node validates the transaction it will send it to other nodes that it knows about.

> So, part of the node code will be another class called `OtherNode`

```python
class OtherNode:
    def __init__(self, ip: str, port: int):
        self.base_url = f"http://{ip}:{port}/"

    def send(self, transaction_data: dict) -> requests.Response:
        url = f"{self.base_url}transactions"
        req_return = requests.post(url, json=transaction_data)
        req_return.raise_for_status()
        return req_return
```

> After creating the new node class, I need to add a `broadcast` method to `NodeTransaction` class that will take care of broadcasting the transaction data to other nodes. This method is called right after transactions are validated.

```python
class NodeTransaction:
    def broadcast(self):
        node_list = [OtherNode("127.0.0.1", 5001), OtherNode("127.0.0.1", 5002)]
        for node in node_list:
            try:
                node.send(self.transaction_data)
            except requests.ConnectionError:
                pass
```

> At This point the code should send transactions from a wallet to a node via http, thave that transaction validated by the node and broadcasted to other nodes. Those two elements (wallet and node) don't have to be on the same laptop anymore. They can be anywhere as long as the wallet can reach the node via http.

But to get test this is working I have to build a script to send and receive transactions:

```python
from datetime import datetime

from blockchain_users.albert import private_key as albert_private_key
from blockchain_users.bertrand import private_key as bertrand_private_key
from blockchain_users.camille import private_key as camille_private_key
from common.transaction_input import TransactionInput
from common.transaction_output import TransactionOutput
from node.block import Block
from wallet.wallet import Owner

albert_wallet = Owner(private_key=albert_private_key)
bertrand_wallet = Owner(private_key=bertrand_private_key)
camille_wallet = Owner(private_key=camille_private_key)


def blockchain():
    timestamp_0 = datetime.timestamp(
        datetime.fromisoformat('2011-11-04 00:05:23.111'))
    input_0 = TransactionInput(transaction_hash="abcd1234",
                               output_index=0)
    output_0 = TransactionOutput(public_key_hash=b"Albert",
                                 amount=40)
    inputs = [input_0.to_json()]
    outputs = [output_0.to_json()]
    block_0 = Block(
        transaction_data={"inputs": inputs, "outputs": outputs},
        timestamp=timestamp_0
    )

    timestamp_1 = datetime.timestamp(
        datetime.fromisoformat('2011-11-04 00:05:23.111'))
    input_0 = TransactionInput(transaction_hash=block_0.transaction_hash,
                               output_index=0)
    output_0 = TransactionOutput(public_key_hash=bertrand_wallet.public_key_hash,
                                 amount=30)
    output_1 = TransactionOutput(public_key_hash=albert_wallet.public_key_hash,
                                 amount=10)
    inputs = [input_0.to_json()]
    outputs = [output_0.to_json(), output_1.to_json()]

    block_1 = Block(
        transaction_data={"inputs": inputs, "outputs": outputs},
        timestamp=timestamp_1,
        previous_block=block_0
    )

    timestamp_2 = datetime.timestamp(
        datetime.fromisoformat('2011-11-07 00:05:13.222'))
    input_0 = TransactionInput(transaction_hash=block_1.transaction_hash,
                               output_index=1)
    output_0 = TransactionOutput(public_key_hash=camille_wallet.public_key_hash,
                                 amount=10)
    inputs = [input_0.to_json()]
    outputs = [output_0.to_json()]
    block_2 = Block(
        transaction_data={"inputs": inputs, "outputs": outputs},
        timestamp=timestamp_2,
        previous_block=block_1
    )

    timestamp_3 = datetime.timestamp(
        datetime.fromisoformat('2011-11-09 00:11:13.333'))
    input_0 = TransactionInput(transaction_hash=block_1.transaction_hash,
                               output_index=0)
    output_0 = TransactionOutput(public_key_hash=camille_wallet.public_key_hash,
                                 amount=5)
    output_1 = TransactionOutput(public_key_hash=bertrand_wallet.public_key_hash,
                                 amount=25)
    inputs = [input_0.to_json()]
    outputs = [output_0.to_json(), output_1.to_json()]
    block_3 = Block(
        transaction_data={"inputs": inputs, "outputs": outputs},
        timestamp=timestamp_3,
        previous_block=block_2
    )
    return block_3
```
