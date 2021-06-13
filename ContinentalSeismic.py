import os
import sys
import numpy as np
import segyio
import pylops
import matplotlib.pyplot as plt
import h5py
import six
import uuid
import pandas as pd
import shutil
import math
from scipy.interpolate import RegularGridInterpolator
from shutil import copyfile
from datetime import datetime
import threading
import concurrent.futures

try:
    sys.path.append(basePath)
except NameError:
    pass


def update_geometry_parameters(attrs, interval, trace_sample_count, result_data):
    attrs["minX"] = np.amin(result_data[:]['SourceX'])
    attrs["maxX"] = np.amax(result_data[:]['SourceX'])
    attrs["minY"] = np.amin(result_data[:]['SourceY'])
    attrs["maxY"] = np.amax(result_data[:]['SourceY'])

    index_inline_end = np.amax(result_data[:]['CDP']) - np.amin(result_data[:]['CDP']) + 1
    index_inline_end_crossline_end = len(result_data)
    index_crossline_end = index_inline_end_crossline_end - index_inline_end + 1

    origin_x = result_data['SourceX'][1]
    origin_y = result_data['SourceY'][1]
    origin_z = result_data['DelayRecordingTime'][1]
    inline_end_x = result_data['SourceX'][index_inline_end]
    inline_end_y = result_data['SourceY'][index_inline_end]
    crossline_end_x = result_data['SourceX'][index_crossline_end]
    crossline_end_y = result_data['SourceY'][index_crossline_end]
    inline_end_crossline_end_x = result_data['SourceX'][index_inline_end_crossline_end]
    inline_end_crossline_end_y = result_data['SourceY'][index_inline_end_crossline_end]

    attrs["interval"] = interval
    attrs["traceSampleCount"] = trace_sample_count
    attrs["inlineCount"] = index_inline_end
    attrs["crosslineCount"] = len(result_data) / attrs["inlineCount"]
    attrs["originX"] = origin_x
    attrs["originY"] = origin_y
    attrs["originZ"] = origin_z
    attrs["inlineEndX"] = inline_end_x
    attrs["inlineEndY"] = inline_end_y
    attrs["crosslineEndX"] = crossline_end_x
    attrs["crosslineEndY"] = crossline_end_y
    attrs["inlineEndCrosslineEndX"] = inline_end_crossline_end_x
    attrs["inlineEndCrosslineEndY"] = inline_end_crossline_end_y


def updateHdf5(fileHdf5, isAttribute, attributeName, colorMap, segyNameProject, interval, trace_sample_count, resultData):
    #
    timestamp = datetime.today().strftime('%Y-%m-%dT%H:%M:%S')

    # create the HDF5 NeXus file
    fhdf5 = h5py.File(fileHdf5, "r+")
    # give the HDF5 root some more attributes
    fhdf5.attrs[u'file_name'] = fileHdf5
    fhdf5.attrs[u'file_time'] = timestamp
    fhdf5.attrs[u'instrument'] = u'APS USAXS at 32ID-B'
    fhdf5.attrs[u'creator'] = u'ContinentalSeismic.py'
    fhdf5.attrs[u'NeXus_version'] = u'4.3.0'
    fhdf5.attrs[u'HDF5_Version'] = six.u(h5py.version.hdf5_version)
    fhdf5.attrs[u'h5py_version'] = six.u(h5py.version.version)

    if (isAttribute):
        # create the attributes group
        group = fhdf5["attributes"]
        if group:
            attributes = fhdf5["attributes"]
        else:
            attributes = fhdf5.create_group(u'attributes')

        idAttributeGroup = attributes.create_group(segyNameProject)
        idAttributeGroup.attrs[u'id'] = segyNameProject
        idAttributeGroup.attrs[u'attributeName'] = attributeName
        idAttributeGroup.attrs[u'segyfile'] = segyNameProject + '.sgy'
        idAttributeGroup.attrs[u'ldmfile'] = ''
        idAttributeGroup.attrs[u'colormap'] = colorMap
        update_geometry_parameters(idAttributeGroup.attrs, interval, trace_sample_count, resultData)

        # Create  Dataset Atrubute
        exists = fhdf5.get("headers1")
        if exists is None:
            attributeseismicDS = idAttributeGroup.create_dataset(u'trace_header', data=resultData)
            # ilineDS = idAttributeGroup.create_dataset(u'iline', data=datailine)
    else:
        # se nao existe o grupo cria
        existsSeismicGroup = fhdf5.get("seismic")
        if existsSeismicGroup is None:
            seismicGroup = fhdf5.create_group("seismic")
        else:
            seismicGroup = fhdf5["seismic"]

        seismicGroup.attrs[u'segyfile'] = segyNameProject + '.sgy'
        seismicGroup.attrs[u'ldmfile'] = ''
        seismicGroup.attrs[u'id'] = segyNameProject
        seismicGroup.attrs["minX"] = np.amin(resultData[:]['SourceX'])
        seismicGroup.attrs["maxX"] = np.amax(resultData[:]['SourceX'])
        seismicGroup.attrs["minY"] = np.amin(resultData[:]['SourceY'])
        seismicGroup.attrs["maxY"] = np.amax(resultData[:]['SourceY'])
        seismicGroup.attrs[u'colormap'] = colorMap
        update_geometry_parameters(seismicGroup.attrs, interval, trace_sample_count, resultData)

        exists_seismic_dataset = seismicGroup.get("seismic")
        if exists_seismic_dataset is None:
            seismicGroup.create_dataset(u'trace_header', data=resultData)
        else:
            seismicGroup.get("seismic")


