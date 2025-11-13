import os
from e2b import Sandbox
from dotenv import load_dotenv

load_dotenv()

def test_springboot_with_e2b():
    # Buat sandbox dengan template springboot-dev
    sbx = Sandbox.create(template='springboot-dev')

    # Path lokal ke project Spring Boot
    local_project_path = '/Users/zeihanaulia/Programming/research/agent/dataset/codes/springboot-demo'
    sandbox_project_path = '/app'

    # Upload semua files dari project ke sandbox
    def upload_dir(local_path, sandbox_path):
        for root, dirs, files in os.walk(local_path):
            rel_root = os.path.relpath(root, local_path)
            sandbox_dir = os.path.join(sandbox_path, rel_root).replace('\\', '/')
            try:
                sbx.files.make_dir(sandbox_dir)
            except Exception:
                pass  # Directory mungkin sudah ada
            for file in files:
                local_file = os.path.join(root, file)
                try:
                    with open(local_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    sandbox_file = os.path.join(sandbox_dir, file).replace('\\', '/')
                    sbx.files.write(sandbox_file, content)
                    print(f"Uploaded: {sandbox_file}")
                except UnicodeDecodeError:
                    print(f"Skipped binary file: {local_file}")
                except Exception as e:
                    print(f"Error uploading {local_file}: {e}")

    upload_dir(local_project_path, sandbox_project_path)

    # Jalankan Maven untuk build dan run Spring Boot
    print("Building and running Spring Boot project...")
    
    def on_build_stdout(data):
        print(f"BUILD STDOUT: {data}")
    
    def on_build_stderr(data):
        print(f"BUILD STDERR: {data}")
    
    try:
        # Build dulu - gunakan package untuk memastikan semua dependencies
        sbx.commands.run('cd /app && mvn clean package -DskipTests -q', on_stdout=on_build_stdout, on_stderr=on_build_stderr)
        print("Build successful")
    except Exception as e:
        print(f"Build failed: {e}")
        return

    def on_stdout(data):
        print(f"STDOUT: {data}")

    def on_stderr(data):
        print(f"STDERR: {data}")

    try:
        # Run Spring Boot (akan berjalan di background, tapi untuk test, batasi waktu)
        sbx.commands.run('cd /app && timeout 30 mvn spring-boot:run -q', on_stdout=on_stdout, on_stderr=on_stderr)
        print("Run completed")
    except Exception as e:
        print(f"Run failed: {e}")

    # Cleanup
    sbx.kill()
    print("Sandbox killed")

if __name__ == "__main__":
    test_springboot_with_e2b()