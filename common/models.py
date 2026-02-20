from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, ClassVar
from pyodmongo import DbModel
import semver

# Current Project Version
VERSION = "1.0.0"
# Minimum Client version the server supports
MIN_CLIENT_VERSION = "1.0.0"
# Minimum Server version the client supports
MIN_SERVER_VERSION = "1.0.0"

class DuplicateStatus(str, Enum):
    NONE = "NONE"
    DUPLICATE_CONTENTS = "DUPLICATE_CONTENTS"
    DUPLICATE = "DUPLICATE"
    PREVIOUSLY_SCANNED = "PREVIOUSLY_SCANNED"
    MARKED_FOR_DELETION = "MARKED_FOR_DELETION"

class ActionUpdate(BaseModel):
    action: str
    action_args: Optional[str] = None

class FileModel(DbModel):
    #id: Optional[str] = Field(alias="_id", default=None)
    name: str
    size: int
    kind: str
    md5: str
    parent_dir: str
    full_path: str
    action: Optional[str] = None
    action_args: Optional[str] = None
    duplicate_status: DuplicateStatus
    _collection: ClassVar[str] = "files"
