"""A small personal package created to store code and data I often reuse. 

I'll continue to update it with useful functions that I find myself reusing. The `apoor.data` module has some common datasets and functions for reading them in as pandas DataFrames.
"""

# Version string
__version__ = "1.3.1"



import itertools as it
import numpy as np
from . import data

from typing import Any, List, Callable, Tuple, Iterable


def fdir(o: Any) -> List[str]:
    """Filtered dir(). Same as builtin dir()
    function without private attributes.

    :param o: Object being inspected
    :return: "Public attributes" of o
    """
    return [a for a in dir(o) if a[0] != "_"]

def set_seed(n:int):
    """Sets numpy's random seed.

    :param n: The value used to set numpy's random seed.
    :type n: int
    """
    np.random.seed(n)


def make_scale(dmin:float,dmax:float,rmin:float,rmax:float,clamp:bool=False) -> Callable[[float],float]:
    """Scale function factory.
    
    Creates a scale function to map a number from a domain to a range.

    :param dmin: Domain's start value
    :param dmax: Domain's end value
    :param rmin: Range's start value
    :param rmax: Range's end value
    :param clamp: If the result is outside the range, return 
        clamped value (default: False)
    :return: A scale function taking one numeric argument and 
        returns the value mapped from the domain to the range 
        (and clamped if `clamp` flag is set).

    Examples:
        >>> s = make_scale(0,1,0,10)
        >>> s(0.1)
        1.0

        >>> s = make_scale(0,10,10,0)
        >>> s(1.0)
        9.0

        >>> s = make_scale(0,1,0,1,clamp=True)
        >>> s(100)
        1.0
    """
    drange = dmax - dmin
    rrange = rmax - rmin
    scale_factor = rrange / drange
    def scale(n):
        n_ = (n - dmin) * scale_factor + rmin
        if clamp: return min(max(n_,rmin),rmax)
        else: return n_ 
    return scale
    

def train_test_split(*arrays, test_pct: float = 0.15, val_set: bool = False, val_pct: float = 0.15) -> Tuple[np.ndarray]:
    """Splits arrays into train & test sets.

    Splits arrays into train, test, and (optionally) validation sets using the supplied percentages.

    :param *arrays: An arbitrary number of sequences to be split
        into train, test, and (optionally) validation sets. Must 
        have at least one array.
    :param test_pct: Float in the range ``[0,1]``. Percent of total 
        ``n`` values to include in test set.
        
        The train set will have `1.0 - test_pct` pct of
        values (or `1.0 - test_pct - val_pct` pct of values
        if `val_set == True`).

    :param val_set: Whether or not to return a validation set,
        in addition to a test set.

    :param val_pct: `float` in the range ``[0,1]``. Percent 
        of total n values to include in test set.
        
        Ignored if ``val_set == False``.
        
        The train set will have ``1.0 - test_pct - val_pct`` 
        pct of values.

    :returns: splits tuple of numpy arrays. Input arrays 
        split into train, test, val sets.
        
        If ``val_set == False``, ``len(splits) == 2 * len(arrays)``,
        or if ``val_set == True``, ``len(splits) == 3 * len(arrays)``.

    Example:
        >>> x = np.arange(10)
        >>> train_test_split(x)
        (array([3, 9, 4, 2, 1, 0, 7, 5, 8]), array([6]))

        >>> x = np.arange(10)
        >>> y = x[::-1]
        >>> x_train, x_test, y_train, y_test = train_test_split(x,y)
        >>> x_train, x_test, y_train, y_test
        (array([1, 3, 5, 8, 4, 7, 6, 9]),
         array([0, 2]),
         array([8, 6, 4, 1, 5, 2, 3, 0]),
         array([9, 7]))

        >>> train_test_split(x,test_pct=0.3,val_set=True,val_pct=0.2)
        (array([0, 9, 5, 7, 6, 2, 8]), 
         array([1, 3, 4]), 
         array([3, 4]))

    """
    # Perform input checks
    assert arrays, "No arrays supplied"
    lens = [len(a) for a in arrays]
    assert len(set(lens)) == 1, "arrays have varying lengths"
    assert lens[0] > 0, "supplied arrays have `len == 0`"
    if val_set:
        assert 0.0 <= test_pct <= 1.0, "`test_pct` must be in the range `0.0 <= test_pct <= 1.0`"
        assert 0.0 <= val_pct <= 1.0, "`val_pct` must be in the range `0.0 <= val_pct <= 1.0`"
        assert test_pct + val_pct <= 1.0, "Can't have `test_pc + val_pct >= 1.0`"
    else:
        assert 0.0 <= test_pct <= 1.0, "`test_pct` must be in the range `0.0 <= test_pct <= 1.0`"
        assert test_pct <= 1.0, "Can't have `test_pc >= 1.0`"
    # Calculate lengths
    n = lens[0]
    n_test = int(n * test_pct)
    # Shuffle the indexes
    indexes = np.arange(n)
    np.random.shuffle(indexes)
    # Split the data
    if val_set:
        n_val = int(n * val_pct)
        n_train = n - n_test - n_val
        splits = (
            (
                a[indexes[:n_train]], 
                a[indexes[n_train:n_train+n_test]], 
                a[indexes[-n_val:]]
            )
            for a in map(np.asarray,arrays)
        )
    else:
        n_train = n - n_test
        splits = (
            (a[indexes[:n_train]], a[indexes[n_train:]])
            for a in map(np.asarray,arrays)
        )
    return tuple(it.chain(*splits))


