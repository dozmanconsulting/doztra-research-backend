#!/bin/bash

# Simple script to fix the PDF dependency issue
# This script will add PyPDF2 to requirements.txt and install it

echo "=== FIXING PDF DEPENDENCY ISSUE ==="

# Check if PyPDF2 is already in requirements.txt
if grep -q "PyPDF2" requirements.txt; then
  echo "PyPDF2 is already in requirements.txt"
else
  echo "Adding PyPDF2 to requirements.txt..."
  echo "PyPDF2==3.0.1" >> requirements.txt
  echo "Added PyPDF2 to requirements.txt"
fi

# Install the dependency
echo "Installing PyPDF2..."
pip install PyPDF2==3.0.1

# Check if installation was successful
if pip list | grep -q "PyPDF2"; then
  echo "PyPDF2 installed successfully"
else
  echo "Failed to install PyPDF2"
  exit 1
fi

echo "=== PDF DEPENDENCY FIX COMPLETE ==="
echo "The PyPDF2 dependency has been added to requirements.txt and installed."
