# -*- coding: utf-8 -*-
import asyncio
import binascii
import ctypes
import io
import json
import re
import threading
import time
import webbrowser
import winsound as ws

from PIL import Image
from bs4 import BeautifulSoup as bs
from pystray import Icon, Menu, MenuItem
from win11toast import notify
import darkdetect as dd
import requests
import schedule
import winsdk.windows.devices.geolocation as wdg

from utils import resource_path

INTERVAL = 60
TITLE = 'sapporo fire department dispatch information'
URL = 'https://www.119.city.sapporo.jp/saigai/sghp.html'

PreferredAppMode = {
    'Light': 0,
    'Dark': 1,
}
# https://github.com/moses-palmer/pystray/issues/130
ctypes.windll['uxtheme.dll'][135](PreferredAppMode[dd.theme()])


def check():
    NONDISPATCH = '現在出動中の災害はありません'
    dispatches = {
        # '札幌市': {
        #     火災出動: [],
        #     車両火災出動: [],
        #     救助出動: [],
        #     水難救助出動: [],
        #     警戒出動: [],
        #     ガス漏れ出動: [],
        #     救急隊支援出動: [],
        # }
    }
    with requests.get(URL) as r:
        soup = bs(r.content.decode('utf-8'), 'html.parser')
        contents = soup.find(id='tmp_contents').text.replace(' 付近', '付近').split('現在の')[1].split('\u3007')[1:]
        # parse
        for c in contents:
            city, _contents = c.split('\r\n', 1)
            for d in _contents.strip().replace(NONDISPATCH, '').strip().split('\u25cf'):
                if d:
                    ls = d.split()
                    if city not in dispatches:
                        dispatches[city] = {}
                    dispatches[city][ls[0]] = ls[1:]

    return dispatches


class taskTray:
    def __init__(self):
        self.running = False
        self.body = ''
        self.ward = self.getNearWard()
        self.use_filter = False

        self.normal_icon = Image.open(io.BytesIO(binascii.unhexlify(ICON.replace('\n', '').strip())))
        self.amb_icon = Image.open(io.BytesIO(binascii.unhexlify(AMB.replace('\n', '').strip())))
        menu = self.buildMenu()
        self.app = Icon(name='PYTHON.win32.sapporo-fddi', title=TITLE, icon=self.normal_icon, menu=menu)
        self.doCheck()

    def buildMenu(self, locations=[]):
        item = [
            MenuItem('Open', self.doOpen, default=True, visible=False),
            MenuItem(self.ward, self.on_clicked, checked=lambda _: self.use_filter),
            Menu.SEPARATOR,
        ]
        for loc in locations:
            if loc:
                if loc.startswith('\u30fb'):
                    item.append(MenuItem(loc, self.openMap))
                else:
                    item.append(MenuItem(loc, lambda _: False))
        item.append(Menu.SEPARATOR)
        item.append(MenuItem('Exit', self.stopApp))
        return Menu(*item)

    def doOpen(self):
        webbrowser.open(URL)

    def openMap(self, _, item):
        m = re.match(r'・(.*?)（', str(item))
        if m:
            webbrowser.open('https://maps.google.com/?q=' + m.group(1).replace('付近', ''))

    async def getCoords(self):
        locator = wdg.Geolocator()
        pos = await locator.get_geoposition_async()
        return [pos.coordinate.latitude, pos.coordinate.longitude]

    def getLoc(self):
        try:
            return asyncio.run(self.getCoords())
        except Exception as e:
            print(e)

    def getNearWard(self):
        lat, lng = self.getLoc()
        url = f'https://geoapi.heartrails.com/api/json?method=searchByGeoLocation&x={lng}&y={lat}'
        with requests.get(url) as r:
            loc = json.loads(r.content.decode('utf-8'))['response']['location'][0]
            return loc['city'].replace('札幌市', '')
        return ''

    def on_clicked(self, _, __):
        self.use_filter = not self.use_filter
        self.doCheck()

    def doCheck(self):
        image = self.normal_icon
        dispatches = {}
        try:
            dispatches = check()
        except Exception as e:
            print(e)

        lines = []
        for city in dispatches:
            lines.append(city)
            for dispatch in dispatches[city]:
                lines.append(dispatch)
                for location in dispatches[city][dispatch]:
                    lines.append(location)

        body = '\n'.join(lines)
        if body:
            if self.body != body:
                notify(
                    title=body,
                    # app_id=TITLE,
                    audio={'silent': 'true'},
                )
                ws.PlaySound(resource_path('Assets/ambulance.wav'), ws.SND_FILENAME)
            if (self.use_filter and self.ward in body) or (not self.use_filter):
                image = self.amb_icon
            # buile title
            ward = self.ward
            lines = []
            for city in dispatches:
                for dispatch in dispatches[city]:
                    for location in dispatches[city][dispatch]:
                        if '\uff08' in location:
                            location = location[:location.index('\uff08')]
                        if (self.use_filter and ward in location) or (not self.use_filter):
                            for w in ['市', '区']:
                                if w in location:
                                    location = location[location.index(w) + 1:]
                            tmp = '\n'.join(lines + [location])
                            tmpl = len(tmp)
                            print(tmpl, tmp)
                            # ValueError: string too long (nnn, maximum length 128)
                            if tmpl > 128:
                                lines.append('...')
                                break
                            else:
                                lines.append(location.replace('\u30fb', ''))
            self.app.title = '\n'.join(lines)
            self.body = body
        else:
            self.app.title = body

        if self.use_filter and not self.app.title:
            self.app.title = self.body = f'現在{self.ward}に出動中の災害はありません'
        if not self.app.title:
            self.app.title = self.body = '現在出動中の災害はありません'

        self.app.menu = self.buildMenu(self.body.split('\n'))
        self.app.icon = image
        self.app.update_menu()

    def runSchedule(self):
        schedule.every(INTERVAL).seconds.do(self.doCheck)

        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def stopApp(self):
        self.running = False
        self.app.stop()

    def runApp(self):
        self.running = True

        task_thread = threading.Thread(target=self.runSchedule)
        task_thread.start()

        self.app.run()


