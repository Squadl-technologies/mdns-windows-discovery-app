mdns-windows-discovery-app
==========================

Windows mDNS discovery tooling for building:

* ``sq-discovery.exe``
* ``sq-discovery-tray.exe``

The command-line executable can run one-off scans or manage the Windows service.
The tray executable shows service and device status from the service state files.

Build on Windows
================

From the repository root:

.. code-block:: powershell

   Set-ExecutionPolicy -Scope Process Bypass
   .\build-windows.ps1

The build script creates ``.venv``, installs the required dependencies, creates
the icon asset, and runs PyInstaller for both spec files.

Build outputs:

.. code-block:: powershell

   .\dist\sq-discovery.exe
   .\dist\sq-discovery-tray.exe

Install the service
===================

.. code-block:: powershell

   .\install-service.ps1

Install the tray startup task
=============================

Run PowerShell as Administrator:

.. code-block:: powershell

   .\install-tray.ps1

Usage
=====

See ``use.md`` for scan examples, service commands, tray behavior, and
troubleshooting notes.
