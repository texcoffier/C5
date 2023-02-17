/*

Each seconds, kill the process groups named C5_* using more than 1 second of CPU

 */
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <fcntl.h>
#include <stdio.h>
#include <dirent.h>

long value(const char *buffer, const char *key)
{
   return atol(strstr(buffer, key) + strlen(key));
}

int main(int argc, char **argv)
{
    char cpustat_filename[256*2], kill_filename[256*2], cpustat_buffer[256*2];
    int cpustat_fildes;
    FILE *kill_file;
    DIR *dir;
    struct dirent *group;

    chdir("/sys/fs/cgroup");
    dir = opendir(".");
    for(;;) {
        rewinddir(dir);
        while( (group = readdir(dir)) ) {
            if ( strncmp(group->d_name, "C5_", 3) != 0 )
                continue;
            sprintf(cpustat_filename, "%s/cpu.stat", group->d_name);
            cpustat_fildes = open(cpustat_filename, 0);
            if ( cpustat_fildes < 0 )
                continue;
            if ( read(cpustat_fildes, cpustat_buffer, sizeof(cpustat_buffer) - 1) > 0 ) {
                if ( value(cpustat_buffer, "usage_usec ") > 1000000 ) {
                    sprintf(kill_filename, "%s/cgroup.kill", group->d_name);
                    kill_file = fopen(kill_filename, "w");
                    if(kill_file)
                        {
                            fprintf(kill_file, "1\n");
                            fclose(kill_file);
                        }
                }
            }
            close(cpustat_fildes);
        }
        sleep(1);
    }
}
