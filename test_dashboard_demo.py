#!/usr/bin/env python3
"""
Real-time Testing Dashboard for Demo File API Testing
Provides live monitoring of parallel test execution with visual feedback
"""

import time
import threading
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
import curses
from dataclasses import dataclass

@dataclass
class LiveTestResult:
    """Live test result for dashboard display"""
    agent_id: str
    test_name: str
    status: str  # 'running', 'passed', 'failed', 'pending'
    start_time: Optional[float]
    end_time: Optional[float]
    error_message: Optional[str]
    files_used: List[str]
    template_used: Optional[str]

class TestDashboard:
    """Real-time dashboard for monitoring parallel tests"""
    
    def __init__(self):
        self.test_results = {}  # test_id -> LiveTestResult
        self.agent_status = {}  # agent_id -> status
        self.test_queue = deque()
        self.completed_tests = deque(maxlen=50)  # Keep last 50 completed tests
        self.error_log = deque(maxlen=20)  # Keep last 20 errors
        self.start_time = None
        self.stats = {
            'total_tests': 0,
            'completed': 0,
            'passed': 0,
            'failed': 0,
            'running': 0
        }
        self.lock = threading.Lock()
        
    def start_test_session(self, total_tests: int):
        """Initialize a new test session"""
        with self.lock:
            self.start_time = time.time()
            self.stats['total_tests'] = total_tests
            self.stats['completed'] = 0
            self.stats['passed'] = 0
            self.stats['failed'] = 0
            self.stats['running'] = 0
    
    def update_agent_status(self, agent_id: str, status: str):
        """Update agent status"""
        with self.lock:
            self.agent_status[agent_id] = {
                'status': status,
                'last_update': time.time()
            }
    
    def start_test(self, test_id: str, agent_id: str, test_name: str, 
                   files_used: List[str], template_used: Optional[str] = None):
        """Mark test as started"""
        with self.lock:
            self.test_results[test_id] = LiveTestResult(
                agent_id=agent_id,
                test_name=test_name,
                status='running',
                start_time=time.time(),
                end_time=None,
                error_message=None,
                files_used=files_used,
                template_used=template_used
            )
            self.stats['running'] += 1
    
    def complete_test(self, test_id: str, success: bool, error_message: Optional[str] = None):
        """Mark test as completed"""
        with self.lock:
            if test_id in self.test_results:
                result = self.test_results[test_id]
                result.status = 'passed' if success else 'failed'
                result.end_time = time.time()
                result.error_message = error_message
                
                self.completed_tests.append(result)
                
                if not success and error_message:
                    self.error_log.append({
                        'test_id': test_id,
                        'agent_id': result.agent_id,
                        'test_name': result.test_name,
                        'error': error_message,
                        'files': result.files_used,
                        'timestamp': time.time()
                    })
                
                self.stats['running'] -= 1
                self.stats['completed'] += 1
                if success:
                    self.stats['passed'] += 1
                else:
                    self.stats['failed'] += 1
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get current dashboard data"""
        with self.lock:
            elapsed_time = time.time() - self.start_time if self.start_time else 0
            
            # Calculate success rate
            success_rate = 0
            if self.stats['completed'] > 0:
                success_rate = (self.stats['passed'] / self.stats['completed']) * 100
            
            # Get running tests
            running_tests = [r for r in self.test_results.values() if r.status == 'running']
            
            # Get recent errors (last 5)
            recent_errors = list(self.error_log)[-5:]
            
            return {
                'stats': self.stats.copy(),
                'success_rate': success_rate,
                'elapsed_time': elapsed_time,
                'agent_status': self.agent_status.copy(),
                'running_tests': [self._result_to_dict(r) for r in running_tests],
                'recent_errors': recent_errors,
                'completed_tests': [self._result_to_dict(r) for r in list(self.completed_tests)[-10:]]
            }
    
    def _result_to_dict(self, result: LiveTestResult) -> Dict[str, Any]:
        """Convert result to dictionary"""
        duration = None
        if result.start_time and result.end_time:
            duration = result.end_time - result.start_time
        elif result.start_time:
            duration = time.time() - result.start_time
            
        return {
            'agent_id': result.agent_id,
            'test_name': result.test_name,
            'status': result.status,
            'duration': duration,
            'error_message': result.error_message,
            'files_used': result.files_used,
            'template_used': result.template_used
        }

class ConsoleTestDashboard:
    """Console-based real-time dashboard using curses"""
    
    def __init__(self, dashboard: TestDashboard):
        self.dashboard = dashboard
        self.running = False
        
    def start(self):
        """Start the console dashboard"""
        self.running = True
        curses.wrapper(self._run_dashboard)
    
    def stop(self):
        """Stop the dashboard"""
        self.running = False
    
    def _run_dashboard(self, stdscr):
        """Main dashboard loop"""
        curses.curs_set(0)  # Hide cursor
        stdscr.nodelay(1)   # Non-blocking input
        stdscr.timeout(100) # Refresh every 100ms
        
        # Color pairs
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Success
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)    # Error
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Warning
        curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)   # Info
        curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK) # Running
        
        while self.running:
            stdscr.clear()
            
            try:
                self._draw_dashboard(stdscr)
                stdscr.refresh()
                
                # Check for quit command
                key = stdscr.getch()
                if key == ord('q') or key == ord('Q'):
                    break
                    
            except Exception as e:
                # If dashboard fails, continue without crashing
                stdscr.addstr(0, 0, f"Dashboard error: {str(e)}")
                stdscr.refresh()
            
            time.sleep(0.1)
    
    def _draw_dashboard(self, stdscr):
        """Draw the dashboard interface"""
        data = self.dashboard.get_dashboard_data()
        height, width = stdscr.getmaxyx()
        
        row = 0
        
        # Title
        title = "🧪 Document-Slides-POC API Testing Dashboard"
        stdscr.addstr(row, 0, title[:width-1], curses.A_BOLD)
        row += 1
        
        # Separator
        stdscr.addstr(row, 0, "=" * min(width-1, 60))
        row += 2
        
        # Stats section
        stats = data['stats']
        elapsed = data['elapsed_time']
        success_rate = data['success_rate']
        
        stdscr.addstr(row, 0, "📊 TEST STATISTICS", curses.A_BOLD)
        row += 1
        
        stats_text = [
            f"Total Tests: {stats['total_tests']}",
            f"Completed: {stats['completed']}",
            f"Running: {stats['running']}",
            f"Passed: {stats['passed']}",
            f"Failed: {stats['failed']}",
            f"Success Rate: {success_rate:.1f}%",
            f"Elapsed: {elapsed:.1f}s"
        ]
        
        for i, text in enumerate(stats_text):
            if i % 2 == 0:  # Left column
                stdscr.addstr(row + i//2, 2, text[:width//2-3])
            else:  # Right column
                stdscr.addstr(row + i//2, width//2, text[:width//2-3])
        
        row += (len(stats_text) + 1) // 2 + 1
        
        # Progress bar
        if stats['total_tests'] > 0:
            progress = stats['completed'] / stats['total_tests']
            bar_width = min(40, width - 20)
            filled = int(progress * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)
            stdscr.addstr(row, 2, f"Progress: [{bar}] {progress*100:.1f}%")
            row += 2
        
        # Agent status
        stdscr.addstr(row, 0, "🤖 AGENT STATUS", curses.A_BOLD)
        row += 1
        
        for agent_id, status_info in data['agent_status'].items():
            status = status_info['status']
            color = curses.color_pair(5) if status == 'running' else curses.color_pair(1)
            stdscr.addstr(row, 2, f"{agent_id}: {status}", color)
            row += 1
        
        row += 1
        
        # Running tests
        if data['running_tests']:
            stdscr.addstr(row, 0, "🏃 RUNNING TESTS", curses.A_BOLD)
            row += 1
            
            for test in data['running_tests'][:5]:  # Show first 5
                duration = test['duration'] or 0
                files_str = ', '.join(test['files_used'][:2])  # Show first 2 files
                if len(test['files_used']) > 2:
                    files_str += f" +{len(test['files_used'])-2} more"
                
                test_line = f"{test['agent_id']}: {test['test_name'][:30]} ({duration:.1f}s) [{files_str}]"
                stdscr.addstr(row, 2, test_line[:width-3], curses.color_pair(5))
                row += 1
            
            row += 1
        
        # Recent errors
        if data['recent_errors']:
            stdscr.addstr(row, 0, "❌ RECENT ERRORS", curses.A_BOLD)
            row += 1
            
            for error in data['recent_errors'][-3:]:  # Show last 3 errors
                error_line = f"{error['agent_id']}: {error['test_name'][:25]} - {error['error'][:40]}..."
                stdscr.addstr(row, 2, error_line[:width-3], curses.color_pair(2))
                row += 1
                
                # Show files that caused the error
                files_line = f"  Files: {', '.join(error['files'][:3])}"
                stdscr.addstr(row, 4, files_line[:width-5], curses.color_pair(3))
                row += 1
            
            row += 1
        
        # Help text
        if row < height - 2:
            stdscr.addstr(height - 2, 0, "Press 'q' to quit", curses.color_pair(4))

class SimpleDashboard:
    """Simple text-based dashboard for environments without curses"""
    
    def __init__(self, dashboard: TestDashboard):
        self.dashboard = dashboard
        self.last_update = 0
        
    def update(self, force: bool = False):
        """Update dashboard display"""
        current_time = time.time()
        
        # Update every 2 seconds unless forced
        if not force and current_time - self.last_update < 2:
            return
        
        self.last_update = current_time
        data = self.dashboard.get_dashboard_data()
        
        # Clear screen (simple approach)
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print("🧪 Document-Slides-POC API Testing Dashboard")
        print("=" * 60)
        
        # Stats
        stats = data['stats']
        elapsed = data['elapsed_time']
        success_rate = data['success_rate']
        
        print(f"📊 Stats: {stats['completed']}/{stats['total_tests']} completed | "
              f"{stats['running']} running | {success_rate:.1f}% success | {elapsed:.1f}s elapsed")
        
        # Progress bar
        if stats['total_tests'] > 0:
            progress = stats['completed'] / stats['total_tests']
            bar_width = 40
            filled = int(progress * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)
            print(f"Progress: [{bar}] {progress*100:.1f}%")
        
        # Agent status
        print("\n🤖 Agents:")
        for agent_id, status_info in data['agent_status'].items():
            status = status_info['status']
            print(f"  {agent_id}: {status}")
        
        # Running tests
        if data['running_tests']:
            print(f"\n🏃 Running Tests ({len(data['running_tests'])}):")
            for test in data['running_tests'][:3]:
                duration = test['duration'] or 0
                files = ', '.join(test['files_used'][:2])
                print(f"  {test['agent_id']}: {test['test_name'][:35]} ({duration:.1f}s) [{files}]")
        
        # Recent errors
        if data['recent_errors']:
            print(f"\n❌ Recent Errors ({len(data['recent_errors'])}):")
            for error in data['recent_errors'][-2:]:
                print(f"  {error['agent_id']}: {error['test_name'][:30]}")
                print(f"    Error: {error['error'][:50]}...")
                print(f"    Files: {', '.join(error['files'][:2])}")

def create_dashboard(use_curses: bool = True) -> tuple:
    """Create dashboard components"""
    dashboard = TestDashboard()
    
    if use_curses:
        try:
            import curses
            display = ConsoleTestDashboard(dashboard)
            return dashboard, display
        except ImportError:
            print("Curses not available, using simple dashboard")
    
    display = SimpleDashboard(dashboard)
    return dashboard, display

def main():
    """Test the dashboard functionality"""
    dashboard, display = create_dashboard(use_curses=False)
    
    # Simulate test session
    dashboard.start_test_session(10)
    
    # Simulate some test activity
    dashboard.update_agent_status('agent_0', 'running')
    dashboard.update_agent_status('agent_1', 'running')
    
    dashboard.start_test('test_1', 'agent_0', 'health_check', [])
    time.sleep(0.5)
    dashboard.complete_test('test_1', True)
    
    dashboard.start_test('test_2', 'agent_1', 'slide_generation', ['budget_model.xlsx'], 'simple_template')
    time.sleep(1)
    dashboard.complete_test('test_2', False, "RGBColor attribute error")
    
    # Show final state
    if isinstance(display, SimpleDashboard):
        display.update(force=True)
        print("\nDashboard test completed!")

if __name__ == "__main__":
    main()