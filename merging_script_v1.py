import subprocess
import os
import pandas as pd

def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running command: {command}")
        print(result.stderr)
    else:
        print(result.stdout)

# Get the filenames from the user
example_file = input("Enter the name of the 23andMe text file (e.g., example.txt): ")
dataset_name = input("Enter the name of your dataset (e.g., dataset): ")

# Step 1: Convert 23andMe text file to plink.exe binary files
run_command(f"plink.exe --23file {example_file} --out mergesample")

# Step 2: Write SNP list from the original dataset
run_command(f"plink.exe --bfile {dataset_name} --write-snplist")

# Step 3: Extract SNPs from the 23andMe dataset using the SNP list and create new binary files
run_command("plink.exe --bfile mergesample --extract plink.snplist --make-bed --out B1")

# Step 4: Manually update B1.fam file (replace -9 with 1 and update sample ID)
# This part requires manual intervention as it involves editing a file
# Alternatively, this can be automated using pandas for file manipulation:

# Load B1.fam file
fam_df = pd.read_csv("B1.fam", delim_whitespace=True, header=None)
# Replace -9 with 1 in the sixth column
fam_df[5] = 1
# Update sample ID in the second column
fam_df[1] = "MyData"
# Save the updated file
fam_df.to_csv("B1.fam", sep=' ', header=False, index=False)

# Step 5: Merge the datasets
run_command(f"plink.exe --bfile {dataset_name} --bmerge B1.bed B1.bim B1.fam --indiv-sort 0 --allow-no-sex --make-bed --out newfile")

# Step 6: Handle merge errors if they occur
# If merge fails, run these commands in sequence until successful
merge_commands = [
    "plink.exe --bfile B1 --flip newfile-merge.missnp --make-bed --out B1_flip",
    f"plink.exe --bfile {dataset_name} --bmerge B1_flip.bed B1_flip.bim B1_flip.fam --indiv-sort 0 --allow-no-sex --make-bed --out newfile",
    "plink.exe --bfile B1_flip --exclude newfile-merge.missnp --make-bed --allow-no-sex --out B1_tmp",
    f"plink.exe --bfile {dataset_name} --bmerge B1_tmp.bed B1_tmp.bim B1_tmp.fam --indiv-sort 0 --allow-no-sex --make-bed --out newfile"
]

for command in merge_commands:
    run_command(command)
    if all([os.path.exists(f"newfile.{ext}") for ext in ["fam", "bed", "bim"]]):
        break

# Step 7: Convert files to EIGENSTRAT format
# Create convertf_param.par file
with open("convertf_param.par", "w") as f:
    f.write("""genotypename: newfile.bed
snpname: newfile.bim
indivname: newfile.fam
outputformat: EIGENSTRAT
genotypeoutname: newfile.geno
snpoutname: newfile.snp
indivoutname: newfile.ind
familynames: NO
""")

# Run convertf command
run_command("convertf -p convertf_param.par")

print("Process completed.")
