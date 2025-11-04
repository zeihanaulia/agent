#!/usr/bin/env python3
"""Test Spring Boot in E2B sandbox"""

import os
import time
from pathlib import Path
from dotenv import load_dotenv
from e2b import Sandbox

load_dotenv()

def main():
    api_key = os.getenv('E2B_API_KEY')
    if not api_key:
        print("❌ E2B_API_KEY not found")
        return False
    
    print("=" * 80)
    print("🚀 TESTING SPRING BOOT IN E2B SANDBOX")
    print("=" * 80)
    
    print("\n1️⃣ Creating sandbox...")
    sandbox = Sandbox.create(template="springboot-dev", api_key=api_key)
    print("✅ Sandbox created")
    
    try:
        # Upload project
        print("\n2️⃣ Uploading springboot-demo...")
        project_path = Path("/Users/zeihanaulia/Programming/research/agent/dataset/codes/springboot-demo")
        
        # Check home directory first
        result = sandbox.commands.run("pwd && ls -la ~", timeout=10)
        print(f"Home info: {result.stdout}")
        
        # Try home directory
        app_dir = "/home/user/springboot-demo"
        sandbox.commands.run(f"mkdir -p {app_dir}/src/main/java/com/example/springboot", timeout=10)
        print(f"Created directory: {app_dir}")
        
        # Copy pom.xml
        pom_path = project_path / "pom.xml"
        with open(pom_path, 'r') as f:
            sandbox.files.write(f"{app_dir}/pom.xml", f.read())
        
        # Copy Java files
        src_path = project_path / "src" / "main" / "java" / "com" / "example" / "springboot"
        for java_file in ["Application.java", "HelloController.java"]:
            with open(src_path / java_file, 'r') as f:
                sandbox.files.write(
                    f"{app_dir}/src/main/java/com/example/springboot/{java_file}",
                    f.read()
                )
        print("✅ Project uploaded")
        
        # Build
        print("\n3️⃣ Building project...")
        result = sandbox.commands.run(
            f"cd {app_dir} && mvn clean package -DskipTests -q",
            timeout=300
        )
        if result.exit_code != 0:
            print(f"❌ Build failed: {result.stderr}")
            return False
        print("✅ Build successful")
        
        # Start app in background
        print("\n4️⃣ Starting Spring Boot...")
        # Run with & to background it, don't wait
        sandbox.commands.run(
            f"cd {app_dir} && (java -jar target/*.jar > spring.log 2>&1 &); sleep 1",
            timeout=5
        )
        print("   ✅ Application started in background")
        
        time.sleep(14)  # Give app time to start (total 15 seconds)
        
        # Test endpoints
        print("\n5️⃣ Testing endpoints...")
        
        tests = [
            ("GET /hello", "curl -s http://localhost:8080/hello"),
            ("GET /", "curl -s http://localhost:8080/"),
            ("GET /api/users/by-role (no filter)", "curl -s http://localhost:8080/api/users/by-role"),
            ("GET /api/users/by-role?role=admin", "curl -s 'http://localhost:8080/api/users/by-role?role=admin'"),
            ("GET /api/users/by-role?role=user", "curl -s 'http://localhost:8080/api/users/by-role?role=user'"),
        ]
        
        for name, cmd in tests:
            result = sandbox.commands.run(cmd, timeout=10)
            print(f"\n{name}:")
            print(f"   Response: {result.stdout[:200]}")
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
