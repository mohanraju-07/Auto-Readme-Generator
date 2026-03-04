import subprocess 
import os 
from groq import Groq
import time 
import shutil
import stat
from collections import defaultdict

pat=os.getenv("GITHUB_PAT")
print(pat)
repo_url = f"https://{pat}@github.com/mohanraju-07/basicWeb"
repo_name = repo_url.split("/")[-1].replace(".git","")

if not os.path.exists(repo_name):
    subprocess.run(["git", "clone", repo_url])
else:
    print("Repo already exists, using existing folder")

os.chdir(repo_name)
print("now inside repo folder: ", os.getcwd())

ignore_folders = {"venv", ".git", "__pycache__", "node_modules"}

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# group files by folder
folder_files = defaultdict(list)

for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in ignore_folders]

    for file in files:
        if file.endswith((".py", ".cs", ".js", ".html", ".css", ".ipynb", ".c")):
            file_path = os.path.join(root, file)
            folder_files[root].append(file_path)  # group by folder

print(f"Found {len(folder_files)} folders with code files!")

all_folder_summaries = ""

# generate one readme per folder
for folder, files in folder_files.items():
    print(f"\nGenerating README for folder: {folder} ({len(files)} files)")

    # combine all files in this folder
    combined_code = ""
    for file_path in files:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            combined_code += f"\n\n===== {os.path.basename(file_path)} =====\n"
            combined_code += f.read()

    combined_code = combined_code[:6000]  # limit per folder

    prompt = f"""
    You are a software documentation expert.
    Generate a detailed README.md for this folder: {folder}
    
    This folder contains these files: {[os.path.basename(f) for f in files]}

    Include:
    # Folder Overview
    # File-by-File Explanation
    # Functions/Classes explained
    # Dependencies used

    Code:
    {combined_code}
    """

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a software documentation expert."},
            {"role": "user", "content": prompt}
        ]
    )

    folder_readme = response.choices[0].message.content

    # save readme inside that folder
    readme_path = os.path.join(folder, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(folder_readme)

    print(f"README.md saved in {folder}")
    time.sleep(1)

    all_folder_summaries += f"\n\n===== FOLDER: {folder} =====\n{folder_readme[:500]}"


# generate overall readme
print("\nGenerating overall README.md...")

overall_prompt = f"""
You are a software documentation expert.
Generate an overall README.md for the GitHub project: {repo_name}

Based on these folder summaries:
{all_folder_summaries[:8000]}

Include:
# Project Overview
# Folder Structure & Explanation
# Features
# Technologies Used
# How to Run the Project
"""

response = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[
        {"role": "system", "content": "You are a software documentation expert."},
        {"role": "user", "content": overall_prompt}
    ]
)

overall_readme = response.choices[0].message.content

with open("README.md", "w", encoding="utf-8") as f:
    f.write(overall_readme)

print("Overall README.md generated successfully!")

# push to github
subprocess.run(["git", "status"])
subprocess.run(["git", "add", "."])
subprocess.run(["git", "status"])
result = subprocess.run(["git", "commit", "-m", "Add folder-wise README files"], capture_output=True, text=True)
print("Commit output:", result.stdout)
result2 = subprocess.run(["git", "push"], capture_output=True, text=True)
print("Push output:", result2.stdout)
print("Push error:", result2.stderr)
print("Changes pushed to GitHub!")

# delete cloned folder
def force_delete(func, path, exc_info):
    os.chmod(path, stat.S_IWRITE)
    func(path)

os.chdir("..")
shutil.rmtree(repo_name, onerror=force_delete)
print(f"{repo_name} folder deleted successfully!")