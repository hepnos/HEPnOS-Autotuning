import numpy as np
import pandas as pd
from sklearn.preprocessing import scale
# from scipy._lib.six import xrange
from six.moves import xrange
import numpy as np

import numbers

# Sourced from:
# https://sourceforge.net/projects/gower-distance-4python/files/

#Normalize the array
def normalize_mixed_data_columns(arr, dtypes):
  
    if isinstance(arr,pd.DataFrame):
       arr =np.asmatrix(arr.copy())
    elif isinstance(arr,np.ndarray):
       arr =arr.copy()
    else:
       raise ValueError('A DataFrame or ndarray must be provided.')
    rows,cols = arr.shape
    for col in xrange(cols):
        if np.issubdtype(dtypes[col],np.number):
            max = arr[:,col].max()+0.0  #Converts it to double
            if (cols>1):
                arr[:,col] /= max
            else:    
                arr= arr/max
    return( arr)

#This is to obtain the range (max-min) values of each numeric column
def calc_range_mixed_data_columns(arr, dtypes):
    rows,cols = arr.shape
    
    result = np.zeros(cols)
    for col in xrange(cols):
        if np.issubdtype(dtypes[col],np.number):
            result[col]= arr[:,col].max()-arr[:,col].min()
    return( result)
    

#This function must be refactored on pdist module to support mixed data
def _copy_array_if_base_present(a):
    if a.base is not None:
        return a.copy()
    elif np.issubsctype(a, np.float32):
        return np.array(a, dtype=np.double)
    else:
        return a

#This function must be refactored on pdist module to support mixed data
def _convert_to_double(X):
    if X.dtype == np.object:
        return X.copy()
    if X.dtype != np.double:
        X = X.astype(np.double)
    if not X.flags.contiguous:
        X = X.copy()
    return X

#This function was copied from pdist because it is private. No change in the original function.
def _validate_vector(u, dtype=None):
    # XXX Is order='c' really necessary?
    u = np.asarray(u, dtype=dtype, order='c').squeeze()
    # Ensure values such as u=1 and u=[1] still return 1-D arrays.
    u = np.atleast_1d(u)
    if u.ndim > 1:
        raise ValueError("Input vector should be 1-D.")
    return u


#An excerpt from pdist function only with the basic structure to call the gower dist. 
#The original pdist must be adapted for Gower using this as example.
def pdist_(X, metric='euclidean', p=2, w=None, V=None, VI=None):
    X = np.asarray(X, order='c')

    # The C code doesn't do striding.
    X = _copy_array_if_base_present(X)

    s = X.shape
    #if len(s) != 2:
    #    raise ValueError('A 2-dimensional array must be passed.')

    m, n = s
    dm = np.zeros((m * (m - 1)) // 2, dtype=np.double)

    #(...)
    dfun = metric
    k = 0
    for i in xrange(0, m - 1):
        for j in xrange(i + 1, m):
            dm[k] = dfun(X[i], X[j],V=V,w=w,VI=VI)
            k = k + 1

    return dm


from scipy.spatial.distance import pdist, squareform
import numbers

def gower(xi, xj,V=None,w=None,VI=None):
    cols = len(xj)
    
##    xi=_validate_vector(xi)
##    xj=_validate_vector(xj)
##
##    if V is None:
##        raise ValueError('An array with the (max-min) ranges for each numeric column must be passed in V.')
##
##    if VI is None:
##        raise ValueError('An array with the dtypes or each numeric column must be passed in VI.')

    if w is None:
        w=[1]*cols
    
    sum_sij =0.0
    sum_wij =0.0
    for col in xrange(cols):
        sij=0.0
        wij=0.0
        
        if np.issubdtype(VI[col], np.number):
            sij=abs(xi[col]-xj[col])/(V[col])
            wij=(w[col],0)[pd.isnull(xi[col]) or pd.isnull(xj[col])]
            
        else:
            sij=(1,0)[xi[col]==xj[col]]
            wij=(w[col],0)[pd.isnull(xi[col]) and pd.isnull(xj[col])]
        
        sum_sij+= (wij*sij)
        sum_wij+=wij

    
    return(sum_sij/sum_wij)




