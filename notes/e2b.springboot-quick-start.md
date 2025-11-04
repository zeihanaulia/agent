# E2B Spring Boot - Quick Start Guide

## Prerequisites

### 1. Environment Setup
```bash
# Ensure .env file has E2B API key
cat .env | grep E2B_API_KEY

# Expected output:
# E2B_API_KEY=e2b_24ce67e8089ef9e158c29dda0892438821da3546
```

### 2. Virtual Environment
```bash
# Activate Python environment
source .venv/bin/activate

# Verify E2B SDK is installed
python -c "from e2b import Sandbox; print('✅ E2B installed')"
```

## Running the Generator

### Basic Usage
```bash
cd /Users/zeihanaulia/Programming/research/agent
source .venv/bin/activate
python scripts/springboot_generator.py
```

### Expected Output
```
🔧 Step 1: Setup and Initialization
🚀 Creating Spring Boot sandbox...
✅ Sandbox created successfully!
📁 Step 2: Project Creation
...
🎉 Spring Boot application setup completed!
📍 Application should be accessible at: http://localhost:8080
🌐 Sandbox host: 8080-XXXXX.e2b.app
```

### Access the Application
```bash
# Replace XXXXX with sandbox host from output
curl http://8080-XXXXX.e2b.app/

# Or use in browser
# http://8080-XXXXX.e2b.app/
```

## What the Script Does

### Phase 1: Initialization
- Creates E2B sandbox with `springboot-dev` template
- Verifies Java 17 and Maven 3.8.7 available

### Phase 2: Project Setup
- Creates Maven project structure
- Writes pom.xml with Spring Boot 3.4.0 dependencies
- Creates Application.java (entry point)
- Creates HelloController.java (REST endpoints)

### Phase 3: Build
- Runs `mvn clean package`
- Downloads dependencies (first run: ~30s)
- Compiles and packages as Spring Boot JAR

### Phase 4: Deployment
- Starts JAR in background with nohup
- Verifies process is running
- Provisions public sandbox host URL

### Phase 5: Cleanup
- Stops sandbox after testing

## Project Structure in Sandbox

```
/home/user/spring-boot/
├── pom.xml
├── app.log (application logs)
├── target/
│   └── spring-boot-0.0.1-SNAPSHOT.jar (20.6 MB)
└── src/
    ├── main/java/com/example/springboot/
    │   ├── Application.java
    │   └── HelloController.java
    └── test/java/com/example/springboot/
```

## Available Endpoints

### Hello Endpoint
```bash
curl http://8080-XXXXX.e2b.app/
# Response: "Greetings from Spring Boot!"

curl http://8080-XXXXX.e2b.app/hello
# Response: "Hello from Spring Boot!"
```

## Configuration

### Modify Application
Edit `scripts/springboot_generator.py` to change:
- Controller endpoints
- Application properties
- Dependencies in pom.xml
- Package structure

### Environment
- **Java Version**: 17.0.17 (OpenJDK)
- **Maven Version**: 3.8.7
- **Spring Boot Version**: 3.4.0
- **Tomcat Version**: 10.1.x
- **Port**: 8080

## Troubleshooting

### Issue: E2B_API_KEY not found
**Solution**: Add to `.env`:
```bash
E2B_API_KEY=your_actual_key_here
```

### Issue: Sandbox creation fails
**Solution**: Check API key is valid:
```bash
python -c "from e2b import Sandbox; Sandbox.create(api_key='YOUR_KEY')"
```

### Issue: Maven downloads slow
**Solution**: First run downloads all dependencies (~500MB), subsequent runs are faster

### Issue: Port 8080 not responding immediately
**Solution**: Application startup takes 5-10 seconds, try again after waiting

### Issue: Application startup logs empty
**Solution**: Check app.log in sandbox:
```bash
# From inside script or after sandbox is still running
cat /home/user/spring-boot/app.log
```

## Advanced Usage

### Modify HelloController
Edit in `step_2_create_project_structure()`:
```python
controller_content = '''
// Add custom endpoints here
@GetMapping("/api/users")
public List<User> getUsers() {
    return new ArrayList<>();
}
'''
```

### Add Dependencies
Edit pom.xml in `step_2_create_project_structure()`:
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-jpa</artifactId>
</dependency>
```

### Custom Configuration
Edit `Application.java` to add:
- @Configuration classes
- @Bean definitions
- Custom runners
- Property sources

## Key Components

### The E2B Template
Location: `.e2b/templates/springboot/`
- Pre-configured with Java 17
- Maven 3.8.7 included
- All Spring Boot dependencies cached

### The Generator Script
Location: `scripts/springboot_generator.py`
- 9-step orchestration
- Streaming build output
- Automatic cleanup
- Error handling

### Configuration Files
Location: Root directory
- `.env` - API keys and model settings
- `.e2b/` - E2B templates

## Performance Metrics

### First Run (Fresh Downloads)
- Setup: ~2s
- Build: ~30-40s (downloading 500MB dependencies)
- **Total**: ~35-45s

### Subsequent Runs (Cached Dependencies)
- Setup: ~2s
- Build: ~20-25s
- **Total**: ~25-30s

### Network
- Maven Central downloads: ~1-2 MB/s
- Sandbox provisioning: ~5s
- Host registration: ~10s

## Common Commands

### View Build Progress
```bash
# The script streams output automatically
python scripts/springboot_generator.py
```

### Check Sandbox Status
```bash
# Inside the script, check logs
# Or monitor from another terminal (while script running):
# curl http://SANDBOX_HOST:8080/
```

### Manual Cleanup
If script stops unexpectedly:
```python
from e2b import Sandbox
# Existing sandboxes can be accessed via API
# See E2B documentation for cleanup methods
```

## Next Steps

1. **Basic Testing**
   - Run the script
   - Test endpoints with curl
   - View logs in app.log

2. **Customization**
   - Modify HelloController endpoints
   - Add more services
   - Integrate database

3. **Integration**
   - Connect to CI/CD pipeline
   - Automate testing
   - Deploy to production environment

4. **Advanced Features**
   - Add authentication (Spring Security)
   - Add API documentation (Swagger)
   - Add database (JPA/Hibernate)
   - Add messaging (Kafka/RabbitMQ)

## Documentation References

- [Spring Boot Official Docs](https://spring.io/projects/spring-boot)
- [E2B Documentation](https://e2b.dev/docs)
- [Maven Documentation](https://maven.apache.org/guides/)
- [Spring Getting Started Guide](https://spring.io/guides/gs/spring-boot/)

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review E2B API documentation
3. Check Spring Boot logs in app.log
4. Verify environment in `.env`

---

**Created**: 2025-11-04  
**Version**: 1.0  
**Status**: ✅ Production Ready
