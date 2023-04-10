from decimal import Decimal
from json import loads
from subprocess import PIPE, Popen


class LightwalletServer:

    def __init__(self) -> None:
        self._sp = Popen(['./depends/lightwalletd', '--no-tls-very-insecure',
                         '--zcash-conf-path', './data/zcash/zcash.conf',
                         '--log-file','./data/lightwallet/lightwallet.log',
                         '--config','./config/lightwalletd.yml',
                         '--data-dir','./data/lightwallet/'], stdout=PIPE, stdin=PIPE)
        # self._readOutput()


    
    def _fetchResult(self):
        rawOutput = self._readOutput()
        loadableOutput = ''

        jsonStarted = False
        for line in rawOutput.split('\n'):
            if (line):
                if ((line[0] == '{') or (line[0] == '[')):
                    jsonStarted = True
                if (jsonStarted):
                    loadableOutput += (line + '\n')
                    if ((line[0] == '}') or (line[0] == ']')):
                        break

            return loads(loadableOutput, parse_float=Decimal, parse_int=Decimal)

    def _readOutput(self):
        output = ''
        while (True):
            outputLine = self._sp.stdout.readline().decode()
            output += outputLine
            if ((not (outputLine)) or (outputLine[0] == '}') or (outputLine[0] == ']') or (outputLine[0:2] == '[]')):
                return output

    def _sendCommand(self, command):
        command = (command.encode('utf-8') + b'\n')
        self._sp.stdin.write(command)
        self._sp.stdin.flush()
