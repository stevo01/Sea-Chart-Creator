#!/usr/bin/python3
# encoding: utf-8

import threading
import urllib.request
from tile.sqllitedb import TileSqlLiteDB
from Utils import __app_identifier__
from tile.Info import TileInfo
from Utils.glog import getlog
import time
import locale


class DownloadThread(threading.Thread):

    def __init__(self, tileman, force_download, DBDIR):
        threading.Thread.__init__(self)
        self.tileman = tileman

        self.force_download = force_download
        self.DBDIR = DBDIR
        self.stop = False

    def SetTileSrv(self, tileserv):
        self.tileserv = tileserv

    def run(self):
        #log = getlog()
        self.db = TileSqlLiteDB(self.DBDIR)

        while(self.stop is False):
            if len(self.tileman.joblist) is 0:
                self.stop = True
                break
            job = self.tileman.joblist[0]
            self.tileman.joblist.pop(0)
            # print("{} is working on job {} {} {} {}".format(self.name, job[0], job[1], job[2], job[3]))

            x = job[1]
            y = job[2]
            z = job[3]

            tile_osm2 = self.db.GetTile(self.tileserv.name, z, x, y)

            # skip download if tile is available
            if(tile_osm2 is not None) and (self.force_download is False):
                #print("skip update of tile z={} x={} y={} from {}".format(z, x, y, self.tileserv.name))
                self.tileman.tileskipped += 1
            # skip download if tile is newer the 7 days
            elif(tile_osm2 is not None) and (self.CheckTimespan(tile_osm2, 7 * 24) is False):
                #print("skip update of tile z={} x={} y={} from {}".format(z, x, y, self.tileserv.name))
                self.tileman.tileskipped += 1
            else:
                tile_osm2 = self._HttpLoadFile(self.tileserv, z, x, y, tile_osm2)
                if tile_osm2 is None:
                    return
                if (tile_osm2.updated is True) or (tile_osm2.date_updated is True):
                    self.db.StoreTile(self.tileserv.name, tile_osm2, z, x, y)
            self.tileman.tile += 1
        self.db.CloseDB()

    # load single file with http protocol
    def _HttpLoadFile(self, ts, z, x, y, tile=None):
        log = getlog()

        ret = None

        url = "{}/{}/{}/{}.png".format(ts.url, z, x, y)

        # set user agent to meet the tile usage policy
        # https://operations.osmfoundation.org/policies/tiles/
        # print("HttpLoadFile open {}".format(url))

        req = urllib.request.Request(url, data=None, headers={'User-Agent': __app_identifier__})

        if(tile is not None):
            req.add_header('If-None-Match', tile.etag)

        try:
            f = urllib.request.urlopen(req)
            data = f.read()
            date = f.headers['Date']
            lastmodified = f.headers['Last-Modified']
            etag = f.headers['ETag']
            ret = TileInfo(data, etag, date, lastmodified)
            ret.updated = True
            ret.date_updated = True
            self.tileman.tiledownloaded += 1
        except urllib.error.HTTPError as err:
            print("HTTPError: {}".format(err.code))

            if(err.code == 404):
                print("Error 404 / Not Found / url: {}".format(url))

            try:
                tile.date = err.headers['Date']
                ret = tile
                ret.date_updated = True
                if ret is not None:
                    ret.updated = False
                self.tileman.tiledownloadskipped += 1
            except Exception as e:
                print("Exception: {}".format(e))
                self.tileman.tiledownloaderror += 1
                ret = tile
                if ret is not None:
                    ret.updated = False
        except urllib.error.URLError as err:
            print("URLError: {}".format(err.reason))
            print("url: {}".format(url))
            self.tileman.tiledownloaderror += 1

        return ret

    '''
     @brief This method returns
            - True if Tile requires update
            - False if Tile requires no update

     @param tile - tile
     @param max_timespan - max time span (in hours)
    '''
    def CheckTimespan(self, tile, max_timespan):
        last_update = tile.date  # sample format Thu, 18 Apr 2019 07:01:25 GMT
        retv = True

        try:
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        except Exception as e:
            print('Error:', e)

        # https://www.journaldev.com/23365/python-string-to-datetime-strptime
        # %a Weekday as locale�s abbreviated name.                / Sun, Mon, �, Sat (en_US)
        # %d    Day of the month as a zero-padded decimal number. / 01, 02, �, 31
        # %b    Month as locale�s abbreviated name.               / Jan, Feb, �, Dec (en_US)
        # %H    Hour (24-hour clock) as a zero-padded decimal number.    01, 02, � , 23
        # %M    Minute as a zero-padded decimal number.    01, 02, � , 59
        # %S    Second as a zero-padded decimal number.    01, 02, � , 59
        # %m Month as a zero-padded decimal number.    01, 02 � 12
        # %Z    Time zone name (empty string if the object is naive).    (empty), UTC, IST, CST

        try:
            last_update = time.strptime(last_update, "%a, %d %b %Y %H:%M:%S %Z")
        except ValueError as e:
            print('ValueError:', e)
            return True

        diff = (time.time() - time.mktime(last_update)) / 3600

        if diff < max_timespan:
            retv = False
        else:
            retv = True

        return retv