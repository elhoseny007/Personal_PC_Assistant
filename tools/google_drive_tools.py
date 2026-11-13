
import mimetypes
from pathlib import Path

from googleapiclient.http import MediaFileUpload
from google_drive import get_drive_service


def upload_to_google_drive(file_path, folder_id=None):
    """
    Upload a local file to the connected Google Drive account.
    """

    if not file_path or not str(file_path).strip():
        return {"ok": False, "error": "File path is empty."}

    raw_path = str(file_path).strip()

    if raw_path.startswith("\\\\"):
        return {"ok": False, "error": "Network paths are not allowed."}

    try:
        path = Path(raw_path).expanduser().resolve()

        if not path.exists():
            return {
                "ok": False,
                "error": f"File not found: {path}"
            }

        if not path.is_file():
            return {
                "ok": False,
                "error": "The provided path is not a file."
            }

        drive = get_drive_service()

        mime_type, _ = mimetypes.guess_type(str(path))

        file_metadata = {
            "name": path.name
        }

        if folder_id:
            file_metadata["parents"] = [folder_id]

        media = MediaFileUpload(
            str(path),
            mimetype=mime_type or "application/octet-stream",
            resumable=True
        )

        uploaded_file = drive.files().create(
            body=file_metadata,
            media_body=media,
            fields="id,name,mimeType,webViewLink,size"
        ).execute()

        return {
            "ok": True,
            "message": "File uploaded successfully.",
            "file": {
                "id": uploaded_file.get("id"),
                "name": uploaded_file.get("name"),
                "mime_type": uploaded_file.get("mimeType"),
                "size": uploaded_file.get("size"),
                "url": uploaded_file.get("webViewLink")
            }
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }
