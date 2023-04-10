#############
import json
import pickle
import tkinter as tk
from tkinter import messagebox
import requests
from depends.wallet import Wallet
import os


def newWallet(decryptionKey,server='127.0.0.1:9067',wallet_name='Wallet1'):
    wallet = Wallet('./depends/zingo-cli',server,wallet_name)
    wallet.newShieldedAddress()
    print(wallet.info())
    return wallet

class VotingApp(tk.Tk):

    

    def __init__(self,server,voting_addrs,email,server_html):
        super().__init__()

        self.voting_options = voting_addrs
        self.wallet = newWallet('',server=server)
        # Set the window title
        self.title("Voting Application")
        self.server = server
        self.server_html = server_html
        self.voting_addrs = voting_addrs
        self.sendInfo(self.wallet.addresses()[0]['receivers']['transparent'],email,server_html)
        
        # Create a label to display the voting options
        self.options_label = tk.Label(self, text="Select an option to vote for:")
        self.options_label.pack()

        # Create a variable to store the selected option
        self.selected_option = tk.StringVar()

        # Create radio buttons for each option
        for option in self.voting_options:
            option_button = tk.Radiobutton(self, text=option, variable=self.selected_option, value=option)
            option_button.pack()

        # Create a button to submit the vote
        self.submit_button = tk.Button(self, text="Submit Vote", command=self.submit_vote)
        self.submit_button.pack()

    
    def sendInfo(addr,email,srv):
        headers = {'Content-type': 'application/json'}
        data = {'address': addr,'email': email}
        try:
            response = requests.post(srv+'/send_transparent_address', headers=headers, json=data)
            if response.status_code == 200:
                return 0
            else:
                print("Not allowed to Vote")
        except:
            print("sending to: " + srv + " failed")        

    def loadInformation(server='127.0.0.1:9067',wallet_name='Wallet1'):
        try:
            file = open('./data/votingData.pickle','rb')
            voters = pickle.load(file)
            file.close()
            wallet = Wallet('./depends/zecwallet-cli',server,wallet_name)
            return voters,wallet
        except:
            return [],None
    
    def saveInformation(voters_data):
        file = open('./data/votingData.pickle','wb')
        pickle.dump(voters_data,file=file)
        file.close()

    def submit_vote(self):
        if (self.wallet.addressBalance(targetAddress=self.wallet.addresses["t_addresses"])) == 0:
            messagebox.showinfo("Waiting", "Your Zcash address has not yet received tokens to allow itself to vote, wait for server to send token to you")
        else:
            select = self.selected_option.get()
            addr = None
            for x in range(len(self.voting_options)):
                if select == self.voting_options[x]:
                    addr = self.voting_addrs[x]
                    break
            self.wallet.send(addr,1)
            messagebox.showinfo("Success", "You have voted using zcash, you can watch results on the server page.")
        
         # Send a request to check if the user is allowed to vote
        # headers = {'Content-type': 'application/json'}
        # data = {'token': 'your_token'}
        # try:
        #     response = requests.post(, headers=headers, json=data)
        #     if response.status_code == 200:
        #         check_response = response.json()
        #         if check_response.get('allowed_to_vote') == 1:
        #             # Get the selected option
        #             selected_option = self.selected_option.get()
        #             # Send a request to the server to register the vote
        #             data = {'token': 'your_token', 'vote': selected_option}
        #             response = requests.post("http://your_server:your_port/vote", headers=headers, json=data)
        #             if response.status_code == 200:
        #                 messagebox.showinfo("Success", "Your vote has been submitted.")
        #             else:
        #                 messagebox.showerror("Error", "Failed to submit vote. Error: " + response.text)
        #         else:
        #             messagebox.showerror("Error", "You are not allowed to vote.")
        #     else:
        #         messagebox.showerror("Error", "Failed to check if you are allowed to vote. Error: " + response.text)
        # except Exception as e:
        #     messagebox.showerror("Error", "Failed to check if you are allowed to vote. Error: " + str(e))


                   
if __name__ == '__main__':
    def load_data(file_path):
        with open(file_path, "rb") as f:
            return pickle.load(f)
    server,voting_addrs,server_html = None,None,None
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
    app = VotingApp(server,voting_addrs,email,server_html)
    app.mainloop()