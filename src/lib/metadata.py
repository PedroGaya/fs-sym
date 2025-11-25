from dataclasses import dataclass
from typing import Dict, Union
from enum import Enum

class FileType(Enum):
    REGULAR = 1
    DIRECTORY = 2
    SYMLINK = 2
    
@dataclass
class Inode:
    ino: int
    file_type: FileType # should be part of mode
    mode: int # only perms here (ease of impl)
    uid: int # user id, not used since ownership is not modeled
    gid: int # user group id, see above
    size: int # in bytes
    atime: float  # access time
    mtime: float  # modification time
    ctime: float  # change time
    nlink: int    # hard link count
    data: Union[bytes, Dict[str, int]]  # file data or directory entries. should be blocks!

@dataclass
class Superblock:
    magic = 0xDEADBEEF # used by other syscalls not modeled here
    block_size = 4096 # not used, but needed
    total_blocks = 1024 # not used, but needed
    free_blocks = 1024 # not used, but needed
    total_inodes = 256
    free_inodes = 256
    mounted = False # not used, but needed