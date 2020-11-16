from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg

from mcs_data_reader import McsDataReader
from meae_data_reader import MeaeDataReader
from SC_data_reader import SCDataReader

from mea_grid import MeaGrid

from settings import Settings
from file_manager import FileManager

from spike_detection.spike_detection_settings_dialog import SpikeDetectionSettingsDialog
from spike_detection.spike_detection_settings import SpikeDetectionSettings
from spike_detection.spike_detection_tab import SpikeDetectionTab

from filtering.filter_settings_dialog import FilterSettingsDialog
from filtering.filter_settings import FilterSettings
from filtering.filter_tab import FilterTab

from plots.csd_plot.csd_plot_tab import CsdPlotTab
from plots.raster_plot.rasterplot_tab import RasterplotTab
from plots.heatmap.heatmap_tab import HeatmapTab

from plots.csd_plot.csd_plot_settings import CsdPlotSettings
from plots.csd_plot.csd_plot_settings_dialog import CsdPlotSettingsDialog
from plots.raster_plot.rasterplot_settings_dialog import RasterplotSettingsDialog
from plots.raster_plot.rasterplot_settings import RasterplotSettings
from plots.heatmap.heatmap_settings_dialog import HeatmapSettingsDialog
from plots.heatmap.heatmap_settings import HeatmapSettings


