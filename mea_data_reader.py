import os
import numpy as np
import h5py
from IPython import embed

class MeaDataReader:
    def __init__(self, path):
        self.file_path = path
        self.analysis_file_path = None
        overall_path, filename = os.path.split(path)
        if filename.endswith('.h5'):
            analysis_filename = filename[:-2] + 'meae'
        if os.path.exists(overall_path + analysis_filename):
            self.analysis_file_path = overall_path + '\\' + analysis_filename[0]
        if self.analysis_file_path:
            self.file, self.voltage_traces, self.sampling_frequency = self.open_mea_file(self.analysis_file_path)
            self.channel_indices = range(len(self.voltage_traces))
        else:
            self.file, self.voltage_traces, self.sampling_frequency = self.open_mea_file(self.file_path)
            self.channel_indices, self.labels = self.get_channel_indices(self.file)

    def open_mea_file(self, path):
        file = h5py.File(path, 'r')
        if self.analysis_file_path:
            voltage_traces = file['filter']
            sampling_frequency = file['fs']
            channel_indices = file['channel_indices']
            channel_labels = file['channel_labels']
            return file, voltage_traces, sampling_frequency
        voltage_traces = file['Data']['Recording_0']['AnalogStream']['Stream_0']['ChannelData']
        sampling_frequency = 1000000/file['Data']['Recording_0']['AnalogStream']['Stream_0']['InfoChannel']['Tick'][0]
        # infos of the recording:
        # Total recording duration in microseconds:
        # file['Data']['Recording_0'].attrs['Duration']
        # Conversion factor for the mapping ADC-Step ⇒ measured value:
        # file['Data']['Recording_0']['AnalogStream']['Stream_0']['InfoChannel']['ConversionFactor']
        # Matrix ChannelDataTimeStamps → k × 3 matrix of segments where the rows are one segment and the columns are:
        # first column → time stamp of the first sample point of the segment
        # second column → first index (column) of the segment in ChannelData
        # third column → last index (column) of the segment in ChannelData
        # file['Data']['Recording_0']['AnalogStream']['Stream_0']['ChannelDataTimeStamps'][0][2]
        # file = McsPy.McsData.RawData(path)
        return file, voltage_traces, sampling_frequency

    def get_channel_indices(self, file):
        ids = [ch[1] for ch in self.file['Data']['Recording_0']['AnalogStream']['Stream_0']['InfoChannel']]
        labels = [ch[4].decode('utf8') for ch in
                  self.file['Data']['Recording_0']['AnalogStream']['Stream_0']['InfoChannel']]
        same_len_labels = [str(label[0]) + '0' + str(label[1]) if len(label) < 3 else label for label in labels]
        ordered_indices = list(np.argsort(same_len_labels))
        return list(np.asarray(ids)[ordered_indices]), list(np.asarray(labels)[ordered_indices])
