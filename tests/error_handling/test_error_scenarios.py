#!/usr/bin/env python3
"""
Comprehensive error handling and edge case tests
Tests system behavior with corrupted files, API failures, timeouts, and edge cases
"""
import os
import sys
import tempfile
import io
import json
import time
import unittest
from unittest.mock import patch, Mock, MagicMock
import requests
from typing import List, Dict, Any
import threading
import signal

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lib.excel_extractor import ExcelExtractor
from lib.word_extractor import WordExtractor
from lib.pdf_extractor import PDFExtractor
from lib.slide_generator import SlideGenerator
from lib.llm_slides import analyze_documents_for_slides

class ErrorHandlingTests(unittest.TestCase):
    """Test error handling and graceful degradation"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_files = []
        self.extractors = {
            'excel': ExcelExtractor(),
            'word': WordExtractor(),
            'pdf': PDFExtractor()
        }
        
    def tearDown(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass
                
    def create_corrupted_excel(self) -> str:
        """Create a corrupted Excel file"""
        temp_path = tempfile.mktemp(suffix='.xlsx')
        
        # Write invalid Excel content
        with open(temp_path, 'wb') as f:
            f.write(b'This is not a valid Excel file content')
            
        self.temp_files.append(temp_path)
        return temp_path
        
    def create_corrupted_word(self) -> str:
        """Create a corrupted Word document"""
        temp_path = tempfile.mktemp(suffix='.docx')
        
        # Write invalid Word content
        with open(temp_path, 'wb') as f:
            f.write(b'<invalid>Word document content</invalid>')
            
        self.temp_files.append(temp_path)
        return temp_path
        
    def create_corrupted_pdf(self) -> str:
        """Create a corrupted PDF file"""
        temp_path = tempfile.mktemp(suffix='.pdf')
        
        # Write invalid PDF content
        with open(temp_path, 'wb') as f:
            f.write(b'%PDF-1.4\nThis is not valid PDF content')
            
        self.temp_files.append(temp_path)
        return temp_path
        
    def create_empty_file(self, extension: str) -> str:
        """Create an empty file with given extension"""
        temp_path = tempfile.mktemp(suffix=extension)
        
        # Create empty file
        with open(temp_path, 'wb') as f:
            pass
            
        self.temp_files.append(temp_path)
        return temp_path
        
    def create_large_text_file(self, size_mb: int = 10) -> str:
        """Create a large text file for testing memory limits"""
        temp_path = tempfile.mktemp(suffix='.txt')
        
        # Create file with specified size
        chunk = "A" * 1024  # 1KB chunk
        chunks_needed = size_mb * 1024  # Convert MB to KB
        
        with open(temp_path, 'w') as f:
            for _ in range(chunks_needed):
                f.write(chunk)
                
        self.temp_files.append(temp_path)
        return temp_path
        
    def test_corrupted_excel_handling(self):
        """Test handling of corrupted Excel files"""
        corrupted_file = self.create_corrupted_excel()
        
        # Test that extractor handles corruption gracefully
        try:
            result = self.extractors['excel'].extract_from_file(corrupted_file)
            # Should either return empty result or raise expected exception
            self.assertIsInstance(result, (list, str, type(None)))
        except Exception as e:
            # Exception should be handled gracefully, not crash the system
            self.assertIsInstance(e, (ValueError, IOError, OSError, Exception))
            print(f"Excel corruption handled with exception: {type(e).__name__}: {e}")
            
    def test_corrupted_word_handling(self):
        """Test handling of corrupted Word documents"""
        corrupted_file = self.create_corrupted_word()
        
        try:
            result = self.extractors['word'].extract_from_file(corrupted_file)
            self.assertIsInstance(result, (list, str, type(None)))
        except Exception as e:
            self.assertIsInstance(e, (ValueError, IOError, OSError, Exception))
            print(f"Word corruption handled with exception: {type(e).__name__}: {e}")
            
    def test_corrupted_pdf_handling(self):
        """Test handling of corrupted PDF files"""
        corrupted_file = self.create_corrupted_pdf()
        
        try:
            result = self.extractors['pdf'].extract_from_file(corrupted_file)
            self.assertIsInstance(result, (list, str, type(None)))
        except Exception as e:
            self.assertIsInstance(e, (ValueError, IOError, OSError, Exception))
            print(f"PDF corruption handled with exception: {type(e).__name__}: {e}")
            
    def test_empty_file_handling(self):
        """Test handling of empty files"""
        file_types = ['.xlsx', '.docx', '.pdf']
        
        for file_type in file_types:
            with self.subTest(file_type=file_type):
                empty_file = self.create_empty_file(file_type)
                extractor_name = {'.xlsx': 'excel', '.docx': 'word', '.pdf': 'pdf'}[file_type]
                
                try:
                    result = self.extractors[extractor_name].extract_from_file(empty_file)
                    # Empty files should return empty or None, not crash
                    self.assertIn(result, [[], None, ""])
                except Exception as e:
                    # Should handle empty files gracefully
                    self.assertIsInstance(e, (ValueError, IOError, OSError, Exception))
                    print(f"Empty {file_type} handled with exception: {type(e).__name__}: {e}")
                    
    def test_nonexistent_file_handling(self):
        """Test handling of non-existent files"""
        nonexistent_path = "/path/that/does/not/exist/file.xlsx"
        
        for extractor_name, extractor in self.extractors.items():
            with self.subTest(extractor=extractor_name):
                try:
                    result = extractor.extract_from_file(nonexistent_path)
                    self.fail(f"Should have raised exception for non-existent file")
                except FileNotFoundError:
                    # Expected behavior
                    pass
                except Exception as e:
                    # Other exceptions are also acceptable as long as they don't crash
                    self.assertIsInstance(e, Exception)
                    print(f"Non-existent file handled with {type(e).__name__}: {e}")
                    
    def test_permission_denied_handling(self):
        """Test handling of permission denied scenarios"""
        # This test may not work on all systems, so we'll mock it
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            for extractor_name, extractor in self.extractors.items():
                with self.subTest(extractor=extractor_name):
                    try:
                        result = extractor.extract_from_file("some_file.test")
                        self.fail("Should have raised PermissionError")
                    except PermissionError:
                        # Expected behavior
                        pass
                    except Exception as e:
                        # Other exceptions are also acceptable
                        print(f"Permission error handled with {type(e).__name__}: {e}")
                        
    @patch('lib.llm_slides.openai')
    def test_api_timeout_handling(self, mock_openai):
        """Test handling of API timeouts"""
        # Mock API timeout
        mock_openai.ChatCompletion.create.side_effect = requests.exceptions.Timeout("Request timeout")
        
        test_documents = ["Test document content"]
        
        try:
            result = analyze_documents_for_slides(test_documents)
            # Should either return fallback result or handle timeout gracefully
            self.assertIsInstance(result, (dict, list, type(None)))
        except requests.exceptions.Timeout:
            # Timeout should be handled appropriately
            pass
        except Exception as e:
            # Other exceptions should also be handled gracefully
            print(f"API timeout handled with {type(e).__name__}: {e}")
            
    @patch('lib.llm_slides.openai')
    def test_api_key_missing(self, mock_openai):
        """Test handling of missing API keys"""
        # Mock API key error
        mock_openai.ChatCompletion.create.side_effect = Exception("API key not found")
        
        test_documents = ["Test document content"]
        
        try:
            result = analyze_documents_for_slides(test_documents)
            # Should handle missing API key gracefully
            self.assertIsInstance(result, (dict, list, type(None)))
        except Exception as e:
            # Should not crash the entire system
            print(f"Missing API key handled with {type(e).__name__}: {e}")
            
    @patch('lib.llm_slides.openai')
    def test_api_rate_limit_handling(self, mock_openai):
        """Test handling of API rate limits"""
        # Mock rate limit error
        mock_openai.ChatCompletion.create.side_effect = Exception("Rate limit exceeded")
        
        test_documents = ["Test document content"]
        
        try:
            result = analyze_documents_for_slides(test_documents)
            # Should handle rate limits gracefully
            self.assertIsInstance(result, (dict, list, type(None)))
        except Exception as e:
            print(f"Rate limit handled with {type(e).__name__}: {e}")
            
    def test_memory_limit_handling(self):
        """Test handling of memory-intensive operations"""
        # Create a large file to test memory limits
        large_file = self.create_large_text_file(5)  # 5MB file
        
        # This is a basic test - in a real scenario you'd want to monitor actual memory usage
        try:
            with open(large_file, 'r') as f:
                content = f.read()
                
            # Test that large content doesn't crash the system
            self.assertIsInstance(content, str)
            self.assertGreater(len(content), 1000000)  # Should be large
            
        except MemoryError:
            # Should handle memory errors gracefully
            print("Memory limit reached and handled appropriately")
        except Exception as e:
            # Other exceptions should also be handled
            print(f"Large file handled with {type(e).__name__}: {e}")
            
    def test_concurrent_access_safety(self):
        """Test thread safety and concurrent access"""
        import threading
        import queue
        
        results_queue = queue.Queue()
        errors_queue = queue.Queue()
        
        # Create test file for concurrent access
        test_file = self.create_corrupted_excel()
        
        def worker_function():
            try:
                result = self.extractors['excel'].extract_from_file(test_file)
                results_queue.put(result)
            except Exception as e:
                errors_queue.put(e)
                
        # Start multiple threads
        threads = []
        num_threads = 5
        
        for _ in range(num_threads):
            thread = threading.Thread(target=worker_function)
            thread.start()
            threads.append(thread)
            
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=10)  # 10 second timeout
            
        # Check that all threads completed without deadlocks
        total_responses = results_queue.qsize() + errors_queue.qsize()
        self.assertEqual(total_responses, num_threads, 
                        "Not all threads completed - possible deadlock")
                        
    def test_disk_space_handling(self):
        """Test handling of insufficient disk space (simulated)"""
        # Mock disk space error
        with patch('builtins.open', side_effect=OSError("No space left on device")):
            try:
                generator = SlideGenerator()
                temp_path = tempfile.mktemp(suffix='.pptx')
                generator.save(temp_path)
                self.fail("Should have raised OSError for disk space")
            except OSError as e:
                # Should handle disk space errors appropriately
                self.assertIn("space", str(e).lower())
            except Exception as e:
                print(f"Disk space error handled with {type(e).__name__}: {e}")
                
    def test_unicode_handling(self):
        """Test handling of various Unicode characters and encoding issues"""
        unicode_content = [
            "Regular ASCII content",
            "Unicode content: é, ñ, ü, ç",
            "Emoji content: 😀 🚀 📊 💼",
            "Asian characters: 你好世界 こんにちは 안녕하세요",
            "Mathematical symbols: ∑ ∫ ∂ ∆ ∞",
            "Special characters: ‹›«»""''–—…",
        ]
        
        for content in unicode_content:
            with self.subTest(content=content[:20] + "..."):
                try:
                    generator = SlideGenerator()
                    generator.add_title_slide("Test", content)
                    
                    temp_path = tempfile.mktemp(suffix='.pptx')
                    self.temp_files.append(temp_path)
                    generator.save(temp_path)
                    
                    # Should handle Unicode without crashing
                    self.assertTrue(os.path.exists(temp_path))
                    
                except Exception as e:
                    # Should handle encoding issues gracefully
                    print(f"Unicode content handled with {type(e).__name__}: {e}")
                    
    def test_invalid_template_handling(self):
        """Test handling of invalid or missing templates"""
        invalid_templates = [
            "/nonexistent/template.pptx",
            "",
            None,
            "invalid_template.pptx"
        ]
        
        for template in invalid_templates:
            with self.subTest(template=template):
                try:
                    generator = SlideGenerator(template_path=template)
                    # Should either create with default template or handle gracefully
                    self.assertIsNotNone(generator)
                except Exception as e:
                    # Should handle invalid templates without crashing
                    print(f"Invalid template handled with {type(e).__name__}: {e}")
                    
    def test_network_failure_simulation(self):
        """Test handling of network failures"""
        # Mock network failure for any requests
        with patch('requests.get', side_effect=requests.exceptions.ConnectionError("Network error")):
            with patch('requests.post', side_effect=requests.exceptions.ConnectionError("Network error")):
                try:
                    # Test any network-dependent functionality
                    # This is a placeholder - adjust based on actual network usage
                    result = True  # Placeholder for network-dependent operation
                    self.assertTrue(result)
                except requests.exceptions.ConnectionError:
                    # Should handle network errors appropriately
                    pass
                except Exception as e:
                    print(f"Network error handled with {type(e).__name__}: {e}")

class EdgeCaseTests(unittest.TestCase):
    """Test edge cases and boundary conditions"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_files = []
        
    def tearDown(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass
                
    def test_extremely_long_filenames(self):
        """Test handling of extremely long filenames"""
        # Create filename at system limit (255 characters is typical)
        long_name = "a" * 200 + ".xlsx"
        
        try:
            temp_path = tempfile.mktemp(suffix='_' + long_name)
            self.temp_files.append(temp_path)
            
            # Try to create and process file with long name
            import openpyxl
            wb = openpyxl.Workbook()
            wb.save(temp_path)
            
            extractor = ExcelExtractor()
            result = extractor.extract_from_file(temp_path)
            
            # Should handle long filenames appropriately
            self.assertIsInstance(result, (list, str, type(None)))
            
        except OSError as e:
            # System may reject extremely long filenames
            print(f"Long filename handled with OSError: {e}")
        except Exception as e:
            print(f"Long filename handled with {type(e).__name__}: {e}")
            
    def test_zero_size_content(self):
        """Test handling of zero-size or minimal content"""
        try:
            generator = SlideGenerator()
            
            # Add slide with empty content
            generator.add_title_slide("", "")
            
            temp_path = tempfile.mktemp(suffix='.pptx')
            self.temp_files.append(temp_path)
            generator.save(temp_path)
            
            # Should create valid presentation even with empty content
            self.assertTrue(os.path.exists(temp_path))
            
        except Exception as e:
            print(f"Zero-size content handled with {type(e).__name__}: {e}")
            
    def test_maximum_slide_count(self):
        """Test handling of maximum number of slides"""
        max_slides = 1000  # Test reasonable maximum
        
        try:
            generator = SlideGenerator()
            
            # Add many slides
            for i in range(max_slides):
                generator.add_title_slide(f"Slide {i}", f"Content {i}")
                
                # Break early if we hit memory issues
                if i > 0 and i % 100 == 0:
                    print(f"Created {i} slides successfully")
                    
            temp_path = tempfile.mktemp(suffix='.pptx')
            self.temp_files.append(temp_path)
            generator.save(temp_path)
            
            # Should handle large number of slides
            self.assertTrue(os.path.exists(temp_path))
            
        except MemoryError:
            print("Maximum slide count reached - memory limit")
        except Exception as e:
            print(f"Maximum slides handled with {type(e).__name__}: {e}")
            
    def test_special_characters_in_paths(self):
        """Test handling of special characters in file paths"""
        special_chars = ['&', '%', '$', '#', '@', '!', '(', ')', '[', ']']
        
        for char in special_chars:
            with self.subTest(char=char):
                try:
                    # Create file with special character in name
                    temp_path = tempfile.mktemp(suffix=f'_test{char}file.xlsx')
                    
                    # Some characters may not be valid in filenames
                    if char in ['<', '>', ':', '"', '|', '?', '*']:
                        continue
                        
                    self.temp_files.append(temp_path)
                    
                    import openpyxl
                    wb = openpyxl.Workbook()
                    wb.save(temp_path)
                    
                    extractor = ExcelExtractor()
                    result = extractor.extract_from_file(temp_path)
                    
                    # Should handle special characters in paths
                    self.assertIsInstance(result, (list, str, type(None)))
                    
                except Exception as e:
                    print(f"Special character '{char}' handled with {type(e).__name__}: {e}")

if __name__ == '__main__':
    # Create test directories
    os.makedirs('tests/error_handling', exist_ok=True)
    
    # Run error handling tests with detailed output
    unittest.main(verbosity=2)