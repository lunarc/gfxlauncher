:layout: landing

.. |logo-light| image:: images/app_icon_text.png
   :width: 70%
   :alt: GFX Launcher
   :class: only-light

.. |logo-dark| image:: images/app_icon_text_dark.png
   :width: 70%
   :alt: GFX Launcher
   :class: only-dark

|logo-light|\ |logo-dark|
=========================

.. container:: hero-intro

   Launch GUI applications, hardware-accelerated graphics, Jupyter/RStudio
   notebooks, Ollama chat sessions and Windows desktops on Slurm - without
   users having to know SSH, VirtualGL or ``srun`` exist. GfxLauncher provides
   a configurable launcher UI (**gfxlaunch**) plus a tool that generates
   desktop menus and shortcuts for it (**gfxmenu**).

   New to GfxLauncher? Start with the :doc:`quickstart` - a working desktop
   menu entry in four steps - or see :doc:`technical_description` for how each
   launch method works under the hood.

.. grid:: 1 2 2 3
    :gutter: 3
    :class-container: sd-mb-4

    .. grid-item-card:: :octicon:`rocket;1.5em;sd-mr-1` Quickstart
        :link: quickstart
        :link-type: doc

        Install with pip and get one application launching from a desktop
        menu in a few minutes.

    .. grid-item-card:: :octicon:`package;1.5em;sd-mr-1` Installation
        :link: installation
        :link-type: doc

        PyPI install, source package layout, and the runtime environment
        GfxLauncher expects.

    .. grid-item-card:: :octicon:`gear;1.5em;sd-mr-1` Configuration
        :link: configuration
        :link-type: doc

        ``gfxlauncher.conf`` reference: Slurm partitions, features, groups,
        and the Jupyter/RStudio/Ollama backends.

    .. grid-item-card:: :octicon:`terminal;1.5em;sd-mr-1` gfxlaunch reference
        :link: gfxlaunch
        :link-type: doc

        Every command line switch for the launcher UI, with examples for
        each launch method.

    .. grid-item-card:: :octicon:`list-unordered;1.5em;sd-mr-1` gfxmenu reference
        :link: gfxmenu
        :link-type: doc

        ``##LDT`` script tags and generating desktop menus/shortcuts for
        your applications.

    .. grid-item-card:: :octicon:`server;1.5em;sd-mr-1` Compute node setup
        :link: node_config
        :link-type: doc

        Configuring nodes with pam_exec so launched applications get the
        job's resource limits.

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
