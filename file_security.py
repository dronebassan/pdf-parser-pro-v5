"""
File security and malware scanning
"""

import hashlib
import magic
import os
import subprocess
import tempfile
import zipfile
import tarfile
from typing import Optional, Dict, List
import requests
from pathlib import Path

class FileSecurityScanner:
    def __init__(self):
        # Maximum file sizes
        self.MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
        self.MAX_PAGE_COUNT = 500
        
        # Allowed file types
        self.ALLOWED_MIME_TYPES = {
            'application/pdf',
            'application/x-pdf',
        }
        
        # Known malicious file signatures (hexadecimal)
        self.MALICIOUS_SIGNATURES = {
            # Common malware signatures
            'b64d4c0d': 'Potential malware header',
            '4d5a': 'Windows PE executable (suspicious in PDF)',
            '7f454c46': 'Linux ELF executable (suspicious in PDF)',
        }
        
        # Suspicious PDF patterns
        self.SUSPICIOUS_PDF_PATTERNS = [
            b'/JavaScript',  # Embedded JavaScript
            b'/JS',         # JavaScript shorthand
            b'/Launch',     # Launch external apps
            b'/EmbeddedFile', # Embedded files
            b'/XFA',        # Adobe XML Forms (can be exploited)
            b'/RichMedia',  # Rich media content
            b'/3D',         # 3D content
            b'/Sound',      # Audio files
            b'/Movie',      # Video files
        ]
    
    def scan_file(self, file_path: str) -> Dict[str, any]:
        """Comprehensive file security scan"""
        
        scan_result = {
            'safe': True,
            'issues': [],
            'warnings': [],
            'file_info': {},
            'risk_score': 0
        }
        
        try:
            # Basic file checks
            self._check_file_size(file_path, scan_result)
            self._check_file_type(file_path, scan_result)
            self._check_file_structure(file_path, scan_result)
            
            # PDF-specific security checks
            if scan_result['file_info'].get('mime_type', '').startswith('application/pdf'):
                self._scan_pdf_content(file_path, scan_result)
                self._check_pdf_metadata(file_path, scan_result)
            
            # Malware signature check
            self._scan_for_malware_signatures(file_path, scan_result)
            
            # Calculate risk score
            scan_result['risk_score'] = self._calculate_risk_score(scan_result)
            
            # Final safety determination
            scan_result['safe'] = scan_result['risk_score'] < 50 and len([i for i in scan_result['issues'] if i['severity'] == 'critical']) == 0
            
        except Exception as e:
            scan_result['safe'] = False
            scan_result['issues'].append({
                'type': 'scan_error',
                'severity': 'critical',
                'message': f'File scanning failed: {str(e)}'
            })
        
        return scan_result
    
    def _check_file_size(self, file_path: str, result: Dict):
        """Check file size limits"""
        file_size = os.path.getsize(file_path)
        result['file_info']['size_bytes'] = file_size
        result['file_info']['size_mb'] = round(file_size / (1024 * 1024), 2)
        
        if file_size > self.MAX_FILE_SIZE:
            result['issues'].append({
                'type': 'file_too_large',
                'severity': 'critical',
                'message': f'File size {result["file_info"]["size_mb"]}MB exceeds limit of {self.MAX_FILE_SIZE // (1024*1024)}MB'
            })
        elif file_size < 100:  # Less than 100 bytes is suspicious
            result['warnings'].append({
                'type': 'file_too_small',
                'message': f'File is very small ({file_size} bytes) - may be corrupted'
            })
    
    def _check_file_type(self, file_path: str, result: Dict):
        """Validate file type and MIME type"""
        try:
            # Check MIME type
            mime_type = magic.from_file(file_path, mime=True)
            result['file_info']['mime_type'] = mime_type
            
            # Check if allowed MIME type
            if mime_type not in self.ALLOWED_MIME_TYPES:
                result['issues'].append({
                    'type': 'invalid_file_type',
                    'severity': 'critical',
                    'message': f'File type {mime_type} not allowed. Only PDF files accepted.'
                })
            
            # Check file extension matches content
            file_extension = Path(file_path).suffix.lower()
            if file_extension not in ['.pdf'] and mime_type.startswith('application/pdf'):
                result['warnings'].append({
                    'type': 'extension_mismatch',
                    'message': f'File extension {file_extension} does not match PDF content'
                })
                
        except Exception as e:
            result['issues'].append({
                'type': 'file_type_check_failed',
                'severity': 'warning',
                'message': f'Could not determine file type: {str(e)}'
            })
    
    def _check_file_structure(self, file_path: str, result: Dict):
        """Check file structure integrity"""
        try:
            # Try to open as PDF to check structure
            import fitz  # PyMuPDF
            
            with fitz.open(file_path) as pdf_doc:
                page_count = len(pdf_doc)
                result['file_info']['page_count'] = page_count
                
                # Check page count limits
                if page_count > self.MAX_PAGE_COUNT:
                    result['issues'].append({
                        'type': 'too_many_pages',
                        'severity': 'warning',
                        'message': f'PDF has {page_count} pages, exceeds recommended limit of {self.MAX_PAGE_COUNT}'
                    })
                
                # Check for password protection
                if pdf_doc.needs_pass:
                    result['issues'].append({
                        'type': 'password_protected',
                        'severity': 'critical',
                        'message': 'Password-protected PDFs are not supported for security reasons'
                    })
                
                # Check metadata
                metadata = pdf_doc.metadata
                if metadata:
                    result['file_info']['metadata'] = {
                        'title': metadata.get('title', ''),
                        'author': metadata.get('author', ''),
                        'creator': metadata.get('creator', ''),
                        'producer': metadata.get('producer', ''),
                        'creation_date': metadata.get('creationDate', ''),
                        'modification_date': metadata.get('modDate', '')
                    }
                
        except Exception as e:
            result['issues'].append({
                'type': 'pdf_structure_invalid',
                'severity': 'critical',
                'message': f'Invalid PDF structure: {str(e)}'
            })
    
    def _scan_pdf_content(self, file_path: str, result: Dict):
        """Scan PDF for suspicious content"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Check for suspicious patterns
            for pattern in self.SUSPICIOUS_PDF_PATTERNS:
                if pattern in content:
                    pattern_name = pattern.decode('utf-8', errors='ignore')
                    result['warnings'].append({
                        'type': 'suspicious_content',
                        'message': f'PDF contains potentially risky content: {pattern_name}'
                    })
            
            # Check for excessive object count (can indicate malware)
            object_count = content.count(b'obj')
            result['file_info']['pdf_objects'] = object_count
            
            if object_count > 10000:  # Arbitrary threshold
                result['warnings'].append({
                    'type': 'excessive_objects',
                    'message': f'PDF contains {object_count} objects, which is unusually high'
                })
            
            # Check for suspicious URLs
            url_patterns = [b'http://', b'https://', b'ftp://']
            urls_found = []
            for pattern in url_patterns:
                if pattern in content:
                    urls_found.append(pattern.decode())
            
            if urls_found:
                result['file_info']['contains_urls'] = True
                result['warnings'].append({
                    'type': 'contains_urls',
                    'message': f'PDF contains URLs: {urls_found}'
                })
                
        except Exception as e:
            result['warnings'].append({
                'type': 'content_scan_failed',
                'message': f'Could not scan PDF content: {str(e)}'
            })
    
    def _check_pdf_metadata(self, file_path: str, result: Dict):
        """Check PDF metadata for suspicious indicators"""
        metadata = result['file_info'].get('metadata', {})
        
        # Check for suspicious creators/producers
        suspicious_creators = [
            'malware', 'virus', 'trojan', 'exploit', 'hack'
        ]
        
        creator = metadata.get('creator', '').lower()
        producer = metadata.get('producer', '').lower()
        
        for suspicious in suspicious_creators:
            if suspicious in creator or suspicious in producer:
                result['warnings'].append({
                    'type': 'suspicious_metadata',
                    'message': f'PDF metadata contains suspicious terms in creator/producer fields'
                })
                break
        
        # Check for very old creation dates (could indicate template reuse)
        creation_date = metadata.get('creation_date', '')
        if creation_date and '199' in creation_date:  # Files from 1990s
            result['warnings'].append({
                'type': 'old_creation_date',
                'message': f'PDF has very old creation date: {creation_date}'
            })
    
    def _scan_for_malware_signatures(self, file_path: str, result: Dict):
        """Scan file for known malware signatures"""
        try:
            with open(file_path, 'rb') as f:
                # Read first 1MB for signature checking
                content = f.read(1024 * 1024)
            
            # Convert to hex for signature matching
            hex_content = content.hex()
            
            for signature, description in self.MALICIOUS_SIGNATURES.items():
                if signature in hex_content:
                    result['issues'].append({
                        'type': 'malware_signature',
                        'severity': 'critical',
                        'message': f'Malware signature detected: {description}'
                    })
            
        except Exception as e:
            result['warnings'].append({
                'type': 'signature_scan_failed',
                'message': f'Malware signature scan failed: {str(e)}'
            })
    
    def _calculate_risk_score(self, result: Dict) -> int:
        """Calculate overall risk score (0-100)"""
        score = 0
        
        # Critical issues
        critical_issues = [i for i in result['issues'] if i['severity'] == 'critical']
        score += len(critical_issues) * 30
        
        # Warning issues
        warning_issues = [i for i in result['issues'] if i['severity'] == 'warning']
        score += len(warning_issues) * 10
        
        # Warnings
        score += len(result['warnings']) * 5
        
        # File size factor
        file_size_mb = result['file_info'].get('size_mb', 0)
        if file_size_mb > 50:
            score += 10
        
        # Page count factor
        page_count = result['file_info'].get('page_count', 0)
        if page_count > 100:
            score += 5
        
        return min(score, 100)  # Cap at 100
    
    def quarantine_file(self, file_path: str, reason: str) -> str:
        """Move suspicious file to quarantine"""
        quarantine_dir = "/tmp/quarantine"
        os.makedirs(quarantine_dir, exist_ok=True)
        
        # Generate unique quarantine filename
        file_hash = hashlib.md5(open(file_path, 'rb').read()).hexdigest()
        quarantine_path = os.path.join(quarantine_dir, f"{file_hash}_{int(time.time())}.quarantined")
        
        # Move file to quarantine
        os.rename(file_path, quarantine_path)
        
        # Log quarantine event
        with open(os.path.join(quarantine_dir, "quarantine.log"), "a") as log:
            log.write(f"{time.time()},{file_hash},{reason}\n")
        
        return quarantine_path

# Integration with FastAPI
class SecureFileHandler:
    def __init__(self):
        self.scanner = FileSecurityScanner()
    
    def validate_uploaded_file(self, file_path: str, filename: str) -> Dict:
        """Validate uploaded file before processing"""
        
        # Scan file
        scan_result = self.scanner.scan_file(file_path)
        
        # Log scan result
        self._log_file_scan(filename, scan_result)
        
        if not scan_result['safe']:
            # Quarantine unsafe file
            quarantine_path = self.scanner.quarantine_file(
                file_path, 
                f"Risk score: {scan_result['risk_score']}, Issues: {len(scan_result['issues'])}"
            )
            
            # Return security error
            return {
                'valid': False,
                'error': 'File failed security scan',
                'details': scan_result['issues'],
                'risk_score': scan_result['risk_score']
            }
        
        return {
            'valid': True,
            'warnings': scan_result['warnings'],
            'risk_score': scan_result['risk_score'],
            'file_info': scan_result['file_info']
        }
    
    def _log_file_scan(self, filename: str, scan_result: Dict):
        """Log file scan results for security monitoring"""
        import json
        import time
        
        log_entry = {
            'timestamp': time.time(),
            'filename': filename,
            'safe': scan_result['safe'],
            'risk_score': scan_result['risk_score'],
            'issues_count': len(scan_result['issues']),
            'warnings_count': len(scan_result['warnings']),
            'file_size': scan_result['file_info'].get('size_bytes', 0)
        }
        
        # In production, send to logging service
        print(f"📁 File Scan: {filename} - Safe: {scan_result['safe']} - Risk: {scan_result['risk_score']}")

# Global file handler
secure_file_handler = SecureFileHandler()