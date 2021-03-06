from PyQt5 import QtCore
import numpy as np
from scipy import signal
from spike_detection.spike_detection_settings import SpikeDetectionSettings
import time
from IPython import embed

from .spike_detection_settings import SpikeDetectionSettings


class SpikeDetectionThread(QtCore.QThread):
    operation_changed = QtCore.pyqtSignal(str)
    progress_made = QtCore.pyqtSignal(float)
    single_spike_data_updated = QtCore.pyqtSignal(list)
    channel_data_updated = QtCore.pyqtSignal(list)
    finished = QtCore.pyqtSignal()

    def __init__(self, parent, reader, file_mode, spike_window, mode, threshold_factor, grid_indices):
        super().__init__(parent)
        self.reader = reader
        self.file_mode = file_mode
        self.spike_window = spike_window
        self.mode = mode
        self.threshold_factor = threshold_factor
        self.grid_indices = grid_indices

        self.spike_indices, self.spike_mat = None, None

    def old_spike_detection(self, mea_data_reader):
        indices = []
        spike_mat = []

        reader = mea_data_reader
        if self.file_mode == SpikeDetectionSettings.FileMode.MCS:
            signals = reader.voltage_traces
        elif self.file_mode == SpikeDetectionSettings.FileMode.MEAE:
            signals = reader.filtered_traces
        ids = reader.channel_ids
        fs = reader.sampling_frequency

        # To Do: get this right and think of how to solve it, when a already analysed file comes in
        selected_ids = range(3)
        # selected_ids = [ids[g_idx] for g_idx in self.grid_indices]

        above_upper_threshold = False
        below_lower_threshold = False
        current_extreme_index_and_value = None  # current local minimum or maximum

        for idx, ch_id in enumerate(selected_ids):
            # in this case, the whole channel should be loaded, since the filter should be applied at once
            signal = signals[ch_id]
            threshold = self.threshold_factor * np.median(np.absolute(signal) / 0.6745)
            print(threshold)
            collect_peaks = (self.mode == SpikeDetectionSettings.Mode.PEAKS or
                             self.mode == SpikeDetectionSettings.Mode.BOTH)
            collect_troughs = (self.mode == SpikeDetectionSettings.Mode.TROUGHS or
                               self.mode == SpikeDetectionSettings.Mode.BOTH)
            channel_spike_indices = []
            for index, value in enumerate(signal):
                if above_upper_threshold:  # last value was above positive threshold limit
                    if value <= threshold:  # leaving upper area
                        # -> add current maximum index to list
                        if collect_peaks:
                            channel_spike_indices.append(current_extreme_index_and_value[0])

                            lower_index = current_extreme_index_and_value[0] - int((self.spike_window / 2) * fs)
                            upper_index = current_extreme_index_and_value[0] + int((self.spike_window / 2) * fs)
                            single_spike_voltage = signal[lower_index:upper_index]
                            single_spike_index = (current_extreme_index_and_value[0] - lower_index)
                            single_spike_height = signal[current_extreme_index_and_value[0]]
                            single_spike_data = [single_spike_voltage, single_spike_index, single_spike_height,
                                                 threshold]
                            self.single_spike_data_updated.emit(single_spike_data)
                    else:  # still above positive threshold
                        # check if value is bigger than current maximum
                        if value > current_extreme_index_and_value[1]:
                            current_extreme_index_and_value = (index, value)

                elif below_lower_threshold:  # last value was below negative threshold limit
                    if value <= threshold:  # leaving lower area
                        # -> add current minimum index to list
                        if collect_troughs:
                            channel_spike_indices.append(current_extreme_index_and_value[0])

                            lower_index = current_extreme_index_and_value[0] - int((self.spike_window / 2) * fs)
                            upper_index = current_extreme_index_and_value[0] + int((self.spike_window / 2) * fs)
                            single_spike_voltage = signal[lower_index:upper_index]
                            single_spike_index = (current_extreme_index_and_value[0] - lower_index)
                            single_spike_height = signal[current_extreme_index_and_value[0]]
                            single_spike_data = [single_spike_voltage, single_spike_index, single_spike_height,
                                                 threshold]
                            self.single_spike_data_updated.emit(single_spike_data)
                    else:  # still below negative threshold
                        # check if value is smaller than current maximum
                        if value < current_extreme_index_and_value[1]:
                            current_extreme_index_and_value = (index, value)

                else:  # last value was within threshold limits
                    if value > threshold or value < -threshold:  # crossing threshold limit
                        # initialise new local extreme value
                        current_extreme_index_and_value = (index, value)

                # update state
                below_lower_threshold = (value < -threshold)
                above_upper_threshold = (value > threshold)
            spiketimes = channel_spike_indices / fs
            spike_mat.append(spiketimes)
            data = [spiketimes]
            self.channel_data_updated.emit(data)

            indices.append(np.asarray(channel_spike_indices))

            progress = round(((idx + 1) / len(ids)) * 100.0, 2)
            self.progress_made.emit(progress)
        return indices, spike_mat

    def new_spike_detection(self, mea_data_reader):
        indices = []
        spike_mat = []

        reader = mea_data_reader
        if self.file_mode == SpikeDetectionSettings.FileMode.MCS:
            signals = reader.voltage_traces
        elif self.file_mode == SpikeDetectionSettings.FileMode.MEAE:
            signals = reader.filtered_traces
        ids = reader.channel_ids
        fs = reader.sampling_frequency
        print('grid indices:', self.grid_indices, '\n', 'channel ids:', ids)
        if self.grid_indices in ids:
            selected_ids = [ids[g_idx] for g_idx in self.grid_indices]
        else:
            selected_ids = ids

        for idx, ch_id in enumerate(selected_ids):
            # in this case, the whole channel should be loaded, since the filter should be applied at once
            ch_signal = signals[ch_id]
            print(ch_id, ch_signal)
            threshold = self.threshold_factor * np.median(np.absolute(ch_signal) / 0.6745)
            collect_peaks = (self.mode == SpikeDetectionSettings.Mode.PEAKS or
                             self.mode == SpikeDetectionSettings.Mode.BOTH)
            collect_troughs = (self.mode == SpikeDetectionSettings.Mode.TROUGHS or
                               self.mode == SpikeDetectionSettings.Mode.BOTH)
            channel_spike_indices = []
            if collect_peaks:
                peaks = signal.find_peaks(ch_signal, height=threshold)
                channel_spike_indices.append(peaks[0])

            if collect_troughs:
                troughs = signal.find_peaks(ch_signal, height=-threshold)
                channel_spike_indices.append(troughs[0])

            indices.append(channel_spike_indices)
            single_spike_data = [ch_signal, indices[-1], threshold]
            self.single_spike_data_updated.emit(single_spike_data)

            spiketimes = np.asarray(channel_spike_indices) / fs
            print(spiketimes)
            spike_mat.append(spiketimes)
            data = [spiketimes]
            self.channel_data_updated.emit(data)

            progress = round(((idx + 1) / len(selected_ids)) * 100.0, 2)
            self.progress_made.emit(progress)
        return indices, spike_mat

    def run(self):
        self.operation_changed.emit("Detecting spikes")
        t0 = time.time()
        self.spike_indices, self.spike_mat = self.old_spike_detection(self.reader)
        t1 = time.time() - t0
        print('time for one channel via new spike detection: ', t1)
        self.finished.emit()
