Introduction
============

Running applications requiring graphical user interfaces, hardware-accelerated graphics, or interactive web-based notebooks on HPC resources through SLURM can be a challenge for users. GfxLauncher is a tool for making the process of launching these applications through SLURM. The tool provides a simple user interface where the user can specify resource requirements and launch the desired application. GfxLauncher will also track the application and display information on how much allocated time is left. The user also has the ability to stop the running application, restart it and reconnect to any web services running on an allocated node.

GfxLauncher supports several methods for launching interactive applications in a HPC environment:

•	OpenGL applications using VirtualGL and the vglconnect mechanism.
•	Normal applications using the SSH mechanism.
•	Jupyter Notebooks/Lab through SSH.
•	Windows desktop sessions through SSH and Xrdp.





