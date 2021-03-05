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
import segyio
from scipy.interpolate import RegularGridInterpolator
from shutil import copyfile

def updateHdf5(fileHdf5, isAttribute, attributeName, resultData):
    #
    timestamp = u"2010-10-18T17:17:04-0500"
    idAttributeName = str(uuid.uuid4())
    
    # create the HDF5 NeXus file
    fhdf5 = h5py.File(fileHdf5, "r+")
    # give the HDF5 root some more attributes
    fhdf5.attrs[u'file_name']        = fileHdf5
    fhdf5.attrs[u'file_time']        = timestamp
    fhdf5.attrs[u'instrument']       = u'APS USAXS at 32ID-B'
    fhdf5.attrs[u'creator']          = u'Unisinos.py'
    fhdf5.attrs[u'NeXus_version']    = u'4.3.0'
    fhdf5.attrs[u'HDF5_Version']     = six.u(h5py.version.hdf5_version)
    fhdf5.attrs[u'h5py_version']     = six.u(h5py.version.version)

    if(isAttribute):
        # create the attributes group
        group = fhdf5["attributes"]
        if group:
            attributes = fhdf5["attributes"]
        else:
            attributes = fhdf5.create_group(u'attributes')

        idAttributeGroup = attributes.create_group(idAttributeName)
        idAttributeGroup.attrs[u'attributeName'] = attributeName

        # Create  Dataset Atrubute
        exists = fhdf5.get("headers1")
        if exists is None:
            headersDS = idAttributeGroup.create_dataset(u'headers1', data=resultData)
            #ilineDS = idAttributeGroup.create_dataset(u'iline', data=datailine)


def createHdf5(fileHdf5):
    #
    timestamp = u"2010-10-18T17:17:04-0500"
    
    # create the HDF5 NeXus file
    fhdf5 = h5py.File(fileHdf5, "w")
    # give the HDF5 root some more attributes
    fhdf5.attrs[u'file_name']        = fileHdf5
    fhdf5.attrs[u'file_time']        = timestamp
    fhdf5.attrs[u'instrument']       = u'APS USAXS at 32ID-B'
    fhdf5.attrs[u'creator']          = u'Unisinos.py'
    fhdf5.attrs[u'NeXus_version']    = u'4.3.0'
    fhdf5.attrs[u'HDF5_Version']     = six.u(h5py.version.hdf5_version)
    fhdf5.attrs[u'h5py_version']     = six.u(h5py.version.version)

    # create the attributes group
    attributes = fhdf5.create_group(u'attributes')
    seismicGroup = fhdf5.create_group(u'seismic')
    return True

def loadDatasgy(fileSgy):
    with segyio.open(fileSgy, ignore_geometry=True) as f:
   
        header_keys = segyio.tracefield.keys    
        trace_headers = pd.DataFrame(index=range(1, f.tracecount+1),
                                     columns=header_keys.keys())
       
        for k, v in header_keys.items():
            trace_headers[k] = f.attributes(v)[:]
    
    f.close()
    return trace_headers
    
def process(fileSgy, isAttribute, attributeName, fileHdf5):
    
    resultData = loadDatasgy(fileSgy)
    
    if os.path.isfile(fileHdf5):
        updateHdf5(fileHdf5, isAttribute, attributeName, resultData);
    else:
        createHdf5(fileHdf5)
        updateHdf5(fileHdf5, isAttribute, attributeName, resultData);
        
    return True
    
def main():
    print("***INICIANDO O PROCESSO*****!")
    
    #fileSgy = 'C:\\Git\\ContinentalSeismic\\data_test\\long.sgy'
    #isAttribute = True
    #attributeName = u"teste"
    #fileHdf5 = u"C:\\Users\\cristianheylmann\\Desktop\\conversao\\continental_seismic.hdf5"
    #process(fileSgy, isAttribute, attributeName, fileHdf5)
    
    print("***PROCESSO FINALIZADO*****!")

if __name__ == "__main__":
    main()