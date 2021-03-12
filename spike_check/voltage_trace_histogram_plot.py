from PyQt5 import QtWidgets
import numpy as np
import seaborn as sns
from scipy.signal import filtfilt, butter

from plot_manager import PlotManager
from utility.channel_utility import ChannelUtility

from plots.plot_widget import PlotWidget


class VoltageTraceHistogramPlot(QtWidgets.QWidget):
    def __init__(self, parent, reader, label, label_index):
        super().__init__(parent)
        self.reader = reader
        self.label = label
        self.label_index = label_index

        main_layout = QtWidgets.QVBoxLayout(self)

        plot_name = 'VT_Histogram_' + self.reader.filename + '_' + self.label
        plot_widget = PlotWidget(self, plot_name)
        self.figure = plot_widget.figure
        self.ax = self.figure.add_subplot(111)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['top'].set_visible(False)
        self.ax.get_xaxis().tick_bottom()
        self.ax.get_yaxis().tick_left()
        self.ax.tick_params(labelsize=10, direction='out')
        self.ax.set_xlabel(r'amplitude [$\mu$ V]')
        self.ax.set_ylabel('prevelance')
        main_layout.addWidget(plot_widget)
        sns.set()

    def plot(self, label, label_index):
        self.label_index = label_index
        idx = ChannelUtility.get_ordered_index(label)
        trace = self.reader.voltage_traces[self.label_index]
        self.ax.cla()
        self.ax.hist(trace, density=True, bins=1000)
        self.figure.canvas.draw_idle()
