from PyQt5 import QtCore, QtWidgets
import matplotlib.gridspec as gridspec
import numpy as np

from frequency_analysis.frequency_analysis_thread import FrequencyAnalysisThread
from frequency_analysis.frequency_plot_creation_thread import FrequencyPlotCreationThread

from plots.plot_widget import PlotWidget
from plot_manager import PlotManager


class FrequencyAnalysisTab(QtWidgets.QWidget):
    def __init__(self, parent, reader, grid_indices, settings):
        super().__init__(parent)
        self.reader = reader
        self.grid_indices = grid_indices
        self.settings = settings

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignCenter)

        operation_layout = QtWidgets.QVBoxLayout(self)
        operation_layout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)

        self.operation_label = QtWidgets.QLabel(self)
        self.operation_label.setText('Nothing happens so far')
        operation_layout.addWidget(self.operation_label)
        self.progress_label = QtWidgets.QLabel(self)
        operation_layout.addWidget(self.progress_label)

        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(True)
        operation_layout.addWidget(self.progress_bar)

        main_layout.addLayout(operation_layout)

        plot_name = 'Frequency_analysis_' + self.reader.filename

        self.plot_widget = PlotWidget(self, plot_name)
        main_layout.addWidget(self.plot_widget)
        self.figure = self.plot_widget.figure

        self.frequency_analysis_thread = None
        self.frequencies = None

        self.plot_thread = None

    def initialize_frequency_analysis(self):
        if self.frequencies is None:
            self.progress_bar.setValue(0)
            self.progress_bar.setText('')
            self.operation_label.setText('Analyzing frequency components of recording')
            self.frequency_analysis_thread = FrequencyAnalysisThread(self, self.reader, self.grid_indices)
            self.frequency_analysis_thread.progress_made.connect(self.on_progress_made)
            self.frequency_analysis_thread.operation_changed.connect(self.on_operation_changed)
            self.frequency_analysis_thread.data_updated.connect(self.on_data_updated)
            self.frequency_analysis_thread.finished.connect(self.on_frequency_analysis_thread_finished)

            debug_mode = False  # set to 'True' in order to debug with embed
            if debug_mode:
                # synchronous plotting (runs in main thread and thus allows debugging)
                self.frequency_analysis_thread.run()
            else:
                # asynchronous plotting (default):
                self.frequency_analysis_thread.start()  # start will start thread (and run),
                # but main thread will continue immediately

        # this function updates the progress bar

    @QtCore.pyqtSlot(float)
    def on_progress_made(self, progress):
        self.progress_bar.setValue(int(progress))
        self.progress_label.setText(str(progress) + "%")

    def on_frequency_analysis_thread_finished(self):
        self.progress_label.setText('Finished :)')
        if self.filtering_thread.filtered_mat:
            print('copying found frequencies...')
            self.frequencies = self.frequency_analysis_thread.frequencies.copy()
        self.frequency_analysis_thread = None
        self.initialize_plotting()

    def initialize_plotting(self):
        self.toolbar.hide()
        self.plot_thread = FrequencyPlotCreationThread(self, self.figure, self.frequencies)
        self.plot_thread.finished.connect(self.on_plot_thread_is_done)

        debug_mode = False  # set to 'True' in order to debug plot creation with embed
        if debug_mode:
            # synchronous plotting (runs in main thread and thus allows debugging)
            self.plot_thread.run()
        else:
            # asynchronous plotting (default):
            self.plot_thread.start()  # start will start thread (and run), but main thread will continue immediately

    def plot(self, figure, frequencies):
        spec = gridspec.GridSpec(ncols=4, nrows=4, figure=figure, wspace=.7)
        for row in range(4):
            for col in range(4):
                for idx, frequency_component in enumerate(frequencies):
                    ax = figure.add_subplot(spec[row, col])
                    N = int(len(frequency_component)/2 + 1)
                    fs = self.reader.fs
                    X = np.linspace(0, fs / 2, N, endpoint=True)
                    ax.plot(X, 2.0*np.abs(frequency_component[:N])/N)
                    ax.set_xlabel('frequency [Hz]')
                    ax.set_ylabel('Amplitude [$\mu$V/Hz]')
                    ax.spines['right'].set_visible(False)
                    ax.spines['top'].set_visible(False)
                    ax.get_xaxis().tick_bottom()
                    ax.get_yaxis().tick_left()
                    ax.tick_params(labelsize=10, direction='out')
                    ax.grid(True)

