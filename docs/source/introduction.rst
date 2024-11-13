Introduction
============

Running applications requiring graphical user interfaces, hardware-accelerated graphics, or interactive web-based notebooks on HPC resources can be a challenge for users. The GFX Launcher framework makes the process of launching these applications through Slurm easier. The framework consists of two main parts. The graphical launcher (gfxlaunch) a command line tool providing a user interface and methods of launching applications. The second part is the menu generation tool (gfxmenu) that generate menus and gfxlaunch shortcuts for applications from special shell scripts. These tools together creates an easy to use solution for launching applications on HPC resources.

The **gfxlaunch** command line tool provides a customisable user interface where the user can specify resource requirements and launch the application. **gfxlaunch** will also track the application and display information on how much allocated time is left. Through this user interface,the user also has the ability to stop the running application, restart and reconnect to any web services running on the allocated node.

The GFX Launcher framework currently supports the following methods for launching interactive applications in a HPC environment:

•	OpenGL applications using VirtualGL and the vglconnect mechanism.
•	Normal applications using the SSH mechanism.
•	Jupyter Notebooks/Lab through SSH.
•	Windows desktop sessions through SSH and Xrdp.





