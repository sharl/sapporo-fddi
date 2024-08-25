# -*- coding: utf-8 -*-
import time
import io
import binascii
import threading
import re
import webbrowser

import schedule
from pystray import Icon, Menu, MenuItem
from PIL import Image
import requests
from win11toast import notify

INTERVAL = 60
URL = 'http://www.119.city.sapporo.jp/saigai/sghp.html'


class taskTray:
    def __init__(self):
        self.running = False
        self.body = ''

        self.normal_icon = Image.open(io.BytesIO(binascii.unhexlify(ICON.replace('\n', '').strip())))
        self.amb_icon = Image.open(io.BytesIO(binascii.unhexlify(AMB.replace('\n', '').strip())))
        menu = Menu(
            MenuItem('Open', self.doOpen, default=True, visible=False),
            MenuItem('Exit', self.stopApp),
        )
        self.app = Icon(name='PYTHON.win32.sapporo-fddi', title='sapporo fire department dispatch information', icon=self.normal_icon, menu=menu)
        self.doCheck()

    def doOpen(self):
        webbrowser.open(URL)

    def doCheck(self):
        r = None
        try:
            r = requests.get(URL)
        except Exception:
            pass
        if r and r.status_code == 200:
            content = r.content.decode('utf-8')
            m = re.search(r'(?s)<h2>現在の災害出動</h2>(.*?)出動中の災害は以上です', content)
            if m:
                match = m.group(1).replace('<BR>', '').replace('\u3000', '').split('\u25cf')[1:]
                lines = []
                for t in match:
                    lines.append(t.strip())
                body = '\r\n'.join(lines)
                if self.body != body:
                    self.body = body
                    notify(self.body)
                image = self.amb_icon
            else:
                self.body = '現在出動中の災害はありません'
                image = self.normal_icon
        self.app.title = self.body
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
89504e470d0a1a0a0000000d4948445200000010000000100803000000282d0f530000000467414d410000b18f0bfc6105000000206348524d00007a
26000080840000fa00000080e8000075300000ea6000003a98000017709cba513c00000186504c5445000000b30000ca0000e87568e74432ebebeb0d
0d0d272727010101c10000cd0000cc0000e87265e58075e5a49de8e0e0eaeaeae8e8e8eaecece8b5b0e55849e45a4bffffffc9bcbbc4b4b2d0b2aefd
ffff282a2a000000d9d9d9b9babab0b1b1f6f6f6302928898483dbd9d9bebcbcedebebdab0acd8aeaae2bbb6e5bebaeceae9e9e5e5e6e2e2e5e1e0e7
e3e3e5e1e1e7e3e2eae6e6edeae9e7e7e7e7e7e7e2e2e2b0b0b0a2a2a2d6d6d6e6e6e6c3c3c39e9e9ec5c5c5eaeaeaededede3e3e3e6e6e6cccccc97
9797a6a6a6a8a8a8e8e8e8e6e6e6e5e5e5e2e2e2949494959595e3e3e3e6e6e6f2f2f2ffffff696969787878808080646464e6e6e66e6e6e8383836d
6d6debebeb0b0b0b0d0d0d070707060606d1cdcdc8c8c8b6b6b6cacacac5c5c5b6acabb7918da9aaaabbbbbb8c8c8c6464648f8f8f84848466666667
6969c9c7c7bebcbccccaca9e9c9b787676a09e9e9694947a78787b7979e2bdb9e2bbb7e3bdb9deb8b4d9b2addfb9b5ddb7b3d9b2aee5e2e1e6e2e2e6
e6e6e5e5e5acacacffffff8ac838dd0000005c74524e530000000000000000000101010e6c9e8d8a8a8a8a8a3d0171fbb40a010142e7e1280859cef2
441fc9f85444f2fbf9fdf8fef95659faf7dadaeafedfdbe1f44c42a9a5e5fcb0aeb0b1a9cac79a27010309769d22044caa460102030101e3c5d34400
000001624b4744167cd1a8190000000774494d4507e808180c0f27b896573e000000b94944415418d363602006307272713321f1997978f9f8050404
058584454459181858c5c4256262e3e2e213e2129324a518a46564e5925352d3d2d233d232b3e41518149594b37372f3f2f30b0af38b8a555419d4d4
4b4a4bcbca2b2a2aab2aaaab353419b4b46b74746b6a6a6b6b6af5f40d0c8d188c4d4ccdcc2deaeaeaea2dadac6d6ced18ec1d1c9d9c5d5cdddcdc3d
3c1bbcbc7d187cfdfc030283fc828383fd4242c3c4c2810e638b8864073990232a329a289fa10300eb692a09b4930abd000000257445587464617465
3a63726561746500323032342d30382d32345430333a31353a35372b30393a303033b3331d0000002574455874646174653a6d6f6469667900323032
342d30382d32345430333a31353a33392b30393a3030d4bef97b0000000049454e44ae426082
"""

AMB = """
89504e470d0a1a0a0000000d4948445200000010000000100803000000282d0f530000000467414d410000b18f0bfc6105000000206348524d00007a
26000080840000fa00000080e8000075300000ea6000003a98000017709cba513c0000016b504c5445e16255e06255e16154e06053e05f52e06154e0
6254e06d61e28a81e4a7a1e5aba5e4aaa4e5aaa4e5aca6e48f86e35c4ed48880c4b3b1d1cfcfc8cacab5b7b7caccccc5c7c7b5b7b8b5aeadb6938fd3
9993e1675bdf6053dd7f76bcb1b0a8aaaabbbbbb8c8c8c6464648f8f8f848484666666666969b4a7a6e2786ddb6053bf6c63dbc1bec9c9c9bebcbccc
caca9e9c9b787676a09e9e9694947a78787b7979bfb7b6e2857cde6a5ed89d97e2bebae2bbb7e3bdb9deb8b4d9b2addfb9b5ddb7b3d9b2aedab3aee1
b8b3e17f75e1857be7dfdee5e2e2e5e0dfe4dddde5e2e1e6e2e2e7e2e2e5dddce9e3e2e09087e6e6e6e1dfdfb4a3a2a89795d5cdcce6e9e9e6e8e8e5
e8e8e6e7e7c4b6b4a59492c6b8b7e8e5e5df8278e0b7b3d0a5a09e9291a5a6a6b8928ee6bdb9e4bcb8e4bdb9e0b6b1a28986abafafa38986e0afaae0
756ae06256dc6155af6b64a4746fd06156e16457e16357e16356be655ca27773c0645bde6053dd6053ffffff0e030bfd00000001624b474478d6dbe4
460000000774494d4507e8081916001c2708e316000000c04944415418d363602002303231b33043002b03135080898d9d83938b8b9b87978f9f8511
c8671010141216111115139790949266609591959357505452525651525553d760d0d4d2d6d1d5d33730303432303631356330b7b0b4b2b2b6b1b5b5
b3b7757074726670717573f7f0f4f4f2f2f4f2f6f1f2e563f0f30f080c0a0e090d0d0b8f888c8ae66088898d8b4f484c4a4e4e494d4bcfc8cc6260cc
cec9cdcb2f282c2c2c2a2e2965003a8d8989b58c8915089898ca811c90d389f11f1200004f0e20d2a4c385670000002574455874646174653a637265
61746500323032342d30382d32355431333a30303a33332b30393a303015537aea0000002574455874646174653a6d6f6469667900323032342d3038
2d32355431333a30303a32382b30393a3030aaa396320000000049454e44ae426082
"""

if __name__ == '__main__':
    taskTray().runApp()
