import xarray as xr
import cf_xarray as cfxr

def set_event_names(pows, period_type, col='event', copy=False):
    if copy:
        pows = pows.copy()
    events_mi = pows[col].to_index()
    events_mi = events_mi.rename(
        [name+'_'+period_type for name in events_mi.names])
    pows[col] = events_mi
    pows = pows.rename({col: col+'_'+period_type})
    return pows

def load_nc(fp, is_stacked=False):
    word_arr = xr.open_dataarray(fp, engine='scipy')
    word_arr.load()
    event_names = word_arr.event.coords._names - {'samplerate'}
    word_arr = word_arr.set_index(event=list(event_names))
    if not is_stacked:
        word_arr = word_arr.stack(features=("frequency", "channel"))
    return word_arr

def normalize_features(pows, countdown_pows=None, use_ddof=0):
    if countdown_pows is None:
        print('normalizing across events')
        if 'time' in pows.coords:
            pows = (pows - pows.mean(['event', 'time'])) / pows.std(['event', 'time'], ddof=use_ddof)
        else:
            pows = (pows - pows.mean(['event'])) / pows.std(['event'], ddof=use_ddof)
    else:
        pows = (pows - countdown_pows.mean(['event', 'time'])) / countdown_pows.std(['event', 'time'], ddof=use_ddof) 
    return pows

def load_nc_cfxr(nc_fp, idxnames=None):
    encoded_read = xr.open_dataset(nc_fp)
    decoded = cfxr.decode_compress_to_multi_index(encoded_read, idxnames=idxnames)
    return decoded.to_array().squeeze()
