// Arguments:
//   * The executable PATH
//   * The SECCOMP_SYSCALL_ALLOW value
//   * The UID
// Create a process group named C5_UID and make it killable by C5 UID
// Limit to 100MB of memory and 10 concurrent threads.

#include <stdlib.h>
#include <unistd.h>
#include <stdio.h>
#include <sys/stat.h>
#include <sys/resource.h>

int main(int argc, char **argv)
{
    char filename[80];
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
    setrlimit(RLIMIT_CPU, &cpu);
    setrlimit(RLIMIT_DATA, &data);
    setrlimit(RLIMIT_NPROC, &nproc);

    // Drop root rights
    setreuid(uid, uid);

    // Run the real job
    setenv("LD_PRELOAD", "sandbox/libsandbox.so", 1);
    setenv("SECCOMP_SYSCALL_ALLOW", argv[2], 1);
    execl(argv[1], argv[1], NULL);
}