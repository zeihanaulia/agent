#!/usr/bin/env python3
"""Debug Shipping Status Transitions"""

import os
import time
import json
from pathlib import Path
from dotenv import load_dotenv
from e2b import Sandbox

load_dotenv()

def main():
    api_key = os.getenv('E2B_API_KEY')
    if not api_key:
        print("❌ E2B_API_KEY not found")
        return False

    print("🔍 DEBUGGING SHIPPING STATUS TRANSITIONS")
    print("=" * 50)

    sandbox = Sandbox.create(template="springboot-dev", api_key=api_key)

    try:
        # Upload project
        project_path = Path("/Users/zeihanaulia/Programming/research/agent/dataset/codes/springboot-demo")
        app_dir = "/home/user/springboot-demo"

        # Create directories and upload files (same as before)
        sandbox.commands.run(f"mkdir -p {app_dir}/src/main/java/com/example/springboot", timeout=10)

        # Copy pom.xml
        with open(project_path / "pom.xml", 'r') as f:
            sandbox.files.write(f"{app_dir}/pom.xml", f.read())

        dirs = ["controller", "dto", "model", "repository", "service"]
        for dir_name in dirs:
            sandbox.commands.run(f"mkdir -p {app_dir}/src/main/java/com/example/springboot/{dir_name}", timeout=10)

        java_files = [
            "Application.java", "HelloController.java",
            "controller/OrderController.java", "dto/OrderRequest.java", "dto/OrderResponse.java",
            "model/Order.java", "model/Shipping.java", "repository/OrderRepository.java", "service/OrderService.java"
        ]

        for java_file in java_files:
            file_path = project_path / "src" / "main" / "java" / "com" / "example" / "springboot" / java_file
            if file_path.exists():
                with open(file_path, 'r') as f:
                    sandbox.files.write(f"{app_dir}/src/main/java/com/example/springboot/{java_file}", f.read())

        # Build
        result = sandbox.commands.run(f"cd {app_dir} && mvn clean package -DskipTests -q", timeout=300)
        if result.exit_code != 0:
            print(f"❌ Build failed: {result.stderr}")
            return False

        # Start app
        sandbox.commands.run(f"cd {app_dir} && (java -jar target/*.jar > spring.log 2>&1 &); sleep 1", timeout=5)
        time.sleep(15)

        print("\n1️⃣ Testing direct shipping status transitions...")

        # Create order
        create_data = {
            "item": "Test Item",
            "quantity": 1,
            "price": 100.00,
            "carrier": "UPS",
            "shippingAddress": "Test Address"
        }

        result = sandbox.commands.run(
            f"""cd {app_dir} && curl -s -X POST http://localhost:8080/api/orders \
            -H "Content-Type: application/json" \
            -d '{json.dumps(create_data)}'""",
            timeout=10
        )

        if result.exit_code == 0:
            response = json.loads(result.stdout)
            order_id = response.get('id')
            print(f"   Order created: ID={order_id}, Shipping Status={response.get('shippingStatus')}")

            # Update to PAID
            result = sandbox.commands.run(
                f"""cd {app_dir} && curl -s -X PUT http://localhost:8080/api/orders/{order_id} \
                -H "Content-Type: application/json" \
                -d '{{"status": "PAID"}}'""",
                timeout=10
            )

            if result.exit_code == 0:
                response = json.loads(result.stdout)
                print(f"   After PAID: Shipping Status={response.get('shippingStatus')}")

                # Update to SHIPPED
                result = sandbox.commands.run(
                    f"""cd {app_dir} && curl -s -X PUT http://localhost:8080/api/orders/{order_id} \
                    -H "Content-Type: application/json" \
                    -d '{{"status": "SHIPPED"}}'""",
                    timeout=10
                )

                if result.exit_code == 0:
                    response = json.loads(result.stdout)
                    print(f"   After SHIPPED: Shipping Status={response.get('shippingStatus')}")

                    # Update to DELIVERED
                    result = sandbox.commands.run(
                        f"""cd {app_dir} && curl -s -X PUT http://localhost:8080/api/orders/{order_id} \
                        -H "Content-Type: application/json" \
                        -d '{{"status": "DELIVERED"}}'""",
                        timeout=10
                    )

                    if result.exit_code == 0:
                        response = json.loads(result.stdout)
                        print(f"   After DELIVERED: Shipping Status={response.get('shippingStatus')}")

        # Check logs for shipping transition errors
        print("\n2️⃣ Checking logs for shipping transition errors...")
        result = sandbox.commands.run(f"cd {app_dir} && grep -i shipping spring.log", timeout=10)
        if result.exit_code == 0:
            print("   Shipping logs:")
            for line in result.stdout.split('\n'):
                if line.strip():
                    print(f"      {line}")
        else:
            print("   No shipping logs found")

        # Check for invalid transition messages
        result = sandbox.commands.run(f"cd {app_dir} && grep -i 'Invalid status transition' spring.log", timeout=10)
        if result.exit_code == 0:
            print("   ❌ Found invalid transition errors:")
            for line in result.stdout.split('\n'):
                if line.strip():
                    print(f"      {line}")
        else:
            print("   ✅ No invalid transition errors found")

        print("\n✅ DEBUGGING COMPLETED")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)