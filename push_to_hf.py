import os
from huggingface_hub import login, upload_folder

def main():
    print("Welcome to the Hugging Face Upload Hook!")
    
    # Check if we already have the token in the environment to avoid blocking if possible
    hf_token = os.environ.get("HF_TOKEN")
    
    if hf_token:
        print("HF_TOKEN detected. Logging in securely...")
        login(token=hf_token)
    else:
        print("No HF_TOKEN found in environment variables.")
        print("Please securely provide your Hugging Face Access Token when prompted:")
        login()
        
    repo_target = "openenv-customer-support/openenv-customer-support"
    print(f"\nPushing current workspace files to Space -> {repo_target}")
    
    # Push the Space files
    upload_folder(
        folder_path=".", 
        repo_id=repo_target, 
        repo_type="space",
        ignore_patterns=[
            "frontend/node_modules/**", 
            "frontend/.next/**", 
            "__pycache__/**", 
            ".git/**", 
            ".venv/**", 
            "venv/**", 
            "env/**", 
            ".DS_Store"
        ] # Keeps the upload lightweight preventing the 504 Timeout
    )
    
    print("\n✅ Successfully uploaded OpenEnv Customer Support to Hugging Face!")

if __name__ == "__main__":
    main()
