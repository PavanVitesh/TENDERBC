from datetime import datetime
import os
import regex as re
from pypdf import PdfReader, PdfWriter
from cryptography.hazmat.backends import default_backend
import boto3
from dotenv import load_dotenv
import hashlib
from typing import List
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3 import exceptions as Web3Exceptions
import json

def encrypt_file(input_file_path: str, tender_id: str, bid_id: str) -> List[str]:
    """Encrypts a PDF file using a randomly generated encryption key (256 bit), deletes the original file, 
    and saves the encrypted file to the disk with name 'tender_id-bid_id.pdf' ( the new file name).

    Returns the path to the encrypted file, the encryption key, and the new file name.
    """
    try:
        load_dotenv()
        backend = default_backend()
        encryption_key = os.urandom(32)
        pdf_writer = PdfWriter()
        pdf_file_path = fr'{os.getenv('BID_DOCUMENTS_PATH')}{input_file_path}'
        with open(pdf_file_path, 'rb') as file:
            pdf_reader = PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                pdf_writer.add_page(pdf_reader.pages[page_num])
            pdf_writer.encrypt(user_password=encryption_key.hex(), algorithm='AES-256')
        new_file_name =  str(tender_id) + '-' + str(bid_id) + '.pdf'
        encrypted_pdf_file_path = os.getenv('BID_DOCUMENTS_PATH') + new_file_name
        with open(encrypted_pdf_file_path, 'wb') as file:
            pdf_writer.write(file)
        os.remove(pdf_file_path)
        return new_file_name, encryption_key.hex()
    except BaseException as e:
        print(e)
        raise BaseException("There is a problem at our end. Please try again later.")

def decrypt_file(encrypted_pdf_file_name: str, decryption_key: str) -> None:
    """Decrypts a PDF file using a decryption key provided, and replaces the encrypted file with the decrypted file.
    """
    try:
        print("Decrypting")
        pdf_writer = PdfWriter()
        with open(os.getenv('BID_DOCUMENTS_PATH') + encrypted_pdf_file_name, 'rb') as file:
            pdf_reader = PdfReader(file, password=decryption_key)
            for page_num in range(len(pdf_reader.pages)):
                pdf_writer.add_page(pdf_reader.pages[page_num])
        with open(os.getenv('BID_DOCUMENTS_PATH') + encrypted_pdf_file_name, 'wb') as file:
            pdf_writer.write(file)
    except BaseException as e:
        print(e)
        raise BaseException("There is a problem at our end. Please try again later.")
    
def connect_to_dstorage() -> boto3.client:
    """Connects to the decentralized storage.

    Returns the instance of the S3 client.
    """
    try:
        load_dotenv()
        s3 = boto3.client('s3',
                        aws_access_key_id=os.getenv('STORJ_ACCESS_KEY'),
                        aws_secret_access_key=os.getenv('STORJ_SECRET_KEY'),
                        endpoint_url=os.getenv('STORJ_ENDPOINT_URL'))
        return s3
    except BaseException as e:
        print(e)
        raise BaseException("There is a problem at our end. Please try again later.")

def save_to_dstorage(file_path: str, file_name: str) -> None:
    """
    Save a file to the decentralized storage.
    Args:
        file_path (str): The path to the file.
        file_name (str): The name of the file.
    Returns:
        None
    """
    try:
        load_dotenv()
        s3 = connect_to_dstorage()
        bucket_name = 'tender-bucket'
        with open(file_path, 'rb') as file:
            s3.upload_fileobj(file, bucket_name, file_name)
    except BaseException as e:
        print(e)
        raise BaseException("There is a problem at our end. Please try again later.")

def get_from_dstorage(file_name: str) -> str:
    """Retreives the file from the decentralized storage, and saves it to the disk with the same name.
    Returns the path to the file.
    """
    try:
        load_dotenv()
        s3 = connect_to_dstorage()
        bucket_name = 'tender-bucket'
        file_path = os.getenv('BID_DOCUMENTS_PATH') + file_name
        print(file_path)
        print(file_name)
        s3.download_file(bucket_name, file_name, file_path)
    except BaseException as e:
        print(e)
        raise BaseException("There is a problem at our end. Please try again later.")

def calculate_checksum(file_path: str) -> str:
    """Calculates the checksum of a file using SHA-256 algorithm.

    Returns the checksum of the file.
    """
    try:
        sha256 = hashlib.sha512()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except BaseException as e:
        print(e)
        raise BaseException("There is a problem at our end. Please try again later.")

def connect_to_chain() -> List[str]:
    """Connects to the Geth node and the smart contract within the blockchain.

    Returns the Web3 instance and the Contract instance.
    """
    try:
        load_dotenv()
        w3 = Web3(Web3.HTTPProvider(os.getenv('GETH_NODE_ENDPOINT_URL')))
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        contract_abi = None
        with open(os.getenv('PATH_TO_CONTRACT_ABI'), 'r') as f:
            contract_abi = json.load(f)
        contract_address = os.getenv('CONTRACT_ADDRESS')
        contract = w3.eth.contract(contract_address, abi=contract_abi)
        w3.eth.default_account = w3.eth.accounts[0]
        return w3, contract
    except BaseException as e:
        print(e)
        raise BaseException("There is a problem at our end. Please try again later.")

