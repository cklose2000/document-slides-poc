Sample Data for Document Extraction Testing
===========================================

This directory contains comprehensive test documents for validating 
document extraction functionality across PDF, Excel, and Word formats.

Files:
------

📊 sample_financial_comprehensive.xlsx
   - Multi-sheet Excel workbook with financial data
   - Contains formulas, cross-sheet references, and complex calculations
   - Sheets: Financial Summary, Quarterly Performance, Regional Performance, KPIs Dashboard
   - Tests: Formula parsing, cell referencing, source attribution

📄 sample_business_plan_comprehensive.docx  
   - Comprehensive business plan document
   - Contains headers, tables, financial projections, and structured content
   - Tests: Heading extraction, table parsing, paragraph structure, section identification

📈 sample_simple.xlsx
   - Basic Excel file with simple data structure
   - Tests: Basic extraction, cell values, simple formulas

📝 sample_simple.docx
   - Simple Word document with basic structure
   - Tests: Basic extraction, simple tables, heading detection

Test Data Values:
----------------

Excel Financial Data:
- Total Revenue: $12,500,000
- Gross Profit: $7,500,000  
- Net Income: $2,250,000
- EBITDA: $3,125,000
- Q1 Revenue: $3,000,000
- Q2 Revenue: $3,200,000
- Q3 Revenue: $3,100,000
- Q4 Revenue: $3,200,000

Word Business Plan Data:
- Projected 2024 Revenue: $18.5M
- Projected Net Income: $3.7M
- Market Size: $125B (2023)
- Growth Rate: 48%
- Employee Target: 185 (2024)

Usage:
------
These documents are used by the test suite to validate:
1. Accurate data extraction
2. Source attribution and tracking
3. Formula and calculation handling
4. Table and structure parsing
5. Cross-reference resolution
6. Error handling and edge cases

The test suite automatically loads these documents and validates that
extraction results match expected values and maintain proper source
attribution for slide generation.
