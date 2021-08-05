from deephyper.problem import HpProblem
import ConfigSpace as cs
import ConfigSpace.hyperparameters as CSH

Problem = HpProblem(seed=45)

#Problem.add_dim('units', (1, 100))
#Problem.add_dim('activation', ['NA', 'relu', 'sigmoid', 'tanh'])
#Problem.add_dim('lr', (0.0001, 1.))

# parameters 
'''
Number of threads: the number of threads that a server can use, not including the progress thread. Since 2 servers are deployed on each node, this number can range from 0 to 31.

Number of databases: the number of databases per server for event data and for product data. For example if set to 16, each server will create 16 databases for event data and 16 other databases for produåct data.

Busy spin: true or false, indicating whether Mercury should be set to busy-spin.

Async: true or false, indicating whether the client will execute store operation asynchronously, trying to overlap with file read operations.

Batch size: the batch size on clients (int).
'''

Problem.add_dim('num_threads', (0, 31)) # int x1 
Problem.add_dim('num_databases', (1,10)) # int  x2
Problem.add_dim('busy_spin', [True, False]) # True of false x3
Problem.add_dim('progress_thread', [True, False]) # True of false Async x4 
Problem.add_dim('batch_size', (1, 2048)) # int  x5
# benchmark
num_threads_b_choice = [0.0]
a = 0
for _ in range(32): 
    a += 1/32. 
    num_threads_b_choice.append(a)
ord_hp_1 = CSH.OrdinalHyperparameter(name='num_threads_b', sequence=num_threads_b_choice,default_value=1.0)
Problem.add_hyperparameter(ord_hp_1)
# Problem.add_dim('num_threads_b', (0., 1.)) # int  x6
Problem.add_dim('batch_size_in', (8, 1024)) # int  x7
Problem.add_dim('batch_size_out', (8, 1024)) # int  x8
Problem.add_dim('pep_pes_per_node', (1, 64)) # x9 
pep_cores_per_pe_choice = [0.0]    
a = 0
for _ in range(64): 
    a += 1/64. 
    pep_cores_per_pe_choice.append(a)

# Problem.add_dim('pep_cores_per_pe', (0., 1.)) # x10
ord_hp_2 = CSH.OrdinalHyperparameter(name='pep_cores_per_pe', sequence=pep_cores_per_pe_choice,default_value=1.0)
Problem.add_hyperparameter(ord_hp_2)
'''
Number of threads used by each benchmark process (should be between 1 and 31)
Size of the batches read from HEPnOS (I would suggest between 8 and 1024, to start with)
Size of the batches exchanged by benchmark processes (same range)
x6<=x10 and x9*x10<= 64

x6_0 = [0,1]  # actual range [1,31] integer: the number of processing threads per benchmark process
x9 = [1,64]   # actual range [1,64] integer: the number of PE per node for the benchmark
x10_0 = [0,1] # actual range [1,64] integer: the number of cores per PE for the benchmark
x10 = max(1, int(x10_0*64/x9)) where x10 ranges in [1,64] and x9*x10 <= 64. 
x6 = min(31, int(1+(x6_0*0.5*(x10-1)))) where x6 ranges in [1,31] and x6 <= x10 


'''

Problem.add_starting_point(
    num_threads=31,
    num_databases=1,
    busy_spin=False,
    progress_thread=False,
    batch_size=1024,
    num_threads_b=1.0,
    batch_size_in=32,
    batch_size_out=1024, 
    pep_pes_per_node = 2,
    pep_cores_per_pe = 1.0
)

if __name__ == '__main__':
    print(Problem)
