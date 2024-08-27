# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'lmod_query.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_LmodQueryWindow(object):
    def setupUi(self, LmodQueryWindow):
        LmodQueryWindow.setObjectName("LmodQueryWindow")
        LmodQueryWindow.resize(836, 726)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(LmodQueryWindow)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(LmodQueryWindow)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.search_edit = QtWidgets.QLineEdit(LmodQueryWindow)
        self.search_edit.setObjectName("search_edit")
        self.horizontalLayout.addWidget(self.search_edit)
        self.verticalLayout_3.addLayout(self.horizontalLayout)
        self.splitter_3 = QtWidgets.QSplitter(LmodQueryWindow)
        self.splitter_3.setOrientation(QtCore.Qt.Vertical)
        self.splitter_3.setObjectName("splitter_3")
        self.splitter_2 = QtWidgets.QSplitter(self.splitter_3)
        self.splitter_2.setOrientation(QtCore.Qt.Horizontal)
        self.splitter_2.setObjectName("splitter_2")
        self.module_list = QtWidgets.QListWidget(self.splitter_2)
        self.module_list.setObjectName("module_list")
        self.version_list = QtWidgets.QListWidget(self.splitter_2)
        self.version_list.setObjectName("version_list")
        self.widget = QtWidgets.QWidget(self.splitter_2)
        self.widget.setObjectName("widget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.widget)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.alt_list = QtWidgets.QComboBox(self.widget)
        self.alt_list.setObjectName("alt_list")
        self.verticalLayout_2.addWidget(self.alt_list)
        self.parent_list = QtWidgets.QListWidget(self.widget)
        self.parent_list.setObjectName("parent_list")
        self.verticalLayout_2.addWidget(self.parent_list)
        self.splitter = QtWidgets.QSplitter(self.splitter_3)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.module_help_text = QtWidgets.QTextEdit(self.splitter)
        font = QtGui.QFont()
        font.setFamily("DejaVu Sans Mono")
        self.module_help_text.setFont(font)
        self.module_help_text.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.module_help_text.setReadOnly(True)
        self.module_help_text.setObjectName("module_help_text")
        self.verticalLayoutWidget = QtWidgets.QWidget(self.splitter)
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.copy_cmds_button = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.copy_cmds_button.setObjectName("copy_cmds_button")
        self.horizontalLayout_2.addWidget(self.copy_cmds_button)
        self.start_term_button = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.start_term_button.setObjectName("start_term_button")
        self.horizontalLayout_2.addWidget(self.start_term_button)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.module_cmds_text = QtWidgets.QPlainTextEdit(self.verticalLayoutWidget)
        font = QtGui.QFont()
        font.setFamily("DejaVu Sans Mono")
        self.module_cmds_text.setFont(font)
        self.module_cmds_text.setObjectName("module_cmds_text")
        self.verticalLayout.addWidget(self.module_cmds_text)
        self.verticalLayout_3.addWidget(self.splitter_3)

        self.retranslateUi(LmodQueryWindow)
        QtCore.QMetaObject.connectSlotsByName(LmodQueryWindow)

    def retranslateUi(self, LmodQueryWindow):
        _translate = QtCore.QCoreApplication.translate
        LmodQueryWindow.setWindowTitle(_translate("LmodQueryWindow", "Module selector"))
        self.label.setText(_translate("LmodQueryWindow", "Module search:"))
        self.copy_cmds_button.setText(_translate("LmodQueryWindow", "Copy"))
        self.start_term_button.setText(_translate("LmodQueryWindow", "Terminal"))

