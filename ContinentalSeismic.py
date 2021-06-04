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

try:
    sys.path.append(basePath)
except NameError:
    pass

def update_geometry_parameters(attrs, interval, result_data):
    attrs["minX"] = np.amin(result_data[:]['SourceX'])
    attrs["maxX"] = np.amax(result_data[:]['SourceX'])
    attrs["minY"] = np.amin(result_data[:]['SourceY'])
    attrs["maxY"] = np.amax(result_data[:]['SourceY'])

    index_inline_end = np.amax(result_data[:]['CDP']) - np.amin(result_data[:]['CDP']) + 1
    index_inline_end_crossline_end = len(result_data)
    index_crossline_end = index_inline_end_crossline_end - index_inline_end + 1

    origin_x = result_data['SourceX'][1]
    origin_y = result_data['SourceY'][1]
    origin_z = result_data['SourceSurfaceElevation'][1]
    inline_end_x = result_data['SourceX'][index_inline_end]
    inline_end_y = result_data['SourceY'][index_inline_end]
    crossline_end_x = result_data['SourceX'][index_crossline_end]
    crossline_end_y = result_data['SourceY'][index_crossline_end]
    inline_end_crossline_end_x = result_data['SourceX'][index_inline_end_crossline_end]
    inline_end_crossline_end_y = result_data['SourceY'][index_inline_end_crossline_end]

    attrs["interval"] = interval
    attrs["traceSampleCount"] = result_data['TRACE_SAMPLE_COUNT'][1]
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

def updateHdf5(fileHdf5, isAttribute, attributeName, colorMap, segyNameProject, interval, resultData):
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
        update_geometry_parameters(idAttributeGroup.attrs, interval, resultData)

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
        update_geometry_parameters(seismicGroup.attrs, interval, resultData)

        existsSeismicDataset = seismicGroup.get("seismic")
        if existsSeismicDataset is None:
            seismicDS = seismicGroup.create_dataset(u'trace_header', data=resultData)
        else:
            seismicDS = seismicGroup.get("seismic")
            seismicDS = resultData


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


def loadDatasgy(fileSgy):
    with segyio.open(fileSgy, ignore_geometry=True) as f:
        header_keys = segyio.tracefield.keys
        trace_headers = pd.DataFrame(index=range(1, f.tracecount + 1),
                                     columns=header_keys.keys())

        interval = f.bin[segyio.BinField.Interval]
        for k, v in header_keys.items():
            trace_headers[k] = f.attributes(v)[:]

    f.close()
    return interval, trace_headers

def process(fileSgy, isAttribute, attributeName, colorMap, pathProject, nameFileHdf5, guidId):
    print("***process*****!")
    result_process = False

    # copia o segy original para pasta do projeto com o novo ID
    file_hdf5 = pathProject + '\\' + nameFileHdf5
    segy_name_project = guidId
    path_new_segy = pathProject + '\\seismic\\' + segy_name_project + '.sgy'
    shutil.copy(fileSgy, path_new_segy)

    # Le o arquivo segy e salva o HDF5
    interval, result_data = loadDatasgy(fileSgy)

    if os.path.isfile(file_hdf5):
        updateHdf5(file_hdf5, isAttribute, attributeName, colorMap, segy_name_project, interval, result_data)
    else:
        createHdf5(file_hdf5)
        updateHdf5(file_hdf5, isAttribute, attributeName, colorMap, segy_name_project, interval, result_data)

    result_process = True

    return result_process


def main():
    """print("***INICIANDO O PROCESSO*****!")
    print("***INICIANDO O PROCESSO*****!")

    fileSgy = 'D:/Arquivos/SyntheticSeismicForStratBR/output_lithology.sgy'
    isAttribute = False
    attributeName = u"aaaaa"
    pathProject = u"D:/Arquivos/Sapinhoa_100k/Sapinhoa_100k/Sapinhoa_100k_continentalcarbonate"
    nameFileHdf5 = u"continental_seismic.hdf5"
    guidId = 'f82d363d-24a6-48ea-981b-56334f26b6b4'
    result = process(fileSgy, isAttribute, attributeName, "", pathProject, nameFileHdf5, guidId)

    # print(result)
    print("***PROCESSO FINALIZADO*****!")
    print("***PROCESSO FINALIZADO*****!")"""

if __name__ == "__main__":
    main()
