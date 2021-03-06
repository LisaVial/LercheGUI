from PyQt5 import QtCore, QtWidgets, QtGui
import os
import pyqtgraph as pg
import numpy as np
import h5py
from IPython import embed

from spike_detection.spike_detection_thread import SpikeDetectionThread


class SpikeDetectionTab(QtWidgets.QWidget):
    def __init__(self, parent, meae_filename, reader, grid_indices, grid_labels, settings):
        super().__init__(parent)
        # set input class variables
        self.meae_filename = meae_filename
        self.reader = reader
        self.grid_indices = grid_indices
        self.grid_labels = grid_labels
        self.settings = settings

        # set spike_detection_thread to none
        self.spike_detection_thread = None

        self.spike_mat = None
        self.spike_indices = None
        self.analysis_file_path = None

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)

        status_update_layout = QtWidgets.QVBoxLayout(self)
        status_update_layout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignCenter)

        # operation and progress_label is linked to the progress bar, so that the user sees, what is happening in the
        # background of the GUI
        self.operation_label = QtWidgets.QLabel(self)
        self.operation_label.setText('Nothing happens so far')
        status_update_layout.addWidget(self.operation_label)
        self.progress_label = QtWidgets.QLabel(self)
        status_update_layout.addWidget(self.progress_label)

        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(True)
        status_update_layout.addWidget(self.progress_bar)

        # set styles for plot
        styles = {'color': 'k', 'font-size': '10px'}
        # get sampling frequency, this is important for time ratios in plots
        self.fs = self.reader.sampling_frequency

        # open plot that will show raster plot of overall spiketimes of a channel, this will be portrayed at the bottom
        # on the left handside, that is why it is added to the spike_detection_settings_layout
        self.channel_raster_plot = pg.GraphicsLayoutWidget()
        self.channel_raster_plot.useOpenGL(True)
        self.channel_raster_plot.setBackground('w')

        # the timer is needed to draw the plot -> has to be refined
        self.timer = pg.QtCore.QTimer(self)
        self.timer.timeout.connect(self.on_timer)

        # This code block sets the y lims of the Rasterplot, which should appear at the end of the analysis of each
        # channel
        vtick = QtGui.QPainterPath()
        vtick.moveTo(0, -0.5)
        vtick.lineTo(0, 0.5)

        p1 = self.channel_raster_plot.addPlot(row=0, col=0)
        p1.setXRange(-0.05, 1.05)
        p1.hideAxis('bottom')

        s1 = pg.ScatterPlotItem(pxMode=False)
        s1.setSymbol(vtick)
        s1.setSize(1)
        s1.setPen(QtGui.QColor('black'))
        p1.addItem(s1)

        s2 = pg.ScatterPlotItem(pxMode=False, symbol=vtick, size=1,
                                pen=QtGui.QColor('#d0797a'))
        p1.addItem(s2)
        self.spis = [s1, s2]
        status_update_layout.addWidget(self.channel_raster_plot)
        main_layout.addLayout(status_update_layout)

        # open plot that will portray single spikes that are found, it will be portrayed on the right side of the
        # dialog, this is why it is added to the main layout
        self.voltage_trace_and_spikes_plot = pg.PlotWidget()
        self.voltage_trace_and_spikes_plot.setBackground('w')
        self.voltage_trace_and_spikes_plot.setLabel('left', 'amplitude [&#956;V]', **styles)
        self.voltage_trace_and_spikes_plot.setLabel('bottom', 'time [s]', **styles)
        main_layout.addWidget(self.voltage_trace_and_spikes_plot)

        # set up initial values to plot (everything is set to zero with dimensions according to default values of
        # settings
        # self.voltage_trace = [np.zeros(self.settings.spike_window * self.reader.fs)]
        self.voltage_trace = [[0, 0, 0, 0]]
        # self.time_vt = [np.zeros(self.settings.spike_window * self.reader.fs)]
        self.time_vt = [[0, 0, 0, 0]]
        self.spike_indices_plot = []
        self.spike_height = []
        self.threshold = 0

        # plot initial values
        pen_spike_voltage = pg.mkPen(color='#006e7d')
        self.signal_plot = self.voltage_trace_and_spikes_plot.plot(self.time_vt[-1], self.voltage_trace[-1],
                                                                   pen=pen_spike_voltage,
                                                                   name='voltage trace')
        pen_thresh = pg.mkPen(color='k')
        self.hLine = pg.InfiniteLine(angle=0, movable=False, pen=pen_thresh)
        self.hLine.setValue(self.threshold)
        self.voltage_trace_and_spikes_plot.addItem(self.hLine)
        self.hLine2 = pg.InfiniteLine(angle=0, movable=False, pen=pen_thresh)
        self.hLine2.setValue(-1 * self.threshold)
        self.voltage_trace_and_spikes_plot.addItem(self.hLine2)

        self.scatter = self.voltage_trace_and_spikes_plot.plot(pen=None, symbol='o', name='spiketimes')
        self.voltage_trace_and_spikes_plot.addLegend()

    def on_channel_data_updated(self, data):
        spiketimes = data[0]
        self.spis[-1].setData(spiketimes, 0 + 0.5 + np.zeros((len(spiketimes))))

    @QtCore.pyqtSlot()
    def initialize_spike_detection(self):
        if self.spike_mat is None:
            self.progress_bar.setValue(0)
            self.progress_label.setText("")
            self.progress_label.setText("Detecting Spikes")
            self.spike_detection_thread = SpikeDetectionThread(self, self.reader, self.settings.file_mode,
                                                               self.settings.spike_window, self.settings.mode,
                                                               self.settings.threshold_factor, self.grid_indices)
            self.spike_detection_thread.progress_made.connect(self.on_progress_made)
            self.spike_detection_thread.operation_changed.connect(self.on_operation_changed)
            self.spike_detection_thread.channel_data_updated.connect(self.on_channel_data_updated)
            self.spike_detection_thread.single_spike_data_updated.connect(self.on_spike_data_updated)
            self.spike_detection_thread.finished.connect(self.on_spike_detection_thread_finished)

            debug_mode = True  # set to 'True' in order to debug plot creation with embed
            if debug_mode:
                # synchronous plotting (runs in main thread and thus allows debugging)
                self.spike_detection_thread.run()
            else:
                # asynchronous plotting (default):
                self.spike_detection_thread.start()  # start will start thread (and run),
                # but main thread will continue immediately

            self.timer.start(500)  # time in [ms]

    # this function changes the label of the progress bar to inform the user what happens in the backgound
    @QtCore.pyqtSlot(str)
    def on_operation_changed(self, operation):
        self.operation_label.setText(operation)

    # this function updates the progress bar
    @QtCore.pyqtSlot(float)
    def on_progress_made(self, progress):
        self.progress_bar.setValue(int(progress))
        self.progress_label.setText(str(progress) + "%")

    # once the spike_detection_thread is finnished it is set back to None and depending on the save_check_box, the
    # spike_mat is saved to a .csv file
    @QtCore.pyqtSlot()
    def on_spike_detection_thread_finished(self):
        self.timer.stop()
        self.progress_label.setText("Finished :)")
        if self.spike_detection_thread.spike_mat:
            self.spike_indices = self.spike_detection_thread.spike_indices.copy()
            self.spike_mat = self.spike_detection_thread.spike_mat.copy()
        self.spike_detection_thread = None
        if self.settings.save_spiketimes:
            path = os.path.split(self.reader.file_path)[0]
            if self.meae_filename is None:
                self.meae_filename = os.path.split(self.reader.file_path)[-1][:-3] + '.meae'
            self.save_spike_mat(self.spike_mat, self.spike_indices, self.reader.file_path)

    @QtCore.pyqtSlot(list)
    def on_spike_data_updated(self, data):

        if len(data) == 4: # old spike detection
            signal, spiketime_index, spike_value, threshold = data[0], data[1], data[2], data[3]
            if len(signal) > 0:
                self.voltage_trace.append(signal)
                self.time_vt.append(list(np.arange(0, len(signal) * (1 / self.fs), 1 / self.fs)))
                self.spike_indices_plot.append(spiketime_index)
                self.spike_height.append(spike_value)
        else: # new spike detection
            signal, spiketime_indices, threshold = data[0], data[1], data[2]
            if len(signal) > 0 and len(spiketime_indices) > 0:
                self.voltage_trace.append(signal)
                self.time_vt.append(list(np.arange(0, len(signal) * (1 / self.fs), 1 / self.fs)))
                self.spike_indices_plot.append(list(spiketime_indices))
                # ToDo: next line causes a bug:
                self.spike_height.append(list(np.asarray(signal)[np.asarray(spiketime_indices[-2:]).flatten()]))

    @QtCore.pyqtSlot()
    def on_timer(self):
        if len(self.time_vt) == 0 or len(self.voltage_trace) == 0:
            return  # nothing to plot

        self.signal_plot.setData(self.time_vt[-1], self.voltage_trace[-1])
        self.hLine.setValue(self.threshold)
        self.hLine2.setValue(-1 * self.threshold)
        self.scatter.setData(np.asarray(self.spike_indices_plot[-1]) / self.fs, self.spike_height)

    # function to save the found spiketimes stored in spike_mat as .csv file
    def save_spike_mat(self, spike_mat, spike_indices, mea_file):
        self.progress_label.setText('saving spike times...')
        # take filepath and filename, to get name of mea file and save it to the same directory
        overall_path, filename = os.path.split(mea_file)
        if filename.endswith('.h5'):
            analysis_filename = filename[:-2] + 'meae'
        else:
            analysis_filename = filename
        analysis_file_path = os.path.join(overall_path, analysis_filename)
        if os.path.exists(analysis_file_path):
            if self.settings.append_to_file:
                analysis_filename = self.meae_filename
                analysis_file_path = os.path.join(overall_path, analysis_filename)
            with h5py.File(analysis_file_path, 'a') as hf:
                for idx, (spikes, indices) in enumerate(zip(spike_mat, spike_indices)):
                    spike_key = 'spiketimes_' + str(idx)
                    if spike_key in list(hf.keys()):
                        del hf[spike_key]
                        dset_4 = hf.create_dataset(spike_key, data=np.array(spikes))
                    else:
                        dset_4 = hf.create_dataset(spike_key, data=np.array(spikes))
                    indices_key = 'spiketimes_indices_' + str(idx)
                    if indices_key in list(hf.keys()):
                        del hf[indices_key]
                        dset_5 = hf.create_dataset(indices_key, data=np.array(indices))
                    else:
                        dset_5 = hf.create_dataset(indices_key, data=np.array(indices))
        else:
            with h5py.File(analysis_file_path, 'w') as hf:
                for idx, (spikes, indices) in enumerate(zip(spike_mat, spike_indices)):
                    spike_key = 'spiketimes_' + str(idx)
                    dset_4 = hf.create_dataset(spike_key, data=np.array(spikes))
                    indices_key = 'spiketimes_indices_' + str(idx)
                    dset_5 = hf.create_dataset(indices_key, data=np.array(indices))
        self.progress_label.setText('spike times saved in: ' + analysis_file_path)

    def is_busy_detecting_spikes(self):
        return self.spike_detection_thread is not None

    def can_be_closed(self):
        # only closeable if spike detection is not running currently
        return not self.is_busy_detecting_spikes()
