from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
import os

# Create a new document
doc = Document()

# Set document title
title = doc.add_heading('Team Piping Work Order & QC System', 0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

# Add version and company info
version_para = doc.add_paragraph('Version 2.0 - User Manual')
version_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
company_para = doc.add_paragraph('NAEC & MIE Partnership')
company_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

doc.add_page_break()

# Table of Contents
doc.add_heading('Table of Contents', level=1)
toc = doc.add_paragraph()
toc.add_run('1. Introduction\n')
toc.add_run('2. System Requirements\n')
toc.add_run('3. Installation & Setup\n')
toc.add_run('4. Getting Started\n')
toc.add_run('5. User Authentication & Permissions\n')
toc.add_run('6. Main Features\n')
toc.add_run('7. Module Descriptions\n')
toc.add_run('8. Reports & Documentation\n')
toc.add_run('9. Administrative Functions\n')
toc.add_run('10. Troubleshooting\n')
toc.add_run('11. Support & Maintenance\n')

doc.add_page_break()

# 1. Introduction
doc.add_heading('1. Introduction', level=1)
doc.add_paragraph(
    'The Team Piping Work Order & QC System is a comprehensive software solution designed for '
    'managing piping fabrication projects. This system provides end-to-end tracking of spool '
    'fabrication from initial fit-up through final delivery, including quality control processes, '
    'reporting, and project management capabilities.'
)

doc.add_heading('1.1 Purpose', level=2)
doc.add_paragraph(
    'This system is designed to streamline piping fabrication workflows by providing:'
)
features_list = doc.add_paragraph()
features_list.style = 'List Bullet'
features_list.add_run('• Real-time tracking of spool progress through fabrication stages\n')
features_list.add_run('• Quality control documentation and reporting\n')
features_list.add_run('• Project management and progress monitoring\n')
features_list.add_run('• Automated report generation\n')
features_list.add_run('• User access control and permissions management\n')
features_list.add_run('• Integration with existing workflows and templates')

doc.add_heading('1.2 Key Benefits', level=2)
benefits = doc.add_paragraph()
benefits.style = 'List Bullet'
benefits.add_run('• Improved project visibility and tracking\n')
benefits.add_run('• Standardized quality control processes\n')
benefits.add_run('• Reduced manual paperwork and data entry\n')
benefits.add_run('• Enhanced reporting capabilities\n')
benefits.add_run('• Better resource allocation and planning\n')
benefits.add_run('• Compliance with industry standards')

# 2. System Requirements
doc.add_heading('2. System Requirements', level=1)

doc.add_heading('2.1 Hardware Requirements', level=2)
hardware = doc.add_paragraph()
hardware.add_run('Minimum Requirements:\n').bold = True
hardware.add_run('• Processor: Intel Core i3 or equivalent\n')
hardware.add_run('• Memory: 4GB RAM\n')
hardware.add_run('• Storage: 2GB available space\n')
hardware.add_run('• Display: 1024x768 resolution\n\n')
hardware.add_run('Recommended Requirements:\n').bold = True
hardware.add_run('• Processor: Intel Core i5 or higher\n')
hardware.add_run('• Memory: 8GB RAM or more\n')
hardware.add_run('• Storage: 10GB available space\n')
hardware.add_run('• Display: 1920x1080 resolution or higher')

doc.add_heading('2.2 Software Requirements', level=2)
software = doc.add_paragraph()
software.add_run('• Operating System: Windows 10 or later\n')
software.add_run('• Microsoft Office Excel (for report templates)\n')
software.add_run('• PDF viewer (for generated reports)\n')
software.add_run('• Network connection (for database synchronization)')

# 3. Installation & Setup
doc.add_heading('3. Installation & Setup', level=1)

doc.add_heading('3.1 Installation Process', level=2)
installation = doc.add_paragraph()
installation.add_run('Step 1: ').bold = True
installation.add_run('Download the TeamPiping.exe installer from the provided location.\n')
installation.add_run('Step 2: ').bold = True
installation.add_run('Run the installer as Administrator (right-click → Run as administrator).\n')
installation.add_run('Step 3: ').bold = True
installation.add_run('Follow the installation wizard prompts.\n')
installation.add_run('Step 4: ').bold = True
installation.add_run('Choose the installation directory (default is recommended).\n')
installation.add_run('Step 5: ').bold = True
installation.add_run('Wait for the installation to complete.\n')
installation.add_run('Step 6: ').bold = True
installation.add_run('Launch the application from the desktop shortcut or Start menu.')

doc.add_heading('3.2 Initial Configuration', level=2)
config = doc.add_paragraph()
config.add_run('Upon first launch:\n').bold = True
config.add_run('1. The system will initialize the database automatically\n')
config.add_run('2. Default user accounts and templates will be set up\n')
config.add_run('3. Contact your system administrator for initial login credentials\n')
config.add_run('4. Configure project-specific settings through the administrative interface')

# 4. Getting Started
doc.add_heading('4. Getting Started', level=1)

doc.add_heading('4.1 First Login', level=2)
first_login = doc.add_paragraph()
first_login.add_run('1. Launch the Team Piping application\n')
first_login.add_run('2. Enter your username and password in the login screen\n')
first_login.add_run('3. Click "Sign In" to access the system\n')
first_login.add_run('4. The dashboard will load showing your available modules based on permissions')

doc.add_heading('4.2 Main Interface Overview', level=2)
interface = doc.add_paragraph()
interface.add_run('The main interface consists of:\n').bold = True
interface.add_run('• Header: Contains company logos and user information\n')
interface.add_run('• Tab Navigation: Access to different modules based on your permissions\n')
interface.add_run('• Main Content Area: Where module-specific content is displayed\n')
interface.add_run('• Status Bar: Shows current user and connection status')

# 5. User Authentication & Permissions
doc.add_heading('5. User Authentication & Permissions', level=1)

doc.add_heading('5.1 User Roles', level=2)
roles = doc.add_paragraph()
roles.add_run('The system supports multiple user roles:\n').bold = True
roles.add_run('• Fit-Up Personnel: Can update fit-up status and records\n')
roles.add_run('• Welding Personnel: Can update welding progress and documentation\n')
roles.add_run('• Quality Control: Can access QC reports and inspection modules\n')
roles.add_run('• Project Management: Can access project summaries and manpower reports\n')
roles.add_run('• Administrators: Full system access including inventory and user management\n')
roles.add_run('• Painting/Delivery: Can update painting and delivery status')

doc.add_heading('5.2 Permission Matrix', level=2)
permissions_table = doc.add_table(rows=8, cols=3)
permissions_table.style = 'Table Grid'
hdr_cells = permissions_table.rows[0].cells
hdr_cells[0].text = 'Module'
hdr_cells[1].text = 'Required Permission'
hdr_cells[2].text = 'Description'

rows_data = [
    ['Update Fit-Up', 'fitup', 'Allows updating spool fit-up status and records'],
    ['Update Welding', 'welding', 'Allows updating welding progress and documentation'],
    ['QC Reports', 'qc', 'Access to all quality control reports and inspections'],
    ['Project Summary', 'pmt', 'Access to project management and summary reports'],
    ['Inventory Tools', 'admin', 'Administrative functions and inventory management'],
    ['Manpower Report', 'manpower', 'Access to manpower allocation and tracking'],
    ['All Access', 'all', 'Complete system access (super admin)']
]

for i, (module, permission, description) in enumerate(rows_data, 1):
    row_cells = permissions_table.rows[i].cells
    row_cells[0].text = module
    row_cells[1].text = permission
    row_cells[2].text = description

# 6. Main Features
doc.add_heading('6. Main Features', level=1)

doc.add_heading('6.1 Dashboard', level=2)
dashboard = doc.add_paragraph()
dashboard.add_run('The Dashboard provides:\n').bold = True
dashboard.add_run('• Real-time project statistics and KPIs\n')
dashboard.add_run('• Progress visualization charts and graphs\n')
dashboard.add_run('• Recent activity timeline\n')
dashboard.add_run('• Quick access to critical notifications\n')
dashboard.add_run('• Summary of pending tasks and deliverables')

doc.add_heading('6.2 Spool Tracking', level=2)
tracking = doc.add_paragraph()
tracking.add_run('Comprehensive tracking through fabrication stages:\n').bold = True
tracking.add_run('• Fit-Up: Initial assembly and alignment\n')
tracking.add_run('• Welding: Welding progress and quality checks\n')
tracking.add_run('• Painting: Surface preparation and coating application\n')
tracking.add_run('• Site Delivery: Final inspection and delivery tracking\n')
tracking.add_run('• Real-time status updates and progress monitoring')

doc.add_heading('6.3 Quality Control', level=2)
qc = doc.add_paragraph()
qc.add_run('Integrated QC processes include:\n').bold = True
qc.add_run('• Visual Inspection Reports\n')
qc.add_run('• Radiographic Testing (RT) - Both BSR and ASR\n')
qc.add_run('• Post-Weld Heat Treatment (PWHT) documentation\n')
qc.add_run('• Non-Destructive Testing (NDT) reports\n')
qc.add_run('• Inspection Request Notes (IRN) management\n')
qc.add_run('• Automated report generation and distribution')

# 7. Module Descriptions
doc.add_heading('7. Module Descriptions', level=1)

modules = [
    ('Dashboard', '📊', 'Central overview of project status, statistics, and key performance indicators'),
    ('Update Fit-Up', '🔧', 'Record and update spool fit-up progress, including measurements and quality checks'),
    ('Update Welding', '⚡', 'Track welding progress, welder assignments, and welding procedure compliance'),
    ('Painting Delivery', '🎨', 'Manage painting schedules, surface preparation, and coating applications'),
    ('Site Delivery', '🚚', 'Track final inspections, delivery schedules, and site handover documentation'),
    ('Fit-Up Report', '📋', 'Generate detailed fit-up status reports and progress summaries'),
    ('Visual Report', '👁️', 'Create and manage visual inspection reports with photo documentation'),
    ('RT BSR', '🔬', 'Radiographic Testing - Before Service Release documentation'),
    ('PWHT Report', '🔥', 'Post-Weld Heat Treatment tracking and certification'),
    ('RT ASR', '📊', 'Radiographic Testing - After Service Release documentation'),
    ('NDT Report', '🔍', 'Non-Destructive Testing reports and certifications'),
    ('IRN Report', '📝', 'Inspection Request Notes management and tracking'),
    ('ISO Drawing', '📐', 'Isometric drawing management and revision control'),
    ('Generate Reports', '📊', 'Automated report generation for various project requirements'),
    ('Project Summary', '📈', 'High-level project overview, progress tracking, and milestone management'),
    ('Inventory Tools', '📦', 'Material tracking, inventory management, and procurement support'),
    ('Manpower Report', '👷', 'Workforce allocation, productivity tracking, and resource planning')
]

for module_name, icon, description in modules:
    doc.add_heading(f'{icon} {module_name}', level=2)
    doc.add_paragraph(description)

# 8. Reports & Documentation
doc.add_heading('8. Reports & Documentation', level=1)

doc.add_heading('8.1 Available Reports', level=2)
reports = doc.add_paragraph()
reports.add_run('The system generates various reports:\n').bold = True
reports.add_run('• Daily Progress Reports\n')
reports.add_run('• Weekly Summary Reports\n')
reports.add_run('• QC Inspection Reports\n')
reports.add_run('• Material Tracking Reports\n')
reports.add_run('• Manpower Utilization Reports\n')
reports.add_run('• Project Milestone Reports\n')
reports.add_run('• Custom Ad-hoc Reports')

doc.add_heading('8.2 Report Templates', level=2)
templates = doc.add_paragraph()
templates.add_run('Standard templates are included for:\n').bold = True
templates.add_run('• Excel-based reports with charts and formatting\n')
templates.add_run('• PDF documents for official submissions\n')
templates.add_run('• Email-ready summaries\n')
templates.add_run('• Custom branding and company logos\n')
templates.add_run('• Regulatory compliance formats')

# 9. Administrative Functions
doc.add_heading('9. Administrative Functions', level=1)

doc.add_heading('9.1 User Management', level=2)
user_mgmt = doc.add_paragraph()
user_mgmt.add_run('Administrative capabilities include:\n').bold = True
user_mgmt.add_run('• Creating and managing user accounts\n')
user_mgmt.add_run('• Assigning permissions and roles\n')
user_mgmt.add_run('• Monitoring user activity and login sessions\n')
user_mgmt.add_run('• Password reset and security management\n')
user_mgmt.add_run('• Audit trail and access logging')

doc.add_heading('9.2 System Configuration', level=2)
sys_config = doc.add_paragraph()
sys_config.add_run('Configure system settings for:\n').bold = True
sys_config.add_run('• Database connections and backups\n')
sys_config.add_run('• Report templates and formats\n')
sys_config.add_run('• Email notifications and alerts\n')
sys_config.add_run('• Integration with external systems\n')
sys_config.add_run('• Customization of workflows and processes')

# 10. Troubleshooting
doc.add_heading('10. Troubleshooting', level=1)

doc.add_heading('10.1 Common Issues', level=2)
issues_table = doc.add_table(rows=6, cols=3)
issues_table.style = 'Table Grid'
issue_hdr = issues_table.rows[0].cells
issue_hdr[0].text = 'Issue'
issue_hdr[1].text = 'Cause'
issue_hdr[2].text = 'Solution'

issues_data = [
    ['Login Failed', 'Invalid credentials', 'Verify username/password with administrator'],
    ['Database Error', 'Connection issue', 'Check network connectivity and database server'],
    ['Report Generation Failed', 'Template missing', 'Ensure all report templates are in correct folder'],
    ['Slow Performance', 'Large dataset', 'Contact administrator for database optimization'],
    ['Permission Denied', 'Insufficient access', 'Request appropriate permissions from administrator']
]

for i, (issue, cause, solution) in enumerate(issues_data, 1):
    row = issues_table.rows[i].cells
    row[0].text = issue
    row[1].text = cause
    row[2].text = solution

doc.add_heading('10.2 System Logs', level=2)
logs = doc.add_paragraph()
logs.add_run('System maintains logs for:\n').bold = True
logs.add_run('• User login/logout activities\n')
logs.add_run('• Database operations and queries\n')
logs.add_run('• Report generation activities\n')
logs.add_run('• Error messages and exceptions\n')
logs.add_run('• System performance metrics')

# 11. Support & Maintenance
doc.add_heading('11. Support & Maintenance', level=1)

doc.add_heading('11.1 Getting Help', level=2)
support = doc.add_paragraph()
support.add_run('For technical support:\n').bold = True
support.add_run('• Contact your system administrator first\n')
support.add_run('• Refer to this user manual for guidance\n')
support.add_run('• Check system logs for error messages\n')
support.add_run('• Document any recurring issues for analysis\n')
support.add_run('• Provide detailed information when requesting support')

doc.add_heading('11.2 System Maintenance', level=2)
maintenance = doc.add_paragraph()
maintenance.add_run('Regular maintenance includes:\n').bold = True
maintenance.add_run('• Database backups and integrity checks\n')
maintenance.add_run('• Software updates and patches\n')
maintenance.add_run('• Performance monitoring and optimization\n')
maintenance.add_run('• User account cleanup and security reviews\n')
maintenance.add_run('• Report template updates and customizations')

doc.add_heading('11.3 Best Practices', level=2)
best_practices = doc.add_paragraph()
best_practices.add_run('To ensure optimal system performance:\n').bold = True
best_practices.add_run('• Log out properly when finished\n')
best_practices.add_run('• Keep login credentials secure\n')
best_practices.add_run('• Report any unusual system behavior\n')
best_practices.add_run('• Use standard workflows and procedures\n')
best_practices.add_run('• Regular training on new features and updates')

# Add footer
doc.add_page_break()
footer_para = doc.add_paragraph()
footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
footer_para.add_run('Team Piping Work Order & QC System\n').bold = True
footer_para.add_run('User Manual - Version 2.0\n')
footer_para.add_run('© NAEC & MIE Partnership\n')
footer_para.add_run('For internal use only')

# Save the document
output_file = 'Team_Piping_User_Manual.docx'
doc.save(output_file)
print(f'User manual created successfully: {output_file}')