# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'notebook_job_prop_win.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_notebook_prop_form(object):
    def setupUi(self, notebook_prop_form):
        notebook_prop_form.setObjectName("notebook_prop_form")
        notebook_prop_form.setWindowModality(QtCore.Qt.ApplicationModal)
        notebook_prop_form.resize(428, 262)
        notebook_prop_form.setModal(True)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(notebook_prop_form)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.control_frame = QtWidgets.QFrame(notebook_prop_form)
        self.control_frame.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.control_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.control_frame.setObjectName("control_frame")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.control_frame)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.use_custom_env_check = QtWidgets.QCheckBox(self.control_frame)
        self.use_custom_env_check.setText("")
        self.use_custom_env_check.setObjectName("use_custom_env_check")
        self.gridLayout.addWidget(self.use_custom_env_check, 3, 1, 1, 1)
        self.conda_module_label = QtWidgets.QLabel(self.control_frame)
        self.conda_module_label.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.conda_module_label.setObjectName("conda_module_label")
        self.gridLayout.addWidget(self.conda_module_label, 0, 0, 1, 1)
        self.conda_env_label = QtWidgets.QLabel(self.control_frame)
        self.conda_env_label.setObjectName("conda_env_label")
        self.gridLayout.addWidget(self.conda_env_label, 8, 0, 1, 1)
        self.label_3 = QtWidgets.QLabel(self.control_frame)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 3, 0, 1, 1)
        self.conda_env_list = QtWidgets.QComboBox(self.control_frame)
        self.conda_env_list.setObjectName("conda_env_list")
        self.gridLayout.addWidget(self.conda_env_list, 8, 1, 1, 1)
        self.browse_modules_button = QtWidgets.QPushButton(self.control_frame)
        self.browse_modules_button.setObjectName("browse_modules_button")
        self.gridLayout.addWidget(self.browse_modules_button, 1, 1, 1, 1)
        self.conda_module_text = QtWidgets.QPlainTextEdit(self.control_frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.conda_module_text.sizePolicy().hasHeightForWidth())
        self.conda_module_text.setSizePolicy(sizePolicy)
        self.conda_module_text.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.conda_module_text.setPlainText("")
        self.conda_module_text.setObjectName("conda_module_text")
        self.gridLayout.addWidget(self.conda_module_text, 0, 1, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        self.verticalLayout_2.addWidget(self.control_frame)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.ok_button = QtWidgets.QPushButton(notebook_prop_form)
        self.ok_button.setObjectName("ok_button")
        self.horizontalLayout.addWidget(self.ok_button)
        self.cancel_button = QtWidgets.QPushButton(notebook_prop_form)
        self.cancel_button.setObjectName("cancel_button")
        self.horizontalLayout.addWidget(self.cancel_button)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.env_status_text = QtWidgets.QLabel(notebook_prop_form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.env_status_text.sizePolicy().hasHeightForWidth())
        self.env_status_text.setSizePolicy(sizePolicy)
        self.env_status_text.setMinimumSize(QtCore.QSize(26, 0))
        self.env_status_text.setMaximumSize(QtCore.QSize(16777215, 26))
        self.env_status_text.setBaseSize(QtCore.QSize(0, 26))
        self.env_status_text.setFrameShape(QtWidgets.QFrame.Panel)
        self.env_status_text.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.env_status_text.setText("")
        self.env_status_text.setObjectName("env_status_text")
        self.verticalLayout_2.addWidget(self.env_status_text)

        self.retranslateUi(notebook_prop_form)
        QtCore.QMetaObject.connectSlotsByName(notebook_prop_form)

    def retranslateUi(self, notebook_prop_form):
        _translate = QtCore.QCoreApplication.translate
        notebook_prop_form.setWindowTitle(_translate("notebook_prop_form", "Notebook job properties"))
        self.conda_module_label.setText(_translate("notebook_prop_form", "Python modules"))
        self.conda_env_label.setText(_translate("notebook_prop_form", "Conda environment"))
        self.label_3.setText(_translate("notebook_prop_form", "Use custom conda env"))
        self.browse_modules_button.setText(_translate("notebook_prop_form", "Select modules"))
        self.ok_button.setText(_translate("notebook_prop_form", "OK"))
        self.cancel_button.setText(_translate("notebook_prop_form", "Cancel"))

