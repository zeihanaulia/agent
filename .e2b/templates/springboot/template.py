from e2b import Template

template = (
    Template()
    .from_image("e2bdev/base")
    # Install Java 17 and Maven with sudo
    .run_cmd("sudo apt-get update && sudo apt-get install -y openjdk-17-jdk maven")
    # Set Java environment variables
    .set_envs({
        "JAVA_HOME": "/usr/lib/jvm/java-17-openjdk-amd64",
        "PATH": "/usr/lib/jvm/java-17-openjdk-amd64/bin:$PATH"
    })
    # Verify installations
    .run_cmd("java -version && mvn -version")
)