from __future__ import division

# TODO: Andreza
import numpy as np
import pandas as pd
import time
from scipy.interpolate import interp1d

from pymove.core import grid

#from scipy.ndimage.interpolation import shift
import math

#import timeutils
import datetime
from pandas._libs.tslibs.timestamps import Timestamp
from ipywidgets import IntProgress, HTML, VBox
from IPython.display import display


"""main labels """
dic_labels = {"id" : 'id', 'lat' : 'lat', 'lon' : 'lon', 'datetime' : 'datetime'}

dic_features_label = {'tid' : 'tid', 'dist_to_prev' : 'dist_to_prev', "dist_to_next" : 'dist_to_next', 'dist_prev_to_next' : 'dist_prev_to_next', 
                    'time_to_prev' : 'time_to_prev', 'time_to_next' : 'time_to_next', 'speed_to_prev': 'speed_to_prev', 'speed_to_next': 'speed_to_next',
                    'period': 'period', 'day': 'day', 'index_grid_lat': 'index_grid_lat', 'index_grid_lon' : 'index_grid_lon',
                    'situation':'situation'}

def format_labels(df_, current_id, current_lat, current_lon, current_datetime):
    """ 
    Format the labels for the PyRoad lib pattern 
        labels output = lat, lon and datatime
    """ 
    dic_labels['id'] = current_id
    dic_labels['lon'] = current_lon
    dic_labels['lat'] = current_lat
    dic_labels['datetime'] = current_datetime
    return dic_labels

    
def show_trajectories_info(df_, dic_labels=dic_labels):
    """
        show dataset information from dataframe, this is number of rows, datetime interval, and bounding box 
    """
    try:
        print('\n======================= INFORMATION ABOUT DATASET =======================\n')
        print('Number of Points: {}\n'.format(df_.shape[0]))
        if dic_labels['id'] in df_:
            print('Number of IDs objects: {}\n'.format(df_[dic_labels['id']].nunique()))
        if dic_features_label['tid'] in df_:
            print('Number of TIDs trajectory: {}\n'.format(df_[dic_features_label['tid']].nunique()))
        if dic_labels['datetime'] in df_:
            print('Start Date:{}     End Date:{}\n'.format(df_[dic_labels['datetime']].min(), df_[dic_labels['datetime']].max()))
        if dic_labels['lat'] and dic_labels['lon'] in df_:
            print('Bounding Box:{}\n'.format(get_bbox(df_, dic_labels))) # bbox return =  Lat_min , Long_min, Lat_max, Long_max) 
        if dic_features_label['time_to_prev'] in df_:            
            print('Gap time MAX:{}     Gap time MIN:{}\n'.format(round(df_[dic_features_label['time_to_prev']].max(),3), round(df_[dic_features_label['time_to_prev']].min(), 3)))
        if dic_features_label['speed_to_prev'] in df_:            
            print('Speed MAX:{}    Speed MIN:{}\n'.format(round(df_[dic_features_label['speed_to_prev']].max(), 3), round(df_[dic_features_label['speed_to_prev']].min(), 3))) 
        if dic_features_label['dist_to_prev'] in df_:            
            print('Distance MAX:{}    Distance MIN:{}\n'.format(round(df_[dic_features_label['dist_to_prev']].max(),3), round(df_[dic_features_label['dist_to_prev']].min(), 3))) 
            
        print('\n=========================================================================\n')
    except Exception as e:
        raise e    

def get_bbox(df_, dic_labels=dic_labels):
    """
    A bounding box (usually shortened to bbox) is an area defined by two longitudes and two latitudes, where:
    Latitude is a decimal number between -90.0 and 90.0. Longitude is a decimal number between -180.0 and 180.0.
    They usually follow the standard format of: 
    bbox = left,bottom,right,top 
    bbox = min Longitude , min Latitude , max Longitude , max Latitude 
    """
    try:
        return (df_[dic_labels['lat']].min(), df_[dic_labels['lon']].min(), df_[dic_labels['lat']].max(), df_[dic_labels['lon']].max())
    except Exception as e:
        raise e