def createHdf5(fileHdf5):
    #
    timestamp = u"2010-10-18T17:17:04-0500"

    # create the HDF5 NeXus file
    fhdf5 = h5py.File(fileHdf5, "w")
    # give the HDF5 root some more attributes
    fhdf5.attrs[u'file_name'] = fileHdf5
    fhdf5.attrs[u'file_time'] = timestamp
    fhdf5.attrs[u'instrument'] = u'APS USAXS at 32ID-B'
    fhdf5.attrs[u'creator'] = u'ContinentalSeismic.py'
    fhdf5.attrs[u'NeXus_version'] = u'4.3.0'
    fhdf5.attrs[u'HDF5_Version'] = six.u(h5py.version.hdf5_version)
    fhdf5.attrs[u'h5py_version'] = six.u(h5py.version.version)

    # create the attributes group
    fhdf5.create_group(u'attributes')
    fhdf5.create_group(u'seismic')
    return True


def load_data_segy(file_segy):
    print("BEGIN ContinentalSeismic::load_data_segy - " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    header_keys_filter = ['SourceX', 'SourceY', 'LagTimeA', 'DelayRecordingTime', 'CDP']

    segy = segyio.open(file_segy, ignore_geometry=True)
    header_keys = segyio.tracefield.keys
    trace_headers = pd.DataFrame(index=range(1, segy.tracecount + 1), columns=header_keys.keys(), dtype=int).fillna(0)

    interval = segy.bin[segyio.BinField.Interval]
    trace_sample_count = segy.bin[segyio.BinField.Samples]

    for name_attribute in header_keys_filter:
        trace_headers[name_attribute] = segy.attributes(header_keys[name_attribute])[:]

    segy.close()
    print("END ContinentalSeismic::load_data_segy - " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    return interval, trace_sample_count, trace_headers


def load_data_segy_multithread_part(segy, index_attribute, name_attribute):
    print("BEGIN ContinentalSeismic::load_data_segy_multithread_part - " + name_attribute + " - " +
          datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    result = list(segy.attributes(index_attribute)[:]) * 1
    print("END ContinentalSeismic::load_data_segy_multithread_part - " + name_attribute + " - " +
          datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    return result


def load_data_segy_multithread(file_segy):
    print("BEGIN ContinentalSeismic::load_data_segy_multithread - " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    header_keys = segyio.tracefield.keys
    header_keys_filter = ['SourceX', 'SourceY', 'LagTimeA', 'DelayRecordingTime', 'CDP']

    segy = segyio.open(file_segy, ignore_geometry=True)
    interval = segy.bin[segyio.BinField.Interval]
    trace_count = segy.tracecount
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = []
        for index in range(len(header_keys_filter)):
            futures.append(executor.submit(
                load_data_segy_multithread_part,
                segy=segy,
                index_attribute=header_keys[header_keys_filter[index]],
                name_attribute=header_keys_filter[index]
            ))
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    trace_headers = pd.DataFrame(index=range(1, trace_count + 1), columns=header_keys.keys(), dtype=int).fillna(0)
    for index in range(len(results)):
        name_attribute = header_keys_filter[index]

        trace_headers[name_attribute] = results[index]
    print("END ContinentalSeismic::load_data_segy_multithread - " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    return interval, trace_headers


def process(file_segy, isAttribute, attributeName, colorMap, pathProject, nameFileHdf5, guidId):
    print("BEGIN ContinentalSeismic::process - " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # copia o segy original para pasta do projeto com o novo ID
    file_hdf5 = pathProject + '\\' + nameFileHdf5
    segy_name_project = guidId
    path_new_segy = pathProject + '\\seismic\\' + segy_name_project + '.sgy'
    shutil.copy(file_segy, path_new_segy)

    # Le o arquivo segy e salva o HDF5
    interval, trace_sample_count, result_data = load_data_segy(file_segy)

    if os.path.isfile(file_hdf5):
        updateHdf5(file_hdf5, isAttribute, attributeName, colorMap, segy_name_project, interval, trace_sample_count, result_data)
    else:
        createHdf5(file_hdf5)
        updateHdf5(file_hdf5, isAttribute, attributeName, colorMap, segy_name_project, interval, trace_sample_count, result_data)

    print("END ContinentalSeismic::process - " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    return True


def main():
    '''file_segy = 'D:/Arquivos/SyntheticSeismicForStratBR/output_lithology.sgy'
    isAttribute = False
    attributeName = u"Litologia"
    pathProject = u"D:/Arquivos/SyntheticSeismicForStratBR"
    nameFileHdf5 = u"continental_seismic.hdf5"
    guidId = 'ddece425-e5d4-4a2d-a798-1899f48af13e'
    process(file_segy, isAttribute, attributeName, "", pathProject, nameFileHdf5, guidId)'''


if __name__ == "__main__":
    main()
