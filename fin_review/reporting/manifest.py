"""Reproducibility manifest generation module."""

import json
import hashlib
import structlog
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import platform

logger = structlog.get_logger()


class ManifestGenerator:
    """Generates reproducibility manifest for audit trail."""
    
    def __init__(self, output_path: Path, config: Optional[Dict] = None):
        """
        Initialize manifest generator.
        
        Args:
            output_path: Path to output manifest JSON file
            config: Configuration dictionary
        """
        self.output_path = output_path
        self.config = config or {}
    
    def generate_manifest(
        self,
        input_files: Dict[str, Path],
        validation_result: Dict,
        processing_stats: Dict,
        config_snapshot: Dict
    ) -> Dict:
        """
        Generate reproducibility manifest.
        
        Args:
            input_files: Dictionary of input file paths {name: path}
            validation_result: Validation result dictionary
            processing_stats: Processing statistics
            config_snapshot: Configuration snapshot
        
        Returns:
            Manifest dictionary
        """
        logger.info("Generating reproducibility manifest")
        
        manifest = {
            'metadata': self._generate_metadata(),
            'input_files': self._generate_file_info(input_files),
            'validation': validation_result,
            'processing_stats': processing_stats,
            'configuration': config_snapshot,
            'environment': self._generate_environment_info()
        }
        
        # Save manifest
        with open(self.output_path, 'w') as f:
            json.dump(manifest, f, indent=2, default=str)
        
        logger.info(f"Manifest generated: {self.output_path}")
        
        return manifest
    
    def _generate_metadata(self) -> Dict:
        """Generate metadata section."""
        return {
            'generated_at': datetime.now().isoformat(),
            'manifest_version': '1.0',
            'pipeline_version': '1.0.0'
        }
    
    def _generate_file_info(self, files: Dict[str, Path]) -> Dict:
        """Generate file information with checksums."""
        if not self.config.get('calculate_checksums', True):
            return {name: {'path': str(path)} for name, path in files.items()}
        
        file_info = {}
        
        for name, path in files.items():
            if not path.exists():
                logger.warning(f"File not found: {path}")
                file_info[name] = {
                    'path': str(path),
                    'exists': False
                }
                continue
            
            # Calculate checksums
            md5_hash = self._calculate_md5(path)
            sha256_hash = self._calculate_sha256(path)
            
            file_info[name] = {
                'path': str(path),
                'exists': True,
                'size_bytes': path.stat().st_size,
                'modified_at': datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
                'md5': md5_hash,
                'sha256': sha256_hash
            }
        
        return file_info
    
    def _calculate_md5(self, file_path: Path) -> str:
        """Calculate MD5 checksum of file."""
        try:
            md5 = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    md5.update(chunk)
            return md5.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating MD5 for {file_path}: {e}")
            return "error"
    
    def _calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file."""
        try:
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating SHA256 for {file_path}: {e}")
            return "error"
    
    def _generate_environment_info(self) -> Dict:
        """Generate environment information."""
        import sys
        
        return {
            'python_version': sys.version,
            'platform': platform.platform(),
            'system': platform.system(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'hostname': platform.node()
        }


def generate_manifest(
    output_path: Path,
    input_files: Dict[str, Path],
    validation_result: Dict,
    processing_stats: Dict,
    config_snapshot: Dict,
    config: Optional[Dict] = None
) -> Dict:
    """
    Convenience function to generate manifest.
    
    Args:
        output_path: Path to output manifest file
        input_files: Input file paths
        validation_result: Validation results
        processing_stats: Processing statistics
        config_snapshot: Configuration snapshot
        config: Configuration dictionary
    
    Returns:
        Manifest dictionary
    """
    generator = ManifestGenerator(output_path, config)
    return generator.generate_manifest(
        input_files,
        validation_result,
        processing_stats,
        config_snapshot
    )

