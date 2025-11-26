
import os
import time
from typing import Dict, Optional
from metadata import FileType, Inode, Superblock

class FileSystem:
  def __init__(self):
    self.superblock = Superblock()
    self.inodes: Dict[int, Inode] = {}
    self.free_inodes = set(range(1, self.superblock.total_inodes + 1))
    self.fd_table: Dict[int, int] = {} # fd -> inode mapping
    self.next_fd = 3 # 0,1,2 are stdin, stdout, stderr
  
    self._create_root()
 
  def _create_root(self):
    root_inode = Inode(
      ino=1,
      file_type=FileType.DIRECTORY,
      mode=0o755,
      uid=0,
      gid=0,
      size=0,
      atime=time.time(),
      mtime=time.time(),
      ctime=time.time(),
      nlink=2, # '.' and parent link
      data={'.': 1, '..': 1} # self and parent reference
    )
    
    self.inodes[1] = root_inode
    self.free_inodes.discard(1)
    self.superblock.free_inodes -= 1

  def _allocate_inode(self) -> Optional[int]:
    if not self.free_inodes:
      return None
    return self.free_inodes.pop()
  
  def _get_inode_by_path(self, path: str) -> Optional[Inode]:
      if path == '/':
        return self.inodes[1]
      
      components = path.strip('/').split('/')
      current_inode = self.inodes[1]
      
      for comp in components:
        if current_inode.file_type != FileType.DIRECTORY:
          return None
        
        if not isinstance(current_inode.data, dict):
          return None
          
        if comp in current_inode.data:
          next_ino = current_inode.data[comp]
          current_inode = self.inodes[next_ino]
        else:
          return None
      
      return current_inode

  def _get_parent_inode(self, path: str) -> tuple[Optional[Inode], str]:
    components = path.strip('/').split('/')
    if len(components) == 1:
      return self.inodes[1], components[0]
    
    parent_path = '/' + '/'.join(components[:-1])
    filename = components[-1]
    return self._get_inode_by_path(parent_path), filename
  
  # Modes and flags don't matter for sim
  def open(self, pathname: str, _flags: int, _mode: int = 0o644) -> int:
    inode = self._get_inode_by_path(pathname)
  
    if inode is None:
      raise FileNotFoundError(f"File not found: {pathname}")
      
    inode.atime = time.time()
      
    # Allocate file descriptor
    fd = self.next_fd
    self.next_fd += 1
    self.fd_table[fd] = inode.ino
      
    return fd
    
  def creat(self, pathname: str, mode: int) -> int:
    parent_inode, filename = self._get_parent_inode(pathname)
    
    if parent_inode is None or parent_inode.file_type != FileType.DIRECTORY:
      return -1
    
    if not isinstance(parent_inode.data, dict):
      return -1
    
    if filename in parent_inode.data:
        # Truncate existing file
        # Should check for os flags!
        existing_ino = parent_inode.data[filename]
        existing_inode = self.inodes[existing_ino]
        existing_inode.size = 0
        existing_inode.mtime = time.time()
        existing_inode.ctime = time.time()
    else:
        # Create new file
        ino = self._allocate_inode()
        if ino is None:
            return -1
        
        new_inode = Inode(
            ino=ino,
            file_type=FileType.REGULAR,
            mode=mode,
            uid=0, gid=0,
            size=0,
            atime=time.time(),
            mtime=time.time(),
            ctime=time.time(),
            nlink=1,
            data=b''
        )
        
        self.inodes[ino] = new_inode
        parent_inode.data[filename] = ino
        parent_inode.mtime = time.time()
        parent_inode.ctime = time.time()
        parent_inode.nlink += 1
    
    # Open the file
    return self.open(pathname, os.O_WRONLY)

  def read(self, fd: int, count: int) -> bytes:
    if fd not in self.fd_table:
      return b''
        
    ino = self.fd_table[fd]
    inode = self.inodes[ino]
    
    if inode.file_type != FileType.REGULAR:
      return b''
    
    # Update access time
    inode.atime = time.time()
    
    # Return requested bytes
    if isinstance(inode.data, bytes):
      return inode.data[:count]
    return b''
    
  def write(self, fd: int, data: bytes) -> int:
    if fd not in self.fd_table:
      return -1

    ino = self.fd_table[fd]
    inode = self.inodes[ino]

    if inode.file_type != FileType.REGULAR:
      return -1

    # Real fs would allocate blocks and keep pointers
    if isinstance(inode.data, bytes):
        inode.data = data
    else:
        inode.data = data

    inode.size = len(data)
    inode.mtime = time.time()
    inode.ctime = time.time()

    return len(data)
    
  def close(self, fd: int) -> int:
    if fd in self.fd_table:
      del self.fd_table[fd]
      return 0
    return -1
    
  def stat(self, path: str) -> Optional[Dict]:
    inode = self._get_inode_by_path(path)
    if inode is None:
      return None

    return {
      'st_ino': inode.ino,
      'st_mode': inode.mode,
      'st_uid': inode.uid,
      'st_gid': inode.gid,
      'st_size': inode.size,
      'st_atime': inode.atime,
      'st_mtime': inode.mtime,
      'st_ctime': inode.ctime,
      'st_nlink': inode.nlink
    }
  
  def unlink(self, pathname: str) -> int:
    parent_inode, filename = self._get_parent_inode(pathname)
    if not parent_inode or filename not in parent_inode.data: # type: ignore
        return -1
        
    ino = parent_inode.data[filename] # type: ignore
    inode = self.inodes[ino]
    
    inode.nlink -= 1
    if inode.nlink == 0:
        del self.inodes[ino]
        self.free_inodes.add(ino)
    
    del parent_inode.data[filename] # type: ignore
    return 0
  
  def mkdir(self, pathname: str, mode: int = 0o755) -> int:
    parent_inode, dirname = self._get_parent_inode(pathname)

    if parent_inode is None or parent_inode.file_type != FileType.DIRECTORY:
      return -1
      
    ino = self._allocate_inode()
    if ino is None:
      return -1

    dir_inode = Inode(
      ino=ino,
      file_type=FileType.DIRECTORY,
      mode=mode,
      uid=0, gid=0,
      size=0,
      atime=time.time(),
      mtime=time.time(),
      ctime=time.time(),
      nlink=2,  # '.' and parent link
      data={'.': ino, '..': parent_inode.ino}
    )

    self.inodes[ino] = dir_inode
    parent_inode.data[dirname] = ino # type: ignore
    parent_inode.mtime = time.time()
    parent_inode.ctime = time.time()
    parent_inode.nlink += 1

    return 0
  
  def rmdir(self, pathname: str) -> int:
    inode = self._get_inode_by_path(pathname)
    if inode is None:
      return -1

    if inode.file_type != FileType.DIRECTORY:
      return -1

    if isinstance(inode.data, dict) and len(inode.data) > 2:
      return -1  # Directory not empty

    # Remove from parent directory
    parent_inode, dirname = self._get_parent_inode(pathname)
    if parent_inode and dirname in parent_inode.data: # type: ignore
      del parent_inode.data[dirname] # type: ignore
      parent_inode.mtime = time.time()
      parent_inode.ctime = time.time()
      parent_inode.nlink -= 1

    # Free the inode
    del self.inodes[inode.ino]
    self.free_inodes.add(inode.ino)
    self.superblock.free_inodes += 1

    return 0
  
