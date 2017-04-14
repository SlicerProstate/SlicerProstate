import slicer
import os, shutil
import unittest
from threading import Thread
import time

from multiprocessing.dummy import Pool as ThreadPool

from SlicerProstateUtils.helpers import DirectoryWatcher
from SlicerProstateUtils.mixins import ModuleLogicMixin

from SampleData import SampleDataLogic

__all__ = ['SlicerProstateTests']


class DirectoryWatcherTest(unittest.TestCase, ModuleLogicMixin):

  @classmethod
  def setUpClass(cls):
    slicer.mrmlScene.Clear(0)
    cls.tempDir = slicer.app.temporaryPath
    cls.watchedDirectory = os.path.join(cls.tempDir, "SlicerProstateTesting", cls.__class__.__name__)
    cls.createDirectory(cls.watchedDirectory)
    cls.watcher = DirectoryWatcher(cls.watchedDirectory)
    cls.sampleDataLogic = SampleDataLogic()

    cls.startedEventEmitted = False
    cls.stoppedEventEmitted = False
    cls.fileCountChangedEmitted = False

  # def tearDown(self):
  #   shutil.rmtree(os.path.join(slicer.app.temporaryPath, "SlicerProstateTesting"))

  def runTest(self):
    self.test_DirectoryWatcherEvents()
    self.test_DirectoryWatcherStart()
    self.test_DirectoryWatcherFileCountChanged()
    self.test_DirectoryWatcherStop()

  def test_DirectoryWatcherEvents(self):
    self.watcher.addEventObserver(self.watcher.StartedWatchingEvent,
                                  lambda event,caller:setattr(self, "startedEventEmitted", True))
    self.watcher.addEventObserver(self.watcher.StoppedWatchingEvent,
                                  lambda event,caller:setattr(self, "stoppedEventEmitted", True))
    self.watcher.start()
    self.watcher.stop()
    self.watcher.removeEventObservers()
    self.assertTrue(self.startedEventEmitted)
    self.assertTrue(self.stoppedEventEmitted)

  def test_DirectoryWatcherStart(self):
    self.watcher.start()
    self.assertTrue(self.watcher.isRunning())

  def test_DirectoryWatcherFileCountChanged(self):
    self.watcher.addEventObserver(self.watcher.IncomingFileCountChangedEvent,
                                  lambda event,caller,callData:setattr(self, "fileCountChangedEmitted", True))
    mrHead = self.sampleDataLogic.sourceForSampleName('MRHead')
    self.sampleDataLogic.downloadFile(mrHead.uris[0], self.tempDir, mrHead.fileNames[0])
    mrHeadPath = os.path.join(self.tempDir, mrHead.fileNames[0])
    shutil.copy(mrHeadPath, os.path.join(self.watchedDirectory, mrHead.fileNames[0]))

    def checkTimerExecuted():
      while not self.fileCountChangedEmitted:
        print "timer not done"
        time.sleep(1)
      print "timer done"

    pool = ThreadPool(4)
    results = pool.apply(checkTimerExecuted)
    pool.close()
    pool.join()
    #
    # t = Thread(target=checkTimerExecuted)
    # t.start()
    # t.run()

    self.assertTrue(self.fileCountChangedEmitted)
    self.watcher.removeEventObservers()

  def print_time(self, threadName, delay):
    count = 0
    while count < 5:
      time.sleep(delay)
      count += 1
      print "%s: %s" % (threadName, time.ctime(time.time()))

  def test_DirectoryWatcherStop(self):
    self.watcher.stop()
    self.assertFalse(self.watcher.isRunning())