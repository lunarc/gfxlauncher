:layout: landing

.. image:: images/app_icon.svg
  :width: 15%
  :align: left
  :alt: GFX Launcher

GFX Launcher
============

Launch GUI applications, hardware-accelerated graphics, Jupyter/RStudio
notebooks and Ollama chat sessions on Slurm - without users having to know
SSH, VirtualGL or ``srun`` exist. GfxLauncher provides a configurable
launcher UI (**gfxlaunch**) plus a tool that generates desktop menus and
shortcuts for it (**gfxmenu**).

New to GfxLauncher? Start with the :doc:`quickstart` - a working desktop
menu entry in four steps.

.. grid:: 1 2 2 3
    :gutter: 3
    :class-container: sd-mb-4

    .. grid-item-card:: 🚀 Quickstart
        :link: quickstart
        :link-type: doc

        Install with pip and get one application launching from a desktop
        menu in a few minutes.

    .. grid-item-card:: 📦 Installation
        :link: installation
        :link-type: doc

        PyPI install, source package layout, and the runtime environment
        GfxLauncher expects.

    .. grid-item-card:: ⚙️ Configuration
        :link: configuration
        :link-type: doc

        ``gfxlauncher.conf`` reference: Slurm partitions, features, groups,
        and the Jupyter/RStudio/Ollama backends.

    .. grid-item-card:: 🖥️ gfxlaunch reference
        :link: gfxlaunch
        :link-type: doc

        Every command line switch for the launcher UI, with examples for
        each launch method.

    .. grid-item-card:: 🗂️ gfxmenu reference
        :link: gfxmenu
        :link-type: doc

        ``##LDT`` script tags and generating desktop menus/shortcuts for
        your applications.

    .. grid-item-card:: 🧩 Compute node setup
        :link: node_config
        :link-type: doc

        Configuring nodes with pam_exec so launched applications get the
        job's resource limits.

Supported launch methods
-------------------------

* OpenGL applications using VirtualGL and ``vglconnect``.
* Normal applications using SSH.
* Jupyter Notebook/Lab and RStudio Server sessions.
* Ollama-backed local LLM chat sessions.
* Windows desktop sessions through SSH and Xrdp.

See :doc:`technical_description` for how each of these works under the hood.

.. toctree::
   :maxdepth: 2
   :hidden:

   quickstart.rst
   installation.rst
   configuration.rst
   node_config.rst
   gfxlaunch.rst
   gfxmenu.rst
   configuration_slurmvm.rst
   introduction.rst
   technical_description.rst
   code_documentation.rst
