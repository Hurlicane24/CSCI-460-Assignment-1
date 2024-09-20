import math
import numpy as np
from collections import deque
import sys
import pandas as pd
#py Simple_Paging_Simulation.py 65536 4096 input_requests_1.txt

#Function that checks if a string is castable to an int (returns boolean)
#------------------------------------------------------------------------
def isInt(string):
     try:
        int(string)
        return True
     except:
         return False
#------------------------------------------------------------------------

#Function that splits processes into pages, and returns them in a list
#--------------------------------------------------------------------- 
def generate_pages(job_number, job_size, page_size):
    number_of_pages = math.ceil(int(job_size)/int(page_size))
    last_page_internal_frag = (number_of_pages - (int(job_size)/int(page_size))) * int(page_size)
    page_list = []
    for i in range(number_of_pages):
        page_list.append("page_{},{}".format(job_number, i+1))

    #Internal fragmentation of last page will be stored as last element in page_list
    page_list.append(last_page_internal_frag)
    
    return(page_list)
#---------------------------------------------------------------------

#Function that adds a new process to main memory. Returns free frames so it can be reassigned outside of the function since it is immutable
#------------------------------------------------------------------------------------------------------------------------------------------
def add_new_process(existing_jobs, job_info, memory_info_list, internal_fragmentation, jobs_to_pages_map, free_frames, page_tables, job_age_queue, main_memory, secondary_memory):
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

    return(free_frames)
#------------------------------------------------------------------------------------------------------------------------------------------

#Function that removes a process from memory. Returns free frames to be modified outside of the function since it's immutable
#----------------------------------------------------------------------------------------------------------------------------
def remove_process(main_memory, jobs_to_pages_map, job_info, existing_jobs, free_frames, job_age_queue, page_tables, internal_fragmentation, secondary_memory):      
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
        marked_for_deletion = ""
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
        marked_for_deletion = ""
        for page_table in page_tables:
            if(page_table == job_info[0]):
                marked_for_deletion = page_table
        del page_tables[marked_for_deletion]
    
        #Remove from existing jobs
        existing_jobs.remove(job_info[0])
    
        #Remove all of the pages associated with the job from the internal fragmentation dictionary
        for page in jobs_to_pages_map[job_info[0]]:
            internal_fragmentation.pop(page)

        #Remove job from jobs_to_pages map
        jobs_to_pages_map.pop(job_info[0])

    return(free_frames)
#----------------------------------------------------------------------------------------------------------------------------

#Function that suspends a process in main memory (moves it to secondary memory). Returns free_frames so it can be modified outside of function since it's immutable
#------------------------------------------------------------------------------------------------------------------------------------------------------------------
def suspend_process(main_memory, secondary_memory, page_tables, internal_fragmentation, jobs_to_pages_map, job_age_queue, free_frames, job_info):
    
    #If the user tries to suspend a process that is already suspended, reject request
    if("page_{},1".format(job_info[0]) in secondary_memory):
        print("ERROR: PROCESS IS ALREADY SUSPENDED")
    
    else:

        #Remove pages of process from main_memory and update free_frames
        for i in range(len(main_memory)):
            if(main_memory[i] in jobs_to_pages_map[job_info[0]]):
                main_memory[i] = None
                free_frames += 1

        #Put pages into secondary memory
        for page in jobs_to_pages_map[job_info[0]]:
            secondary_memory.append(page)

        #Map pages to None in page_table
        for page in page_tables[job_info[0]]:
            page_tables[job_info[0]][page] = None

        #Remove from job_age_queue
        job_age_queue.remove(job_info[0])

    return(free_frames)
#------------------------------------------------------------------------------------------------------------------------------------------------------------------

