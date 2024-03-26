import os
import regex as re
from pypdf import PdfReader, PdfWriter
from cryptography.hazmat.backends import default_backend
import boto3
from dotenv import load_dotenv
from typing import List

def encrypt_file(input_file_path, tender_id, bid_id) -> List[str]:
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

def decrypt_file(encrypted_pdf_file_path, decryption_key) -> None:
    pdf_writer = PdfWriter()
    with open(encrypted_pdf_file_path, 'rb') as file:
        pdf_reader = PdfReader(file, password=decryption_key.hex())
        for page_num in range(len(pdf_reader.pages)):
            pdf_writer.add_page(pdf_reader.pages[page_num])
    with open(encrypted_pdf_file_path, 'wb') as file:
        pdf_writer.write(file)
    
def save_to_dstorage(file_path, file_name) -> None:
    load_dotenv()
    s3 = boto3.client('s3',
                    aws_access_key_id=os.getenv('jxhifggcl6c7j3v27e3h4ett67dq'),
                    aws_secret_access_key=os.getenv('jyk6vmunj4pk3ydjdq5dz4z4lleemm3ftq5zdk6zijknhhmkysytc'),
                    endpoint_url=os.getenv('https://gateway.storjshare.io'))
    bucket_name = 'tender-bucket'
    with open(file_path, 'rb') as file:
        s3.upload_fileobj(file, bucket_name, file_name)

def save_dkey_to_chain(decryption_key):
    pass
def retreive_from_chain(tender_id):
    pass

def save_to_chain(input_path, tender_id, bid_id, end_time):
    outputpath, dkey, file_name_on_dstorage = encrypt_file(input_path, tender_id, bid_id)
    save_to_dstorage(outputpath, file_name_on_dstorage)
    save_dkey_to_chain(dkey)
    return outputpath
