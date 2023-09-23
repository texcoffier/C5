// Arguments:
//   * The executable PATH
//   * The SECCOMP_SYSCALL_ALLOW value
//   * The UID
//   * The HOME path
// Create a process group named C5_UID and make it killable by C5 UID
// Limit to 100MB of memory and 10 concurrent threads.

#include <stdlib.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/resource.h>
#include <sys/types.h>
#include <dirent.h>

void chown_dir(const char *dir, int uid)
{
    DIR *content;
    chown(dir, uid, -1);
    chmod(dir, 0775);
    content = opendir(dir);
    if(content) {
        struct dirent *item;
        char buffer[999];
        while( (item = readdir(content)) )
            {
                if (strcmp(item->d_name, ".") == 0 || strcmp(item->d_name, "..") == 0)
                    continue;
                snprintf(buffer, sizeof(buffer), "%s/%s", dir, item->d_name);
                chown_dir(buffer, uid);
            }
    }
}

int main(int argc, char **argv)
{
    char filename[999], execname[999];
    if (argc != 5)
        exit(2);
    int uid = atoi(argv[3]);
    if (uid < 3000)
        exit(1);

    // Create control group
    sprintf(filename, "/sys/fs/cgroup/C5_%d", uid);
    if ( mkdir(filename, 0555) )
        {
            rmdir(filename); // Clear stats
            mkdir(filename, 055);
        }

    // Add this processus to the control group
    sprintf(filename, "/sys/fs/cgroup/C5_%d/cgroup.procs", uid);
    FILE *cgroup_procs = fopen(filename, "w");
    if ( cgroup_procs == NULL )
        return -1;
    fprintf(cgroup_procs, "%d\n", getpid());
    fclose(cgroup_procs);

    // Allow the real UID to kill the control group
    sprintf(filename, "/sys/fs/cgroup/C5_%d/cgroup.kill", uid);
    chown(filename, getuid(), getgid());

    // Limit resource usage
    struct rlimit cpu = {1, 1};
    struct rlimit data = {100*1024*1024, 100*1024*1024};
    struct rlimit nproc = {11, 11};
    struct rlimit fsize = {1024*1024, 1014*1024};
    setrlimit(RLIMIT_CPU, &cpu);
    setrlimit(RLIMIT_DATA, &data);
    setrlimit(RLIMIT_NPROC, &nproc);
    setrlimit(RLIMIT_FSIZE, &fsize);

    // Give its home dir to itself
    chown_dir(argv[4], uid);

    // The created files must be writable/destroyable by compile_server
    umask(7);


    // Drop root rights
    setreuid(uid, uid);
    setregid(uid, uid);

    getcwd(filename, sizeof(filename) - 100);
    strcat(filename, "/sandbox/libsandbox.so");

    getcwd(execname, sizeof(execname) - strlen(argv[1]) - 1);
    strcat(execname, "/");
    strcat(execname, argv[1]);

    setenv("LD_PRELOAD", filename, 1);
    setenv("SECCOMP_SYSCALL_ALLOW", argv[2], 1);

    // Goto home
    chdir(argv[4]);

    execl(execname, argv[1], NULL);
}