def main():
  # Create file system instance
  fs = FileSystem()

  # Create a directory called 'docs'
  fs.mkdir("/docs", 0o755)

  # Create a file in the docs directory
  fd = fs.creat("/docs/notes.txt", 0o644)

  # Write to the file
  data = b"Simple file content"
  bytes_written = fs.write(fd, data)
  print(f"Wrote {bytes_written} bytes to file")

  # Close the file
  fs.close(fd)

  # Reopen the file for reading
  read_fd = fs.open("/docs/notes.txt", os.O_RDONLY)
  print(f"Opened file for reading with fd {read_fd}")

  # Read the contents
  file_content = fs.read(read_fd, 1024)
  print(f"File contents: {file_content.decode('utf-8')}")

  # Close the file again
  fs.close(read_fd)
  print("Closed file after reading")

  # Verify the structure
  root_inode = fs._get_inode_by_path("/")
  print(f"Root directory contents: {root_inode.data}") # type: ignore

  docs_inode = fs._get_inode_by_path("/docs") 
  print(f"Docs directory contents: {docs_inode.data}") # type: ignore

  # Show file stats
  file_stat = fs.stat("/docs/notes.txt")
  print(f"File inode: {file_stat['st_ino']}, size: {file_stat['st_size']}") # type: ignore
  
if __name__ == "__main__":
  main()