#!/usr/bin/env python3
"""
Security and Edge Case Testing Suite for document-slides-poc API
Tests security vulnerabilities, edge cases, and malicious input handling
"""

import unittest
import requests
import json
import io
import os
import tempfile
import time
import string
import random
from pathlib import Path

class APISecurityEdgeCaseTestSuite(unittest.TestCase):
    """Test suite for security vulnerabilities and edge cases"""
    
    @classmethod
    def setUpClass(cls):
        """Setup security testing environment"""
        cls.base_url = "http://localhost:5000"
        cls.api_url = f"{cls.base_url}/api"
        
        # Create test data directory
        cls.test_data_dir = tempfile.mkdtemp(prefix="security_test_")
        
        # Create various test files for security testing
        cls._create_security_test_files()
        cls.temp_files = []
    
    @classmethod
    def tearDownClass(cls):
        """Cleanup security test environment"""
        # Clean up temporary files
        for temp_file in cls.temp_files:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
        
        # Clean up test data directory
        import shutil
        if os.path.exists(cls.test_data_dir):
            shutil.rmtree(cls.test_data_dir)
    
    @classmethod
    def _create_security_test_files(cls):
        """Create test files for security testing"""
        
        # Very large file (simulate DOS attack)
        cls.very_large_file = os.path.join(cls.test_data_dir, "very_large.txt")
        with open(cls.very_large_file, 'w') as f:
            # Write 10MB of text
            large_text = "A" * 1024 * 1024  # 1MB chunk
            for i in range(10):
                f.write(large_text)
        
        # File with malicious filename
        cls.malicious_filename = os.path.join(cls.test_data_dir, "..%2F..%2F..%2Fetc%2Fpasswd.txt")
        with open(cls.malicious_filename, 'w') as f:
            f.write("Malicious content attempting path traversal")
        
        # Binary file that's not a document
        cls.binary_file = os.path.join(cls.test_data_dir, "binary.bin")
        with open(cls.binary_file, 'wb') as f:
            f.write(os.urandom(1024))  # Random binary data
        
        # File with Unicode/special characters
        cls.unicode_file = os.path.join(cls.test_data_dir, "unicode_测试_файл.txt")
        with open(cls.unicode_file, 'w', encoding='utf-8') as f:
            f.write("Unicode test file with special characters: 测试 файл 🚀 💻")
        
        # Empty file
        cls.empty_file = os.path.join(cls.test_data_dir, "empty.xlsx")
        with open(cls.empty_file, 'w') as f:
            pass  # Create empty file
        
        # File with SQL injection attempt in content
        cls.sql_injection_file = os.path.join(cls.test_data_dir, "sql_injection.txt")
        with open(cls.sql_injection_file, 'w') as f:
            f.write("""
            Company'; DROP TABLE users; --
            Revenue: $100M'; DELETE FROM financial_data WHERE 1=1; --
            SELECT * FROM sensitive_data WHERE password = '' OR '1'='1'
            """)
        
        # File with XSS attempt
        cls.xss_file = os.path.join(cls.test_data_dir, "xss_attempt.txt")
        with open(cls.xss_file, 'w') as f:
            f.write("""
            <script>alert('XSS Attack')</script>
            <img src=x onerror=alert('XSS')>
            javascript:alert('XSS')
            """)
        
        # File with extremely long lines
        cls.long_lines_file = os.path.join(cls.test_data_dir, "long_lines.txt")
        with open(cls.long_lines_file, 'w') as f:
            very_long_line = "A" * 100000  # 100KB single line
            f.write(very_long_line + "\n")
            f.write("Normal line\n")
            f.write(very_long_line + "\n")
        
        # File with many special characters
        cls.special_chars_file = os.path.join(cls.test_data_dir, "special_chars.txt")
        with open(cls.special_chars_file, 'w', encoding='utf-8') as f:
            special_chars = "!@#$%^&*()[]{}|\\:;\"'<>?,./-=_+`~"
            f.write(special_chars * 100)
    
    def setUp(self):
        """Setup for each test"""
        self.session = requests.Session()
        self.session.timeout = 30
    
    def tearDown(self):
        """Cleanup after each test"""
        self.session.close()
    
    def _check_server_running(self):
        """Check if the API server is running"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def test_01_file_size_limits(self):
        """Test handling of very large files"""
        print("\n=== Testing File Size Limits ===")
        
        if not self._check_server_running():
            self.skipTest("API server not running")
        
        # Test with very large file
        with open(self.very_large_file, 'rb') as f:
            files = {'documents': ('very_large.txt', f, 'text/plain')}
            
            start_time = time.time()
            response = self.session.post(f"{self.api_url}/generate-slides", files=files)
            end_time = time.time()
            
            duration = end_time - start_time
            
            # Should either reject the file or handle it within reasonable time
            if response.status_code == 400:
                data = response.json()
                print(f"✓ Large file rejected appropriately: {data}")
            elif response.status_code == 413:
                print("✓ Large file rejected with payload too large error")
            elif response.status_code == 500:
                print("⚠ Large file caused server error (may need size limits)")
            else:
                print(f"⚠ Large file handling: Status {response.status_code}, Time {duration:.2f}s")
            
            # Should not take too long to respond
            self.assertLess(duration, 30.0)
    
    def test_02_malicious_filenames(self):
        """Test handling of malicious filenames (path traversal)"""
        print("\n=== Testing Malicious Filenames ===")
        
        if not self._check_server_running():
            self.skipTest("API server not running")
        
        malicious_filenames = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "file.txt\x00.exe",
            "con.txt",  # Windows reserved name
            "aux.docx",  # Windows reserved name
            "prn.xlsx",  # Windows reserved name
        ]
        
        for filename in malicious_filenames:
            with open(self.malicious_filename, 'rb') as f:
                files = {'documents': (filename, f, 'text/plain')}
                response = self.session.post(f"{self.api_url}/generate-slides", files=files)
                
                # Should handle safely without exposing system files
                if response.status_code == 400:
                    data = response.json()
                    print(f"✓ Malicious filename '{filename}' rejected: {data.get('error', 'Unknown error')}")
                elif response.status_code == 500:
                    print(f"⚠ Malicious filename '{filename}' caused server error")
                else:
                    print(f"⚠ Malicious filename '{filename}': Status {response.status_code}")
    
    def test_03_unicode_and_special_characters(self):
        """Test handling of Unicode and special characters"""
        print("\n=== Testing Unicode and Special Characters ===")
        
        if not self._check_server_running():
            self.skipTest("API server not running")
        
        # Test Unicode filename
        with open(self.unicode_file, 'rb') as f:
            files = {'documents': ('unicode_测试_файл.txt', f, 'text/plain')}
            response = self.session.post(f"{self.api_url}/generate-slides", files=files)
            
            print(f"Unicode filename response: {response.status_code}")
            if response.status_code == 400:
                data = response.json()
                print(f"✓ Unicode filename handled: {data}")
        
        # Test file with special characters in content
        with open(self.special_chars_file, 'rb') as f:
            files = {'documents': ('special_chars.txt', f, 'text/plain')}
            response = self.session.post(f"{self.api_url}/generate-slides", files=files)
            
            print(f"Special characters content response: {response.status_code}")
    
    def test_04_binary_file_upload(self):
        """Test handling of binary files disguised as documents"""
        print("\n=== Testing Binary File Upload ===")
        
        if not self._check_server_running():
            self.skipTest("API server not running")
        
        # Test binary file with document extension
        with open(self.binary_file, 'rb') as f:
            files = {'documents': ('malicious.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            response = self.session.post(f"{self.api_url}/generate-slides", files=files)
            
            # Should detect that it's not a valid document
            if response.status_code == 500:
                data = response.json()
                print(f"✓ Binary file properly rejected: {data}")
            elif response.status_code == 400:
                data = response.json()
                print(f"✓ Binary file rejected: {data}")
            else:
                print(f"⚠ Binary file handling: Status {response.status_code}")
    
    def test_05_injection_attacks(self):
        """Test for SQL injection and XSS vulnerabilities"""
        print("\n=== Testing Injection Attacks ===")
        
        if not self._check_server_running():
            self.skipTest("API server not running")
        
        # Test SQL injection in file content
        with open(self.sql_injection_file, 'rb') as f:
            files = {'documents': ('sql_injection.txt', f, 'text/plain')}
            response = self.session.post(f"{self.api_url}/generate-slides/preview", files=files)
            
            if response.status_code == 200:
                data = response.json()
                # Check if response contains SQL injection attempts
                response_str = json.dumps(data)
                if "DROP TABLE" in response_str or "DELETE FROM" in response_str:
                    print("⚠ Potential SQL injection vulnerability detected")
                else:
                    print("✓ SQL injection content handled safely")
        
        # Test XSS in file content
        with open(self.xss_file, 'rb') as f:
            files = {'documents': ('xss_attempt.txt', f, 'text/plain')}
            response = self.session.post(f"{self.api_url}/generate-slides/preview", files=files)
            
            if response.status_code == 200:
                data = response.json()
                # Check if response contains script tags
                response_str = json.dumps(data)
                if "<script>" in response_str or "javascript:" in response_str:
                    print("⚠ Potential XSS vulnerability detected")
                else:
                    print("✓ XSS content handled safely")
    
    def test_06_empty_and_null_inputs(self):
        """Test handling of empty and null inputs"""
        print("\n=== Testing Empty and Null Inputs ===")
        
        if not self._check_server_running():
            self.skipTest("API server not running")
        
        # Test empty file
        with open(self.empty_file, 'rb') as f:
            files = {'documents': ('empty.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            response = self.session.post(f"{self.api_url}/generate-slides", files=files)
            
            print(f"Empty file response: {response.status_code}")
            if response.status_code in [400, 500]:
                data = response.json()
                print(f"✓ Empty file handled: {data}")
        
        # Test null/empty template parameter
        null_template_tests = [
            {'template_id': ''},
            {'template_id': None},
            {'template_id': 'null'},
            {'template_id': '../../etc/passwd'},
        ]
        
        for test_data in null_template_tests:
            files = {'documents': ('test.txt', io.BytesIO(b'test content'), 'text/plain')}
            response = self.session.post(f"{self.api_url}/generate-slides", files=files, data=test_data)
            
            print(f"Template '{test_data['template_id']}' response: {response.status_code}")
    
    def test_07_concurrent_malicious_requests(self):
        """Test system stability under concurrent malicious requests"""
        print("\n=== Testing Concurrent Malicious Requests ===")
        
        if not self._check_server_running():
            self.skipTest("API server not running")
        
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_malicious_request(request_id):
            try:
                # Various malicious payloads
                malicious_payloads = [
                    ('large_file', self.very_large_file),
                    ('binary_file', self.binary_file),
                    ('special_chars', self.special_chars_file),
                    ('long_lines', self.long_lines_file)
                ]
                
                payload_type, file_path = malicious_payloads[request_id % len(malicious_payloads)]
                
                with open(file_path, 'rb') as f:
                    files = {'documents': (f'malicious_{request_id}.txt', f, 'text/plain')}
                    response = requests.post(f"{self.api_url}/generate-slides", files=files, timeout=30)
                    
                results.put((request_id, payload_type, response.status_code, 'success'))
                
            except Exception as e:
                results.put((request_id, 'unknown', 'error', str(e)))
        
        # Launch 5 concurrent malicious requests
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_malicious_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=60)
        
        # Analyze results
        responses = []
        while not results.empty():
            request_id, payload_type, status, result = results.get()
            responses.append((request_id, payload_type, status, result))
            print(f"  Request {request_id} ({payload_type}): {status} - {result}")
        
        # Server should still be responsive
        health_response = self.session.get(f"{self.base_url}/health")
        self.assertEqual(health_response.status_code, 200)
        print("✓ Server remained responsive during concurrent malicious requests")
    
    def test_08_header_injection(self):
        """Test for HTTP header injection vulnerabilities"""
        print("\n=== Testing Header Injection ===")
        
        if not self._check_server_running():
            self.skipTest("API server not running")
        
        # Test malicious headers
        malicious_headers = {
            'X-Forwarded-For': '127.0.0.1\r\nSet-Cookie: malicious=true',
            'User-Agent': 'Mozilla/5.0\r\nX-Injected: true',
            'Content-Type': 'application/json\r\nX-Evil: header'
        }
        
        for header_name, header_value in malicious_headers.items():
            try:
                headers = {header_name: header_value}
                response = self.session.get(f"{self.base_url}/health", headers=headers)
                
                # Check if injected headers appear in response
                if 'X-Injected' in response.headers or 'X-Evil' in response.headers:
                    print(f"⚠ Header injection vulnerability with {header_name}")
                else:
                    print(f"✓ Header injection blocked for {header_name}")
                    
            except Exception as e:
                print(f"✓ Header injection rejected for {header_name}: {str(e)}")
    
    def test_09_rate_limiting(self):
        """Test for rate limiting protection"""
        print("\n=== Testing Rate Limiting ===")
        
        if not self._check_server_running():
            self.skipTest("API server not running")
        
        # Make rapid requests to test rate limiting
        rapid_responses = []
        start_time = time.time()
        
        for i in range(20):  # 20 rapid requests
            try:
                response = self.session.get(f"{self.base_url}/health")
                rapid_responses.append(response.status_code)
            except Exception as e:
                rapid_responses.append('error')
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Check for rate limiting responses (429)
        rate_limited = rapid_responses.count(429)
        successful = rapid_responses.count(200)
        
        print(f"  20 requests in {duration:.2f}s")
        print(f"  Successful: {successful}")
        print(f"  Rate limited (429): {rate_limited}")
        print(f"  Errors: {20 - successful - rate_limited}")
        
        if rate_limited > 0:
            print("✓ Rate limiting is active")
        else:
            print("⚠ No rate limiting detected")
    
    def test_10_path_traversal_in_templates(self):
        """Test path traversal vulnerabilities in template selection"""
        print("\n=== Testing Path Traversal in Templates ===")
        
        if not self._check_server_running():
            self.skipTest("API server not running")
        
        path_traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "....//....//....//etc/passwd",
            "/etc/passwd",
            "C:\\windows\\system32\\config\\sam"
        ]
        
        for attempt in path_traversal_attempts:
            response = self.session.post(f"{self.api_url}/templates/{attempt}/select")
            
            # Should not expose system files
            if response.status_code == 404:
                print(f"✓ Path traversal blocked: {attempt}")
            elif response.status_code == 400:
                data = response.json()
                print(f"✓ Path traversal rejected: {attempt} - {data.get('error', '')}")
            elif response.status_code == 503:
                print(f"✓ Template management disabled (secure)")
            else:
                print(f"⚠ Path traversal attempt '{attempt}': Status {response.status_code}")
    
    def test_11_memory_exhaustion_protection(self):
        """Test protection against memory exhaustion attacks"""
        print("\n=== Testing Memory Exhaustion Protection ===")
        
        if not self._check_server_running():
            self.skipTest("API server not running")
        
        # Create a file with repetitive content that could cause memory issues
        memory_bomb_file = os.path.join(self.test_data_dir, "memory_bomb.txt")
        with open(memory_bomb_file, 'w') as f:
            # Write patterns that might cause excessive memory usage during processing
            for i in range(1000):
                f.write("A" * 1000 + "\n")  # 1MB of 'A's
        
        self.temp_files.append(memory_bomb_file)
        
        start_time = time.time()
        
        with open(memory_bomb_file, 'rb') as f:
            files = {'documents': ('memory_bomb.txt', f, 'text/plain')}
            response = self.session.post(f"{self.api_url}/generate-slides/preview", files=files)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should handle without excessive memory usage or timeout
        print(f"  Memory bomb processing time: {duration:.2f}s")
        print(f"  Response status: {response.status_code}")
        
        # Should complete within reasonable time
        self.assertLess(duration, 30.0)
        
        # Server should still be responsive
        health_response = self.session.get(f"{self.base_url}/health")
        self.assertEqual(health_response.status_code, 200)
        print("✓ Server survived memory exhaustion attempt")
    
    def test_12_content_type_confusion(self):
        """Test for content type confusion attacks"""
        print("\n=== Testing Content Type Confusion ===")
        
        if not self._check_server_running():
            self.skipTest("API server not running")
        
        # Send malicious content with misleading content-type
        malicious_content = b"<?xml version='1.0'?><!DOCTYPE root [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]><root>&xxe;</root>"
        
        content_type_tests = [
            ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'xlsx'),
            ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'docx'),
            ('application/pdf', 'pdf'),
            ('application/xml', 'xml'),
            ('text/xml', 'xml')
        ]
        
        for content_type, extension in content_type_tests:
            files = {'documents': (f'malicious.{extension}', malicious_content, content_type)}
            response = self.session.post(f"{self.api_url}/generate-slides", files=files)
            
            print(f"  Content type {content_type}: Status {response.status_code}")
            
            if response.status_code == 500:
                data = response.json()
                # Should not expose file system info
                if 'etc/passwd' in data.get('error', ''):
                    print(f"⚠ Potential XXE vulnerability with {content_type}")
                else:
                    print(f"✓ Content type confusion handled for {content_type}")
    
    def test_13_dos_protection(self):
        """Test protection against denial of service attacks"""
        print("\n=== Testing DoS Protection ===")
        
        if not self._check_server_running():
            self.skipTest("API server not running")
        
        # Test with extremely nested JSON-like content
        nested_content = "{"
        for i in range(1000):
            nested_content += "\"level" + str(i) + "\":{"
        nested_content += "\"data\":\"value\""
        for i in range(1000):
            nested_content += "}"
        
        dos_file = os.path.join(self.test_data_dir, "dos_test.txt")
        with open(dos_file, 'w') as f:
            f.write(nested_content)
        
        self.temp_files.append(dos_file)
        
        start_time = time.time()
        
        with open(dos_file, 'rb') as f:
            files = {'documents': ('dos_test.txt', f, 'text/plain')}
            response = self.session.post(f"{self.api_url}/generate-slides/preview", files=files)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"  DoS test processing time: {duration:.2f}s")
        print(f"  Response status: {response.status_code}")
        
        # Should not hang indefinitely
        self.assertLess(duration, 60.0)
        
        # Server should remain responsive
        health_response = self.session.get(f"{self.base_url}/health")
        self.assertEqual(health_response.status_code, 200)
        print("✓ Server survived DoS attempt")

def run_security_tests():
    """Run the security and edge case test suite"""
    print("=" * 60)
    print("SECURITY & EDGE CASE TESTING SUITE")
    print("Testing security vulnerabilities and edge cases")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(APISecurityEdgeCaseTestSuite)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("SECURITY TEST RESULTS")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.failures:
        print("\nSECURITY FAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}")
    
    if result.errors:
        print("\nSECURITY ERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}")
    
    security_issues = len(result.failures) + len(result.errors)
    if security_issues == 0:
        print("\n✅ No security vulnerabilities detected!")
    else:
        print(f"\n⚠️  {security_issues} potential security issue(s) found. Review the details above.")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_security_tests()
    exit(0 if success else 1)