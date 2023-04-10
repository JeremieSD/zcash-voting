import time
from flask import Flask,render_template,request, redirect,session,url_for
from multiprocessing import Process
import random
from depends.wallet import Wallet
from src.zcash import Zcash
from src.zcash_cli import ZcashCLI
from src.lightwalletserver import LightwalletServer
import requests
import pickle
from src.voters import Voter
import configparser
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import json
import plotly.express as px
import pandas as pd
import os

zcashcli = None
def newWallet(decryptionKey,server='127.0.0.1:9067',wallet_name='Wallet1'):
    wallet = Wallet('./depends/zingo-cli',server,wallet_name)
    wallet.newShieldedAddress()
    voting_shielded_addresses = wallet.addresses()
    voting_shielded_addresses = [x['receivers']['sapling'] for x in voting_shielded_addresses]
    voting_shielded_addresses = list(filter(lambda x: x is not None,voting_shielded_addresses))
    print(voting_shielded_addresses)
    return wallet,voting_shielded_addresses


def loadInformation(server='127.0.0.1:9067',wallet_name='Wallet1'):
    try:

        file = open('./data/votingData.pickle','rb')
        voters = pickle.load(file)
        file.close()
        print("Loaded Voters")
        wallet = Wallet('./depends/zingo-cli',server,wallet_name)
        print("Loaded Wallet")
        voting_shielded_addresses = wallet.addresses()
        voting_shielded_addresses = [x['receivers']['sapling'] for x in voting_shielded_addresses]
        voting_shielded_addresses = list(filter(lambda x: x is not None,voting_shielded_addresses))
        return voters,wallet,voting_shielded_addresses
    except:
        return [],None,None

def saveInformation(voters_data):
    file = open('./data/votingData.pickle','wb')
    pickle.dump(voters_data,file=file)
    file.close()

def sendEmail(email, message, data={}):
    
    msg = MIMEMultipart()
    msg['From'] = config['admin']['email']
    msg['To'] = email
    msg['Subject'] = "Zcash Voting"
    msg.attach(MIMEText(message))

    if data != {}:
        pickle_attachment = MIMEApplication(pickle.dumps(data))
        pickle_attachment.add_header('content-disposition', 'attachment', filename='data.pkl')
        msg.attach(pickle_attachment)
    server = smtplib.SMTP(config['admin']['emailSmtp'])
    server.starttls()
    server.login(config['admin']['email'], config['admin']['appPasswordEmail'])
    server.send_message(msg)
    server.quit()

def validateUserCredentials(username, password):
    for x in voters:
        if username == x.getEmail and x.checkPassword(password):
            return True
    return False

def updateBlockChain():
    zcashcli.generate('60')
    while True:
        time.sleep(600)
        print(zcashcli.generate('10'))
    
config = configparser.ConfigParser()
config.read('./config/admin.conf')
print("Starting Zcash")
zcash = Zcash()
time.sleep(40)
print("Starting LightWallet Server")
lightwalletserver = LightwalletServer()
time.sleep(20)
print("Starting Zcash CLI and Blockchain updates")
zcashcli = ZcashCLI()
process = Process(target=updateBlockChain)
process.start()
voters,myWallet,voting_shielded_addresses = loadInformation(server=config['serverInfo']['server'])
voting_options = config['admin']['votingOptionA'], config['admin']['votingOptionB']
voting_period = True
if myWallet == None:
    myWallet,voting_shielded_addresses = newWallet("",server=config['serverInfo']['server'])
