"""
Diagnostic script to check backend status
"""
import socket
import sys

def check_port(host='localhost', port=8000):
    """Check if port is open"""
    print(f"\n=== Checking Port {port} ===")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()

        if result == 0:
            print(f"Port {port} is OPEN and accepting connections")
            return True
        else:
            print(f"Port {port} is CLOSED (error code: {result})")
            return False
    except Exception as e:
        print(f"Error checking port: {e}")
        return False

def check_http_response(host='localhost', port=8000):
    """Try to get HTTP response"""
    print(f"\n=== Testing HTTP Response ===")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))

        # Send HTTP GET request
        request = b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
        sock.sendall(request)

        # Try to receive response
        response = sock.recv(1024)
        sock.close()

        if response:
            print(f"Received response ({len(response)} bytes):")
            print(response.decode('utf-8', errors='ignore')[:500])
            return True
        else:
            print("No response received (server not responding to HTTP)")
            return False

    except socket.timeout:
        print("TIMEOUT: Server accepted connection but didn't respond")
        print("This usually means:")
        print("  - Server process is hung")
        print("  - Wrong application running on port")
        print("  - Database connection blocking the server")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def check_database_connection():
    """Check if we can import required modules"""
    print(f"\n=== Checking Dependencies ===")
    modules = ['fastapi', 'uvicorn', 'sqlalchemy', 'asyncpg', 'psycopg2']

    for module in modules:
        try:
            __import__(module)
            print(f"OK: {module}")
        except ImportError:
            print(f"MISSING: {module}")

if __name__ == "__main__":
    print("="*60)
    print(" Backend Diagnostic Tool")
    print("="*60)

    port_open = check_port()

    if port_open:
        http_ok = check_http_response()

        if not http_ok:
            print("\nRECOMMENDATION:")
            print("  The port is open but not responding to HTTP requests.")
            print("  You may need to:")
            print("    1. Stop the hung process")
            print("    2. Check database connectivity")
            print("    3. Restart the backend server")
    else:
        print("\nRECOMMENDATION:")
        print("  Backend server is not running.")
        print("  Start it with: python Backend/main.py")

    check_database_connection()

    print("\n" + "="*60)
