.. fastlane documentation master file, created by
   sphinx-quickstart on Tue Dec 18 15:28:21 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Fastlane
====================================

.. image:: https://img.shields.io/github/license/heynemann/fastlane.svg
   :target: https://github.com/heynemann/fastlane/blob/master/LICENSE

**Fastlane** is a redis-based queueing service that outsmarts everyone else by using containers.

https://img.shields.io/github/license/heynemann/fastlane.svg

.. image:: _static/single_task.gif

More seriously, though, **Fastlane** allows you to easily implement new workers in the form of containers.

Instead of the tedious, repetitive work of yesteryear where you had to implement a worker in language X or Y, you just spin a new container with all the dependencies you require already previously installed, and instruct fastlane to run a command in that container. Bang! Instant Super-Powered Workers!

**Fastlane** is licensed under the MIT and it officially supports Python 3.7 and later.

User Guide
----------

This part of the documentation is focused primarily on teaching you how to use **Fastlane**.

.. toctree::
   :maxdepth: 2

   guide
   architecture

Project Info
------------

- `Source Code <https://github.com/heynemann/fastlane>`_
- `Project License <https://github.com/heynemann/fastlane/blob/master/LICENSE>`_
