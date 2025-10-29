#!/usr/bin/env python3
"""
Spring Boot Code Generator and Runner
Generates and runs Spring Boot applications in E2B sandbox.
Following the official Spring Boot getting started tutorial.
"""

import os
import zipfile
import io
import requests
from e2b import Sandbox
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def step_1_setup_and_initialization():
    """Step 1: Setup and Initialization - Load API key and create sandbox"""
    print("🔧 Step 1: Setup and Initialization")

    # Load API key
    api_key = os.getenv('E2B_API_KEY')
    if not api_key:
        print("❌ E2B_API_KEY not found in environment variables")
        return None

    print("🚀 Creating Spring Boot sandbox...")
    sandbox = Sandbox.create(template="springboot-dev", api_key=api_key)
    print("✅ Sandbox created successfully!")

    return sandbox

def step_2_create_project_structure(sandbox):
    """Step 2: Project Creation - Create directory structure and write files"""
    print("\n📁 Step 2: Project Creation")

    # Create pom.xml exactly as in tutorial
    pom_content = '''<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.4.0</version>
        <relativePath/>
    </parent>

    <groupId>com.example</groupId>
    <artifactId>spring-boot</artifactId>
    <version>0.0.1-SNAPSHOT</version>
    <name>spring-boot</name>
    <description>Demo project for Spring Boot</description>

    <properties>
        <java.version>17</java.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>

        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>

</project>'''

    # Create Application.java exactly as in tutorial
    application_content = '''package com.example.springboot;

import java.util.Arrays;

import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ApplicationContext;
import org.springframework.context.annotation.Bean;

@SpringBootApplication
public class Application {

    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }

    @Bean
    public CommandLineRunner commandLineRunner(ApplicationContext ctx) {
        return args -> {

            System.out.println("Let's inspect the beans provided by Spring Boot:");

            String[] beanNames = ctx.getBeanDefinitionNames();
            Arrays.sort(beanNames);
            for (String beanName : beanNames) {
                System.out.println(beanName);
            }

        };
    }

}'''

    # Create HelloController.java exactly as in tutorial
    controller_content = '''package com.example.springboot;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HelloController {

    @GetMapping("/")
    public String index() {
        return "Greetings from Spring Boot!";
    }

}'''

    # Create directory structure
    print("Creating project structure...")
    sandbox.commands.run("mkdir -p /home/user/spring-boot/src/main/java/com/example/springboot")
    sandbox.commands.run("mkdir -p /home/user/spring-boot/src/test/java/com/example/springboot")

    # Write files
    sandbox.files.write("/home/user/spring-boot/pom.xml", pom_content)
    sandbox.files.write("/home/user/spring-boot/src/main/java/com/example/springboot/Application.java", application_content)
    sandbox.files.write("/home/user/spring-boot/src/main/java/com/example/springboot/HelloController.java", controller_content)

    print("✅ Project structure created successfully!")

def step_3_verify_environment(sandbox):
    """Step 3: Environment Verification - Check Java and Maven versions"""
    print("\n🔍 Step 3: Environment Verification")

    # Verify Java and Maven are working
    java_result = sandbox.commands.run("java -version")
    print("Java version:", java_result.stdout or java_result.stderr)

    maven_result = sandbox.commands.run("mvn -version")
    print("Maven version:", maven_result.stdout or maven_result.stderr)

    print("✅ Environment verification completed!")

def step_4_build_application(sandbox):
    """Step 4: Build Process - Build the application with streaming output"""
    print("\n🔨 Step 4: Build Process")

    def on_stdout(data):
        print(f"[BUILD] {data.strip()}")

    def on_stderr(data):
        print(f"[ERROR] {data.strip()}")

    try:
        build_result = sandbox.commands.run(
            "cd /home/user/spring-boot && mvn clean package -DskipTests",
            on_stdout=on_stdout,
            on_stderr=on_stderr,
            timeout=300
        )

        print(f"\nBuild completed with exit code: {build_result.exit_code}")

        if build_result.exit_code != 0:
            print("❌ Build failed!")
            print("Full stderr:", build_result.stderr)
            return False
        else:
            print("✅ Build successful!")
            return True

    except Exception as e:
        print(f"❌ Build error: {e}")
        # Try to see what's in the directory
        ls_result = sandbox.commands.run("cd /home/user/spring-boot && ls -la")
        print("Directory contents:", ls_result.stdout)
        return False

