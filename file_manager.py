from PyQt5 import QtCore, QtWidgets
import os


# This widget enables the user to set paths to .meae files or SpyKING CIRCUS (SC) result files which will then be used
# for plotting
class FileManager(QtWidgets.QWidget):
    def __init__(self, mea_file_view, mcs_file):
        super().__init__(mea_file_view)
        self.mea_file_view = mea_file_view
        self.mcs_file = mcs_file

        self.mcs_file_directory, self.mcs_file_name = os.path.split(self.mcs_file)

        # layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)

        mcs_layout = QtWidgets.QHBoxLayout()
        mcs_label = QtWidgets.QLabel(self)
        mcs_label.setText("MCS file:")
        mcs_layout.addWidget(mcs_label)
        mcs_path_label = QtWidgets.QLabel(self)
        mcs_path_label.setText(mcs_file)
        mcs_layout.addWidget(mcs_path_label)
        main_layout.addLayout(mcs_layout)

        meae_layout = QtWidgets.QHBoxLayout()
        meae_label = QtWidgets.QLabel(self)
        meae_label.setText("MEAE file:")
        meae_layout.addWidget(meae_label)
        self.meae_path_input = QtWidgets.QLineEdit(self)
        self.meae_path_input.setText("")
        meae_layout.addWidget(self.meae_path_input)
        meae_path_change_button = QtWidgets.QPushButton(self)
        meae_path_change_button.setText("...")
        meae_path_change_button.pressed.connect(self.on_meae_path_change_button_pressed)
        meae_layout.addWidget(meae_path_change_button)
        meae_path_remove_button = QtWidgets.QPushButton(self)
        meae_path_remove_button.setText("-")
        meae_path_remove_button.pressed.connect(self.on_meae_path_remove_button_pressed)
        meae_layout.addWidget(meae_path_remove_button)
        main_layout.addLayout(meae_layout)

        sc_layout = QtWidgets.QHBoxLayout()
        sc_label = QtWidgets.QLabel(self)
        sc_label.setText("SC file:")
        sc_layout.addWidget(sc_label)
        self.sc_path_input = QtWidgets.QLineEdit(self)
        self.sc_path_input.setText("")
        sc_layout.addWidget(self.sc_path_input)
        sc_path_change_button = QtWidgets.QPushButton(self)
        sc_path_change_button.setText("...")
        sc_path_change_button.pressed.connect(self.on_sc_path_change_button_pressed)
        sc_layout.addWidget(sc_path_change_button)
        sc_path_remove_button = QtWidgets.QPushButton(self)
        sc_path_remove_button.setText("-")
        sc_path_remove_button.pressed.connect(self.on_sc_path_remove_button_pressed)
        sc_layout.addWidget(sc_path_remove_button)
        main_layout.addLayout(sc_layout)

        sc_base_file_layout = QtWidgets.QHBoxLayout()
        sc_base_file_label = QtWidgets.QLabel(self)
        sc_base_file_label.setText("base file in the SC folder:")
        sc_base_file_layout.addWidget(sc_base_file_label)
        self.sc_base_file_input = QtWidgets.QLineEdit(self)
        self.sc_base_file_input.setText("")
        sc_base_file_layout.addWidget(self.sc_base_file_input)
        sc_base_file_change_button = QtWidgets.QPushButton(self)
        sc_base_file_change_button.setText("...")
        sc_base_file_change_button.pressed.connect(self.on_sc_base_file_path_change_button_pressed)
        sc_base_file_layout.addWidget(sc_base_file_change_button)
        sc_base_file_remove_button = QtWidgets.QPushButton(self)
        sc_base_file_remove_button.setText("-")
        sc_base_file_remove_button.pressed.connect(self.on_sc_base_file_path_remove_button_pressed)
        sc_base_file_layout.addWidget(sc_base_file_remove_button)
        main_layout.addLayout(sc_layout)
        main_layout.addLayout(sc_base_file_layout)

        self.auto_detect_meae_file()
        self.auto_detect_sc_file()

    # This function automatically detects the .meae file if it is in the same folder as the normal .h5 file (with the
    # same filename except for the file extension).
    def auto_detect_meae_file(self):
        file = self.mcs_file
        file_without_extension = ".".join(file.split('.')[:-1])
        file_as_meae = file_without_extension + ".meae"
        if os.path.exists(file_as_meae):
            self.meae_path_input.setText(file_as_meae)

    # This function automatically detects the SC file if it is in the same folder as the normal .h5 file (with the
    # same filename except for the file extension).
    def auto_detect_sc_file(self):
        file = self.mcs_file
        file_without_extension = ".".join(file.split('.')[:-1])
        file_as_sc = file_without_extension + ".clusters.hdf5"
        if os.path.exists(file_as_sc):
            self.sc_path_input.setText(file_as_sc)

    # This function verifies if the file with the given filepath really exists
    def get_verified_meae_file(self):
        file = self.meae_path_input.text().strip()
        if os.path.exists(file):
            return file
        else:
            return None

    # This function verifies if the file with the given filepath really exists
    def get_verified_sc_file(self):
        file = self.sc_path_input.text().strip()
        if os.path.exists(file):
            return file
        else:
            return None

    def get_verified_sc_base_file(self):
        file = self.sc_base_file_input.text().strip()
        if os.path.exists(file):
            return file
        else:
            return None

    @QtCore.pyqtSlot()
    def on_sc_base_file_path_remove_button_pressed(self):
        self.sc_base_file_input.setText("")

    @QtCore.pyqtSlot()
    def on_sc_base_file_path_change_button_pressed(self):
        selectedFile = QtWidgets.QFileDialog.getOpenFileName(self, "Please select SC base file",
                                                             self.mcs_file_directory, "SC files (*.h5)")[0]
        if len(selectedFile) > 0:
            self.sc_base_file_input.setText(selectedFile)

    # This function allows a filepath selection dialog to open, once the mea_path_change_button is pressed
    @QtCore.pyqtSlot()
    def on_meae_path_change_button_pressed(self):
        selectedFile = QtWidgets.QFileDialog.getOpenFileName(self, "Please select Meae file", self.mcs_file_directory,
                                              "Meae files (*.meae)")[0]
        if len(selectedFile) > 0:
            self.meae_path_input.setText(selectedFile)

    # This function removes a filepath, once the mea_path_remove_button is pressed
    @QtCore.pyqtSlot()
    def on_meae_path_remove_button_pressed(self):
        self.meae_path_input.setText("")

    # This function allows a filepath selection dialog to open, once the sc_path_change_button is pressed
    @QtCore.pyqtSlot()
    def on_sc_path_change_button_pressed(self):
        selectedFile = QtWidgets.QFileDialog.getOpenFileName(self, "Please select SC file", self.mcs_file_directory,
                                                             "SC files (*.hdf5)")[0]
        if len(selectedFile) > 0:
            self.sc_path_input.setText(selectedFile)

    # This function removes a filepath, once the sc_path_remove_button is pressed
    @QtCore.pyqtSlot()
    def on_sc_path_remove_button_pressed(self):
        self.sc_path_input.setText("")
