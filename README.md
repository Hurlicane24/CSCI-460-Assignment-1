# CSCI-460-Assignment-1
This is project 1 for my CSCI 460 (Operating Systems) class. The goal of the assignment is to create a memory management simulator that implements a simple paging scheme. Upon startup, the program takes two mandatory command line arguments (memory size, page size) and one optional command line argument (job requests file). If no job requests file is given, the user can dynamically input requests such as putting a new process into main memory, suspending a process, resuming a suspended process, etc. If a job requests file is given, the program will execute all requests in the file, and then allow dynamic requests from the user.