#Function that puts a suspended job back in main memory. Returns free_frames so it can be updated outside of the function since it's immutable
#---------------------------------------------------------------------------------------------------------------------------------------------
def resume_process(main_memory, secondary_memory, page_tables, internal_fragmentation, jobs_to_pages_map, job_age_queue, free_frames, job_info):
    
    #If job is in main memory, reject request
    if("page_{},1".format(job_info[0]) in main_memory):
        print("ERROR: JOB IS ALREADY IN MAIN MEMORY")

    #If process cannot fit in main memory, suspend oldest process(es) to make room
    elif(len(jobs_to_pages_map[job_info[0]]) > free_frames):
        minimum_frames_to_swap = len(jobs_to_pages_map[job_info[0]]) - free_frames
        frames_swapped = 0

        #While we need to swap more frames, keep removing processes
        while(frames_swapped < minimum_frames_to_swap):
            job_move = job_age_queue.popleft()
            pages_to_swap = jobs_to_pages_map[job_move]

            #Remove pages that need to be swapped from main memory
            index = 0
            for frame in main_memory:
                if(frame in pages_to_swap):
                    main_memory[index] = None
                    free_frames += 1
                    frames_swapped += 1
                index += 1
            
            #Add swapped pages to secondary memory
            for page in pages_to_swap:
                secondary_memory.append(page)
            
            #Map swapped pages to none in page table
            for page in page_tables[job_move]:
                page_tables[job_move][page] = None
            
        #Add suspended job to main memory

        #Remove pages from secondary memory
        for page in jobs_to_pages_map[job_info[0]]:
            secondary_memory.remove(page)

        #Add pages to main memory, update page table, update free frames
        job_index = 0
        for i in range(len(main_memory)):
            if(main_memory[i] == None):
                if(job_index == len(jobs_to_pages_map[job_info[0]])):
                    break
                else:
                    main_memory[i] = jobs_to_pages_map[job_info[0]][job_index]
                    page_tables[job_info[0]][jobs_to_pages_map[job_info[0]][job_index]] = i
                    job_index += 1
                    free_frames -= 1
        
        #Add resumed process to job age queue
        job_age_queue.append(job_info[0])

    #If process can fit, simply move it to main memory
    else:
        
        #Remove pages from secondary memory
        for page in jobs_to_pages_map[job_info[0]]:
            secondary_memory.remove(page)

        #Add pages to main memory, update page table, update free frames
        job_index = 0
        for i in range(len(main_memory)):
            if(main_memory[i] == None):
                if(job_index == len(jobs_to_pages_map[job_info[0]])):
                    break
                else:
                    main_memory[i] = jobs_to_pages_map[job_info[0]][job_index]
                    page_tables[job_info[0]][jobs_to_pages_map[job_info[0]][job_index]] = i
                    job_index += 1
                    free_frames -= 1
        
        #Add resumed process to job age queue
        job_age_queue.append(job_info[0])

    return(free_frames)
#---------------------------------------------------------------------------------------------------------------------------------------------