def save_bbox(bbox_tuple, file, tiles='OpenStreetMap', color='red'):
    m = folium.Map(tiles=tiles)
    m.fit_bounds([ [bbox_tuple[0], bbox_tuple[1]], [bbox_tuple[2], bbox_tuple[3]] ])
    points_ = [ (bbox_tuple[0], bbox_tuple[1]), (bbox_tuple[0], bbox_tuple[3]), 
                (bbox_tuple[2], bbox_tuple[3]), (bbox_tuple[2], bbox_tuple[1]),
                (bbox_tuple[0], bbox_tuple[1]) ]
    folium.PolyLine(points_, weight=3, color=color).add_to(m)
    m.save(file) 


#Funcoes do utils.py antigo

def log_progress(sequence, every=None, size=None, name='Items'):

    is_iterator = False
    if size is None:
        try:
            size = len(sequence)
        except TypeError:
            is_iterator = True
    if size is not None:
        if every is None:
            if size <= 200:
                every = 1
            else:
                every = int(size / 200)     # every 0.5%
    else:
        assert every is not None, 'sequence is iterator, set every'

    if is_iterator:
        progress = IntProgress(min=0, max=1, value=1)
        progress.bar_style = 'info'
    else:
        progress = IntProgress(min=0, max=size, value=0)
    label = HTML()
    box = VBox(children=[label, progress])
    display(box)

    index = 0
    try:
        for index, record in enumerate(sequence, 1):
            if index == 1 or index % every == 0:
                if is_iterator:
                    label.value = '{name}: {index} / ?'.format(
                        name=name,
                        index=index
                    )
                else:
                    progress.value = index
                    label.value = u'{name}: {index} / {size}'.format(
                        name=name,
                        index=index,
                        size=size
                    )
            yield record
    except:
        progress.bar_style = 'danger'
        raise
    else:
        progress.bar_style = 'success'
        progress.value = index
        label.value = "{name}: {index}".format(
            name=name,
            index=str(index or '?')
        )

