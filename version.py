"""
Version Manager - System Version Tracking
Tracks API versions and compatibility
Version: 31.0
"""

from datetime import datetime
from typing import Dict, Any, List
import json
import logging

logger = logging.getLogger(__name__)


class VersionManager:
    """Manage API versions and compatibility"""
    
    CURRENT_VERSION = "31.0.0"
    API_VERSION = "v1"
    RELEASE_DATE = "2026-05-31"
    
    VERSION_HISTORY = [
        {"version": "31.0.0", "date": "2026-05-31", "changes": ["Initial production release", "Sovereign Grid launch"]},
        {"version": "30.0.0", "date": "2026-05-15", "changes": ["Billion-user scale architecture", "Edge-native consensus grid"]},
        {"version": "25.0.0", "date": "2026-04-01", "changes": ["Multi-tenant hierarchy", "Budget enforcement"]},
        {"version": "20.0.0", "date": "2026-03-01", "changes": ["Lockless ring buffer", "CRDT implementation"]}
    ]
    
    DEPRECATED_VERSIONS = ["v0.1.0", "v1.0.0"]
    
    @classmethod
    def get_version_info(cls) -> Dict[str, Any]:
        """Get current version information"""
        return {
            "current_version": cls.CURRENT_VERSION,
            "api_version": cls.API_VERSION,
            "release_date": cls.RELEASE_DATE,
            "status": "stable",
            "deprecated": cls.DEPRECATED_VERSIONS
        }
    
    @classmethod
    def get_version_history(cls, limit: int = 10) -> List[Dict]:
        """Get version history"""
        return cls.VERSION_HISTORY[:limit]
    
    @classmethod
    def check_compatibility(cls, client_version: str) -> Dict[str, Any]:
        """
        Check if a client version is compatible
        
        Returns:
            Compatibility result with upgrade recommendation
        """
        # Parse versions (simplified)
        def parse_version(v: str) -> tuple:
            parts = v.replace('v', '').split('.')
            return tuple(int(p) for p in parts[:3])
        
        current = parse_version(cls.CURRENT_VERSION)
        client = parse_version(client_version)
        
        is_compatible = client[0] == current[0]  # Same major version
        
        return {
            "compatible": is_compatible,
            "client_version": client_version,
            "server_version": cls.CURRENT_VERSION,
            "upgrade_required": not is_compatible,
            "recommended_version": cls.CURRENT_VERSION if not is_compatible else None,
            "deprecation_notice": client_version in cls.DEPRECATED_VERSIONS
        }
    
    @classmethod
    def get_release_notes(cls, version: str = None) -> str:
        """Get release notes for a version"""
        target = version or cls.CURRENT_VERSION
        
        for v in cls.VERSION_HISTORY:
            if v["version"] == target:
                notes = f"## Release {v['version']} ({v['date']})\n\n"
                for change in v["changes"]:
                    notes += f"- {change}\n"
                return notes
        
        return f"Release notes not found for version {target}"
