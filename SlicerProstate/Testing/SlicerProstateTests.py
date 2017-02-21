import slicer
import os
import unittest

from SlicerProstateUtils.helpers import DirectoryWatcher
from SlicerProstateUtils.mixins import ModuleLogicMixin

import logging

from SampleData import SampleDataLogic

__all__ = ['SlicerProstateTests']


class DirectoryWatcherTest(unittest.TestCase, ModuleLogicMixin):

  @classmethod
  def setUpClass(cls):
    slicer.mrmlScene.Clear(0)
    cls.directory = os.path.join(slicer.app.temporaryPath, "SlicerProstateTesting", cls.__class__.__name__)
    cls.createDirectory(cls.directory)
    cls.watcher = DirectoryWatcher(cls.directory)
    cls.sampleDataLogic = SampleDataLogic()

  # def tearDown(self):
  #   import shutil
  #   shutil.rmtree(os.path.join(slicer.app.temporaryPath, "SlicerProstateTesting"))

  def runTest(self):
    # self.setUp()
    self.test_DirectoryWatcherStart()
    self.test_DirectoryWatcherFileCountChanged()
    self.test_DirectoryWatcherStop()

  def test_DirectoryWatcherStart(self):
    self.watcher.start()
    self.assertTrue(self.watcher.isRunning())

  def test_DirectoryWatcherFileCountChanged(self):
    mrHead = self.sampleDataLogic.sourceForSampleName('MRHead')
    self.sampleDataLogic.downloadFile(mrHead.uris[0], self.directory, mrHead.fileNames[0])

    def checkFileCount():
      self.assertNotEqual(len(self.watcher.startingFileList), len(self.watcher.currentFileList))

    timer = self.createTimer(interval=2000, slot=checkFileCount, singleShot=True)
    timer.start()

  def test_DirectoryWatcherStop(self):
    self.watcher.stop()
    self.assertFalse(self.watcher.isRunning())