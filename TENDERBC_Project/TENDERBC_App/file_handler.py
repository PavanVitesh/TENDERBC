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
    """
    Encrypt a PDF file using a randomly generated encryption key.
    Args:
        input_file_path (str): The path to the PDF file.
        tender_id (str): The ID of the tender.
        bid_id (str): The ID of the bidder.
    Returns:
        List[str]: The path to the encrypted PDF file, the encryption key, and the new file name.
    """
    backend = default_backend()
    encryption_key = os.urandom(32)
    pdf_writer = PdfWriter()
    pdf_file_path = fr'{input_file_path}'
    with open(pdf_file_path, 'rb') as file:
        pdf_reader = PdfReader(file)
        for page_num in range(len(pdf_reader.pages)):
            pdf_writer.add_page(pdf_reader.pages[page_num])
        pdf_writer.encrypt(user_password=encryption_key.hex(), algorithm='AES-256')
    file_name = re.search(pattern=r'[^\\]+\.pdf', string=input_file_path).group(0)
    new_file_name =  str(tender_id) + '-' + str(bid_id) + '.pdf'
    encrypted_pdf_file_path = pdf_file_path[:-len(file_name)] + new_file_name
    with open(encrypted_pdf_file_path, 'wb') as file:
        pdf_writer.write(file)
    return encrypted_pdf_file_path, encryption_key.hex(), new_file_name

def decrypt_file(encrypted_pdf_file_path: str, decryption_key: str) -> None:
    """
    Decrypt a PDF file using a decryption key.
    Args:
        encrypted_pdf_file_path (str): The path to the encrypted PDF file.
        decryption_key (str): The decryption key.
    Returns:
        None
    """
    pdf_writer = PdfWriter()
    with open(encrypted_pdf_file_path, 'rb') as file:
        pdf_reader = PdfReader(file, password=decryption_key.hex())
        for page_num in range(len(pdf_reader.pages)):
            pdf_writer.add_page(pdf_reader.pages[page_num])
    with open(encrypted_pdf_file_path, 'wb') as file:
        pdf_writer.write(file)
    
def connect_to_dstorage() -> boto3.client:
    """
    Connect to the decentralized storage.
    Returns:
        boto3.client: The S3 client.
    """
    load_dotenv()
    s3 = boto3.client('s3',
                    aws_access_key_id=os.getenv('STORJ_ACCESS_KEY'),
                    aws_secret_access_key=os.getenv('STORJ_SECRET_KEY'),
                    endpoint_url=os.getenv('STORJ_ENDPOINT_URL'))
    return s3

def save_to_dstorage(file_path: str, file_name: str) -> None:
    """
    Save a file to the decentralized storage.
    Args:
        file_path (str): The path to the file.
        file_name (str): The name of the file.
    Returns:
        None
    """
    s3 = connect_to_dstorage()
    bucket_name = 'tender-bucket'
    with open(file_path, 'rb') as file:
        s3.upload_fileobj(file, bucket_name, file_name)

def get_from_dstorage(file_name: str) -> str:
    """
    Get a file from the decentralized storage.
    Args:
        file_name (str): The name of the file.
    Returns:
        str: The path to the file.
    """
    s3 = connect_to_dstorage()
    bucket_name = 'tender-bucket'
    file_path = os.getenv('BID_DOCUMENTS_PATH')
    with open(file_path, 'wb') as file:
        s3.download_fileobj(bucket_name, file_path + file_name, file)

def calculate_checksum(file_path: str):
    """
    Calculate the checksum of a file using SHA-256 algorithm.
    Args:
        file_path (str): The path to the file.
    Returns:
        str: The checksum of the file.
    """
    sha256 = hashlib.sha512()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def connect_to_chain() -> List[str]:
    """
    Connect to the Ethereum blockchain.
    Returns:
        List[str]: The Web3 object and the contract object.
    """
    try:
        w3 = Web3(Web3.HTTPProvider(os.getenv('GETH_NODE_ENDPOINT_URL')))
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        contract_abi = None
        with open(os.getenv('PATH_TO_CONTRACT_ABI'), 'r') as f:
            contract_abi = json.load(f)
        contract_address = os.getenv('CONTRACT_ADDRESS')
        contract = w3.eth.contract(contract_address, abi=contract_abi)
        w3.eth.default_account = w3.eth.accounts[1]
        return w3, contract
    except Exception as e:
        raise e

