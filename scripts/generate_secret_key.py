#!/usr/bin/env python3
"""
Generate Secret Key Script for Doztra Auth Service

This script generates a secure random secret key for the Doztra Auth Service.
It can be used to generate a new secret key for the .env file.

Usage:
    python generate_secret_key.py [--length LENGTH] [--update-env]

Example:
    python generate_secret_key.py --length 64 --update-env
"""

import argparse
import os
import secrets
import sys


def generate_secret_key(length: int = 32) -> str:
    """
    Generate a secure random secret key.

    Args:
        length: The length of the secret key in bytes

    Returns:
        A URL-safe base64-encoded secret key
    """
    return secrets.token_urlsafe(length)


def update_env_file(secret_key: str, env_file: str = '.env') -> bool:
    """
    Update the SECRET_KEY value in the .env file.

    Args:
        secret_key: The new secret key
        env_file: The path to the .env file

    Returns:
        True if the file was updated successfully, False otherwise
    """
    if not os.path.exists(env_file):
        print(f"Error: {env_file} file not found.")
        return False

    with open(env_file, 'r') as f:
        lines = f.readlines()

    with open(env_file, 'w') as f:
        secret_key_found = False
        for line in lines:
            if line.startswith('SECRET_KEY='):
                f.write(f'SECRET_KEY={secret_key}\n')
                secret_key_found = True
            else:
                f.write(line)

        if not secret_key_found:
            f.write(f'\nSECRET_KEY={secret_key}\n')

    return True


def main() -> int:
    """
    Main function.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(description="Generate a secure random secret key")
    parser.add_argument("--length", type=int, default=32, help="Length of the secret key in bytes")
    parser.add_argument("--update-env", action="store_true", help="Update the .env file with the new secret key")
    parser.add_argument("--env-file", default=".env", help="Path to the .env file")
    
    args = parser.parse_args()
    
    # Generate secret key
    secret_key = generate_secret_key(args.length)
    
    # Print the secret key
    print(f"Generated secret key: {secret_key}")
    
    # Update .env file if requested
    if args.update_env:
        if update_env_file(secret_key, args.env_file):
            print(f"Updated {args.env_file} with the new secret key.")
        else:
            print(f"Failed to update {args.env_file}.")
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
