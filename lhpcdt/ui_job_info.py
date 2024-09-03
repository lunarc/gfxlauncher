# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'job_info.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(577, 568)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.job_properties = QtWidgets.QTableWidget(self.centralwidget)
        self.job_properties.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.job_properties.setAlternatingRowColors(True)
        self.job_properties.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.job_properties.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.job_properties.setObjectName("job_properties")
        self.job_properties.setColumnCount(0)
        self.job_properties.setRowCount(0)
        self.job_properties.verticalHeader().setVisible(False)
        self.verticalLayout.addWidget(self.job_properties)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 577, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.toolBar = QtWidgets.QToolBar(MainWindow)
        self.toolBar.setObjectName("toolBar")
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.action_refresh_view = QtWidgets.QAction(MainWindow)
        icon = QtGui.QIcon.fromTheme("view-refresh")
        self.action_refresh_view.setIcon(icon)
        self.action_refresh_view.setObjectName("action_refresh_view")
        self.toolBar.addAction(self.action_refresh_view)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.toolBar.setWindowTitle(_translate("MainWindow", "toolBar"))
        self.action_refresh_view.setText(_translate("MainWindow", "Refresh"))

