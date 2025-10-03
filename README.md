# sapporo-fddi

札幌市消防出動情報 http://www.119.city.sapporo.jp/saigai/sghp.html を利用して、タスクトレイに常駐して災害出動を通知

該当ページのフォーマット変更により

- 札幌市
- 江別市
- 千歳市
- 恵庭市
- 北広島市
- 石狩北部地区

に対応できました

HeartRails 様の [「HeartRails Geo API」(HeartRails Inc.)](https://geoapi.heartrails.com/) を使用しています。

出典:[「位置参照情報」(国土交通省)](https://nlftp.mlit.go.jp/)の加工情報・[「HeartRails Geo API」(HeartRails Inc.)](https://geoapi.heartrails.com/)

## Run

```
git clone https://github.com/sharl/sapporo-fddi.git
cd sapporo-fddi
pip install -r requirements.txt
python sapporo-fddi.py
```
