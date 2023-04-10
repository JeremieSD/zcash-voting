import json
import pickle
import time
import requests
from depends.wallet import Wallet
import os


def newWallet(server='127.0.0.1:9067', wallet_name='Wallet1'):
    wallet = Wallet('./depends/zingo-cli', server, wallet_name)
    return wallet


def sendInfo(addr, email, srv):
    headers = {'Content-type': 'application/json'}
    data = {'address': addr, 'email': email}
    ##comment line below if flask app is production
    srv = 'http://127.0.0.1:5000'
    try:
        print("response before")
        response = requests.post(srv+'/send_transparent_address', headers=headers, json=data)
        print("response sent")
        if response.status_code == 200:
            return 0
        else:
            print("Not allowed to Vote")
    except:
        print("sending to: " + srv + " failed")


def loadInformation(server='127.0.0.1:9067', wallet_name='Wallet1'):
    try:
        file = open('./data/votingData.pickle', 'rb')
        voters = pickle.load(file)
        file.close()
        wallet = Wallet('./depends/zecwallet-cli', server, wallet_name)
        return voters, wallet
    except:
        return [], None


def saveInformation(voters_data):
    file = open('./data/votingData.pickle', 'wb')
    pickle.dump(voters_data, file=file)
    file.close()


def submit_vote(selected_option, wallet):
    if (wallet.balance()[2]['t_addresses'][0]["balance"]) == 0:
        print("Your Zcash address has not yet received tokens to allow itself to vote, wait for server to send token to you")
    else:
        addr = selected_option
        print(addr)
        wallet.shield()
        print("Waiting 1 mins for blockchain to update")
        time.sleep(60)
        txid = wallet.send(addr, "1")
        tx = txid['txid']
        print(tx)
        file = open('./data/tx.txt', 'w')
        file.write(tx)
        file.close()
        print("You have voted using zcash, you can watch results on the server page. \nTransaction ID is present in a file called tx.txt. \nCopy and paste it into " + server_html + '/vertifytx, to verify that you\'re vote counted.')
        print("Go to " + server_html + '/results, to see results, may take some time to update.')

if __name__ == '__main__':
    def load_data(file_path):
        with open(file_path, "rb") as f:
            return pickle.load(f)

    server, voting_addrs, server_html = None, None, None
    try:
        data = load_data('./data.pkl')
        server = data['server']
        voting_addrs = list(data['data'])
        email = data['email']
        server_html = data['html_server']
        print(server)
        print(voting_addrs)
        print(email)
        print(server_html)
    except:
        print("File Not Found, Need Information before voting")
        os._exit(1)

    # wallet = newWallet(wallet_name=email,server=server)
    wallet = newWallet(wallet_name=email)
    wallet.sync()
    print(wallet.addresses())
    sendInfo(wallet.addresses()[0]['receivers']['transparent'], email, server_html)
    voting_options = []
    for i, option in enumerate(voting_addrs):
        voting_options.append(f"{i}: {option}")

    # Print voting options
    print("Select an option to vote for:")
    for option in voting_options:
        print(option)

    # Get user input for selected option
    selection = input()

    try:
        (name,selected_option) = voting_addrs[int(selection)]
    except:
        print("Invalid selection. Please enter a valid option number.")
        os._exit(1)

    submit_vote(selected_option, wallet)
