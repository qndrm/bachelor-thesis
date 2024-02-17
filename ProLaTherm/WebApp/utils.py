import hashlib
import os
import re
from .prolatherm import *
import numpy as np
import pandas as pd
import random
from .config import SEQUENCES_PER_TASK
import time


def evaluate_mock(filepath):
    
    '''
    NOT THE REAL EVALUATION
    '''
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"No file found at {filepath}")

    with open(filepath, 'r') as f:
        user_input = f.read()
        valid_fasta, rejected_fasta, len_valid, len_invalid = validate_file(user_input)  # maybe use rejected_fasta later

    if not valid_fasta:
        raise ValueError(f"No valid protein sequences found in file at {filepath}")

    sequences, protein_ids = read_fasta(filepath)
    
    # Mock predictions

    scores, preds = mock_pred(len(sequences))
    results = pd.DataFrame(columns=["IDs", "aa-seq", "prediction_binary", "prediction", "score"])
    results["IDs"] = protein_ids
    results["prediction_binary"] = preds
    results["score"] = scores
    results["prediction"] = results["prediction_binary"].apply(lambda x: "thermophilic" if x == 1 else "non-thermophilic")
    results["aa-seq"] = sequences
    return results

def evaluate(filepath):
    
    '''
    Validate and evaluate protein sequences from a given file.
    This function validates a given fasta file by calling validate_file() and then let's ProLaTherm evaluate the valid sequences
    
    Args:
        filepath (str): The path to the file containing the protein sequences.

    Returns:
        list: A list of tuples, where each tuple contains a valid protein sequence and its score.

    Raises:
        FileNotFoundError: If the file specified by filepath does not exist.
        ValueError: If the file specified by filepath does not contain any valid protein sequences.
    '''
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"No file found at {filepath}")

    with open(filepath, 'r') as f:
        user_input = f.read()
        valid_fasta, rejected_fasta, len_valid, len_invalid = validate_file(user_input)  # maybe use rejected_fasta later

    if not valid_fasta:
        raise ValueError(f"No valid protein sequences found in file at {filepath}")

    sequences, protein_ids = read_fasta(filepath)
    

    pred_model = ProLaTherm(no_gpu=True)  

    start = 0
    step_size = SEQUENCES_PER_TASK
    num_samples = len(sequences)
    preds = []
    scores = []

    for i in range(0, num_samples, step_size):
        end = i + step_size if i + step_size < num_samples else num_samples
        seqs = sequences[start:end]
        if start + 1 == end:
            seqs = [seqs]
        pred, score = pred_model.predict(seqs)
        preds.extend(pred.flatten().tolist())
        scores.extend(score.flatten().tolist())
        start = end
            
        results = pd.DataFrame(columns=["IDs", "aa-seq", "prediction_binary", "prediction", "score"])
        results["IDs"] = protein_ids
        results["prediction_binary"] = preds
        results["score"] = scores
        results["prediction"] = results["prediction_binary"].apply(lambda x: "thermophilic" if x == 1 else "non-thermophilic")
        results["aa-seq"] = sequences
        return results


def read_fasta(filepath):
    sequences = []
    protein_ids = []
    with (open(filepath,'r') as f):
        user_input = f.read()
        
    fasta_list = re.split("(?=>)", user_input)
    fasta_list.pop(0)
    for seq in fasta_list:
        parts = seq.rsplit("|", 1)
        protein_ids.append(parts[0]+'|')
        sequences.append(parts[1].strip())

    return np.array(sequences), np.array(protein_ids)





def user_input_to_file(user_input):
    """
    Convert user input to a file.

    This function encodes the user input to a SHA-3 hash and then creates a file with the hash as the name. 
    The user input is written to this file.

    Args:
        user_input (str): The user input to write to a file.

    Returns:
        str: The filepath of the created file.
    """
    # Hash the user input using SHA-3
    hash_input = hashlib.sha3_256(str.encode(user_input)).hexdigest()

    # Create the filepath for the new file
    base_dir = os.getcwd()
    request_dir = os.path.join(base_dir,"WebApp", "evalRequests")
    filepath = os.path.join(request_dir, hash_input)
    valid_fasta, rejected_fasta, len_valid , len_rejected = validate_file(user_input)

    # Write the user input to the file
    with open(filepath, "w") as file:
        file.write('\n'.join(valid_fasta))
        
    return filepath , len_valid

def validate_file(user_input):
    """
    Validate protein sequences in a file.

    This function reads a file with protein sequences in FASTA format and validates each sequence.
    Valid and invalid sequences are stored separately.

    Args:
        filepath (str): The path to the file containing the protein sequences.

    Returns:
        tuple: A tuple of two lists. The first list contains valid sequences and the second contains
               invalid sequences.

    Raises:
        FileNotFoundError: If the file specified by filepath does not exist.
    """
    #if not os.path.isfile(filepath):
    #    raise FileNotFoundError(f"No file found at {filepath}")

    valid_fasta = []
    rejected_fasta = []
    to_validate = re.split("(?=>)", user_input)
    for fasta in to_validate:
        if fasta != '':
            fasta, is_valid = validate_fasta(fasta)
            (valid_fasta if is_valid else rejected_fasta).append(fasta)
    return valid_fasta, rejected_fasta, len(valid_fasta) , len(rejected_fasta)


def validate_fasta(fasta):
    """
    Validate a protein sequence in FASTA format.

    This function checks if a given sequence in FASTA format is valid. 
    A valid sequence is prefixed with a '>' character, has identifiers, and contains only standard amino acids.

    Args:
        fasta (str): The protein sequence in FASTA format.

    Returns:
        tuple: A tuple of the protein sequence and a boolean indicating its validity.
    """
    if not fasta:
        return fasta, False

    fasta = fasta.strip()
    if not fasta.startswith('>'):
        fasta = '>' + fasta

    parts = fasta.rsplit("|", 1)
    if len(parts) < 2:

        return fasta, False

    sequence = parts[1].replace('\n', '').strip().upper()
    parts[1] = sequence

    if not verify_alphabet(sequence):

        return '|'.join(parts), False

    return '|'.join(parts), True


def verify_alphabet(sequence):
    """
    Verify that a protein sequence contains only standard amino acids.

    Args:
        sequence (str): The protein sequence to verify.

    Returns:
        bool: True if the sequence contains only standard amino acids, False otherwise.
    """
    standard_amino_acids = set("ACDEFGHIKLMNPQRSTVWY")
    return all(letter in standard_amino_acids for letter in sequence)


def get_script():
    script=b"""
import argparse
import pathlib
import requests
import time

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="ProLaTherm-API")
    parser.add_argument('-e', type=str, help='Provide your email address to get notified')
    parser.add_argument('-f', type=pathlib.Path, help='Provide a file path')
    parser.add_argument('-csv', action='store_true', help='Set to True to download a CSV of your results')
    args = parser.parse_args()

    # Define the URL of the ProLaTherm API
    url = "http://10.154.6.31:8000"

    # Convert the file path to a string that can be used in the requests call
    filename = args.f.as_posix()

    # Read the file data
    with open(filename, 'rb') as f:
        file_data = f.read()

    # Prepare the data payload for the POST request
    data = {'email': args.e} if args.e else {}

    # Prepare the files payload for the POST request
    files = {'file': (filename, file_data)}

    # Make the POST request to submit the file for processing
    request_url = f"{url}/api/user-request/"
    response = requests.post(request_url, data=data, files=files)

    # Check the response status code to ensure the request was successful
    if response.status_code != 200:
        print("Something went wrong")
        exit()

    # Extract the unique hash from the response
    hash = response.json()['user_request']['hash']

    # Define the URL to check the status of the request
    status_url = f"{url}/api/status/{hash}/"

    # Poll the status URL to check the progress of the request
    while True:
        status_response = requests.get(status_url)
        status = status_response.json()['status']
        progress = float(status_response.json()['progress'])
        print(f'Status: {status} | Progress: {progress:.2f}%', end='\\r', flush=True)
        if status == 'ready':
            break
        time.sleep(3)
    print(f'Status: {status} | Progress: {progress:.2f}%                       ')

    # If the CSV download option was specified, download the CSV file
    if args.csv:
        csv_url = f"{url}/api/csv/{hash}/"
        csv_response = requests.get(csv_url)

        # Check the Content-Type header to ensure we received a CSV file
        if csv_response.headers.get('Content-Type') == 'text/csv':
            # Write the CSV data to a file
            with open(f'{hash}_ProLaTherm.csv', 'wb') as csv_file:
                csv_file.write(csv_response.content)
        else:
            print('Error downloading CSV file')

if __name__ == "__main__":
    main()

    """
    return script

def mock_pred(seqs):
    preds = []
    scores = []
    for i in range(seqs):
        time.sleep(0.5)
        score = random.random()
        if score > 0.5 : pred = True 
        else : pred = False
        scores.append(score)
        preds.append(pred)
    return scores,preds