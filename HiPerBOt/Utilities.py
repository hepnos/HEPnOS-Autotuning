import pandas as pd
import warnings
import sys
import matplotlib.pyplot as plt
import numpy as np
import Gower as gow

class Utilities:
    def load_data(self, filename, response = None):
        '''
            Load data from given file and return the domain and signal from the data
            Input:
                filename: Name of csv file from which the data have to be extracted
                response (optional): Explicitly specify the function 'signal' in the data
            Output:
                domain: (num_samples, num_columns - 1)
                signal (optional): function value (typically the response variable) - Shape (num_samples, 1)
                If not specified, the last column of the data is used as the signal
        '''
        data = pd.read_csv(filename)

        # Check if data has column headers, else produce a warning
        colnames = data.columns.values.tolist()
        
        if any(field.isdigit() for field in colnames):
            warnings.warn("Warning: Data might not have headers")

        m, n = data.shape
        if m < 2: # File might have no data or have only column headers
            warnings.warn("No data in the file")

        # Extract domain and signal
        try: 
            if response is not None:
                signal = data[response]
                signal = signal.values.reshape(len(signal), 1)
#                 domain = data.ix[:, data.columns != response] # Domain = all but the response column
                domain = data.iloc[:, data.columns != response] # Domain = all but the response column
                assert (domain.shape[0] == m) and (signal.shape[0] == m), "Domain and signal not of the same size"
                return domain, signal
            
        except Exception as e:
            print("KeyError: No column with the name '", response, "'")

        # If no response has been specified, return the last column as the signal
        # and the rest of the data as the domain
#         domain_alt = data.ix[:, data.columns != colnames[n-1]]
        domain_alt = data.iloc[:, data.columns != colnames[n-1]]
        signal_alt = data[colnames[n-1]]
        signal_alt = signal_alt.values.reshape(len(signal_alt), 1)
        return domain_alt, signal_alt


    def data_norm(self, domain, signal, feats_drop=None, response_name='ExecTime', response_norm=False):
        '''
            Normalize data between 0 and 1 and return a Pandas dataframes
            Input:
                domain: data domain of shape (num_samples, num_features), doesn't include the response variable
                signal: function value (typically the response variable)
                feats_drop (optional): Features to be dropped before normalization
                response_name (optional): Name of the response variable. Default - ExecTime
                response_norm (optional): Normalize the response variable also. Default - Not normalized.
                
            Output:
                data_pd: Normalized data (between 0 and 1) in a dataframe
        '''
    
        # Create a copy of the data and drop unnecessary features
        data = domain.copy()
        if feats_drop is not None:
            data = data.drop(feats_drop, axis=1)
        data[response_name] = signal
        n_feat = data.shape[1] # Get number of columns
        dtypes = data.dtypes   # Get column datatypes
        colnames = data.columns.values # Get column names

        # Normalize and convert to pandas object again
        if response_norm is False:
            # Normalize all columns apart from the response (between 0 and 1) - Divides by max of feature
            sample_norm = gow.normalize_mixed_data_columns(data.iloc[:, :n_feat], dtypes[:n_feat])
            data_pd = pd.DataFrame(sample_norm[:, :n_feat])
            data_pd.columns = colnames[:n_feat]
            data_pd[response_name] = signal
        else:
            sample_norm = gow.normalize_mixed_data_columns(data, dtypes)
            data_pd = pd.DataFrame(sample_norm)
            data_pd.columns = colnames

        return data_pd


    def convert_pd_dtype(self, data, feats=None, totype=None):
        '''
            Convert datatypes of specified features in the input Pandas dataframe to type=totype
        '''
        data_copy = data.copy()
        for f in feats:
            data_copy[f] = data_copy[f].astype(totype)
        
        return data_copy

    def xy_plot(self, x, y=None, xlabel='X', ylabel='Y', title='x vs. y', plot_type='line', tick_label=None,
                marker='o'):
        '''
            Plot a 2-D x vs. y graph
            Input:
                x: 1-D vector/array
                y (optional): 1-D vector/array, if not present and if plot_type is 'line', then x is plotted along with its index
                xlabel and ylabel (optional): Axes labels
                title (optional): Plot title
                plot_type (optional): line, bar and scatter are supported as of now. Default - line.
                tick_label (optional): Tick labels to be used for the bar plot 
                marker (optional): Determine how the data points are highlighted on the plot. Default - 'o'. Other options
                similar to matplotlib.pyplot markers
        '''
        u = np.atleast_1d(x)
        v = np.atleast_1d(y)
        if u.ndim > 1 or v.ndim > 1:
          raise ValueError("Input vectors x and y should be 1-D.")

        if plot_type=='line':
            if y is None:
                plt.plot(np.arange(len(x)), x, marker=marker)
                plt.xlabel('Index')
            else:
                plt.plot(x, y, marker=marker)
                plt.xlabel(xlabel)
        elif plot_type=='bar':
            if y is None:
                print("y cannot be empty for a bar plot")
            else:
                plt.bar(x, y, tick_label=tick_label)
                plt.xlabel(xlabel)
        elif plot_type=='scatter':
            if y is None:
                print("y cannot be empty for a scatter plot")
            else:
                plt.scatter(x, y)
                plt.xlabel(xlabel)
        else:
            print("Only 'bar', 'line' and 'scatter' plots are supported as of now")

        plt.ylabel(ylabel)
        plt.title(title)
        plt.show()

