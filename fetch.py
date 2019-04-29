#!/usr/bin/python3
# encoding: utf-8

'''

Copyright (C) 2017  Steffen Volkmann

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''

import argparse
from Utils.Mobac import ExtractMapsFromAtlas
from Utils.Helper import ChartInfo
from tile.manager import TileManager, TileServer
from Utils.glog import getlog, initlog
from Utils.download import CheckExternelUtils
import time
import os
from config import OpenStreetMap, OpenSeaMap, OpenStreetMap_url, OpenSeaMap_url


def main():
    parser = argparse.ArgumentParser(description='fetch tiles')
    WDIR = os.getcwd() + '/work/'
    DBDIR = WDIR + "database/"
    parser.add_argument("-i",
                        help="MOBAC Project File",
                        dest="ProjectFile",
                        default="./sample/atlas/mobac/mobac-profile-testprj.xml")

    parser.add_argument("-d", "--DatabaseDirectory",
                        help="tile store directory",
                        dest="DBDIR",
                        default=DBDIR)

    parser.add_argument("-f", "--force",
                        action="store_true",
                        dest="force_download",
                        help="force download off tile")

    parser.add_argument("-q", "--quiet",
                        action="store_false",
                        dest="quiet",
                        default=True,
                        help="set log level to info (instead debug)")

    parser.add_argument("-s", "--skip",
                        action="store_true",
                        dest="skip_os",
                        help="skip odd zoom levels")

    args = parser.parse_args()

    initlog('fetch', args.quiet)
    logger = getlog()

    logger.info('Start fetch tiles')

    if(args.skip_os is True):
        zoom_filter = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
    else:
        zoom_filter = []

    # get maps from mobac project file
    if args.ProjectFile is not None:
        # get list of chart areas from project file
        atlas, name = ExtractMapsFromAtlas(args.ProjectFile, zoom_filter)
        logger.info('atlas name={} number of maps={}'.format(name, len(atlas)))
    else:
        exit()

    CheckExternelUtils()
    tm = TileManager(WDIR, args.DBDIR, args.force_download)

    TSOpenStreetMap = TileServer(OpenStreetMap, OpenStreetMap_url)
    TsOpenSeaMap = TileServer(OpenSeaMap, OpenSeaMap_url)

    logger.info('Fetch Open Sea Map tiles from {}'.format(TSOpenStreetMap.name))
    mapcnt = 1
    for singlemap in atlas:
        ti = ChartInfo(singlemap)
        logger.info('\n\nStart UpdateTile for street map {} / {}:'.format(mapcnt, len(atlas)))
        mapcnt += 1
        starttime = time.time()
        logger.info(ti)
        cnt = tm.UpdateTiles(TSOpenStreetMap, ti)
        stoptime = time.time()
        runtime = (stoptime - starttime)
        if runtime == 0:
            runtime = 1
        logger.info('time: {} s'.format(int(stoptime - starttime)))
        logger.info('tiles skipped          {}'.format(tm.tileskipped))
        logger.info('tiles merged           {}'.format(tm.tilemerged))
        logger.info('tiles mergedskipped    {}'.format(tm.tilemergedskipped))
        logger.info('tiles downloaded       {}'.format(tm.tiledownloaded))
        logger.info('tiles download skipped {}'.format(tm.tiledownloadskipped))
        logger.info('tiles download error   {}'.format(tm.tiledownloaderror))
        logger.info('processsed tiles/s     {0:.2f}'.format(cnt / runtime))

    logger.info('Fetch Open Sea Map tiles from {}'.format(TsOpenSeaMap.name))
    mapcnt = 1
    for singlemap in atlas:
        ti = ChartInfo(singlemap)
        logger.info('Start UpdateTile for sea map {} / {}:'.format(mapcnt, len(atlas)))
        mapcnt += 1
        starttime = time.time()
        logger.info(ti)
        cnt = tm.UpdateTiles(TsOpenSeaMap, ti)
        stoptime = time.time()
        runtime = (stoptime - starttime)
        if runtime == 0:
            runtime = 1
        logger.info('time: {} s'.format(int(stoptime - starttime)))
        logger.info('tiles skipped          {}'.format(tm.tileskipped))
        logger.info('tiles merged           {}'.format(tm.tilemerged))
        logger.info('tiles mergedskipped    {}'.format(tm.tilemergedskipped))
        logger.info('tiles downloaded       {}'.format(tm.tiledownloaded))
        logger.info('tiles download skipped {}'.format(tm.tiledownloadskipped))
        logger.info('tiles download error   {}'.format(tm.tiledownloaderror))
        logger.info('processsed tiles/s     {0:.2f}\n'.format(cnt / runtime))

    logger.info('\n\nready')

    return


if __name__ == "__main__":
    exit(main())
