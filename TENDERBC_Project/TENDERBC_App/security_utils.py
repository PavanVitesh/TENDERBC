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
    load_dotenv()
    backend = default_backend()
    encryption_key = os.urandom(32)
    pdf_writer = PdfWriter()
    # print current working directory path
    print(os.getcwd())
    print(os.getenv('BID_DOCUMENTS_PATH'))
    pdf_file_path = fr'{os.getenv('BID_DOCUMENTS_PATH')}{input_file_path}'
    print(pdf_file_path)
    with open(pdf_file_path, 'rb') as file:
        pdf_reader = PdfReader(file)
        for page_num in range(len(pdf_reader.pages)):
            pdf_writer.add_page(pdf_reader.pages[page_num])
        pdf_writer.encrypt(user_password=encryption_key.hex(), algorithm='AES-256')
    file_name = re.search(r'[^/]+\.pdf', pdf_file_path).group(0)
    new_file_name =  str(tender_id) + '-' + str(bid_id) + '.pdf'
    encrypted_pdf_file_path = new_file_name
    with open(os.getenv('BID_DOCUMENTS_PATH') + encrypted_pdf_file_path, 'wb') as file:
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
    with open(os.getenv('BID_DOCUMENTS_PATH') + encrypted_pdf_file_path, 'rb') as file:
        pdf_reader = PdfReader(file, password=decryption_key)
        for page_num in range(len(pdf_reader.pages)):
            pdf_writer.add_page(pdf_reader.pages[page_num])
    with open(os.getenv('BID_DOCUMENTS_PATH') + encrypted_pdf_file_path, 'wb') as file:
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
    load_dotenv()
    s3 = connect_to_dstorage()
    bucket_name = 'tender-bucket'
    with open(os.getenv('BID_DOCUMENTS_PATH') + file_path, 'rb') as file:
        s3.upload_fileobj(file, bucket_name, file_name)

def get_from_dstorage(file_name: str) -> str:
    """
    Get a file from the decentralized storage.
    Args:
        file_name (str): The name of the file.
    Returns:
        str: The path to the file.
    """
    load_dotenv()
    s3 = connect_to_dstorage()
    bucket_name = 'tender-bucket'
    file_path = os.getenv('BID_DOCUMENTS_PATH') + file_name
    print(file_path)
    with open(file_path, 'wb') as file:
        s3.download_fileobj(bucket_name, file_name, file)
    print("safe")

