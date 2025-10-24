#!/usr/bin/env python3
"""
Setup script for advanced Knowledge Base features
Installs dependencies and configures services
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def check_file_exists(file_path, description):
    """Check if a file exists"""
    if Path(file_path).exists():
        print(f"✅ {description} found")
        return True
    else:
        print(f"❌ {description} not found")
        return False

def create_env_file():
    """Create .env file from template"""
    env_template = Path(".env.template")
    env_file = Path(".env")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if env_template.exists():
        print("📝 Creating .env file from template...")
        try:
            content = env_template.read_text()
            env_file.write_text(content)
            print("✅ .env file created successfully")
            print("⚠️  Please review and update the .env file with your specific configuration")
            return True
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    else:
        print("❌ .env.template not found")
        return False

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    
    # Check if requirements_advanced.txt exists
    if not Path("requirements_advanced.txt").exists():
        print("❌ requirements_advanced.txt not found")
        return False
    
    # Install dependencies
    commands = [
        ("pip install --upgrade pip", "Upgrading pip"),
        ("pip install -r requirements_advanced.txt", "Installing advanced dependencies")
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    
    return True

def setup_milvus():
    """Setup Milvus vector database"""
    print("🗄️  Setting up Milvus vector database...")
    
    # Check if Docker is available
    if not run_command("docker --version", "Checking Docker"):
        print("❌ Docker is required for Milvus. Please install Docker first.")
        return False
    
    # Check if Milvus container is already running
    result = subprocess.run("docker ps --filter name=milvus-standalone --format '{{.Names}}'", 
                          shell=True, capture_output=True, text=True)
    
    if "milvus-standalone" in result.stdout:
        print("✅ Milvus container already running")
        return True
    
    # Start Milvus container
    milvus_command = """
    docker run -d \
      --name milvus-standalone \
      -p 19530:19530 -p 9091:9091 \
      -v milvus_data:/var/lib/milvus \
      milvusdb/milvus:latest standalone
    """
    
    if run_command(milvus_command.strip(), "Starting Milvus container"):
        print("⏳ Waiting for Milvus to start (30 seconds)...")
        run_command("sleep 30", "Waiting for Milvus startup")
        return True
    
    return False

def verify_api_keys():
    """Verify API keys are configured"""
    print("🔑 Verifying API keys...")
    
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        return False
    
    env_content = env_file.read_text()
    
    # Check for required API keys
    required_keys = {
        "ASSEMBLYAI_API_KEY": "AssemblyAI",
        "FIRECRAWL_API_KEY": "Firecrawl",
        "YOUTUBE_API_KEY": "YouTube Data API"
    }
    
    missing_keys = []
    for key, service in required_keys.items():
        if f"{key}=" not in env_content or f"{key}=your_" in env_content:
            missing_keys.append(service)
        else:
            print(f"✅ {service} API key configured")
    
    if missing_keys:
        print(f"❌ Missing API keys for: {', '.join(missing_keys)}")
        print("   Please update your .env file with the correct API keys")
        return False
    
    return True

def main():
    """Main setup function"""
    print("🚀 Setting up Advanced Knowledge Base Features")
    print("=" * 60)
    
    setup_steps = [
        ("Creating .env file", create_env_file),
        ("Installing dependencies", install_dependencies),
        ("Setting up Milvus", setup_milvus),
        ("Verifying API keys", verify_api_keys)
    ]
    
    results = []
    for step_name, step_function in setup_steps:
        print(f"\n📋 {step_name}...")
        print("-" * 40)
        result = step_function()
        results.append(result)
        
        if not result:
            print(f"⚠️  {step_name} had issues, but continuing...")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SETUP SUMMARY")
    print("=" * 60)
    
    for i, (step_name, _) in enumerate(setup_steps):
        status = "✅ COMPLETED" if results[i] else "❌ NEEDS ATTENTION"
        print(f"{step_name:25} {status}")
    
    successful_steps = sum(results)
    print(f"\nCompleted: {successful_steps}/{len(results)} steps")
    
    if successful_steps == len(results):
        print("\n🎉 Setup completed successfully!")
        print("\n🧪 Run the test script to verify everything works:")
        print("   python test_api_integrations.py")
    else:
        print("\n⚠️  Setup completed with some issues")
        print("\n📝 Manual steps needed:")
        
        if not results[0]:  # .env file
            print("   1. Copy .env.template to .env and configure your settings")
        if not results[1]:  # Dependencies
            print("   2. Install dependencies: pip install -r requirements_advanced.txt")
        if not results[2]:  # Milvus
            print("   3. Start Milvus: docker run -d --name milvus-standalone -p 19530:19530 milvusdb/milvus:latest standalone")
        if not results[3]:  # API keys
            print("   4. Add your API keys to the .env file")
    
    print("\n🔗 Useful commands:")
    print("   Test APIs:           python test_api_integrations.py")
    print("   Start backend:       uvicorn app.main:app --reload")
    print("   Check Milvus:        docker ps --filter name=milvus")
    print("   View Milvus logs:    docker logs milvus-standalone")

if __name__ == "__main__":
    main()
