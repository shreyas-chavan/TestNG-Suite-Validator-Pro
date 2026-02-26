#!/usr/bin/env python3
"""
Maven Metadata Extractor.
Extracts class/method/parameter information from Maven .m2 repository JARs
and standalone JAR files for semantic validation of TestNG XML suites.
"""

import os
import json
import zipfile
import logging
from typing import Dict, List, Optional, Callable

logger = logging.getLogger(__name__)

# Lazy import for jawa (optional heavy dependency)
_jawa_available = None


def _check_jawa() -> bool:
    """Check if jawa library is available."""
    global _jawa_available
    if _jawa_available is None:
        try:
            from jawa.classfile import ClassFile
            from jawa.util.descriptor import method_descriptor
            _jawa_available = True
        except ImportError:
            _jawa_available = False
            logger.warning("jawa library not available. Install: pip install jawa")
    return _jawa_available


class MavenMetadataExtractor:
    """
    Extract class/method metadata from Maven repository JARs.

    Can scan:
    - Individual JAR files
    - Folders containing JARs
    - Maven .m2 repository by group/artifact coordinates
    """

    def __init__(self, m2_repo_path: Optional[str] = None):
        """
        Initialize the extractor.

        Args:
            m2_repo_path: Custom Maven repository path.
                          Defaults to ~/.m2/repository
        """
        if m2_repo_path is None:
            home = os.path.expanduser("~")
            self.m2_repo = os.path.join(home, ".m2", "repository")
        else:
            self.m2_repo = m2_repo_path

        self.metadata: Dict[str, dict] = {}
        logger.info("Maven repository path: %s", self.m2_repo)

    def find_jars(
        self,
        group_id: Optional[str] = None,
        artifact_id: Optional[str] = None,
    ) -> List[str]:
        """
        Find JAR files in Maven repository.

        Args:
            group_id: Maven group ID (e.g., com.example)
            artifact_id: Maven artifact ID (e.g., my-project)

        Returns:
            List of JAR file paths
        """
        jars: List[str] = []

        if group_id and artifact_id:
            group_path = group_id.replace('.', os.sep)
            search_path = os.path.join(self.m2_repo, group_path, artifact_id)

            if os.path.exists(search_path):
                for root, _, files in os.walk(search_path):
                    for file in files:
                        if (file.endswith('.jar')
                                and not file.endswith('-sources.jar')
                                and not file.endswith('-javadoc.jar')):
                            jars.append(os.path.join(root, file))
            else:
                logger.warning("Maven path not found: %s", search_path)
        else:
            if not os.path.exists(self.m2_repo):
                logger.warning("Maven repository not found: %s", self.m2_repo)
                return jars
            for root, _, files in os.walk(self.m2_repo):
                for file in files:
                    if file.endswith('.jar') and not file.endswith('-sources.jar'):
                        jars.append(os.path.join(root, file))

        logger.info("Found %d JAR files", len(jars))
        return jars

    def extract_from_jar(
        self,
        jar_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Dict[str, dict]:
        """
        Extract class/method metadata from a single JAR file.

        Args:
            jar_path: Path to the JAR file
            progress_callback: Optional (current, total) callback for progress

        Returns:
            Dict mapping fully-qualified class names to their metadata
        """
        if not _check_jawa():
            logger.error("Cannot extract JAR metadata: jawa library not installed")
            return {}

        from jawa.classfile import ClassFile
        from jawa.util.descriptor import method_descriptor

        metadata: Dict[str, dict] = {}

        try:
            with zipfile.ZipFile(jar_path, 'r') as jar:
                class_files = [f for f in jar.filelist if f.filename.endswith('.class')]

                for idx, file_info in enumerate(class_files):
                    if progress_callback:
                        progress_callback(idx, len(class_files))

                    try:
                        class_data = jar.read(file_info.filename)
                        cf = ClassFile(class_data)
                        class_name = cf.this.name.value.replace('/', '.')

                        methods: Dict[str, dict] = {}
                        for method in cf.methods:
                            if method.name.value.startswith('<'):
                                continue

                            annotations: List[str] = []
                            for attr in method.attributes:
                                if hasattr(attr, 'annotations'):
                                    for ann in attr.annotations:
                                        ann_name = str(ann.type.name.value)
                                        annotations.append(ann_name)

                            try:
                                desc = method_descriptor(method.descriptor.value)
                                params = []
                                for i, param_type in enumerate(desc.args):
                                    param_type_str = str(param_type)
                                    if param_type_str.startswith('L') and param_type_str.endswith(';'):
                                        param_type_str = param_type_str[1:-1].replace('/', '.')
                                    params.append({
                                        'name': f'arg{i}',
                                        'type': param_type_str,
                                    })

                                return_type = str(desc.returns)
                                if return_type.startswith('L') and return_type.endswith(';'):
                                    return_type = return_type[1:-1].replace('/', '.')

                                is_test = any('Test' in ann for ann in annotations)

                                methods[method.name.value] = {
                                    'parameters': params,
                                    'is_test': is_test,
                                    'return_type': return_type,
                                    'annotations': annotations,
                                }
                            except Exception:
                                # Skip methods with unparseable descriptors
                                methods[method.name.value] = {
                                    'parameters': [],
                                    'is_test': False,
                                    'return_type': 'unknown',
                                    'annotations': annotations,
                                }

                        if methods:
                            metadata[class_name] = {
                                'methods': methods,
                                'source_jar': os.path.basename(jar_path),
                            }

                    except Exception as e:
                        logger.debug("Skipping class %s: %s", file_info.filename, e)
                        continue

        except zipfile.BadZipFile:
            logger.error("Invalid JAR file: %s", jar_path)
        except Exception as e:
            logger.error("Error processing JAR %s: %s", jar_path, e)

        logger.info("Extracted %d classes from %s", len(metadata), os.path.basename(jar_path))
        return metadata

    def scan_project_jars(
        self,
        group_ids: List[str],
        artifact_ids: List[str],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Dict[str, dict]:
        """
        Scan Maven repository for project JARs and extract metadata.

        Args:
            group_ids: List of Maven group IDs
            artifact_ids: List of Maven artifact IDs
            progress_callback: Optional progress callback

        Returns:
            Combined metadata dict from all JARs
        """
        all_jars: List[str] = []
        for group_id, artifact_id in zip(group_ids, artifact_ids):
            jars = self.find_jars(group_id, artifact_id)
            logger.info("Found %d JARs for %s:%s", len(jars), group_id, artifact_id)
            all_jars.extend(jars)

        if not all_jars:
            logger.warning("No JARs found for the specified coordinates")
            return {}

        logger.info("Processing %d JAR files...", len(all_jars))

        for idx, jar in enumerate(all_jars):
            jar_metadata = self.extract_from_jar(jar, progress_callback)
            self.metadata.update(jar_metadata)
            logger.info("[%d/%d] Extracted %d classes from %s",
                       idx + 1, len(all_jars), len(jar_metadata), os.path.basename(jar))

        logger.info("Total: Extracted metadata for %d classes", len(self.metadata))
        return self.metadata

    def save_metadata(self, output_path: str) -> None:
        """Save extracted metadata to a JSON file."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2)
            logger.info("Metadata saved to: %s", output_path)
        except Exception as e:
            logger.error("Failed to save metadata: %s", e)

    def load_metadata(self, input_path: str) -> Dict[str, dict]:
        """Load metadata from a JSON file."""
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
            logger.info("Loaded metadata for %d classes from %s", len(self.metadata), input_path)
            return self.metadata
        except Exception as e:
            logger.error("Failed to load metadata: %s", e)
            return {}
