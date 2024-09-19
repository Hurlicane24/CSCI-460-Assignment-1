import math
import numpy as np
from collections import deque
import sys
#py Simple_Paging_Simulation.py 65536 4096 input_requests_1.txt

#Function that checks if a string is castable to an int (returns boolean)
def isInt(string):
     try:
        int(string)
        return True
     except:
         return False

#Function that splits processes into pages, and returns them in a list 
def generate_pages(job_number, job_size, page_size):
    number_of_pages = math.ceil(int(job_size)/int(page_size))
    print("Number of pages: {}".format(number_of_pages))
    last_page_internal_frag = (number_of_pages - (int(job_size)/int(page_size))) * int(page_size)
    page_list = []
    for i in range(number_of_pages):
        page_list.append("page_{},{}".format(job_number, i+1))

    #Internal fragmentation of last page will be stored as last element in page_list
    page_list.append(last_page_internal_frag)
    
    return(page_list)

def func():
    pass

#Function that reads job requests and modifies memory appropriately according to the simple paging system
def main_loop(memory_info_list):
    number_of_frames = int(int(memory_info_list[0])/int(memory_info_list[1]))
    main_memory = np.full(number_of_frames, None)
    secondary_memory = []
    page_tables = {}
    internal_fragmentation = {}
    jobs_to_pages_map = {}
    existing_jobs = []
    job_age_queue = deque()
    free_frames = number_of_frames
    EXIT = False
    #requests_user

    #Main loop
    while(EXIT != True):

        #If a file argument is present, execute requests in the file
        if(len(memory_info_list) > 2):

            requests_file = open(memory_info_list[2], "r")

            #Skip header
            line = requests_file.readline()

            while(line != None):
                line = requests_file.readline()
                job_info = line.split()

                #job_info = [job ID, Command]

                #If job ID is exit, terminate simulation
                if(job_info[0] == "exit"):
                    print("You have exited the program")
                    EXIT = True
                    break

                #If Job_ID is "print", print the current state of memory (Complete last)
                elif(job_info[0] == "print"):
                    print("print current state of memory")

                #If job ID is not castable to an int and is not exit or print, reject request
                elif(isInt(job_info[0]) == False and (job_info[0] != "exit" or job_info[0] != "print")):
                     print("ERROR: INVALID COMMAND")

                #If command is not an integer, reject request
                elif(isInt(job_info[1]) == False):
                    print("ERROR: COMMAND IS NOT AN INTEGER")

                #If process is too large to fit in main memory, reject the process
                elif(int(job_info[1]) > (len(main_memory) * int(memory_info_list[1]))):
                    print("ERROR: JOB IS TOO LARGE FOR MAIN MEMORY")

                #If job doesn't yet exist and command 0,-1, or -2 is called, reject request
                elif(job_info[0] not in existing_jobs and (int(job_info[1]) == 0 or int(job_info[1]) == -1 or int(job_info[1]) == -2)):
                    print("ERROR: CANNOT EXECUTE COMMAND. JOB DOES NOT CURRENTLY EXIST")

                #If command value is invalid, reject request
                elif(int(job_info[1]) < -2):
                    print("ERROR: INVALID COMMAND")
            
                #If a new process is being added, perform necessary actions to put it in main memory
                elif(job_info[0] not in existing_jobs):
                    existing_jobs.append(job_info[0])
                    job_pages = generate_pages(job_info[0], job_info[1], memory_info_list[1])

                    #Map each page to its corresponding internal fragmentation
                    for i in range(len(job_pages) - 1):
                        if(i < len(job_pages) - 2):
                            internal_fragmentation[job_pages[i]] = 0
                        else:
                            internal_fragmentation[job_pages[i]] = job_pages[len(job_pages) - 1]

                    #Map the job to a list of its pages
                    del job_pages[len(job_pages) - 1]
                    jobs_to_pages_map[job_info[0]] = job_pages

                    #If process can fit into free frames, put pages into memory immediately
                    if(len(job_pages) <= free_frames):
                        job_index = 0
                        page_table = {}
                        for i in range(len(main_memory)):
                            if(main_memory[i] == None):
                                if(job_index == len(job_pages)):
                                    break
                                else:
                                    main_memory[i] = job_pages[job_index]
                                    page_table[job_pages[job_index]] = i
                                    job_index += 1
                        page_tables[job_info[0]] = page_table

                        free_frames -= len(job_pages)
                        job_age_queue.append(job_info[0])
                        print("MAIN MEMORY:")
                        print(main_memory)
                        print("\nSECONDARY MEMORY:")
                        print(secondary_memory)
                        print("\nPAGE TABLES:")
                        print(page_tables)
                        print("\nINTERNAL FRAGMENTATION:")
                        print(internal_fragmentation)
                        print("\nJOB AGE QUEUE:")
                        print(job_age_queue)
                        print("\nJOB TO PAGES MAP:")
                        print(jobs_to_pages_map)
                        print("\nFREE FRAMES:")
                        print(free_frames)

                    #If process cannot fit into free frames, Remove oldest process(es) to make space. Move these jobs to secondary memory.
                    else:
                        minimum_frames_to_swap = len(job_pages) - free_frames
                        frames_swapped = 0

                        #Swap out jobs until we have enough space
                        while(frames_swapped < minimum_frames_to_swap):
                            job_move = job_age_queue.popleft()
                            pages_to_swap = jobs_to_pages_map[job_move]

                            #If frame in main memory contains a page we wish to swap, replace it with None
                            index = 0
                            for frame in main_memory:
                                if(frame in pages_to_swap):
                                    main_memory[index] = None                 
                                index += 1

                            #Put pages into secondary memory
                            for page in pages_to_swap:
                                secondary_memory.append(page)

                            #Map swapped pages to none in page table
                            for page_table in page_tables:
                                if(page_table == job_move):
                                    for page in page_tables[page_table]:
                                        page_tables[page_table][page] = None

                            #Increase frames_swapped and free_frames
                            frames_swapped += len(pages_to_swap)
                            free_frames += len(pages_to_swap)

                        #Add new job to main memory
                        job_index = 0
                        page_table = {}
                        for i in range(len(main_memory)):
                            if(main_memory[i] == None):
                                if(job_index == len(job_pages)):
                                    break
                                else:
                                    main_memory[i] = job_pages[job_index]
                                    page_table[job_pages[job_index]] = i
                                    job_index += 1
                        page_tables[job_info[0]] = page_table
                    
                        free_frames -= len(job_pages)
                        job_age_queue.append(job_info[0])
                        print("MAIN MEMORY:")
                        print(main_memory)
                        print("\nSECONDARY MEMORY:")
                        print(secondary_memory)
                        print("\nPAGE TABLES:")
                        print(page_tables)
                        print("\nINTERNAL FRAGMENTATION:")
                        print(internal_fragmentation)
                        print("\nJOB AGE QUEUE:")
                        print(job_age_queue)
                        print("\nJOB TO PAGES MAP:")
                        print(jobs_to_pages_map)
                        print("\nFREE FRAMES:")
                        print(free_frames)
            
                #Carries out commands 0, -1, and -2 for already existing jobs
                elif(job_info[0] in existing_jobs):

                    #If job is already in system, reject
                    if(int(job_info[1]) != 0 and int(job_info[1]) != -1 and int(job_info[1]) != -2):
                        print("ERROR: JOB IS ALREADY IN THE MEMORY SYSTEM")

                    #If command is 0, remove the job from memory
                    elif(int(job_info[1]) == 0):  
                        in_main_memory = False
                    
                        #Determine if job is in main memory or secondary memory
                        for frame in main_memory:
                            if(frame in jobs_to_pages_map[job_info[0]]):
                                in_main_memory = True
                                break
                    
                        #If it's in main memory, remove it from main memory
                        remove_index = 0
                        if(in_main_memory == True):

                            #Remove job from main memory
                            for frame in main_memory:
                                if(frame in jobs_to_pages_map[job_info[0]]):
                                    main_memory[remove_index] = None
                                remove_index += 1  
                        
                            #Modify free frames, remove from existing jobs, remove from job age queue
                            free_frames += len(jobs_to_pages_map[job_info[0]])
                            existing_jobs.remove(job_info[0])
                            job_age_queue.remove(job_info[0])
                        
                            #Delete the job's page table
                            marked_for_deletion = {}
                            for page_table in page_tables:
                                if(page_table == job_info[0]):
                                    marked_for_deletion = page_table
                            del page_tables[marked_for_deletion]

                            #Remove all of the pages associated with the job from the internal fragmentation dictionary
                            for page in jobs_to_pages_map[job_info[0]]:
                                internal_fragmentation.pop(page)

                            #Remove job from jobs_to_pages_map
                            jobs_to_pages_map.pop(job_info[0])
                    
                        #If it's in secondary memory, remove from secondary memory
                        else:

                            #Remove job from secondary memory
                            for page in jobs_to_pages_map[job_info[0]]:
                                secondary_memory.remove(page)

                            #Delete the job's page table
                            for page_table in page_tables:
                                if(page_table == job_info[0]):
                                    del page_tables[page_table]
                        
                            #Remove from existing jobs
                            existing_jobs.remove(job_info[0])
                        
                            #Remove all of the pages associated with the job from the internal fragmentation dictionary
                            for page in jobs_to_pages_map[job_info[0]]:
                                internal_fragmentation.pop(page)

                            #Remove job from jobs_to_pages map
                            jobs_to_pages_map.pop(job_info[0])

                        print("MAIN MEMORY:")
                        print(main_memory)
                        print("\nSECONDARY MEMORY:")
                        print(secondary_memory)
                        print("\nPAGE TABLES:")
                        print(page_tables)
                        print("\nINTERNAL FRAGMENTATION:")
                        print(internal_fragmentation)
                        print("\nJOB AGE QUEUE:")
                        print(job_age_queue)
                        print("\nJOB TO PAGES MAP:")
                        print(jobs_to_pages_map)
                        print("\nFREE FRAMES:")
                        print(free_frames)
                        break
                
                    #If command is -1, move job to secondary memory
                    elif(int(job_info[1]) == -1):
                        print("TBC")
            
            #Switch to dynamic user requests by deleting file from the list
            memory_info_list.pop()

        #Dynamic User commands
        else:
            print("Job Requests file has finished running, switching to user requests mode")
            EXIT = True

    
