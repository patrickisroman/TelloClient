
## Tello Client

Easy Tello client for connecting to Tello & issuing commands

    import tello_connect
    
    client = TelloClient()
    client.start()
    cmd, rsp = client.send_command('command')
    
    # cmd = 'command'
    # rsp = 'ok'