def add_tender_data_to_chain(tender_id: int, start_time:datetime, end_time: datetime) -> None:
    """Add tender data (tender id, start time, end time) to the blockchain.
    
    For example:
        >>> tender_id = 1
        >>> start_time = datetime(2021, 9, 1, 0, 0, 0).timestamp() # seconds since epoch
        >>> end_time = datetime(2021, 9, 2, 0, 0, 0).timestamp() # seconds since epoch
    """
    try:
        w3, contract = connect_to_chain()
        tx_hash = contract.functions.createTender(tender_id, int(start_time.timestamp()), int(end_time.timestamp())).transact()
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        decoded_logs = contract.events.TenderCreated().process_receipt(tx_receipt)
        if not decoded_logs:
            raise BaseException("No event logs found for TenderCreated")
    except Web3Exceptions.ContractLogicError as e:
        print(e.args[0].split(":")[1].strip())
        raise BaseException(e.args[0].split(":")[1].strip())
    except BaseException as e:
        print(e)
        raise BaseException("There is a problem at our end. Please try again later.")

def save_checksum_to_chain(tender_id: int, bidder_id: int, checksum: str) -> None:
    """Save the checksum of the file to the blockchain.
    """
    try: 
        w3, contract = connect_to_chain()
        tx_hash = contract.functions.placeBid(tender_id, bidder_id, checksum).transact()
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        decoded_logs = contract.events.BidAdded().process_receipt(tx_receipt)
        if not decoded_logs:
            raise BaseException("No event logs found for BidAdded")
    except Web3Exceptions.ContractLogicError as e:
        print(e.args[0].split(":")[1].strip())
        raise BaseException(e.args[0].split(":")[1].strip())
    except BaseException as e:
        print(e)
        raise BaseException("There is a problem at our end. Please try again later.")

def save_dkey_to_chain(tender_id: int, bidder_id: int, dkey: str) -> None:
    """Save the decryption key to the blockchain.
    """
    try:
        w3, contract = connect_to_chain()
        tx_hash = contract.functions.saveBidDKey(tender_id, bidder_id, dkey).transact()
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        decoded_logs = contract.events.DKeyUploaded().process_receipt(tx_receipt)
        if not decoded_logs:
            raise BaseException("No event logs found for DKeyUploaded")
    except Web3Exceptions.ContractLogicError as e:
        print(e.args[0].split(":")[1].strip())
        raise BaseException(e.args[0].split(":")[1].strip())
    except BaseException as e:
        print(e)
        raise BaseException("There is a problem at our end. Please try again later.")

def check_if_dkey_present(tender_id: int, bidder_id: int) -> bool:
    try:
        w3, contract = connect_to_chain()
        tx_hash = contract.functions.dKeyForBidIsPresent(tender_id, bidder_id).transact()
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        decoded_logs = contract.events.DKeyChecked().process_receipt(tx_receipt)
        if decoded_logs:
            return decoded_logs[0]['args']['dKeyPresent']
        else:
            raise BaseException("No event logs found for DKeyChecked")
    except Web3Exceptions.ContractLogicError as e:
        raise BaseException(e.args[0].split(":")[1].strip())
    except BaseException as e:
        print(e)
        raise BaseException("There is a problem at our end. Please try again later.")

def retreive_tender_dkeys_from_chain(tender_id: int, bidder_ids: List[int]) -> List[int]:
    """Calculates the checksums of the files and retrieves the decryption keys 
    for bids with tender id from the blockchain.

    Returns the list of bidder IDs if their corresponding checksums calculated 
    here doesn't match with the ones saved on blockchain.
    """
    try:
        w3, contract = connect_to_chain()
        checksums = []
        for bidder_id in bidder_ids:
            get_from_dstorage(f'{tender_id}-{bidder_id}.pdf')
            checksums.append(calculate_checksum(os.getenv('BID_DOCUMENTS_PATH') + f'{tender_id}-{bidder_id}.pdf'))
        tx_hash = contract.functions.retrieveDKeysForTender(tender_id, bidder_ids, checksums).transact()
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        decoded_logs = contract.events.TenderKeysRetrieved().process_receipt(tx_receipt)
        print(tender_id, bidder_ids, checksums)
        print(checksums)
        illegal_bidder_ids = []
        if decoded_logs:
            retreived_tender_id = decoded_logs[0]['args']['tenderId']
            print(retreived_tender_id)
            dkeys = decoded_logs[0]['args']['dKeys']
            print(dkeys)
            for i in range(len(bidder_ids)):
                if dkeys[i] != "":
                    try:
                        print("hi")
                        decrypt_file(f'{retreived_tender_id}-{bidder_ids[i]}.pdf', dkeys[i])
                        print("Gone")
                    except BaseException as e:
                        print(e, "ring")
                        illegal_bidder_ids.append(bidder_ids[i])
                else:
                    illegal_bidder_ids.append(bidder_ids[i])
        else:
            raise BaseException("No event logs found for BidderKeyRetrieved")
        return illegal_bidder_ids
    except Web3Exceptions.ContractLogicError as e:
        print(e.args[0].split(":")[1].strip())
        raise BaseException(e.args[0].split(":")[1].strip())
    except BaseException as e:
        print(e)
        raise BaseException("There is a problem at our end. Please try again later.")


def save_to_chain(input_path: str, tender_id: int, bidder_id: int) -> str:
    """Encrypts the file, saves it to the decentralized storage, calculates the checksum, 
    and saves the checksum to the blockchain.
    """
    file_name, dkey,  = encrypt_file(input_path, tender_id, bidder_id)
    file_path = os.getenv('BID_DOCUMENTS_PATH') + file_name
    save_to_dstorage(file_path, file_name)
    checksum = calculate_checksum(file_path)
    print(checksum)
    save_checksum_to_chain(tender_id, bidder_id, checksum)
    return 'Bid documents/' + file_name, dkey