#Obtain memory size, page size, and job requests file from user
proceed = True
memory_info_list = []
print("Welcome to Paging Simulator\n---------------------------")
if(len(sys.argv) < 3):
    print("Error: At least 2 arguments are required (memory size and page size)")
    proceed = False

elif(len(sys.argv) > 4):
    print("Error: Too many arguments")
    proceed = False

elif(isInt(sys.argv[1]) == False or isInt(sys.argv[2]) == False):
    print("Error: Either the memory size or the page size is not an integer")
    proceed = False

elif(int(sys.argv[1]) % int(sys.argv[2]) != 0):
    print("Error: The page size must be a factor of the memory size")
    proceed = False

if(len(sys.argv) == 4):
    if(".txt" not in sys.argv[3]):
        print("Error: your file name does not have the .txt file extension")
        proceed = False

if(proceed == True):
    print("Memory Size:", sys.argv[1])
    print("Page Size:", sys.argv[2])
    if(len(sys.argv) == 3):
        memory_info_list.append(sys.argv[1])
        memory_info_list.append(sys.argv[2])
        main_loop(memory_info_list)
    else:
        memory_info_list.append(sys.argv[1])
        memory_info_list.append(sys.argv[2])
        memory_info_list.append(sys.argv[3])
        main_loop(memory_info_list)