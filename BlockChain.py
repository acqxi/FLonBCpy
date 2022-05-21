import hashlib
import json
from re import L
from time import time
from urllib.parse import urlparse
from uuid import uuid4

from FL_model import Net
import requests
from flask import Flask, jsonify, request

NUM_ZEROS = 4
class Blockchain:
    def __init__(self):
        self.master_chain = []
        self.backup_chains = []
        self.peer_nodes = []
        self.block = self.genesis_block()
    
    def genesis_block(self):
        block = {
            'index': 0,
            'previous_hash': "",
            'timestamp': time(),
            'nonce': 0,
            'model_hash': "default_model_path",
            'previous_model_acc': 0
        }

        self.master_chain.append(block)
        return block

    @staticmethod
    def calculate_hash(block):
        header_string = str(block["index"]) + block["previous_hash"] + \
            str(block["timestamp"]) + str(block["nonce"]) + \
            block["model_hash"] + str(block["previous_model_acc"])

        sha = hashlib.sha256()
        sha.update(header_string.encode("utf-8"))
        return sha.hexdigest()

    def running_FL(self):
        return Net.get_model_hash("Hello World")

    def generate_nonce(self, block):
        import time
        if (block['index'] != 0):
            while self.calculate_hash(block)[0:NUM_ZEROS] != '0' * NUM_ZEROS:
                block['nonce'] += 1
                time.sleep(0.001)
        return block
    
    def send_block_to_peers(self, block):
        pass

    def mining(self):
        block = {
            'index': self.block["index"]+1,
            'previous_hash': self.calculate_hash(self.block),
            'timestamp': time(),
            'nonce': 0,
            'model_hash': "",
            'previous_model_acc': 0
        }
        block['model_hash'] = self.running_FL()
        block['previous_model_acc'] = self.calculate_acc(block['model_hash'])
        block = self.generate_nonce(block)
        if (self.calculate_hash(self.master_chain[-1]) == block["previous_hash"]):
            self.block = block
            self.master_chain.append(self.block)
            self.send_block_to_peers(self.block)

    def update_backup_chains(self):
        for backup_chain in self.backup_chains:
            if (len(backup_chain) <= len(self.master_chain)-6):
                self.backup_chains.remove(backup_chain)

    def update_local_chains(self, block):
        new_chain = []
        for master_block in self.master_chain:
            new_chain.append(master_block)
            if (self.calculate_hash(master_block) == block["previous_hash"]):
                new_chain.append(block)
                break
        # add to master chain
        if (new_chain[-1] == block):
            if (len(new_chain) > len(self.master_chain)):
                self.master_chain = new_chain
                self.update_backup_chains()
            elif (len(new_chain) > len(self.master_chain)-6):
                self.backup_chains.append(new_chain)
            
        # search backup chain
        else:
            new_chain = []
            for backup_chain in self.backup_chains:
                for backup_block in backup_chain:
                    new_chain.append(backup_block)
                    if (self.calculate_hash(backup_block) == block["previous_hash"]):
                        new_chain.append(block)
                        break
            
            if (new_chain[-1] == block):
                if (len(new_chain) > len(self.master_chain)):
                    self.backup_chains.remove(new_chain[:-1])
                    self.backup_chains.append(self.master_chain)
                    self.master_chain = new_chain
                    self.update_backup_chains()

                elif (len(new_chain) > len(self.master_chain)-6):
                    self.backup_chains.remove(new_chain[:-1])
                    self.backup_chains.append(new_chain)

    def calculate_acc(self, model_hash):
        acc = 80
        Net.load_model_by_hash(model_hash)
        # model = TheModelClass(*args, **kwargs)
        # model.load_model(block["model_hash"])
        # model.eval()
        # from DataCenter import get_test1_data, get_test2_acc
        # test1_data = get_test_data(block["nonce"])
        # test2_acc = get_test2_acc(block["nonce"])
        # with torch.no_grad():
        #     for x, label in dataloader:
        #         ...
        return acc

    def valid_model_acc(self, block):
        # Is block accuracy better than previous ?
        # from FL_server import TheModelClass
        # 
        # if test1_acc > block["previous_model_acc"]
        #     

        # is new block ?
        # is 
        return True

    def valid_chain(self, chain):
        # check hash
        for block in chain:
            if (block["index"] != 0):
                if (block['previous_hash'] != self.calculate_hash(last_block)):
                    return False
            last_block = block
            
        return True

    def add_new_block(self, block):
        if self.valid_model_acc(block):
            self.update_local_chains(block)


# # Instantiate the Node
# app = Flask(__name__)

# # Generate a globally unique address for this node
# node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()
print(blockchain.master_chain)

# @app.route('/mine', methods=['GET'])
# def mine():
#     # We run the proof of work algorithm to get the next proof...
#     last_block = blockchain.last_block
#     proof = blockchain.proof_of_work(last_block)

#     # We must receive a reward for finding the proof.
#     # The sender is "0" to signify that this node has mined a new coin.
#     blockchain.new_transaction(
#         sender="0",
#         recipient=node_identifier,
#         amount=1,
#     )

#     # Forge the new Block by adding it to the chain
#     previous_hash = blockchain.hash(last_block)
#     block = blockchain.new_block(proof, previous_hash)

#     response = {
#         'message': "New Block Forged",
#         'index': block['index'],
#         'transactions': block['transactions'],
#         'proof': block['proof'],
#         'previous_hash': block['previous_hash'],
#     }
#     return jsonify(response), 200


# @app.route('/transactions/new', methods=['POST'])
# def new_transaction():
#     values = request.get_json()
    
#     # Check that the required fields are in the POST'ed data
#     required = ['sender', 'recipient', 'amount']
#     if not all(k in values for k in required):
#         return 'Missing values', 400

#     # Create a new Transaction
#     index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

#     response = {'message': f'Transaction will be added to Block {index}'}
#     return jsonify(response), 201


# @app.route('/chain', methods=['GET'])
# def full_chain():
#     response = {
#         'chain': blockchain.chain,
#         'length': len(blockchain.chain),
#     }
#     return jsonify(response), 200


# @app.route('/nodes/register', methods=['POST'])
# def register_nodes():
#     values = request.get_json()
#     nodes = values.get('nodes')
    
#     if nodes is None:
#         return "Error: Please supply a valid list of nodes", 400

#     for node in nodes:
#         blockchain.register_node(node)

#     response = {
#         'message': 'New nodes have been added',
#         'total_nodes': list(blockchain.nodes),
#     }
#     return jsonify(response), 201


# @app.route('/nodes/resolve', methods=['GET'])
# def consensus():
#     replaced = blockchain.resolve_conflicts()

#     if replaced:
#         response = {
#             'message': 'Our chain was replaced',
#             'new_chain': blockchain.chain
#         }
#     else:
#         response = {
#             'message': 'Our chain is authoritative',
#             'chain': blockchain.chain
#         }

#     return jsonify(response), 200


# if __name__ == '__main__':
#     from argparse import ArgumentParser

#     parser = ArgumentParser()
#     parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
#     args = parser.parse_args()
#     port = args.port

#     app.run(host='0.0.0.0', port=port)