## Lightclient's server version works with ipv4 atm
ip = requests.get('https://v4.ident.me/').text.strip()+':9067'
ip2 = requests.get('https://v4.ident.me/').text.strip()+':5000'
print(ip)
print(voting_shielded_addresses)
try:
    


    app = Flask(__name__)
    app.config['SESSION_TYPE'] = 'memcached'
    app.secret_key = 'super secret key'
    app.debug = True

    @app.route('/verifytx',methods=['POST','GET'])
    def verifytx():
        if request.method == 'GET':
            return render_template('verifytx.html')
        elif request.method == 'POST':
            tx = request.form['tx']
            try:
                int(tx,16)
                tx = zcashcli.getTx(tx)
            except ValueError:
                return "Vote has not been verified"
            if tx == None:
                return "Vote has not been verified"
            else:
                return "Vote has been verified. \nTransaction returns: " + str(tx)
    

    @app.route("/")
    def main_page():
        session['adminPerms'] = False
        return render_template('login.html')

    @app.route('/wait_approval')
    def wait_approval():
        return render_template('wait.html')

    @app.route('/results')
    def results():
        print("Results")
        print(myWallet.balance()[1]['z_addresses'][0]['address'] + ':' +str(myWallet.balance()[1]['z_addresses'][0]['zbalance']))
        print(myWallet.balance()[1+3]['z_addresses'][0]['address'] + ':' +str(myWallet.balance()[1+3]['z_addresses'][0]['zbalance']))
        ###calling directly because zingolib is slightly weirder to work with in this circumstance compared to zecwallet
        balances = [myWallet.balance()[1]['z_addresses'][0]['zbalance'], myWallet.balance()[1+3]['z_addresses'][0]['zbalance']]
        
        x_ = list(voting_options)
        df = pd.DataFrame(
            {
                "Options":x_,
                "Votes":balances,
                "Color":['red','blue']
            }
        )
        fig = px.bar(data_frame=df,x="Options",y="Votes",color="Color")
        fig.update_layout(title='Zcash voting Results')
        plot = fig.to_json()
        return render_template('result.html',plot=plot)


    @app.route('/login', methods=['POST'])
    def login():
        username = request.form['username']
        password = request.form['password']
        if username == config['admin']['username'] and password == config['admin']['password']:
            session['adminPerms'] = True
            if voting_period == True:
                return redirect(url_for('review_applications'))
            else:
                return redirect(url_for('results'))
        elif (validateUserCredentials(username,password)):
            if voting_period == True:
                return redirect('review_applications')
            else:
                return redirect('results')
        else:
            return 'Invalid credentials'

    @app.route('/review_applications')
    def review_applications():
        # code to get all the pending applications from the database
        # loop through the applications and render them on the page
        if voting_period == False:
            return redirect('results')

        return render_template('review_applications.html', applications=voters)

    @app.route('/accept_application/<app_id>')
    def accept_application(app_id):
        if session['adminPerms'] == True:
            email = None
            for x in voters:
                if x.getEmail() == app_id:
                    x.setVerified()
                    email = x.getEmail()
                    break
            data = zip(voting_options,voting_shielded_addresses)
            email_send_data = {}
            email_send_data['server'] = ip
            email_send_data['data'] = data
            email_send_data['email'] = email
            email_send_data['html_server'] = ip2
            sendEmail(email, 'Place in main directory of voting application', email_send_data)
            return redirect(url_for('review_applications'))

    @app.route('/reject_application/<app_id>')
    def reject_application(app_id):
        if session['adminPerms'] == True:
            email = None
            for x in voters:
                if x.getEmail() == app_id:
                    email = x.getEmail()
                    voters.remove(x)
                    break
            sendEmail(email, 'You have been not allowed to vote by the admin.')
            return redirect(url_for('review_applications'))

    @app.route('/send_transparent_address', methods=['POST'])
    def send_transparent_address():
        data = request.get_json()
        email = data['email']
        address = data['address']
        print("Received json for voting")
        for x in voters:
            if x.getEmail() == email and x.getVerificationForVote() and x.getTransparentAddress() == None:
                x.setTransparentAddress(address)
                return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 
            elif x.getEmail() == email and x.getVerificationForVote() and x.getTransparentAddress() == address:
                return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 
        return json.dumps({'success':False}), 401, {'ContentType':'application/json'} 

    @app.route('/update_chain')
    def update_chain():
        zcashcli.generate("10")
        return "Block Updated"

    @app.route('/create_user', methods=['POST','GET'])
    def create_user():
        if request.method == 'GET':
            return render_template('home.html')
        elif request.method == 'POST':
            name = request.form['name']
            email = request.form['email']
            password = request.form['password']
            voter = Voter(email=email,name=name)
            voter.setPassword(password)
            voters.append(voter)
            return redirect(url_for('wait_approval'))

    @app.route('/send_to_users')
    def send_to_users():
        if session['adminPerms'] == True:
            zcashcli.generate("1")
            print("Hello")
            for x in voters:
                if x.getVerificationForVote() and x.getTransparentAddress() != None:
                    time.sleep(10)
                    # myWallet.send(x.getTransparentAddress(),1)
                    print(zcashcli.send(x.getTransparentAddress(),1))
                    zcashcli.generate("1")
            global voting_period
            voting_period = False
            return redirect(url_for('results'))

            
    app.run()


except KeyboardInterrupt:
    print("Closing and Saving Information")
    saveInformation(voters)
    os._exit(1)