class MeaFileView(QtWidgets.QWidget):
    def __init__(self, parent, mea_file):
        super().__init__(parent)
        self.reader = McsDataReader(mea_file)
        self.mea_file = mea_file

        self.file_manager = FileManager(self, self.reader.file_path)
        self.filter_settings = Settings.instance.filter_settings
        self.plot_settings = Settings.instance.plot_settings
        self.spike_detection_settings = Settings.instance.spike_detection_settings
        self.csd_plot_settings = Settings.instance.csd_plot_settings

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)

        self.toolbar = QtWidgets.QToolBar(self)

        self.show_file_manager = QtWidgets.QAction("File manager", self)
        self.show_file_manager.triggered.connect(self.on_show_file_manager)
        self.show_file_manager.setCheckable(True)
        self.show_file_manager.setChecked(False)
        self.toolbar.addAction(self.show_file_manager)

        self.show_mea_grid = QtWidgets.QAction("MEA grid", self)
        self.show_mea_grid.triggered.connect(self.on_show_mea_grid)
        self.show_mea_grid.setCheckable(True)
        self.show_mea_grid.setChecked(True)
        self.toolbar.addAction(self.show_mea_grid)

        self.show_filter_dialog = QtWidgets.QAction("Filtering", self)
        self.show_filter_dialog.triggered.connect(self.open_filter_dialog)
        self.toolbar.addAction(self.show_filter_dialog)

        self.show_spike_detection_dialog = QtWidgets.QAction('Spike Detection', self)
        self.show_spike_detection_dialog.triggered.connect(self.open_sd_dialog)
        self.toolbar.addAction(self.show_spike_detection_dialog)

        self.add_csd_plot_tab = QtWidgets.QAction('CSD plot', self)
        self.add_csd_plot_tab.triggered.connect(self.add_csd_plot_to_tabs)
        self.toolbar.addAction(self.add_csd_plot_tab)

        self.add_rasterplot_tab = QtWidgets.QAction('Rasterplot', self)
        self.add_rasterplot_tab.triggered.connect(self.open_rasterplot_settings_dialog)
        self.toolbar.addAction(self.add_rasterplot_tab)

        self.add_heatmap_tab = QtWidgets.QAction('Heatmap', self)
        self.add_heatmap_tab.triggered.connect(self.open_heatmap_settings_dialog)
        self.toolbar.addAction(self.add_heatmap_tab)

        main_layout.addWidget(self.toolbar)

        sub_layout = QtWidgets.QHBoxLayout(self)
        sub_layout.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignTop)

        mea_grid_and_minor_widgets_layout = QtWidgets.QVBoxLayout(self)
        mea_grid_and_minor_widgets_layout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignCenter)
        mea_grid_and_minor_widgets_layout.addWidget(self.file_manager)
        self.mea_grid = MeaGrid(self)
        self.mea_grid.setFixedSize(600, 600)
        mea_grid_and_minor_widgets_layout.addWidget(self.mea_grid)
        sub_layout.addLayout(mea_grid_and_minor_widgets_layout)

        self.tab_widget = QtWidgets.QTabWidget(self)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setTabBarAutoHide(False)

        sub_layout.addWidget(self.tab_widget)
        main_layout.addLayout(sub_layout)

        # make sure widget visibility matches tool bar button check states
        self.file_manager.setVisible(self.show_file_manager.isChecked())
        self.mea_grid.setVisible(self.show_mea_grid.isChecked())

        self.filter_tab = None
        self.spike_detection_tab = None

        self.csd_plot_tab = None
        self.heatmap_tab = None
        self.rasterplot_tab = None

    def open_heatmap_settings_dialog(self, is_pressed):
        allowed_modes = [HeatmapSettings.Mode.MCS]
        if self.file_manager.get_verified_meae_file() is not None:
            allowed_modes.append(HeatmapSettings.Mode.MEAE)
        if self.file_manager.get_verified_sc_file() is not None:
            allowed_modes.append(HeatmapSettings.Mode.SC)
        settings_dialog = HeatmapSettingsDialog(self, allowed_modes, self.plot_settings)
        if settings_dialog.exec() == 1:  # 'Execute' clicked
            self.plot_settings = settings_dialog.get_settings()
            # overwrite global settings as well
            Settings.instance.plot_settings = self.plot_settings

            # initialise plotting
            if self.plot_settings.mode == HeatmapSettings.Mode.MCS:
                self.heatmap_tab = HeatmapTab(self, self.reader, self.plot_settings)
                self.tab_widget.addTab(self.heatmap_tab, "Heatmap")
            elif self.plot_settings.mode == HeatmapSettings.Mode.MEAE:
                meae_path = self.file_manager.get_verified_meae_file()
                meae_reader = MeaeDataReader(meae_path)
                self.heatmap_tab = HeatmapTab(self, meae_reader, self.plot_settings)
                self.tab_widget.addTab(self.heatmap_tab, "Heatmap")
            elif self.plot_settings.mode == HeatmapSettings.Mode.SC:
                sc_path = self.file_manager.get_verified_sc_file()
                sc_reader = SCDataReader(sc_path)
                self.heatmap_tab = HeatmapTab(self, sc_reader, self.plot_settings)
                self.tab_widget.addTab(self.heatmap_tab, "Heatmap")

    def open_rasterplot_settings_dialog(self, is_pressed):
        channel_labels_and_indices = self.mea_grid.get_selected_channels()
        allowed_channel_modes = [RasterplotSettings.ChannelSelection.ALL]
        if len(channel_labels_and_indices) > 0:
            allowed_channel_modes.append(RasterplotSettings.ChannelSelection.SELECTION)

        # determine allowed modes
        allowed_modes = [RasterplotSettings.Mode.MCS]
        if self.file_manager.get_verified_meae_file() is not None:
            allowed_modes.append(RasterplotSettings.Mode.MEAE)
        if self.file_manager.get_verified_sc_file() is not None:
            allowed_modes.append(RasterplotSettings.Mode.SC)
        settings_dialog = RasterplotSettingsDialog(self, allowed_modes, allowed_channel_modes, self.plot_settings)
        if settings_dialog.exec() == 1:  # 'Execute' clicked
            self.plot_settings = settings_dialog.get_settings()
            # overwrite global settings as well
            if self.plot_settings.channel_selection == RasterplotSettings.ChannelSelection.ALL:
                grid_indices = range(len(self.reader.voltage_traces))
            elif self.plot_settings.channel_selection == RasterplotSettings.ChannelSelection.SELECTION:
                grid_labels_and_indices = self.mea_grid.get_selected_channels()
                grid_indices = [values[1] for values in grid_labels_and_indices]

            Settings.instance.raserplot_settings = self.plot_settings
            sampling_rate = self.reader.sampling_frequency
            duration = self.reader.duration

            # initialise plotting
            if self.plot_settings.mode == RasterplotSettings.Mode.MCS:
                self.rasterplot_tab = RasterplotTab(self, self.reader, self.plot_settings, sampling_rate, duration,
                                               grid_indices)
                self.tab_widget.addTab(self.rasterplot_tab, "Rasterplot")
            elif self.plot_settings.mode == RasterplotSettings.Mode.MEAE:
                meae_path = self.file_manager.get_verified_meae_file()
                meae_reader = MeaeDataReader(meae_path)
                self.rasterplot_tab = RasterplotTab(self, meae_reader, self.plot_settings, sampling_rate, duration,
                                               grid_indices)
                self.tab_widget.addTab(self.rasterplot_tab, "Rasterplot")
            elif self.plot_settings.mode == RasterplotSettings.Mode.SC:
                sc_path = self.file_manager.get_verified_sc_file()
                sc_reader = SCDataReader(sc_path)
                self.rasterplot_tab = RasterplotTab(self, sc_reader, self.plot_settings, sampling_rate, duration,
                                               grid_indices)
                self.tab_widget.addTab(self.rasterplot_tab, "Rasterplot")

    @QtCore.pyqtSlot()
    def open_sd_dialog(self):
        channel_labels_and_indices = self.mea_grid.get_selected_channels()
        allowed_modes = [FilterSettings.ChannelSelection.ALL]
        if len(channel_labels_and_indices) > 0:
            allowed_modes.append(SpikeDetectionSettings.ChannelSelection.SELECTION)
        settings_dialog = SpikeDetectionSettingsDialog(self, self.spike_detection_settings, allowed_modes)
        if settings_dialog.exec() == 1:  # 'Execute' clicked
            self.spike_detection_settings = settings_dialog.get_settings()
            if self.spike_detection_settings.channel_selection == SpikeDetectionSettings.ChannelSelection.ALL:
                grid_indices = range(len(self.reader.voltage_traces))
            elif self.spike_detection_settings.channel_selection == SpikeDetectionSettings.ChannelSelection.SELECTION:
                grid_labels_and_indices = self.mea_grid.get_selected_channels()
                grid_indices = [values[1] for values in grid_labels_and_indices]
            # overwrite global settings as well
            Settings.instance.spike_detection_settings = self.spike_detection_settings

            # initialise filtering
            # give FilterThread indices (all is default and if selected, thread has to receive special indices
            # -> via filter tab?)
            self.spike_detection_tab = SpikeDetectionTab(self, self.reader, grid_indices, self.spike_detection_settings)
            self.tab_widget.addTab(self.spike_detection_tab, "Spike detection")
            self.spike_detection_tab.initialize_spike_detection()

    @QtCore.pyqtSlot()
    def open_filter_dialog(self):
        channel_labels_and_indices = self.mea_grid.get_selected_channels()
        allowed_modes = [FilterSettings.ChannelSelection.ALL]
        if len(channel_labels_and_indices) > 0:
            allowed_modes.append(FilterSettings.ChannelSelection.SELECTION)
        settings_dialog = FilterSettingsDialog(self, self.filter_settings, allowed_modes)
        if settings_dialog.exec() == 1:  # 'Execute' clicked
            self.filter_settings = settings_dialog.get_settings()
            if self.filter_settings.channel_selection == FilterSettings.ChannelSelection.ALL:
                grid_indices = range(len(self.reader.voltage_traces))
            elif self.filter_settings.channel_selection == FilterSettings.ChannelSelection.SELECTION:
                grid_labels_and_indices = self.mea_grid.get_selected_channels()
                grid_indices = [values[1] for values in grid_labels_and_indices]
            # overwrite global settings as well
            Settings.instance.filter_settings = self.filter_settings

            # initialise filtering
            # give FilterThread indices (all is default and if selected, thread has to receive special indices
            # -> via filter tab?)
            self.filter_tab = FilterTab(self, self.reader,  grid_indices, self.filter_settings)
            self.tab_widget.addTab(self.filter_tab, "Filtering")
            self.filter_tab.initialize_filtering()

    @QtCore.pyqtSlot()
    def add_csd_plot_to_tabs(self):
        channel_labels_and_indices = self.mea_grid.get_selected_channels()
        allowed_channel_modes = [CsdPlotSettings.ChannelSelection.ALL]
        if len(channel_labels_and_indices) > 0:
            allowed_channel_modes.append(CsdPlotSettings.ChannelSelection.SELECTION)
        settings_dialog = CsdPlotSettingsDialog(self, allowed_channel_modes)
        if settings_dialog.exec() == 1:  # 'Execute' clicked
            self.csd_plot_settings = settings_dialog.get_settings()
            # overwrite global settings as well
            if self.csd_plot_settings.channel_selection == CsdPlotSettings.ChannelSelection.ALL:
                grid_indices = range(len(self.reader.voltage_traces))
            elif self.csd_plot_settings.channel_selection == CsdPlotSettings.ChannelSelection.SELECTION:
                grid_labels_and_indices = self.mea_grid.get_selected_channels()
                grid_indices = [values[1] for values in grid_labels_and_indices]

            Settings.instance.csd_plot_settings = self.csd_plot_settings
            duration = self.reader.duration

            self.csd_plot_tab = CsdPlotTab(self, self.reader, grid_indices, duration, self.csd_plot_settings)
            self.tab_widget.addTab(self.csd_plot_tab, "CSD Plot")

    def on_show_file_manager(self, is_pressed):
        self.file_manager.setVisible(is_pressed)

    def on_show_mea_grid(self, is_pressed):
        self.mea_grid.setVisible(is_pressed)

    # def can_be_closed(self):
    #     if self.filter_tab is None:
    #     return self.filter_tab.can_be_closed(), self.spike_detection_tab.can_be_closed(), \
    #            self.csd_plot_tab.can_be_closed(), self.heatmap_tab.can_be_closed(),self.rasterplot_tab.can_be_closed()
    #
    # def closeEvent(self, close_event):
    #     self.filter_tab.close()
    #     self.spike_detection_tab.close()
    #
    #     self.csd_plot_tab.close()
    #     self.heatmap_tab.close()
    #     self.rasterplot_tab.close()
    #
    #     super().closeEvent(close_event)
