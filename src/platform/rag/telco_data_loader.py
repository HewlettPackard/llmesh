#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Function to download 3GPP standard 
"""

from ftplib import FTP
import os
from posixpath import basename
import zipfile
import yaml


def download_latest(series: str, version: str, destination: str):
    "Download latest 3GPP standard version"
    ftp = FTP('ftp.3gpp.org')
    ftp.login()
    versions_path = f"Specs/archive/{series}_series/{series}.{version}"
    try:
        document_versions = ftp.nlst(versions_path)
        document_path = document_versions[-1]
        target_file_path = os.path.join(destination, basename(document_path))
        with open(target_file_path, "wb") as fp:
            ftp.retrbinary(f'RETR {document_path}', fp.write)
        with zipfile.ZipFile(target_file_path, 'r') as f:
            # print(f"Extracting {f.filename}")
            f.extractall(destination)
        os.remove(target_file_path)
        # print(f"Update config.yaml with {basename(document_path).replace(".zip", ".docx")}")
        yield basename(document_path).replace(".zip", ".docx")
    except Exception as e:  # pylint: disable=W0718
        print(f"Error: {e}")
    ftp.quit()

def main():
    "Entry point"
    destination = "src/platform/rag/data"
    config_yaml = "src/platform/rag/config.yaml"
    files = []
    for version in ["501", "502"]:
        for filename in download_latest(series="23", version=version, destination=destination):
            files.append(filename)
    if len(files) == 0:
        print("No files downloaded.")
        return
    # Update config.yaml with new document name
    with open(config_yaml, encoding="utf-8") as f:
        loaded = yaml.safe_load(f)
        loaded["data"]["files"] = [ {"source": filename} for filename in files ]
        loaded["data"]["path"] = destination
    # Re-write the config.yaml file with updated data
    with open(config_yaml, "wb") as f:
        yaml.safe_dump(
            loaded,
            f,
            default_flow_style=False,
            explicit_start=True,
            allow_unicode=True,
            encoding="utf-8",
            sort_keys=False)


if __name__ == "__main__":
    main()
