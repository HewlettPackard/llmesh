from ftplib import FTP
import os
from posixpath import basename 
import zipfile


dest = "./examples/tool_rag/data"
ftp = FTP('ftp.3gpp.org') 
ftp.login()

for ver in ["501", "502"]:
    versions_path = f"Specs/archive/23_series/23.{ver}"
    try:
        document_versions = ftp.nlst(versions_path)
        document_path = document_versions[-1]
        target_file_path = os.path.join(dest, basename(document_path))

        with open(target_file_path, "wb") as fp:
            ftp.retrbinary(f'RETR {document_path}', fp.write)
        with zipfile.ZipFile(target_file_path, 'r') as f:
            # print(f"Extracting {f.filename}")
            f.extractall(dest)
        os.remove(target_file_path)
        print(f"Update config.yaml with {basename(document_path).replace(".zip", ".docx")}")

    except Exception as e:
        print(f"Error: {e}")

ftp.quit()