#Function that reads job requests and modifies memory appropriately according to the simple paging system
#--------------------------------------------------------------------------------------------------------
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
    main_memory_dataframe = pd.DataFrame()
    EXIT = False

    #Main loop
    while(EXIT != True):

        #If a file argument is present, execute requests in the file
        if(len(memory_info_list) > 2):

            requests_file = open(memory_info_list[2], "r")

            #Skip header
            line = requests_file.readline()

            while(line != ""):
                line = requests_file.readline()
                if(line == ""):
                    break
                job_info = line.split()

                #job_info = [job ID, Command]

                #If request does not contain valid number of arguments, reject request
                if(len(job_info) > 2 or len(job_info) < 1):
                    print("ERROR: REQUEST MUST CONTAIN EITHER 1 OR 2 ARGUMENTS")

                #If job ID is exit, terminate simulation
                elif(job_info[0] == "exit"):
                    print("You have exited the program")
                    EXIT = True
                    break

                #If Job_ID is "print", print the current state of memory (Complete last)
                elif(job_info[0] == "print"):
                    
                    print("MEMORY SNAPSHOT\n--------------------------------------------------\n")

                    #Print main memory as a pandas dataframe
                    main_memory_dataframe = pd.DataFrame(main_memory.copy(), columns=['Main Memory'])
                    row_names = ['Frame ' + str(i+1) for i in range(len(main_memory_dataframe))]
                    main_memory_dataframe.index = row_names
                    for i in range(len(main_memory_dataframe)):
                        if(main_memory_dataframe.loc["Frame {}".format(i+1), "Main Memory"] == None):
                            main_memory_dataframe.loc["Frame {}".format(i+1), "Main Memory"] = "Free"
                    print(main_memory_dataframe)

                    #For each process, print its page table and internal fragmentation
                    print()
                    for process in existing_jobs:
                        print("Process {}\n----------------------".format(process))
                        print("Internal Fragmentation: {}".format(internal_fragmentation[jobs_to_pages_map[process][-1]]))

                        print("\nPage Table:")
                        page_table = page_tables[process]
                        page_table_df = pd.DataFrame(list(page_table.items()), columns=["Pages", "Frames"])
                        for i in range(len(page_table_df)):
                            if(page_table_df.loc[i, "Frames"] != None):
                                page_table_df.loc[i, "Frames"] = page_table_df.loc[i, "Frames"] + 1
                        if(page_table_df.loc[0, "Frames"] == None):
                            for i in range(len(page_table_df)):
                                page_table_df.loc[i, "Frames"] = "In Secondary Memory"
                        print(page_table_df, "\n----------------------\n")
                    print("--------------------------------------------------\n")


                #If job ID is not castable to an int and is not exit or print, reject request
                elif(isInt(job_info[0]) == False and (job_info[0] != "exit" or job_info[0] != "print")):
                     print("ERROR: INVALID COMMAND")

                #If command is not an integer, reject request
                elif(isInt(job_info[1]) == False):
                    print("ERROR: COMMAND IS NOT AN INTEGER")

                #If process is too large to fit in main memory, reject the process
                elif(int(job_info[1]) > (len(main_memory) * int(memory_info_list[1]))):
                    print("ERROR: PROCESS IS TOO LARGE FOR MAIN MEMORY")

                #If job doesn't yet exist and command 0,-1, or -2 is called, reject request
                elif(job_info[0] not in existing_jobs and (int(job_info[1]) == 0 or int(job_info[1]) == -1 or int(job_info[1]) == -2)):
                    print("ERROR: CANNOT EXECUTE COMMAND. JOB DOES NOT CURRENTLY EXIST")

                #If command value is invalid, reject request
                elif(int(job_info[1]) < -2):
                    print("ERROR: INVALID COMMAND")
            
                #If a new process is being added, perform necessary actions to put it in main memory by calling add_new_process()
                elif(job_info[0] not in existing_jobs):
                    free_frames = add_new_process(existing_jobs, job_info, memory_info_list, internal_fragmentation, jobs_to_pages_map, free_frames, page_tables, job_age_queue, main_memory, secondary_memory)
                    
                #Carries out commands 0, -1, and -2 for already existing jobs
                elif(job_info[0] in existing_jobs):

                    #If job is already in system and is added to memory by user, reject
                    if(int(job_info[1]) != 0 and int(job_info[1]) != -1 and int(job_info[1]) != -2):
                        print("ERROR: PROCESS IS ALREADY IN THE MEMORY SYSTEM")

                    #If command is 0, remove the job from memory
                    elif(int(job_info[1]) == 0):
                        free_frames = remove_process(main_memory, jobs_to_pages_map, job_info, existing_jobs, free_frames, job_age_queue, page_tables, internal_fragmentation, secondary_memory)   
                
                    #If command is -1, move job to secondary memory
                    elif(int(job_info[1]) == -1):
                        free_frames = suspend_process(main_memory, secondary_memory, page_tables, internal_fragmentation, jobs_to_pages_map, job_age_queue, free_frames, job_info)
                    
                    #If command is -2, put suspended job back into main memory
                    elif(int(job_info[1]) == -2):
                        free_frames = resume_process(main_memory, secondary_memory, page_tables, internal_fragmentation, jobs_to_pages_map, job_age_queue, free_frames, job_info)
            
            #Switch to dynamic user requests by deleting file from the list
            memory_info_list.pop()

        #Dynamic User commands
        elif(EXIT != True):
            request_string =  input("Input your request in the form 'Job_ID Command': ")
            request_list = request_string.split()

            #request_list = [job ID, Command]

            #input error checking

            #If request doesn't contain valid number of arguments, reject request
            if(len(request_list) > 2 or len(request_list) < 1):
                print("ERROR: REQUEST MUST CONTAIN EITHER 1 OR 2 ARGUMENTS")

            #If job ID is "exit", terminate simulation
            elif(request_list[0] == "exit"):
                print("You have exited the program")
                EXIT = True

            #If job ID is "print", print current state of memory (Complete Last)
            elif(request_list[0] == "print"):

                print("MEMORY SNAPSHOT\n--------------------------------------------------\n")
                
                #Print main memory as a pandas dataframe
                main_memory_dataframe = pd.DataFrame(main_memory.copy(), columns=['Main Memory'])
                row_names = ['Frame ' + str(i+1) for i in range(len(main_memory_dataframe))]
                main_memory_dataframe.index = row_names
                for i in range(len(main_memory_dataframe)):
                    if(main_memory_dataframe.loc["Frame {}".format(i+1), "Main Memory"] == None):
                        main_memory_dataframe.loc["Frame {}".format(i+1), "Main Memory"] = "Free"
                print(main_memory_dataframe)

                #For each process, print its page table and internal fragmentation
                print()
                for process in existing_jobs:
                    print("Process {}\n----------------------".format(process))
                    print("Internal Fragmentation: {}".format(internal_fragmentation[jobs_to_pages_map[process][-1]]))

                    print("\nPage Table:")
                    page_table = page_tables[process]
                    page_table_df = pd.DataFrame(list(page_table.items()), columns=["Pages", "Frames"])
                    for i in range(len(page_table_df)):
                        if(page_table_df.loc[i, "Frames"] != None):
                            page_table_df.loc[i, "Frames"] = page_table_df.loc[i, "Frames"] + 1
                    if(page_table_df.loc[0, "Frames"] == None):
                        for i in range(len(page_table_df)):
                            page_table_df.loc[i, "Frames"] = "In Secondary Memory"
                    print(page_table_df, "\n----------------------\n")
                print("--------------------------------------------------\n")

            #If job ID is not castable to int and it's not exit or print, reject request
            elif(isInt(request_list[0]) == False and (request_list[0] != "exit" or request_list[0] != "print")):
                print("ERROR: INVALID COMMAND")

            #If command is not an integer, reject request
            elif(isInt(request_list[1]) == False):
               print("ERROR: COMMAND IS NOT AN INTEGER")
            
            #If process is too large for main memory, reject process
            elif(int(request_list[1]) > (len(main_memory) * int(memory_info_list[1]))):
                print("ERROR: PROCESS IS TOO LARGE FOR MAIN MEMORY") 

            #If process does not exist and the user issues command 0,-1, or -2, reject request
            elif(request_list[0] not in existing_jobs and (int(request_list[1]) == 0 or int(request_list[1]) == -1 or int(request_list[1]) == -2)):
                print("ERROR: CANNOT EXECUTE COMMAND. PROCESS DOES NOT CURRENTLY EXIST")

            #If command is less than -2, reject request
            elif(int(request_list[1]) < -2):
                print("ERROR: INVALID COMMAND")

            #If new process is being added, perform necessary actions to put it into main memory by calling add_new_process()
            elif(request_list[0] not in existing_jobs):
                free_frames = add_new_process(existing_jobs, request_list, memory_info_list, internal_fragmentation, jobs_to_pages_map, free_frames, page_tables, job_age_queue, main_memory, secondary_memory)

            #Carries out commands 0,-1, and -2
            elif(request_list[0] in existing_jobs):

                #If they try to add an already existing process, reject request
                if(int(request_list[1]) != 0 and int(request_list[1]) != -1 and int(request_list[1]) != -2):
                    print("ERROR: PROCESS IS ALREADY IN THE MEMORY SYSTEM")

                #If command is 0, remove process from memory
                elif(int(request_list[1]) == 0):
                    free_frames = remove_process(main_memory, jobs_to_pages_map, request_list, existing_jobs, free_frames, job_age_queue, page_tables, internal_fragmentation, secondary_memory)
                
                elif(int(request_list[1]) == -1):
                    free_frames = suspend_process(main_memory, secondary_memory, page_tables, internal_fragmentation, jobs_to_pages_map, job_age_queue, free_frames, request_list)

                elif(int(request_list[1]) == -2):
                    free_frames = resume_process(main_memory, secondary_memory, page_tables, internal_fragmentation, jobs_to_pages_map, job_age_queue, free_frames, request_list)
#--------------------------------------------------------------------------------------------------------

#Obtain memory size, page size, and job requests file from user
#--------------------------------------------------------------
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
    if(len(sys.argv) == 3):
        memory_info_list.append(sys.argv[1])
        memory_info_list.append(sys.argv[2])
        main_loop(memory_info_list)
    else:
        memory_info_list.append(sys.argv[1])
        memory_info_list.append(sys.argv[2])
        memory_info_list.append(sys.argv[3])
        main_loop(memory_info_list)
#--------------------------------------------------------------