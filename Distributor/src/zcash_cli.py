import subprocess
import json
class ZcashCLI:
    def __init__(self, rpcuser='xxxxxx', rpcpassword='xxxxxx', host="127.0.0.1", port=8232):
        self.rpcuser = rpcuser
        self.rpcpassword = rpcpassword
        self.host = host
        self.port = port

    
    def execute_command(self, command):
        """
        Executes the given command using zcash-cli and returns the output as a string
        """
        rpc_connection = f'http://{self.rpcuser}:{self.rpcpassword}@{self.host}:{self.port}'
        full_command = f"./depends/zcash-cli -regtest -rpcuser={self.rpcuser} -rpcpassword={self.rpcpassword} {command}"
        
        try:
            output = subprocess.check_output(full_command, shell=True)
            output = output.decode('utf-8').strip()
            try:
                return json.loads(output)
            except:
                try:
                    return list(output)
                except:
                    return output
        except subprocess.CalledProcessError as e:
            print(f"Command execution failed with error: {e}")
            return None
    
    def generate(self,zec):
        return self.execute_command('generate '+ zec)


    def send(self,addr,zec='1'):
        return self.execute_command('sendtoaddress '+ addr + ' ' + str(zec))


    def getBlockchainInfo(self):
        return self.execute_command('getblockchaininfo')

    def getTxProof(self,proof):
        return self.execute_command('verifytxoutproof ' + proof)
    
    def getTx(self,tx):
        return self.execute_command('getrawtransaction ' + tx + ' 1')
    
