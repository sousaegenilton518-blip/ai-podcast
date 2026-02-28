import urllib.request, json, base64, websocket, threading, time, sys

target_id = '43C0CAC08D9D925FB59BCA992CAC8FA8'
ws_url = f'ws://127.0.0.1:18800/devtools/page/{target_id}'
out_path = 'C:/Users/鸢尾花/.openclaw/workspace/ai-news-card.png'

result = {}
done = threading.Event()

def on_message(ws, message):
    msg = json.loads(message)
    if msg.get('id') == 10:
        # got clip coords
        r = msg['result']['result']['value']
        clip = json.loads(r)
        ws.send(json.dumps({'id':20,'method':'Page.captureScreenshot','params':{
            'format':'png',
            'clip':{'x':clip['x'],'y':clip['y'],'width':clip['width'],'height':clip['height'],'scale':2}
        }}))
    elif msg.get('id') == 20:
        data = msg['result']['data']
        with open(out_path, 'wb') as f:
            f.write(base64.b64decode(data))
        print('saved:', out_path)
        done.set()
        ws.close()

def on_open(ws):
    time.sleep(0.5)
    ws.send(json.dumps({'id':10,'method':'Runtime.evaluate','params':{
        'expression': '''
            (function(){
                var el = document.querySelector(".card");
                var r = el.getBoundingClientRect();
                return JSON.stringify({x: r.left, y: r.top, width: r.width, height: r.height});
            })()
        ''',
        'returnByValue': True
    }}))

ws = websocket.WebSocketApp(ws_url, on_message=on_message, on_open=on_open)
t = threading.Thread(target=ws.run_forever)
t.daemon = True
t.start()
done.wait(timeout=15)
if not done.is_set():
    print('timeout')
    sys.exit(1)