ICON = """
89504e470d0a1a0a0000000d4948445200000010000000100803000000282d0f53000000206348524d00007a26000080840000fa00000080e8000075
300000ea6000003a98000017709cba513c00000186504c5445000000b30000ca0000e87568e74432ebebeb0d0d0d272727010101c10000cd0000cc00
00e87265e58075e5a49de8e0e0eaeaeae8e8e8eaecece8b5b0e55849e45a4bffffffc9bcbbc4b4b2d0b2aefdffff282a2a000000d9d9d9b9babab0b1
b1f6f6f6302928898483dbd9d9bebcbcedebebdab0acd8aeaae2bbb6e5bebaeceae9e9e5e5e6e2e2e5e1e0e7e3e3e5e1e1e7e3e2eae6e6edeae9e7e7
e7e7e7e7e2e2e2b0b0b0a2a2a2d6d6d6e6e6e6c3c3c39e9e9ec5c5c5eaeaeaededede3e3e3e6e6e6cccccc979797a6a6a6a8a8a8e8e8e8e6e6e6e5e5
e5e2e2e2949494959595e3e3e3e6e6e6f2f2f2ffffff696969787878808080646464e6e6e66e6e6e8383836d6d6debebeb0b0b0b0d0d0d0707070606
06d1cdcdc8c8c8b6b6b6cacacac5c5c5b6acabb7918da9aaaabbbbbb8c8c8c6464648f8f8f848484666666676969c9c7c7bebcbccccaca9e9c9b7876
76a09e9e9694947a78787b7979e2bdb9e2bbb7e3bdb9deb8b4d9b2addfb9b5ddb7b3d9b2aee5e2e1e6e2e2e6e6e6e5e5e5acacacffffff8ac838dd00
00005c74524e530000000000000000000101010e6c9e8d8a8a8a8a8a3d0171fbb40a010142e7e1280859cef2441fc9f85444f2fbf9fdf8fef95659fa
f7dadaeafedfdbe1f44c42a9a5e5fcb0aeb0b1a9cac79a27010309769d22044caa460102030101e3c5d34400000001624b4744167cd1a81900000007
74494d4507e90a04051117ee8c0b20000000b94944415418d363602006307272713321f1997978f9f8050404058584454459181858c5c4256262e3e2
e213e2129324a518a46564e5925352d3d2d233d232b3e41518149594b37372f3f2f30b0af38b8a555419d4d44b4a4bcbca2b2a2aab2aaaab353419b4
b46b74746b6a6a6b6b6af5f40d0c8d188c4d4ccdcc2deaeaeaea2dadac6d6ced18ec1d1c9d9c5d5cdddcdc3d3c1bbcbc7d187cfdfc030283fc828383
fd4242c3c4c2810e638b8864073990232a329a289fa10300eb692a09b4930abd0000000049454e44ae426082
"""

AMB = """
89504e470d0a1a0a0000000d4948445200000010000000100803000000282d0f53000000206348524d00007a26000080840000fa00000080e8000075
300000ea6000003a98000017709cba513c0000016b504c5445e16255e06255e16154e06053e05f52e06154e06254e06d61e28a81e4a7a1e5aba5e4aa
a4e5aaa4e5aca6e48f86e35c4ed48880c4b3b1d1cfcfc8cacab5b7b7caccccc5c7c7b5b7b8b5aeadb6938fd39993e1675bdf6053dd7f76bcb1b0a8aa
aabbbbbb8c8c8c6464648f8f8f848484666666666969b4a7a6e2786ddb6053bf6c63dbc1bec9c9c9bebcbccccaca9e9c9b787676a09e9e9694947a78
787b7979bfb7b6e2857cde6a5ed89d97e2bebae2bbb7e3bdb9deb8b4d9b2addfb9b5ddb7b3d9b2aedab3aee1b8b3e17f75e1857be7dfdee5e2e2e5e0
dfe4dddde5e2e1e6e2e2e7e2e2e5dddce9e3e2e09087e6e6e6e1dfdfb4a3a2a89795d5cdcce6e9e9e6e8e8e5e8e8e6e7e7c4b6b4a59492c6b8b7e8e5
e5df8278e0b7b3d0a5a09e9291a5a6a6b8928ee6bdb9e4bcb8e4bdb9e0b6b1a28986abafafa38986e0afaae0756ae06256dc6155af6b64a4746fd061
56e16457e16357e16356be655ca27773c0645bde6053dd6053ffffff0e030bfd00000001624b474478d6dbe4460000000774494d4507e90a0405122b
eace2464000000c04944415418d363602002303231b33043002b03135080898d9d83938b8b9b87978f9f8511c8671010141216111115139790949266
609591959357505452525651525553d760d0d4d2d6d1d5d33730303432303631356330b7b0b4b2b2b6b1b5b5b3b7757074726670717573f7f0f4f4f2
f2f4f2f6f1f2e563f0f30f080c0a0e090d0d0b8f888c8ae66088898d8b4f484c4a4e4e494d4bcfc8cc6260cccec9cdcb2f282c2c2c2a2e2965003a8d
8989b58c8915089898ca811c90d389f11f1200004f0e20d2a4c385670000000049454e44ae426082
"""

if __name__ == '__main__':
    taskTray().runApp()
