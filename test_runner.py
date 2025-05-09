import os
import sys
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class TestRunner(FileSystemEventHandler):
    def __init__(self):
        self.last_run = 0
        self.cooldown = 2  # seconds between runs
        
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.py'):
            current_time = time.time()
            if current_time - self.last_run > self.cooldown:
                self.last_run = current_time
                self.run_tests()
    
    def run_tests(self):
        print("\n" + "="*50)
        print("Running automated tests...")
        print("="*50)
        
        # Run Django check
        print("\nRunning Django system check...")
        check_result = subprocess.run(
            ['python', 'manage.py', 'check'],
            capture_output=True,
            text=True
        )
        if check_result.returncode == 0:
            print("✓ Django system check passed")
        else:
            print("✗ Django system check failed:")
            print(check_result.stdout)
            print(check_result.stderr)
        
        # Run model validation
        print("\nRunning model validation...")
        validate_result = subprocess.run(
            ['python', 'manage.py', 'validate'],
            capture_output=True,
            text=True
        )
        if validate_result.returncode == 0:
            print("✓ Model validation passed")
        else:
            print("✗ Model validation failed:")
            print(validate_result.stdout)
            print(validate_result.stderr)
        
        # Run unit tests
        print("\nRunning unit tests...")
        test_result = subprocess.run(
            ['python', 'manage.py', 'test'],
            capture_output=True,
            text=True
        )
        if test_result.returncode == 0:
            print("✓ Unit tests passed")
        else:
            print("✗ Unit tests failed:")
            print(test_result.stdout)
            print(test_result.stderr)
        
        # Check for circular imports
        print("\nChecking for circular imports...")
        import_check = subprocess.run(
            ['python', '-c', 'import myapp.models; import jobs.models'],
            capture_output=True,
            text=True
        )
        if import_check.returncode == 0:
            print("✓ No circular imports detected")
        else:
            print("✗ Circular imports detected:")
            print(import_check.stderr)
        
        print("\n" + "="*50)
        print("Test run completed")
        print("="*50 + "\n")

def main():
    path = "."
    event_handler = TestRunner()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    
    print("Starting automated test runner...")
    print("Watching for file changes...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main() 