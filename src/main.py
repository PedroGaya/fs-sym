import os
from lib.fs import FileSystem

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