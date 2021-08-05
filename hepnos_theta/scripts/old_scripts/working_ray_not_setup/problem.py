from deephyper.problem import HpProblem

Problem = HpProblem()

# parameters 
'''
Number of threads: the number of threads that a server can use, not including the progress thread. Since 2 servers are deployed on each node, this number can range from 0 to 31.
Number of databases: the number of databases per server for event data and for product data. For example if set to 16, each server will create 16 databases for event data and 16 other databases for produåct data.
Busy spin: true or false, indicating whether Mercury should be set to busy-spin.
Async: true or false, indicating whether the client will execute store operation asynchronously, trying to overlap with file read operations.
Batch size: the batch size on clients (int).
Number of threads used by each benchmark process (should be between 1 and 31)
Size of the batches read from HEPnOS (I would suggest between 8 and 1024, to start with)
Size of the batches exchanged by benchmark processes (same range)
'''

Problem.add_dim('num_threads', (0, 31)) # int 
Problem.add_dim('num_databases', (1,10)) # int  
Problem.add_dim('busy_spin', [True, False]) # True of false 
Problem.add_dim('progress_thread', [True, False]) # True of false Async 
Problem.add_dim('batch_size', (1, 2048)) # int  
# benchmark
Problem.add_dim('num_threads_b', (1, 31)) # int  
Problem.add_dim('batch_size_in', (8, 1024)) # int  
Problem.add_dim('batch_size_out', (8, 1024)) # int  

Problem.add_starting_point(
    num_threads=31,
    num_databases=1,
    busy_spin=False,
    progress_thread=False,
    batch_size=1024,
    num_threads_b=31,
    batch_size_in=32,
    batch_size_out=1024
)

if __name__ == '__main__':
    print(Problem)