def calculate_checksum(file_path: str) -> str:
    """
    Calculate the checksum of a file using SHA-256 algorithm.
    Args:
        file_path (str): The path to the file.
    Returns:
        str: The checksum of the file.
    """
    sha256 = hashlib.sha512()
    with open(os.getenv('BID_DOCUMENTS_PATH') + file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    print(sha256.hexdigest())
    return sha256.hexdigest()

def connect_to_chain() -> List[str]:
    """
    Connect to the Ethereum blockchain.
    Returns:
        List[str]: The Web3 object and the contract object.
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
        tx_hash = contract.functions.createTender(tender_id, int(start_time.timestamp()), int(end_time.timestamp())).transact()
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        decoded_logs = contract.events.TenderCreated().process_receipt(tx_receipt)
        if decoded_logs:
            retreived_tender_id = decoded_logs[0]['args']['tenderId']
            # created_time = decoded_logs[0]['args']['createdTime']
            # retreived_start_time = decoded_logs[0]['args']['startTime']
            # retreived_end_time = decoded_logs[0]['args']['endTime']
            print(retreived_tender_id)
            pass
        else:
            raise BaseException("No event logs found for TenderCreated")
    except Web3Exceptions.ContractLogicError as e:
        raise BaseException(e.args[0].split(":")[1].strip())
    except BaseException as e:
        raise e

def save_checksum_to_chain(tender_id: int, bidder_id: int, checksum: str) -> None:
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
        tx_hash = contract.functions.placeBid(tender_id, bidder_id, checksum).transact()
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        decoded_logs = contract.events.BidAdded().process_receipt(tx_receipt)
        if decoded_logs:
            # retreived_tender_id = decoded_logs[0]['args']['tenderId']
            # retreived_bidder_id = decoded_logs[0]['args']['bidderId']
            pass
        else:
            raise BaseException("No event logs found for BidAdded")
    except Web3Exceptions.ContractLogicError as e:
        raise BaseException(e.args[0].split(":")[1].strip())
    except BaseException as e:
        raise e

def retreive_bidder_dkey_from_chain(tender_id: int, bidder_id: int, checksum: str) -> int:
    """
    Retrieve the decryption key from the blockchain.
    Args:
        tender_id (int): The ID of the tender.
        bidder_id (int): The ID of the bidder.
        checksum (str): The checksum of the file.
    Returns:
        int: The bidder ID if the corresponding checksum is not correct.
    """
    try:
        w3, contract = connect_to_chain()
        tx_hash = contract.functions.retrieveDKey(tender_id, bidder_id, checksum).transact()
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        decoded_logs = contract.events.BidderKeyRetrieved().process_receipt(tx_receipt)
        illegal_bidder_id = None
        if decoded_logs:
            retreived_tender_id = decoded_logs[0]['args']['tenderId']
            retreived_bidder_id = decoded_logs[0]['args']['bidderId']
            # retreived_checksum = decoded_logs[0]['args']['checksum']
            dkey = decoded_logs[0]['args']['dKey']
            if dkey:
                get_from_dstorage(f'{retreived_tender_id}-{retreived_bidder_id}.pdf')
                decrypt_file(f'{retreived_tender_id}-{retreived_bidder_id}.pdf', dkey)
            else:
                illegal_bidder_id = retreived_bidder_id
        else:
            raise BaseException("No event logs found for BidderKeyRetrieved")
        return illegal_bidder_id
    except Web3Exceptions.ContractLogicError as e:
        print(e)
    except BaseException as e:
        print(e)

def save_dkey_to_chain(tender_id: int, bidder_id: int, dkey: str) -> None:
    try:
        w3, contract = connect_to_chain()
        tx_hash = contract.functions.saveBidDKey(tender_id, bidder_id, dkey).transact()
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        decoded_logs = contract.events.DKeyUploaded().process_receipt(tx_receipt)
        if decoded_logs:
            # retreived_tender_id = decoded_logs[0]['args']['tenderId']
            # retreived_bidder_id = decoded_logs[0]['args']['bidderId']
            # retreived_dkey = decoded_logs[0]['args']['dKey']
            pass
        else:
            raise BaseException("No event logs found for DKeyUploaded")
    except Web3Exceptions.ContractLogicError as e:
        raise BaseException(e.args[0].split(":")[1].strip())
    except BaseException as e:
        raise e

def check_if_dkey_present(tender_id: int, bidder_id: int) -> bool:
    try:
        print("Pal")
        w3, contract = connect_to_chain()
        tx_hash = contract.functions.dKeyForBidIsPresent(tender_id, bidder_id).transact()
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        decoded_logs = contract.events.DKeyChecked().process_receipt(tx_receipt)
        if decoded_logs:
            return decoded_logs[0]['args']['dKeyPresent']
        else:
            raise BaseException("No event logs found for DKeyChecked")
    except Web3Exceptions.ContractLogicError as e:
        print(e)
    except BaseException as e:
        print(e)

def retreive_tender_dkeys_from_chain(tender_id: int, bidder_ids: List[int]) -> List[int]:
    """
    Retrieve the decryption keys from the blockchain.
    Args:
        tender_id (int): The ID of the tender.
        bidder_ids (List[int]): The list of bidder IDs.
        checksums (List[str]): The list of checksums.
    Returns:
        List[str]: The list of bidder IDs if their corresponding checksums are not correct.
    """
    try:
        print("Pal")
        w3, contract = connect_to_chain()
        checksums = [calculate_checksum(f'{tender_id}-{bidder_id}.pdf') for bidder_id in bidder_ids]
        print(tender_id, type(tender_id))
        print(bidder_ids)
        print(checksums)
        tx_hash = contract.functions.retrieveDKeysForTender(tender_id, bidder_ids, checksums).transact()
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        decoded_logs = contract.events.TenderKeysRetrieved().process_receipt(tx_receipt)
        illegal_bidder_ids = []
        if decoded_logs:
            retreived_tender_id = decoded_logs[0]['args']['tenderId']
            # retreived_checksums = decoded_logs[0]['args']['checksums']
            dkeys = decoded_logs[0]['args']['dKeys']
            print(dkeys)
            for i in range(len(bidder_ids)):
                if dkeys[i] != "":
                    get_from_dstorage(f'{retreived_tender_id}-{bidder_ids[i]}.pdf')
                    try:
                        decrypt_file(f'{retreived_tender_id}-{bidder_ids[i]}.pdf', dkeys[i])
                    except:
                        illegal_bidder_ids.append(bidder_ids[i])
                else:
                    illegal_bidder_ids.append(bidder_ids[i])
        else:
            raise BaseException("No event logs found for BidderKeyRetrieved")
        return illegal_bidder_ids
    except Web3Exceptions.ContractLogicError as e:
        print(e)
    except BaseException as e:
        print(e)
    
def save_to_chain(input_path: str, tender_id: int, bidder_id: int) -> str:
    """
    Save the encrypted file to the blockchain.
    Args:
        input_path (str): The path to the file.
        tender_id (int): The ID of the tender.
        bidder_id (int): The ID of the bidder.
    Returns:
        str: The path to the encrypted file.
    """
    outputpath, dkey, file_name_on_dstorage = encrypt_file(input_path, tender_id, bidder_id)
    save_to_dstorage(outputpath, file_name_on_dstorage)
    checksum = calculate_checksum(file_name_on_dstorage)
    save_checksum_to_chain(tender_id, bidder_id, checksum)
    return outputpath, dkey
