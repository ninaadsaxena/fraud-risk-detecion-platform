"""Optional: upload raw/curated/gold files to Azure Storage (ADLS Gen2) containers."""
import os

from . import config

CONTAINERS = {"raw": config.RAW_DIR, "curated": config.CURATED_DIR, "gold": config.GOLD_DIR}


def run(include_raw: bool = False) -> None:
    conn = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "").strip()
    if not conn:
        print("[upload] AZURE_STORAGE_CONNECTION_STRING not set; skipping upload")
        return
    from azure.storage.blob import BlobServiceClient

    svc = BlobServiceClient.from_connection_string(conn)
    for name, folder in CONTAINERS.items():
        if name == "raw" and not include_raw:
            continue
        cc = svc.get_container_client(name)
        if not cc.exists():
            cc.create_container()
        for f in folder.glob("*"):
            if f.is_file() and f.name != ".gitkeep":
                with open(f, "rb") as fh:
                    cc.upload_blob(name=f.name, data=fh, overwrite=True)
                print(f"[upload] {name}/{f.name}")


if __name__ == "__main__":
    run()
