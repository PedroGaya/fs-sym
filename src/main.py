import os
from lib.fs import FileSystem

def main():
  fs = FileSystem()

  fs.mkdir("/docs", 0o755)

  fd = fs.creat("/docs/notes.txt", 0o644)

  data = b"Simple file content"
  bytes_written = fs.write(fd, data)
  print(f"Wrote {bytes_written} bytes to file")

  fs.close(fd)
  
  res = fs.write(fd, data)
  print(f"Tried to write to closed file. Result: {res}")

  read_fd = fs.open("/docs/notes.txt", os.O_RDONLY)
  print(f"Opened file for reading with fd {read_fd}")

  file_content = fs.read(read_fd, 1024)
  print(f"File contents: {file_content.decode('utf-8')}")

  fs.close(read_fd)
  print("Closed file after reading")
  
  docs_inode = fs._get_inode_by_path("/docs") 
  print(f"Docs directory contents: {docs_inode.data}") # type: ignore

  file_stat = fs.stat("/docs/notes.txt")
  print(f"File inode: {file_stat['st_ino']}, size: {file_stat['st_size']}") # type: ignore
  
  res = fs.rmdir("/docs")
  print(f"Attempted rmdir on non-empty dir. Result: {res}")
  
  root_inode = fs._get_inode_by_path("/")
  print(f"Root directory contents: {root_inode.data}") # type: ignore
  
  res = fs.unlink("/docs/notes.txt")
  print(f"Unlinked file for rmdir. Result: {res}")

  res = fs.rmdir("/docs")
  print(f"Attempted rmdir on empty dir. Result: {res}")

  root_inode = fs._get_inode_by_path("/")
  print(f"Root directory contents: {root_inode.data}") # type: ignore
  
if __name__ == "__main__":
  main()