def to_onehot(y: np.ndarray, num_classes: int = None, dtype="float32") -> np.ndarray:
    """Expands a 1D categorical vector to
    a 2D, onehot-encoded categorical matrix.

    :param y: 1D categorical vector
    :param num_classes: Number of categories in (and width of) 
        the output matrix. 

        If ``num_classes`` is ``None``, setsto ``max(y) + 1``.
    :param dtype: Data type of output matrix
    :returns: 2D one-hot encoded category matrix
    
    Examples:
        >>> data = np.array([0,2,1,3])
        >>> apoor.to_onehot(data)
        array([[1., 0., 0., 0.],
               [0., 0., 1., 0.],
               [0., 1., 0., 0.],
               [0., 0., 0., 1.]])

    """
    if num_classes is None:
        num_classes = np.max(y) + 1
    return np.identity(num_classes,dtype=dtype)[y]


def ibuff(itr: Iterable, bsize: int = 1) -> Iterable[List]:
    """Creates an iterable that yields elements
    from ``itr`` grouped into lists of size ``bsize``.

    If ``itr`` can't evenly be grouped into lists of size
    ``bsize``, the final list will have the remaining
    elements.

    :param itr: The interable to be buffered.
    :param bsize: Positive integer, representing the number of
        values from ``itr`` to be yielded together.

        The final list yielded may not be of size ``bsize`` if
        ``len(itr)`` doesn't evenly divide into groups of ``bsize``.
    :yields: Buffered elements from ``itr``, grouped into lists
        of size up to ``bsize``.
    :raises TypeError: If ``bsize`` isn't an integer.
    :raises ValueError: If ``bsize`` isn't positive.
    
    Examples:
        >>> for b in apoor.ibuff(range(10),3):
        ...     print(b)
        [0, 1, 2]
        [3, 4, 5]
        [6, 7, 8]
        [9]
    """
    # Perform checks
    if not isinstance(bsize,int):
        raise TypeError("bsize needs to be a positive integer.")
    if bsize <= 1:
        raise ValueError("bsize needs to be a positive integer.")
    # Initialize the buffer
    buff = []
    for v in itr:
        if len(buff) < bsize: # If buff not full, append
            buff.append(v)
        else:                 # Otherwise yield and reinit
            yield buff
            buff = [v]
    # Check if there's anything left in the buffer
    if len(buff) > 0:
        yield buff