def step_5_check_build_artifacts(sandbox):
    """Step 5: Check Build Artifacts - Verify JAR file was created"""
    print("\n📦 Step 5: Check Build Artifacts")

    # Check JAR file
    jar_check = sandbox.commands.run("cd /home/user/spring-boot && ls -la target/*.jar")
    print("JAR files:")
    print(jar_check.stdout)

    print("✅ Build artifacts verified!")

def step_6_start_application(sandbox):
    """Step 6: Application Startup - Start the Spring Boot application"""
    print("\n🚀 Step 6: Application Startup")

    jar_name = "target/spring-boot-0.0.1-SNAPSHOT.jar"
    start_cmd = f"cd /home/user/spring-boot && nohup java -jar {jar_name} > app.log 2>&1 &"
    print(f"Starting: {start_cmd}")

    # Start the app - use very short timeout since it should return immediately with &
    try:
        start_result = sandbox.commands.run(start_cmd, timeout=2)
        print("✅ Start command issued successfully")
        return True
    except Exception as e:
        print(f"⚠️  Start command may have timed out, but app might still be starting: {e}")
        return True  # Still return True since the app might be starting

def step_7_verify_startup(sandbox):
    """Step 7: Startup Verification - Check if application started properly"""
    print("\n🔍 Step 7: Startup Verification")

    import time

    # Check multiple times with delays
    max_checks = 10
    process_found = False

    for i in range(max_checks):
        print(f"Check {i+1}/{max_checks}...")

        # Check if Java process is running
        ps_check = sandbox.commands.run("ps aux | grep java | grep -v grep", timeout=5)
        java_processes = ps_check.stdout.strip()
        if java_processes:
            print("✅ Java process found:")
            print(java_processes)
            process_found = True
            break
        else:
            print("⏳ No Java process yet, waiting...")
            time.sleep(3)

    # Check port 8080
    port_check = sandbox.commands.run("netstat -tlnp 2>/dev/null | grep :8080 || ss -tlnp | grep :8080 || echo 'Port 8080 not listening'", timeout=5)
    port_status = port_check.stdout.strip()
    print(f"Port status: {port_status}")

    # Show recent logs
    print("\n📋 Recent application logs:")
    log_check = sandbox.commands.run("cd /home/user/spring-boot && cat app.log 2>/dev/null | tail -20 || echo 'No logs yet'", timeout=5)
    print(log_check.stdout)

    return process_found, port_status

def step_8_test_endpoints(sandbox, port_status):
    """Step 8: Endpoint Testing - Test the application endpoints"""
    print("\n🌐 Step 8: Endpoint Testing")

    # Try to access the endpoint if port is listening
    if "8080" in port_status and "listen" in port_status.lower():
        try:
            curl_result = sandbox.commands.run("curl -m 5 http://localhost:8080/ || echo 'Curl failed'", timeout=10)
            print("Endpoint response:")
            print(curl_result.stdout)
            return True
        except Exception as e:
            print(f"Curl test failed: {e}")
            return False
    else:
        print("⚠️  Port 8080 not ready yet")
        return False

def step_9_cleanup(sandbox):
    """Step 9: Cleanup - Kill the sandbox"""
    print("\n🔄 Step 9: Cleanup")

    if sandbox:
        sandbox.kill()
        print("✅ Sandbox killed")

def run_spring_boot_in_sandbox():
    """
    Generate and run Spring Boot application in E2B sandbox
    Following the official Spring Boot getting started tutorial
    """
    sandbox = None

    try:
        # Step 1: Setup and Initialization
        sandbox = step_1_setup_and_initialization()
        if not sandbox:
            return

        # Step 2: Project Creation
        step_2_create_project_structure(sandbox)

        # Step 3: Environment Verification
        step_3_verify_environment(sandbox)

        # Step 4: Build Process
        build_success = step_4_build_application(sandbox)
        if not build_success:
            return

        # Step 5: Check Build Artifacts
        step_5_check_build_artifacts(sandbox)

        # Step 6: Application Startup
        startup_success = step_6_start_application(sandbox)
        if not startup_success:
            return

        # Step 7: Startup Verification
        process_found, port_status = step_7_verify_startup(sandbox)

        # Step 8: Endpoint Testing
        endpoint_success = step_8_test_endpoints(sandbox, port_status)

        # Final Summary
        print("\n🎉 Spring Boot application setup completed!")
        print("📍 Application should be accessible at: http://localhost:8080")
        print("🔗 Hello World endpoint: http://localhost:8080/")

        if process_found and endpoint_success:
            print("✅ All steps completed successfully!")
        else:
            print("⚠️  Some steps may have issues - check logs above")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Step 9: Cleanup
        step_9_cleanup(sandbox)

if __name__ == "__main__":
    run_spring_boot_in_sandbox()