def add_tender_data_to_chain(tender_id: int, start_time:datetime, end_time: datetime) -> None:
    """
    Add tender data to the blockchain.
    Args:
        tender_id (int): The ID of the tender.
        start_time (datetime): The start time of the tender.
        end_time (datetime): The end time of the tender.
    Returns:
        None
    """
    try:
        w3, contract = connect_to_chain()
        tx_hash = contract.functions.createTender(tender_id, start_time.timestamp, end_time.timestamp).transact()
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        decoded_logs = contract.events.TenderCreated().process_receipt(tx_receipt)
        if decoded_logs:
            retreived_tender_id = decoded_logs[0]['args']['tenderId']
            created_time = decoded_logs[0]['args']['createdTime']
            retreived_start_time = decoded_logs[0]['args']['startTime']
            retreived_end_time = decoded_logs[0]['args']['endTime']
            print("Tender ID:", retreived_tender_id)
            print("Created Time:", created_time)
            print("Start Time:", retreived_start_time)
            print("End Time:", retreived_end_time)
        else:
            print("No event logs found for TenderCreated")
    except Web3Exceptions.ContractLogicError as e:
        print(e)

def save_dkey_checksum_to_chain(tender_id: int, bidder_id: int, dkey: str, checksum: str) -> None:
    """
    Save the decryption key and checksum to the blockchain.
    Args:
        tender_id (int): The ID of the tender.
        bidder_id (int): The ID of the bidder.
        decryption_key (str): The decryption key.
        checksum (str): The checksum of the file.
    Returns:
        None
    """
    try: 
        w3, contract = connect_to_chain()
        tx_hash = contract.functions.placeBid(tender_id, bidder_id, dkey, checksum).transact()
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        decoded_logs = contract.events.BidAdded().process_receipt(tx_receipt)
        if decoded_logs:
            retreived_tender_id = decoded_logs[0]['args']['tenderId']
            retreived_bidder_id = decoded_logs[0]['args']['bidderId']
            print("Tender ID:", retreived_tender_id)
            print("Bid ID:", retreived_bidder_id)
        else:
            print("No event logs found for BidAdded")
    except Web3Exceptions.ContractLogicError as e:
        print(e)
    except Exception as e:
        print(e)

def retreive_bidder_dkey_from_chain(tender_id: int, bidder_id: int, checksum: str) -> str:
    try:
        w3, contract = connect_to_chain()
        tx_hash = contract.functions.retrieveDKey(tender_id, bidder_id, checksum).transact()
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        decoded_logs = contract.events.BidderKeyRetrieved().process_receipt(tx_receipt)
        if decoded_logs:
            retreived_tender_id = decoded_logs[0]['args']['tenderId']
            retreived_bidder_id = decoded_logs[0]['args']['bidderId']
            retreived_checksum = decoded_logs[0]['args']['checksum']
            dkey = decoded_logs[0]['args']['dKey']
            print("Tender ID:", retreived_tender_id)
            print("Bidder ID:", retreived_bidder_id)
            print("Decryption Key:", dkey)
            print("Original Checksum:", retreived_checksum)
            print("Current Checksum:", checksum)
            if dkey:
                get_from_dstorage(f'{retreived_tender_id}-{retreived_bidder_id}.pdf')
                decrypt_file(f'{retreived_tender_id}-{retreived_bidder_id}.pdf', dkey)
        else:
            print("No event logs found for BidderKeyRetrieved")
        return dkey
    except Web3Exceptions.ContractLogicError as e:
        print(e)
    except Exception as e:
        print(e)

def retreive_tender_dkeys_from_chain(tender_id: int, bidder_ids: List[int], checksums: List[str]) -> List[str]:
    try:
        w3, contract = connect_to_chain()
        tx_hash = contract.functions.retrieveDKeysForTender(2, [1, 2], ["ca", "ba"]).transact()
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        decoded_logs = contract.events.TenderKeysRetrieved().process_receipt(tx_receipt)
        illegal_bidder_ids = []
        if decoded_logs:
            retreived_tender_id = decoded_logs[0]['args']['tenderId']
            retreived_checksums = decoded_logs[0]['args']['checksums']
            dkeys = decoded_logs[0]['args']['dKeys']
            print("Tender ID:", retreived_tender_id)
            print("Decryption Keys:", dkeys)
            print("Original Checksums:", retreived_tender_id)
            print("Current Checksums:", checksums)
            for i in range(len(bidder_ids)):
                if dkeys[i]:
                    get_from_dstorage(f'{retreived_tender_id}-{bidder_ids[i]}.pdf')
                    decrypt_file(f'{retreived_tender_id}-{bidder_ids[i]}.pdf', dkeys[i])
                else:
                    illegal_bidder_ids.append(bidder_ids[i])
        else:
            print("No event logs found for BidderKeyRetrieved")
        return illegal_bidder_ids
    except Web3Exceptions.ContractLogicError as e:
        print(e)
    except Exception as e:
        print(e)
    
def save_to_chain(input_path, tender_id, bidder_id):
    outputpath, dkey, file_name_on_dstorage = encrypt_file(input_path, tender_id, bidder_id)
    save_to_dstorage(outputpath, file_name_on_dstorage)
    checksum = calculate_checksum(outputpath)
    save_dkey_checksum_to_chain(tender_id, bidder_id, dkey, checksum)
    return outputpath
