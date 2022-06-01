"""Dataset functions.

Includes functions for loading common datasets as pandas DataFrames.
"""

import io
import gzip
import pkgutil

import pandas as pd

_datasets = [
    "iris",
    "boston"
]

def _decompress(bstr: bytes):
    """CSV gzip decompression helper fn.

    Helper function for decompressing
    a gzip-ed CSV dataset and converting
    it to a pandas DataFrame.

    Args:
        bstr: 
            Binary string of a CSV with gzip compression. 
    Returns:
        Pandas DataFrame from compressed dataset.
    """
    decomp = gzip.decompress(bstr).decode()
    f = io.StringIO(decomp)
    return pd.read_csv(f,encoding="utf-8")

def list_datasets():
    """Get available datasets.
    
    Each dataset in the list can be loaded
    with a load_<name> function, where
    <name> is the name of the dataset.

    Returns:
        Returns a list of the available datasets.
    """
    return _datasets[:]

def load_iris():
    """ Load iris dataset.

    Loads the iris dataset as a Pandas
    DataFrame.

    Iris dataset: https://archive.ics.uci.edu/ml/datasets/iris

    Returns:
        Iris dataset as a Pandas DataFrame.
    """
    compressed = pkgutil.get_data('apoor.data', '_data/iris.csv.gz')
    df = _decompress(compressed)
    df["target"] = df["target"].astype("category")
    return df

def load_boston():
    """Load boston housing dataset.

    Loads the boston housing dataset as a Pandas
    DataFrame.

    Boston Housing dataset: https://www.cs.toronto.edu/~delve/data/boston/bostonDetail.html

    Returns:
        Boston Housing dataset as a Pandas DataFrame.
    """
    compressed = pkgutil.get_data('apoor.data', '_data/boston.csv.gz')
    df = _decompress(compressed)
    df.CHAS = df.CHAS.astype("int8")
    df.MEDV = df.MEDV.astype("int32")
    return df