def deltatime_str(deltatime_seconds):
    """
    input: time in seconds. e.g. 1082.7180936336517 -> output: '00:16:48.271'
    output example if more than 24 hours: 25:33:57.123
    https://stackoverflow.com/questions/3620943/measuring-elapsed-time-with-the-time-module 
    """
    time_int = int(deltatime_seconds)
    time_dec = int((deltatime_seconds - time_int) * 1000)
    time_str = '{:02d}:{:02d}:{:02d}.{:03d}'.format(time_int // 3600, time_int % 3600 // 60, time_int % 60, time_dec)
    return time_str
    
def progress_update(size_processed, size_all, start_time, curr_perc_int, step_perc=1):
    """
    update and print current progress.
    e.g.
    curr_perc_int, _ = pu.progress_update(size_processed, size_all, start_time, curr_perc_int)
    returns: curr_perc_int_new, deltatime_str
    """
    curr_perc_new = size_processed*100.0 / size_all
    curr_perc_int_new = int(curr_perc_new)
    if curr_perc_int_new != curr_perc_int and curr_perc_int_new % step_perc == 0:
        deltatime = time.time() - start_time
        deltatime_str_ = deltatime_str(deltatime)
        est_end = deltatime / curr_perc_new * 100
        est_time_str = deltatime_str(est_end - deltatime)
        print('({}/{}) {}% in {} - estimated end in {}'.format(size_processed, size_all, curr_perc_int_new, deltatime_str_, est_time_str))
        return curr_perc_int_new, deltatime_str
    else:
        return curr_perc_int_new, None

def timestamp_to_millis(timestamp):
    """
    Converts a local datetime to a POSIX timestamp in milliseconds (like in Java).
    e.g. '2015-12-12 08:00:00.123000' -> 1449907200123 (UTC)
    Java: Sat Dec 12 08:00:00 BRT 2015        -> 1449918000123
    """
    return Timestamp(timestamp).value // 1000000

def millis_to_timestamp(milliseconds):
    """
    Converts a POSIX timestamp in milliseconds (like in Java) to a local datetime.
    e.g.  1449907200123 -> Timestamp('2015-12-12 08:00:00.123000')
    Java: 1449918000123 -> Sat Dec 12 08:00:00 BRT 2015
    """
    return Timestamp(milliseconds, unit='ms')

def date_to_str(date1):
    return date1.strftime('%Y-%m-%d')

def time_to_str(time1):
    return time1.strftime('%H:%M:%S')

def str_to_datatime(dt_str):
    if len(dt_str) == 10:
        return datetime.datetime.strptime(dt_str, '%Y-%m-%d')
    else:
        return datetime.datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')

def str_to_time(dt_str):
    return datetime.datetime.strptime(dt_str, '%H:%M:%S')

def datetime_to_str(dt1):
    return dt1.strftime('%Y-%m-%d %H:%M:%S')

def now_str():
    return datetime_to_str(datetime.datetime.now())

def datetime_to_min(datetime):
    """
    Converts a datetime to an int representation in minutes. 
    To do the reverse use: min_to_dtime.
    e.g. in:datetime.datetime(2014, 1, 1, 20, 56) -> out:23143496
    """
    # get an integer time slot from a datetime
    # e.g. in:datetime.datetime(2014, 1, 1, 20, 55) -> out:23143495
    # e.g. in:datetime.datetime(2014, 1, 1, 20, 56) -> out:23143496
    return int((datetime - datetime.datetime.utcfromtimestamp(0)).total_seconds() / 60)

def min_to_datatime(min1):
    """
    Converts an int representation in minutes to a datetime. 
    To do the reverse use: dtime_to_min.
    e.g. in:23143496 -> out:datetime.datetime(2014, 1, 1, 20, 56)
    """
    # get a datetime from an integer time slot
    # e.g. in:23143495 -> out:datetime.datetime(2014, 1, 1, 20, 55)
    # e.g. in:23143496 -> out:datetime.datetime(2014, 1, 1, 20, 56)
    #return datetime.timedelta(minutes=min1) + datetime.datetime.utcfromtimestamp(0)
    # utcfromtimestamp (below) is much faster than the line above
    return datetime.datetime.utcfromtimestamp(min1 * 60)

def slot_of_day_to_time(slot_of_day1, time_window_duration=5):
    min1 = slot_of_day1 * time_window_duration
    return datetime.time(min1 // 60, min1 % 60)

def slot_of_day(dt1, time_window_duration=5):
    return (dt1.hour * 60 + dt1.minute) // time_window_duration

def datetime_slot(dt1, time_window_duration=5):
    minute = (dt1.minute // time_window_duration) * time_window_duration
    return datetime.datetime(dt1.year, dt1.month, dt1.day, dt1.hour, minute)

def datetime_str_to_min_slot(dt_str, time_window_duration=5):
    """
    Converts a datetime string to an int minute time slot (approximated to the time slot).
    Same as datetime_str_to_min_slot, but another implementation.
    To do almost the reverse (consider time slot approximation) use: min_to_dtime.
    e.g. in:'2014-01-01 20:56:00' -> out:23143495
    """
    dt = datetime_to_str(dt_str)
    dt_slot = datetime_slot(dt, time_window_duration)
    return dt_slot

def date_to_day_of_week_int(date):
    # Monday == 0...Sunday == 6
    return date.weekday()

#FUNCOES ARINA


def elapsed_time_dt(start_time):
    """Computes the elapsed time from a specific start time to the moment the function is called.

    Parameters
    ----------
    start_time : Datetime
        Specifies the start time of the time range to be computed.
    
    Returns
    -------
        time_dif : Integer
            Represents the time elapsed from the start time to the current time (when the function was called).        

    """
    time_dif = diff_time(start_time, datetime.datetime.now())
    return time_dif


def diff_time(start_time, end_time):
    """Computes the elapsed time from the start time to the end time specifed by the user.

    Parameters
    ----------
    start_time : Datetime
        Specifies the start time of the time range to be computed.
    
    end_time : Datetime
        Specifies the start time of the time range to be computed.

    Returns
    -------
        time_dif : Integer
            Represents the time elapsed from the start time to the current time (when the function was called).        

    """

    time_dif = int((end_time - start_time).total_seconds() * 1000)
    return time_dif


def working_day(dt, holidays):
    """Indices if a day specified by the user is a working day.

    Parameters
    ----------
    dt : Datetime
        Specifies the day the user wants to know if it is a business day.
    
    holidays : Datetime
        Indicates the days that are vacation days and therefore not working days. 

    Returns
    -------
        result : boolean
            if true, means that the day informed by the user is a working day.
            if false, means that the day is not a working day.
    """
    result = True

    if type(dt) == str:
        dt = date_to_str(dt)

    if type(dt) == datetime.datetime:
        dt = datetime.date(dt.year, dt.month, dt.day)

    if dt in holidays:
        result = False
    else:
        dow = date_to_day_of_week_int(dt)
        # 5 == saturday, 6 == sunday
        if dow == 5 or dow == 6:
            result = False

    return result


#Nao entendi o que ela faz
def std(sum_sq, size, avg):
    try:
        # squaring with * is over 3 times as faster than with **2
        # http://stackoverflow.com/questions/29046346/comparison-of-power-to-multiplication-in-python
        result = math.sqrt(sum_sq / size - avg * avg)
    except ValueError:
        e = '(size - avg^2) (size=%s, avg=%s, sum_sq=%s) should be non negative, but is %s' % \
            (size, avg, sum_sq, size - avg * avg)
        raise ValueError(e)
    return result


def avg_std(sum1, sum_sq, size):
    avg = sum1 / size
    return avg, std(sum_sq, size, avg)


def std_sample(sum_sq, size, avg):
    return std(sum_sq, size, avg) * math.sqrt(size / (size - 1))


def avg_std_sample(sum1, sum_sq, size):
    avg = sum1 / size
    return avg, std_sample(sum_sq, size, avg)


#função está dando erro ao rodar
def arrays_avg(values_array, weights_array=None):
    """Computes the mean of the elements of the array.

    values_array : array of floats
        The numbers used to calculate the mean. 
    
    weights_array : array of floats
        Used to calculate the weighted average, indicates the weight of each element in the array (values_array). 

    Returns 
    -------
        result : Float
            The mean of the array elements.         
    """   
    n = len(values_array)

    if weights_array is None:
        weights_array = np.full(n, 1)
    elif len(weights_array) != n:
        raise ValueError('values_array and qt_array must have the same number of rows')

    n_row = len(values_array[0])
    result = np.full(n_row, 0)
    for i, item in enumerate(values_array):
        for j in range(n_row):
            result[j] += item[j] * weights_array[i]

    sum_qt = array_sum(weights_array)
    for i in range(n_row):
        result[i] /= sum_qt

    return result


def array_sum(values_array):
    """Computes the sum of the elements of the array.

    values_array : array of floats
        The numbers to be added. 

    Returns 
    -------
        sum1 : Float
            The sum of the elements of the array         
    """    
    sum1 = 0
    for item in values_array:
        sum1 += item

    return sum1


def array_stats(values_array):
    """Computes the sum of all the elements in the array, the sum of the square of each element and the number of 
        elements of the array.

    values_array : array of floats 
        The elements used to compute the operations
    
    Returns
    -------
        sum1 : Float
            The sum of all the elements in the array

        sum_sq : Float
            The sum of the square value of each element in the array

        n : Integer
            The number of elements in the array
    """
    sum1 = 0
    sum_sq = 0
    n = 0
    for item in values_array:
        sum1 += item
        sum_sq += item * item
        n += 1

    return sum1, sum_sq, n


def change_df_feature_values_using_filter(df, id_, feature_name, filter_, values):
    """
    equivalent of: df.at[id_, feature_name][filter_] = values
    e.g. df.at[tid, 'time'][filter_nodes] = intp_result.astype(np.int64)
    dataframe must be indexed by id_: df.set_index(index_name, inplace=True)
    """
    values_feature = df.at[id_, feature_name]
    if filter_.shape == ():
        df.at[id_, feature_name] = values
    else:
        values_feature[filter_] = values
        df.at[id_, feature_name] = values_feature


def change_df_feature_values_using_filter_and_indexes(df, id_, feature_name, filter_, idxs, values):
    """
    equivalent of: df.at[id_, feature_name][filter_][idxs] = values
    e.g. df.at[tid, 'deleted'][filter_][idx_not_in_ascending_order] = True
    dataframe must be indexed by id_: df.set_index(index_name, inplace=True)
    """
    values_feature = df.at[id_, feature_name]
    values_feature_filter = values_feature[filter_]
    values_feature_filter[idxs] = values
    values_feature[filter_] = values_feature_filter
    df.at[id_, feature_name] = values_feature


def list_to_str(input_list, delimiter=','):
    """Concatenates the elements of the array, joining them by the separator especified by the parameter "delimiter"

    Parameters
    ----------
    input_list : array 
        The elements to be joined
    
    delimiter : String, optional(',' by default)
        The separator used between elements
    
    Returns
    -------
        String
            Returns a string, wich is the concatenation of the elements of the array, separeted by the delimiter.
    """
    return delimiter.join([x if type(x) == str else repr(x) for x in input_list])  # list comprehension


def list_to_csv_str(input_list):
    """Concatenates the elements of the array, joining them by ",".

    Parameters
    ----------
    input_list : array 
        The elements to be joined
    
    Returns
    -------
        String
            Returns a string, wich is the concatenation of the elements of the array, separeted by ",".
    """
    return list_to_str(input_list)  # list comprehension


#erro se tentar converter int para str e funcao n verifica isso
def fill_list_with_new_values(original_list, new_list_values):
    """ Copies elements from one list to another. The elements will be positioned in the same position in the new list as
    they were in their original list.

    Parameters
    ----------
    original_list : array
    The list to which the elements will be copied

    new_list_values : array
    The list from which elements will be copied

    """
    for i in range(len(new_list_values)):
        type1 = type(original_list[i])
        if type1 == int:
            original_list[i] = int(new_list_values[i])
        elif type1 == float:
            original_list[i] = float(new_list_values[i])
        else:
            original_list[i] = new_list_values[i]


def list_to_svm_line(original_list):
    """

    """
    list_size = len(original_list)
    svm_line = '%s ' % original_list[0]
    for i in range(1, list_size):
        #svm_line += '{}:{} '.format(i, repr(original_list[i]))
        svm_line += '{}:{} '.format(i, original_list[i])
    return svm_line.rstrip()


def interpolation(x0, y0, x1, y1, x):
    """Perfomers interpolation and extrapolation

    Parameters
    ----------
    x0 : float
        The coordinate of the first point on the x axis

    y0 : float
        The coordinate of the first point on the y axis

    x1 : float
        The coordinate of the second point on the x axis

    y1 : float
        The coordinate of the second point on the y axis

    x : float
        A value in the interval (x0, x1)

    Returns
    -------
    y : float
        Is the interpolated  or extrapolated value.

    Examples
    --------
    interpolation 1: (30, 3, 40, 5, 37) -> 4.4
    interpolation 2: (30, 3, 40, 5, 35) -> 4.0
    extrapolation 1: (30, 3, 40, 5, 25) -> 2.0
    extrapolation 2: (30, 3, 40, 5, 45) -> 6.0
    """
    y = y0 + (y1 - y0) * ((x - x0)/(x1 - x0))
    return y

def shift(arr, num, fill_value=np.nan):
    """Shifts the elements of the given array by the number of periods specified.

    Parameters
    ----------
    arr : array
        The array to be shifed.

    num : Integer
        Number of periods to shift. Can be positive or negative. If posite, the elements will be pulled down, and pulled
        up otherwise.

    fill_value : Integer, optional(np.nan by default)
        The scalar value used for newly introduced missing values.

    Returns
    -------
    result : array
        A new array with the same shape and type as the initial given array, but with the indexes shifted.

    Notes
    -----
        Similar to pandas shift, but faster.

    See also
    --------
        https://stackoverflow.com/questions/30399534/shift-elements-in-a-numpy-array
    """

    result = np.empty_like(arr)

    if num > 0:
        result[:num] = fill_value
        result[num:] = arr[:-num]
    elif num < 0:
        result[num:] = fill_value
        result[:num] = arr[-num:]
    else:
        result = arr
    return result




