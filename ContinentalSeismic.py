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
from scipy.interpolate import RegularGridInterpolator
from shutil import copyfile
from datetime import datetime
try:
    sys.path.append(basePath)
except NameError:
    pass
    
def updateHdf5(fileHdf5, isAttribute, attributeName, segyNameProject, resultData):
    #
    timestamp = datetime.today().strftime('%Y-%m-%dT%H:%M:%S')
    
    
    # create the HDF5 NeXus file
    fhdf5 = h5py.File(fileHdf5, "r+")
    # give the HDF5 root some more attributes
    fhdf5.attrs[u'file_name']        = fileHdf5
    fhdf5.attrs[u'file_time']        = timestamp
    fhdf5.attrs[u'instrument']       = u'APS USAXS at 32ID-B'
    fhdf5.attrs[u'creator']          = u'ContinentalSeismic.py'
    fhdf5.attrs[u'NeXus_version']    = u'4.3.0'
    fhdf5.attrs[u'HDF5_Version']     = six.u(h5py.version.hdf5_version)
    fhdf5.attrs[u'h5py_version']     = six.u(h5py.version.version)
    
    print('aaa')
    if(isAttribute):
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
        

        # Create  Dataset Atrubute
        exists = fhdf5.get("headers1")
        if exists is None:
            attributeseismicDS = idAttributeGroup.create_dataset(u'attributeseismic', data=resultData)
            #ilineDS = idAttributeGroup.create_dataset(u'iline', data=datailine)
    else:
        #se nao existe o grupo cria
        existsSeismicGroup = fhdf5.get("seismic")
        if existsSeismicGroup is None:
            seismicGroup = fhdf5.create_group("seismic")
        else:
            seismicGroup = fhdf5["seismic"]
            
        seismicGroup.attrs[u'segyfile'] = segyNameProject + '.sgy'
        seismicGroup.attrs[u'ldmfile'] = ''
        seismicGroup.attrs[u'id'] = segyNameProject
        
        existsSeismicDataset = seismicGroup.get("seismic")
        if existsSeismicDataset is None:
            seismicDS = seismicGroup.create_dataset(u'seismic', data=resultData)
            seismicDS.attrs["minX"] = np.amin(resultData[:]['SourceX'])
            seismicDS.attrs["maxX"] = np.amax(resultData[:]['SourceX'])
            seismicDS.attrs["minY"] = np.amin(resultData[:]['SourceY'])
            seismicDS.attrs["maxY"] = np.amax(resultData[:]['SourceY'])
        else:
            seismicDS = seismicGroup.get("seismic")
            seismicDS = resultData;

def createHdf5(fileHdf5):
    #
    timestamp = u"2010-10-18T17:17:04-0500"
    
    # create the HDF5 NeXus file
    fhdf5 = h5py.File(fileHdf5, "w")
    # give the HDF5 root some more attributes
    fhdf5.attrs[u'file_name']        = fileHdf5
    fhdf5.attrs[u'file_time']        = timestamp
    fhdf5.attrs[u'instrument']       = u'APS USAXS at 32ID-B'
    fhdf5.attrs[u'creator']          = u'ContinentalSeismic.py'
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
    
def process2(fileSgy, isAttribute, attributeName, fileHdf5):
    return True   
    
def process(fileSgy, isAttribute, attributeName, pathProject, nameFileHdf5, guidId):
    print("***process*****!")
    resultprocess = False
 
    #copia o segy original para pasta do projeto com o novo ID
    fileHdf5 = pathProject + '\\'+ nameFileHdf5
    segyNameProject = guidId
    pathNewSegy = pathProject + '\\seismic\\' + segyNameProject + '.sgy'
    shutil.copy(fileSgy, pathNewSegy)
    
    #Le o arquivo segy e salva o HDF5
    resultData = loadDatasgy(fileSgy)
    
    if os.path.isfile(fileHdf5):
        updateHdf5(fileHdf5, isAttribute, attributeName, segyNameProject, resultData);
    else:
        createHdf5(fileHdf5)
        updateHdf5(fileHdf5, isAttribute, attributeName, segyNameProject, resultData);
    
    
    resultprocess =  True
  

    return resultprocess
    
   
def main():
    print("***INICIANDO O PROCESSO*****!")
    print("***INICIANDO O PROCESSO*****!")

    #fileSgy = 'C:/Git/ContinentalSeismic/continentalseismic/data_test/long.sgy'    
    #isAttribute = True
    #attributeName = u"aaaaa"
    #pathProject = u"C:/Users/cristianheylmann/Desktop/teste_projetos/teste1/teste1_continentalcarbonate"
    #nameFileHdf5 = u"continental_seismic.hdf5"
    #guidId = 'aaaaaaaaa-aaaaaaa'
    #result = process(fileSgy, isAttribute, attributeName, pathProject, nameFileHdf5, guidId)

    #print(result)
    print("***PROCESSO FINALIZADO*****!")
    print("***PROCESSO FINALIZADO*****!")
    
if __name__ == "__main__":
    main()