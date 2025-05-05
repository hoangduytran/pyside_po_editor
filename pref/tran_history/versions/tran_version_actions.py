from lg import logger
from pref.tran_history.tran_db_record import DatabasePORecord

def add_version(record: DatabasePORecord, translation: str) -> DatabasePORecord:
    """
    Add a new version to the record (in-memory only).
    """
    record.add_version_mem(translation)
    logger.info(f"Added version {record.msgstr_versions[-1][0]} to record {record.unique_id}")
    return record

def delete_version(record: DatabasePORecord, version_id: int) -> DatabasePORecord:
    """
    Delete a version from the record (in-memory only).
    """
    record.delete_version_mem(version_id)
    logger.info(f"Deleted version {version_id} from record {record.unique_id}")
    return record

def edit_version(record: DatabasePORecord, version_id: int, new_translation: str) -> DatabasePORecord:
    """
    Edit an existing version in the record (in-memory only).
    """
    # We don’t have a pure “edit‐only” mem method, so just mutate the list:
    record.msgstr_versions = [
        (v, new_translation if v == version_id else t)
        for v, t in record.msgstr_versions
    ]
    logger.info(f"Edited version {version_id} of record {record.unique_id}")
    return record

def save_versions(record: DatabasePORecord, connection) -> None:
    """
    Persist all versions of the record to the database.
    """
    cursor = connection.cursor()
    cursor.execute("DELETE FROM tran_text WHERE unique_id = ?", (record.unique_id,))
    for version_id, text in record.msgstr_versions:
        cursor.execute(
            "INSERT INTO tran_text(unique_id, version_id, tran_text) VALUES (?, ?, ?)",
            (record.unique_id, version_id, text)
        )
    connection.commit()
    logger.info(f"Saved {len(record.msgstr_versions)} versions for record {record.unique_id}")

def cancel_edit() -> None:
    """
    Cancel any in-memory changes. (No-op.)
    """
    logger.info("Canceled version edits")
