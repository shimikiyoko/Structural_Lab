import os
import glob
import json
import time
import logging
import signal
import subprocess

# Set up logging
logging.basicConfig(filename='unidock_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger()

# Add a file handler to log error messages
error_handler = logging.FileHandler('error.log')
error_handler.setLevel(logging.ERROR)
logger.addHandler(error_handler)

# Load the config.json file
with open('config.json') as f:
    config = json.load(f)

# Get the receptor file and result directory from the config
receptor_file = config['receptor']
result_dir = config['dir']

# Get the ligand files
ligand_dir = '/home/sherlock/JRF/unidock/trial'
ligand_files = glob.glob(os.path.join(ligand_dir, '*.pdbqt'))

# Start timing
start_time = time.time()

# Define a signal handler to catch segmentation faults
def sigsegv_handler(signum, frame):
    logger.error('Caught segmentation fault! Skipping ligand...')
    raise Exception('Segmentation fault')

signal.signal(signal.SIGSEGV, sigsegv_handler)

# Run Uni-Dock for each ligand
skipped_ligands = []
for ligand_file in ligand_files:
    ligand_name = os.path.basename(ligand_file)
    result_file = os.path.join(result_dir, ligand_name)
    cmd = [
        'unidock',
        '--receptor', receptor_file,
        '--gpu_batch', ligand_file,
        '--search_mode', config["search_mode"],
        '--scoring', config["scoring"],
        '--center_x', str(config["center_x"]),
        '--center_y', str(config["center_y"]),
        '--center_z', str(config["center_z"]),
        '--size_x', str(config["size_x"]),
        '--size_y', str(config["size_y"]),
        '--size_z', str(config["size_z"]),
        '--num_modes', str(config["num_modes"]),
        '--dir', result_dir
    ]
    try:
        # Run Uni-Dock command
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Print command output to the console
        print(result.stdout)
        
        if result.returncode == 0:
            logger.info(f'Processed ligand: {ligand_name}')
        else:
            logger.error(f'Error in file {ligand_file}: {result.stderr}')
            logger.info(f'Skipping ligand: {ligand_name}')
            skipped_ligands.append(ligand_file)
    except Exception as e:
        logger.error(f'Unexpected error in file {ligand_file}: {str(e)}')
        logger.info(f'Skipping ligand: {ligand_name}')
        skipped_ligands.append(ligand_file)

# End timing
end_time = time.time()
elapsed_time = end_time - start_time

# Print the elapsed time
logger.info(f'Elapsed time: {elapsed_time:.2f} seconds')

# If there are skipped ligands, remake the ligand list file
if skipped_ligands:
    logger.info(f'Remaking ligand list file with {len(ligand_files) - len(skipped_ligands)} ligands')
    with open('ligand_list.txt', 'w') as f:
        for ligand_file in ligand_files:
            if ligand_file not in skipped_ligands:
                f.write(ligand_file + '\n')

