#Kindly note:
#If you are using conda to create virtual environment then do as below:

# #!/bin/bash

# # Get the path of the script
# script_path=$(realpath $0)
# script_dir=$(dirname $script_path)

# # Go to the directory
# cd $script_dir

# echo "Tranform service is running to transform files stored in S3, current directory: $(pwd)"

# # Activate conda environment
# source /home/developer/miniconda3/etc/profile.d/conda.sh
# conda activate omoto_env

# # Run the service
# python -m transform.main

#Kindly note:
#If you are using venv to create virtual environment then do as below:

# Get the path of the script
script_path=$(realpath $0)
script_dir=$(dirname $script_path)

# Go to the directory
cd $script_dir

echo "Transform service is running to transform files stored in s3, current directory: $(pwd)"

# Activate the virtual environment
source /home/zd/Documents/Omoto-plm/smtp-file-process-master/omoto_env/bin/activate

# Run the service
python3 -m transform.main