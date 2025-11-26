# Primer

Here's some C code:

```c
#include <stdio.h>

int main() {
    FILE *fp = fopen("/home/user/data.txt", "r");
    char buffer[100];
    fread(buffer, 1, 100, fp);
    fclose(fp);
    return 0;
}
```

Here are the calls that are made under the hood:

```
fopen() → open() → syscall
fread() → read() → syscall
fclose() → close() → syscall
```

The first transition is handled by **libc**, converting a high-level fbar() call to an implementation of bar().

The lower-level function sets the register with `mov eax, #` with a number corresponding to a **syscall**, then other regs with the arguments.

Finally, it calls the assembly instruction `syscall`, handing the code to the kernel functions.

Somewhere in the kernel code, there is a mapping of numbers to functions:

```c
// Simplified kernel code
void *sys_call_table[] = {
    [0] = sys_read,
    [1] = sys_write,
    [2] = sys_open,
    [3] = sys_close,
    // ... hundreds more
};
```

After mapping, we enter a wrapper kernel function like so:

```c
asmlinkage long __x64_sys_open(const struct pt_regs *regs) {
    return __do_sys_open(regs->di, regs->si, regs->dx);
}

long do_sys_open(int dfd, const char __user *filename, int flags, umode_t mode) {
    // Path resolution, permission checks...
    return do_filp_open(dfd, filename, flags, mode);
}

// Then eventually calls filesystem-specific operations:
file->f_op->open(inode, file);  // Calls ext4_file_open(), etc.
```

What `fs_read()` actually is will vary by filesystem - Whatever you have installed will provide the implementation to this function. For example, with ext4:

```c
struct inode_operations ext4_dir_inode_operations = {
    .create     = ext4_create,      // How to create new files
    .lookup     = ext4_lookup,      // How to find files in directories
    .mkdir      = ext4_mkdir,       // How to create directories
    .rmdir      = ext4_rmdir,       // How to remove directories
    .rename     = ext4_rename,      // How to rename files
};
```

The filesystem will handle memory allocation by calling kernel code such as `kmalloc()`. This is NOT a syscall, as syscalls are interfaces between user code and kernel code.
